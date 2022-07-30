import subprocess
import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, create_autospec

from botocore.credentials import Credentials
from pyfakefs.fake_filesystem_unittest import TestCase as FsTestCase
from sceptre.connection_manager import ConnectionManager
from sceptre.exceptions import UnsupportedTemplateFileTypeError
from sceptre.template_handlers import helper

from sam_handler.handler import SAM, SamInvoker


class TestSAM(FsTestCase):
    def setUp(self):
        super().setUp()
        self.setUpPyfakefs()
        self.template_contents = 'hello!'
        self.processed_contents = 'goodbye!'
        self.fs.create_file('my/random/path.yaml', contents=self.template_contents)
        self.arguments = {
            'path': 'my/random/path.yaml',
            'artifact_prefix': 'prefix',
            'artifact_bucket_name': 'bucket'
        }
        self.invoker = Mock(**{
            'spec': SamInvoker,
            'invoke.side_effect': self.fake_invoke
        })
        self.invoker_class = create_autospec(SamInvoker, return_value=self.invoker)
        self.temp_dir = '/temp'
        self.get_temp_dir = lambda: self.temp_dir
        self.render_jinja_template: Mock = create_autospec(
            helper.render_jinja_template,
            return_value=self.processed_contents
        )

        self.region = 'region'

        self.connection_manager = Mock(**{
            'spec': ConnectionManager,
            'region': self.region,
        })
        self.name = 'top/mid/stack'
        self.sceptre_user_data = {'user': 'data'}
        self.stack_group_config = {'j2_environment': 'blah'}
        self.handler = SAM(
            self.name,
            connection_manager=self.connection_manager,
            arguments=self.arguments,
            sceptre_user_data=self.sceptre_user_data,
            stack_group_config=self.stack_group_config,
            invoker_class=self.invoker_class,
            get_temp_dir=self.get_temp_dir,
            render_jinja_template=self.render_jinja_template
        )
        self._is_built = False

    def fake_invoke(self, command, args):
        if command == 'build':
            self._is_built = True
            self.assertTrue(
                Path(args['template-file']).exists()
            )
        elif command == 'package':
            self.assertTrue(self._is_built)
            output_file = Path(args['output-template-file'])
            output_file.write_text(self.processed_contents)

    def test_handle__instantiates_invoker_with_correct_args(self):
        self.handler.handle()
        self.invoker_class.assert_called_with(
            self.connection_manager,
            Path(self.arguments['path']).parent.absolute()
        )

    def test_handle__invokes_build_with_default_arguments(self):
        self.handler.handle()
        self.invoker.invoke.assert_any_call(
            'build',
            {
                'cached': True,
                'template-file': str(Path(self.arguments['path']).absolute())
            }
        )

    def test_handle__build_args_specified__invokes_build_with_all_build_args(self):
        self.arguments['build_args'] = {'use-container': True}
        self.handler.handle()
        self.invoker.invoke.assert_any_call(
            'build',
            {
                'cached': True,
                'template-file': str(Path(self.arguments['path']).absolute()),
                'use-container': True
            }
        )

    def test_handle__invokes_package_with_default_arguments(self):
        self.handler.handle()
        expected_temp_dir = Path(self.temp_dir) / (self.name + '.yaml')
        expected_prefix = '/'.join([
            self.arguments['artifact_prefix'],
            *self.name.split('/'),
            'sam_artifacts'
        ])

        self.invoker.invoke.assert_any_call(
            'package',
            {
                's3-bucket': self.arguments['artifact_bucket_name'],
                'region': self.region,
                's3-prefix': expected_prefix,
                'output-template-file': expected_temp_dir,
            }
        )

    def test_handle__package_args_specified__invokes_package_with_default_arguments(self):
        self.arguments['package_args'] = {'new': 'arg'}
        self.handler.handle()
        expected_temp_dir = Path(self.temp_dir) / (self.name + '.yaml')
        expected_prefix = '/'.join(
            [
                self.arguments['artifact_prefix'],
                *self.name.split('/'),
                'sam_artifacts'
            ]
        )

        self.invoker.invoke.assert_any_call(
            'package',
            {
                's3-bucket': self.arguments['artifact_bucket_name'],
                'region': self.region,
                's3-prefix': expected_prefix,
                'output-template-file': expected_temp_dir,
                'new': 'arg'
            }
        )

    def test_handle__returns_contents_of_destination_template_file(self):
        result = self.handler.handle()
        self.assertEqual(self.processed_contents, result)

    def test_validate_args_schema(self):
        self.arguments['build_args'] = {
            'use-container': True
        }
        self.arguments['package_args'] = {
            'region': 'us-east-1'
        }
        self.handler.validate()

    def test_handle__path_has_jinja_extension__renders_template_with_correct_parameters(self):
        self.arguments['path'] = 'my/random/path.yaml.j2'
        self.handler.handle()
        self.render_jinja_template.assert_any_call(
            str(Path(self.arguments['path']).absolute()),
            {'sceptre_user_data': self.sceptre_user_data},
            self.stack_group_config.get('j2_environment')
        )

    def test_handle__path_has_jinja_extension__invokes_build_with_compiled_jinja_template_path(self):
        self.arguments['path'] = 'my/random/path.yaml.j2'
        expected_file_path = Path('my/random/path.yaml.compiled').absolute()
        self.handler.handle()
        self.invoker.invoke.assert_any_call(
            'build',
            {
                'cached': True,
                'template-file': str(expected_file_path)
            }
        )

    def test_handle__path_has_jinja_extension_and_delete_flag_is_true__deletes_compiled_jinja_file(self):
        self.arguments['path'] = 'my/random/path.yaml.j2'
        expected_file_path = Path('my/random/path.yaml.compiled').absolute()
        self.handler.handle()
        self.assertFalse(expected_file_path.exists())

    def test_handle__path_has_jinja_extension_and_delete_flag_is_false__deletes_compiled_jinja_file(self):
        self.arguments['path'] = 'my/random/path.yaml.j2'
        self.arguments['build_args'] = {'delete_temporary_jinja_file': False}
        expected_file_path = Path('my/random/path.yaml.compiled').absolute()
        self.handler.handle()
        self.assertTrue(expected_file_path.exists())

    def test_handle__path_has_jinja_extension__returns_contents_of_destination_template_file(self):
        result = self.handler.handle()
        self.assertEqual(self.processed_contents, result)

    def test_handle__unsupported_path_extension__raises_unsupported_file_type_error(self):
        self.arguments['path'] = 'my/unsupported/file.yucky'
        with self.assertRaises(UnsupportedTemplateFileTypeError):
            self.handler.handle()


