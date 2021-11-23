# README

## What is this?
`sceptre-sam-handler` is a TemplateHandler for Sceptre (versions 2.7 and up) that lets you use an
AWS SAM template (and its associated project) as a stack's template.

This template handler will run `sam build` and then `sam package` from the indicated SAM Template's
directory in order to generate a CloudFormation-ready template.

## How to install sceptre-sam-handler

Simply `pip install scepre-sam-handler`!

## How to use sceptre-sam-handler

The template "type" for this handler is `sam`.

This handler takes several arguments, two of which are required.

### Arguments:
* `sam_template_path` (string, required): The path **from the current working directory** (NOT the
* project path) to the SAM Template.
* `artifact_bucket_name` (string, required): The bucket name where artifacts should be uploaded to
on S3 during the packaging process. If your project has a `template_bucket_name`, you can set this
to `{{ template_bucket_name }}`.
* `artifact_prefix` (string, optional): The prefix to apply to artifacts uploaded to S3. This can be
the project's `{{ template_key_prefix }}`.
* `sam_build_args` (dict, optional): Additional key/value pairs to supply to `sam build`. For
flag-type arguments that have no value, set the value to "True".
* `sam_package_args` (dict, optional): Additional key/value pairs to apply to `sam package`. The
same is true here as for `sam_build_args` for flag-type arguments.

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
sam build --cached --template-file [sam_template_path as absolute path]
sam package \
  --s3-bucket [artifact_bucket_name argument] \
  --region [the stack region] \
  --s3-prefix [the prefix described above] \
  --template-file [sam_template_path as absolute path]
```

If any additional arguments are desired for to be passed to SAM, you can specify those with dicts for
the `sam_build_args` and `sam_package_args` template handler arguments. These key/value pairs will
override the defaults. For any flag-type arguments, set the value to `True`. If you want to remove
a default argument (such as the `--cached` flag for `sam build`), set the value to `None`.

### IAM and authentication

This handler uses the stack's connection information to generate AWS environment variables and sets
those on the sam process, ensuring that the AWS authentication configuration on the stack config and
project is carried over to SAM without any need for additional arguments.

**Important:** SAM creates CloudFormation-ready templates via `sam package`, which uploads built
artifacts to S3 in the process. This means that Sceptre commands that do not normally require S3
actions (such as `generate`, `validate`, `diff`, and others) will require them when using this
handler. You will need to ensure that any user or role executing these commands has "s3:PutObject"
permissions.

### Example
```yaml
template:
    type: sam
    sam_template_path: path/from/my/cwd/template.yaml
    artifact_bucket_name: {{ template_bucket_name }}
    artifact_prefix: {{ template_key_prefix }}
    sam_build_args:
        use-container: True
```
