from setuptools import setup, find_packages

__version__ = "0.1.0"

# More information on setting values:
# https://github.com/Sceptre/project/wiki/sceptre-template-handler-template

# lowercase, use `-` as separator.
TEMPLATE_HANDLER_NAME = 'custom-template-handler'
# the template_handler call in sceptre e.g. type: custom_template_handler.
TEMPLATE_HANDLER_TYPE = 'custom_template_handler'
# do not change. Rename template_handler/template_handler.py to template_handler/{TEMPLATE_HANDLER_TYPE}.py
TEMPLATE_HANDLER_MODULE_NAME = 'template_handler.{}'.format(TEMPLATE_HANDLER_TYPE)
# CamelCase name of template_handler class in template_handler.template_handler.
TEMPLATE_HANDLER_CLASS = 'CustomTemplateHandler'
# One line summary description
TEMPLATE_HANDLER_DESCRIPTION = 'A Custom Template Handler'
# if multiple use a single string with comma separated names.
TEMPLATE_HANDLER_AUTHOR = 'Sceptre'
# if multiple use single string with commas.
TEMPLATE_HANDLER_AUTHOR_EMAIL = 'sceptre@sceptre.org'
TEMPLATE_HANDLER_URL = 'https://github.com/sceptre/{}'.format(TEMPLATE_HANDLER_NAME)

with open("README.md") as readme_file:
    README = readme_file.read()

install_requirements = [
    "packaging==16.8"
]

test_requirements = [
    "pytest>=3.2"
]

setup_requirements = [
    "pytest-runner>=3"
]

setup(
    name=TEMPLATE_HANDLER_NAME,
    version=__version__,
    description=TEMPLATE_HANDLER_DESCRIPTION,
    long_description=README,
    long_description_content_type="text/markdown",
    author=TEMPLATE_HANDLER_AUTHOR,
    author_email=TEMPLATE_HANDLER_AUTHOR_EMAIL,
    license='Apache2',
    url=TEMPLATE_HANDLER_URL,
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    py_modules=[TEMPLATE_HANDLER_MODULE_NAME],
    entry_points={
        'sceptre.template_handlers': [
            f'{TEMPLATE_HANDLER_TYPE}={TEMPLATE_HANDLER_MODULE_NAME}:{TEMPLATE_HANDLER_CLASS}'
        ]
    },
    include_package_data=True,
    zip_safe=False,
    keywords="sceptre, sceptre-template-handler",
    classifiers=[
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Environment :: Console",
        "Programming Language :: Python :: 3.8"
    ],
    test_suite="tests",
    install_requires=install_requirements,
    tests_require=test_requirements,
    setup_requires=setup_requirements,
    extras_require={
        "test": test_requirements
    }
)
