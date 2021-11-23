import os
import posixpath
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict

from botocore.credentials import Credentials
from sceptre.connection_manager import ConnectionManager
from sceptre.template_handlers import TemplateHandler


class SamInvoker:
    def __init__(
        self,
        connection_manager: ConnectionManager,
        sam_directory: Path,
        *,
        environment_variables: Dict[str, str] = os.environ,
        run_subprocess=subprocess.run
    ):
        """A utility for invoking SAM commands using subprocess

        Args:
            connection_manager: The TemplateHandler's ConnectionManager instance to use for obtaining
                session environment variables
            sam_directory: The directory of the SAM template to use as the CWD when invoking SAM
            environment_variables: The dict of environment variables to use for invoking the SAM
                handler
            run_subprocess: The function to use for invoking subprocesses, matching the signature of
                subprocess.run
        """
        self.connection_manager = connection_manager
        self.sam_directory = sam_directory

        self.environment_variables = environment_variables
        self.run_subprocess = run_subprocess

    def invoke(self, command_name: str, args_dict: dict) -> None:
        """Invokes a SAM Command using the passed dict of arguments.

        Args:
            command_name: The name of the sam command to invoke (i.e. "build" or "package")
            args_dict: The dictionary of arguments to pass to the command
        """
        command_args = self._create_args(args_dict)
        command = f'sam {command_name}'
        if command_args.strip() != '':
            command += f' {command_args}'
        return self._invoke_sam_command(command)

    def _create_args(self, parameters: dict) -> str:
        """Creates a CLI argument string by combining two dictionaries and then formatting them as
        options.

        How the dict will be converted to cli args:
        * Keys with a value of None will be omitted, since they have no value
        * Keys with a value of True will be converted to --flag type of arguments
        * All other key/value pairs will be converted to --key "value" pairs

        Args:
            parameters: The default dictionary of arguments

        Returns:
            The CLI argument string
        """
        args = []
        for arg_name, arg_value in parameters.items():
            if arg_value is None:
                # It's an option with no value, so let's skip it
                continue

            argline = f'--{arg_name}'
            if arg_value is not True:
                # If the value is True, it's a flag, so we don't want a value
                argline += f' "{arg_value}"'
            args.append(argline)

        return ' '.join(args)

    def _invoke_sam_command(self, command: str) -> None:
        environment_variables = self._get_envs()
        self.run_subprocess(
            command,
            shell=True,
            cwd=self.sam_directory,
            check=True,
            # Redirect stdout to stderr so it doesn't combine with stdout that we might want
            # to capture.
            stdout=sys.stderr,
            env=environment_variables
        )

    def _get_envs(self) -> Dict[str, str]:
        """Obtains the environment variables to pass to the subprocess.

        Sceptre can assume roles, profiles, etc... to connect to AWS for a given stack. This is
        very useful. However, we need that SAME connection information to carry over to SAM when we
        invoke it. The most precise way to do this is to use the same session credentials being used
        by Sceptre for other stack operations. This method obtains those credentials and sets them
        as environment variables that are passed to the subprocess and will, in turn, be used by
        SAM CLI.

        The environment variables dict created by this method will inherit all existing
        environment variables in the current environment, but the AWS connection environment
        variables will be saved overridden by the ones for this stack.

        Returns:
            The dictionary of environment variables.
        """
        envs = self.environment_variables.copy()
        # Set aws environment variables specific to whatever AWS configuration has been set on the
        # stack's connection manager.
        credentials: Credentials = self.connection_manager._get_session(
            self.connection_manager.profile,
            self.connection_manager.region,
            self.connection_manager.iam_role
        ).get_credentials()
        envs.update(
            AWS_ACCESS_KEY_ID=credentials.access_key,
            AWS_SECRET_ACCESS_KEY=credentials.secret_key,
        )

        # There might not be a session token, so if there isn't one, make sure it doesn't exist in
        # the envs being passed to the subprocess
        if credentials.token is None:
            envs.pop('AWS_SESSION_TOKEN', None)
        else:
            envs['AWS_SESSION_TOKEN'] = credentials.token

        return envs


class SAM(TemplateHandler):
    """A template handler for AWS SAM templates. Using this will allow Sceptre to work with SAM to
    build and package a SAM template and deploy it with Sceptre.
    """

    SAM_ARTIFACT_DIRECTORY = 'sam_artifacts'

    def __init__(
        self,
        name,
        arguments=None,
        sceptre_user_data=None,
        connection_manager=None,
        stack_group_config=None,
        *,
        invoker_class=SamInvoker,
        get_temp_dir=tempfile.gettempdir
    ):
        super().__init__(name, arguments, sceptre_user_data, connection_manager, stack_group_config)
        self.invoker_class = invoker_class
        self.get_temp_dir = get_temp_dir

    def schema(self) -> dict:
        """This is the json schema of the template handler. It is required by Sceptre to define
        template handler parameters.
        """
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "artifact_prefix": {"type": "string"},
                "artifact_bucket_name": {"type": "string"},
                "build_args": {
                    "type": "object",
                },
                "package_args": {
                    "type": "object",
                }
            },
            "required": [
                "path",
                "artifact_bucket_name",
            ]
        }

    def handle(self) -> str:
        invoker = self.invoker_class(
            connection_manager=self.connection_manager,
            sam_directory=self.sam_directory
        )
        self._create_generation_destination()
        self._build(invoker)
        self._package(invoker)
        return self.destination_template_path.read_text()

    @property
    def sam_template_path(self) -> Path:
        return Path(self.arguments['path']).absolute()

    @property
    def sam_directory(self) -> Path:
        return self.sam_template_path.parent

    @property
    def destination_template_path(self) -> Path:
        suffix = self.sam_template_path.suffix
        path_segments = self.name.split('/')
        path_segments[-1] += suffix
        return Path(self.get_temp_dir()).joinpath(*path_segments).absolute()

    @property
    def destination_template_directory(self) -> Path:
        return self.destination_template_path.parent

    @property
    def artifact_key_prefix(self) -> str:
        """Returns the key prefix that should be passed to SAM CLI for uploading the packaged
        artifacts.
        """
        prefix_segments = [self.name, self.SAM_ARTIFACT_DIRECTORY]
        sam_package_prefix = self.arguments.get('artifact_prefix')

        if sam_package_prefix:
            prefix_segments.insert(0, sam_package_prefix)

        prefix = posixpath.join(*prefix_segments)
        return prefix

    @property
    def artifact_bucket_name(self) -> str:
        """Returns the S3 bucket name that should be passed to SAM CLI for uploading the packaged
        artifacts.
        """
        return self.arguments['artifact_bucket_name']

    def _create_generation_destination(self):
        """Creates the destination_template_directory, if it doesn't exist."""
        self.destination_template_directory.mkdir(parents=True, exist_ok=True)

    def _build(self, invoker: SamInvoker):
        default_args = {
            'cached': True,
            'template-file': str(self.sam_template_path)
        }
        build_args = {**default_args, **self.arguments.get('build_args', {})}
        invoker.invoke('build', build_args)

    def _package(self, invoker: SamInvoker):
        default_args = {
            's3-bucket': self.artifact_bucket_name,
            'region': self.connection_manager.region,
            's3-prefix': self.artifact_key_prefix,
            'output-template-file': self.destination_template_path,
            'template-file': str(self.sam_template_path.absolute())
        }
        package_args = {**default_args, **self.arguments.get('package_args', {})}
        invoker.invoke('package', package_args)