class TestSamInvoker(TestCase):
    def setUp(self):
        super().setUp()
        self.credentials = Mock(
            spec=Credentials,
            access_key='access',
            secret_key='secret',
            token='token'
        )

        self.profile = 'professor'
        self.region = 'down under'
        self.iam_role = 'iam not!'

        self.connection_manager = Mock(**{
            'spec': ConnectionManager,
            '_get_session.return_value.get_credentials.return_value': self.credentials,
            'profile': self.profile,
            'region': self.region,
            'iam_role': self.iam_role

        })
        self.sam_directory = Path('/path/to/my/sam/directory')
        self.envs = {
            'some': 'env'
        }
        self.run_subprocess = Mock(spec=subprocess.run)

        self.invoker = SamInvoker(
            connection_manager=self.connection_manager,
            sam_directory=self.sam_directory,
            environment_variables=self.envs,
            run_subprocess=self.run_subprocess
        )

    def assert_sam_command(self, command, *, expected_envs=None):
        if expected_envs:
            envs = expected_envs
        else:
            envs = self.envs.copy()
            envs.update(
                AWS_ACCESS_KEY_ID=self.credentials.access_key,
                AWS_SECRET_ACCESS_KEY=self.credentials.secret_key
            )
            if self.credentials.token is not None:
                envs['AWS_SESSION_TOKEN'] = self.credentials.token

        self.run_subprocess.assert_called_with(
            command,
            shell=True,
            check=True,
            cwd=self.sam_directory,
            stdout=sys.stderr,
            env=envs
        )

    def test_invoke__runs_sam_command_with_args(self):
        args = {
            'key': 'value',
            'flag': True,
            'ignore me': None,
        }
        self.invoker.invoke('build', args)
        expected_command = 'sam build --key "value" --flag'
        self.assert_sam_command(expected_command)

    def test_invoke__runs_sam_command_with_empty_args(self):
        self.invoker.invoke('build', {})
        expected_command = 'sam build'
        self.assert_sam_command(expected_command)

    def test_sam_command__injects_aws_environment_variables_into_sam_command(self):
        self.invoker.invoke('command', {})

        self.assert_sam_command(
            'sam command',
            expected_envs={
                **self.envs,
                **{
                    'AWS_ACCESS_KEY_ID': self.credentials.access_key,
                    'AWS_SECRET_ACCESS_KEY': self.credentials.secret_key,
                    'AWS_SESSION_TOKEN': self.credentials.token,
                }
            }
        )

    def test_sam_command__session_token_is_none__does_not_inject_that_to_envs(self):
        self.credentials.token = None
        self.invoker.invoke('command', {})

        self.assert_sam_command(
            'sam command',
            expected_envs={
                **self.envs,
                **{
                    'AWS_ACCESS_KEY_ID': self.credentials.access_key,
                    'AWS_SECRET_ACCESS_KEY': self.credentials.secret_key,
                }
            }
        )
