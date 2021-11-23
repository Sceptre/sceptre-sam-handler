# README

## What is this?
`sceptre-sam-handler` is a TemplateHandler for Sceptre (versions 2.7 and up) that lets you use an
AWS SAM template (and its associated project) as a stack's template.

This template handler will run `sam build` and then `sam package` from the indicated SAM Template's
directory in order to generate a CloudFormation-ready template.

**By using the SAM Handler, you are letting SAM compile a SAM template and upload artifacts to S3,
and then using Sceptre to actually do the deployment of the template to a stack.** In other words,
by using this handler with Sceptre, _you skip ever using `sam deploy`; It's not needed_. You also
likely won't need a sam config file with deployment defaults, since you'll be using Sceptre to
deploy rather than SAM.

By using this handler, you can now use SAM templates with all your favorite Sceptre commands, like
`launch`, `validate`, `generate`, and `diff` (along with all the rest)!

## How to install sceptre-sam-handler

Simply `pip install scepre-sam-handler`.

If you want to install `aws-sam-cli` along with this handler using `pip`, you can use the "extra"
like `pip install sceptre-sam-handler[sam]`.

## How to use sceptre-sam-handler

The template "type" for this handler is `sam`.

This handler takes several arguments, two of which are required.

### Arguments:
* `path` (string, required): The path **from the current working directory** (NOT the
* project path) to the SAM Template.
* `artifact_bucket_name` (string, required): The bucket name where artifacts should be uploaded to
on S3 during the packaging process. If your project has a `template_bucket_name`, you can set this
to `{{ template_bucket_name }}`.
* `artifact_prefix` (string, optional): The prefix to apply to artifacts uploaded to S3. This can be
the project's `{{ template_key_prefix }}`.
* `build_args` (dict, optional): Additional key/value pairs to supply to `sam build`. For
flag-type arguments that have no value, set the value to "True".
* `package_args` (dict, optional): Additional key/value pairs to apply to `sam package`. The
same is true here as for `build_args` for flag-type arguments.

### How does this handler work?

When using _only_ sam CLI (not Sceptre) to deploy using `sam deploy`, SAM CLI effectively performs
3 steps:

1. SAM CLI builds the all the various resources special SAM resources, resolving dependencies. These would
include Lambda functions and Lambda layers. It copies any locally-referenced files and resolves any
dependencies into a directory called `.aws-sam`. This is the sam behavior as running `sam build`.
2. SAM CLI then transforms all SAM template URIs that reference local filepaths to S3 keys (among other)
transformations it applies, uploads any built artifacts to those s3 keys, and saves the transformed
template. This is the same behavior as running `sam package`.
3. SAM CLI finally takes that transformed template (along with a local sam config and any other CLI
arguments) and performs CloudFormation stack create/update with them.

When you use Sceptre with this handler, the SAM handler performs steps 1-2 above to create a template
that Sceptre can use, **but it does not use sam to deploy it!**. Instead, Sceptre can use that template
produced in step 2 above (via `sam package`) to perform all it's usual commands with all it's usual
magic!

In other words, using this handler lets you use resolvers, put your SAM stack into StackGroups, let
you name your stack according to Sceptre's naming conventions, `validate`, `diff`, and more! Basically,
the SAM stack can be managed using Sceptre just like any other.

### Default behavior
SAM commands are invoked using the system shell in a subprocess, with stdout redirected to stderr.
Artifacts will be uploaded using the `artifact_bucket_name` and `artifact_prefix` arguments, the
`project_code`, and the Sceptre stack name.

For example, given an `artifact_bucket_name` of "bucket", `artifact_prefix` of "prefix", a
`project_code` of "project" and a stack config located at "config/indigo/sam-application.yaml", SAM
artifacts will be uploaded to:

`s3://bucket/prefix/project/indigo/sam-application/sam_artifacts/`

By default, these will be the sam commands that are run _from the template's directory_:
```shell
sam build --cached --template-file [path as absolute path]
sam package \
  --s3-bucket [artifact_bucket_name argument] \
  --region [the stack region] \
  --s3-prefix [the prefix described above] \
  --template-file [path as absolute path]
```

If any additional arguments are desired for to be passed to SAM, you can specify those with dicts for
the `build_args` and `package_args` template handler arguments. These key/value pairs will
override the defaults. For any flag-type arguments, set the value to `True`. If you want to remove
a default argument (such as the `--cached` flag for `sam build`), set the value to `None`.

### IAM and authentication

This handler uses the stack's connection information to generate AWS environment variables and sets
those on the sam process, ensuring that the AWS authentication configuration on the stack config and
project is carried over to SAM without any need for additional arguments.

If you desire to use a different profile or region when invoking `sam package` than what is set on
the stack, you should specify "profile" and/or "region" values for "package_args".

**Important:** SAM creates CloudFormation-ready templates via `sam package`, which uploads built
artifacts to S3 in the process. This means that Sceptre commands that do not normally require S3
actions (such as `generate`, `validate`, `diff`, and others) will require them when using this
handler. You will need to ensure that any user or role executing these commands has proper
permissions for these operations. For more information on required permissions, see the
[documentation for SAM permissions](
https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-permissions.html).

### Example Stack Config
```yaml
# By using the SAM handler, you let SAM build and package the template and upload artifacts to S3
# and Sceptre will use the packaged template to create the CloudFormation stack, using the stack
# config.
template:
    type: sam
    path: path/from/my/cwd/template.yaml
    artifact_bucket_name: {{ template_bucket_name }}
    artifact_prefix: {{ template_key_prefix }}
    build_args:
        use-container: True

# You can use resolvers to pass parameters, just like any other Sceptre stack!
parameters:
    long_parameter: !file my/file/path
    my_template_parameter: !stack_output some/other/stack.yaml::SomeOutput

# The SAM Handler will work with all the other stack parameters you might want to use too!
profile: my_profile
iam_role: arn:aws:iam::1111111111:role/My-Deployment-Role
region: us-east-1

stack_tags:
    SomeTag: SomeValue
```
