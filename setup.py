from setuptools import setup, find_packages

__version__ = "0.1.0"

TEMPLATE_HANDLER_NAME = 'sceptre-sam-handler'
TEMPLATE_HANDLER_TYPE = 'sam'
TEMPLATE_HANDLER_MODULE_NAME = 'sam_handler.handler'
TEMPLATE_HANDLER_CLASS = 'SAM'
TEMPLATE_HANDLER_DESCRIPTION = 'Packages and renders SAM templates for use'
TEMPLATE_HANDLER_AUTHOR = 'Jon Falkenstein'
TEMPLATE_HANDLER_AUTHOR_EMAIL = 'sceptre@sceptre.org'
# if multiple use single string with commas.
TEMPLATE_HANDLER_URL = 'https://github.com/sceptre/{}'.format(TEMPLATE_HANDLER_NAME)

with open("README.md") as readme_file:
    README = readme_file.read()

install_requirements = [
    'sceptre>=2.7',
]

test_requirements = [
    "pytest>=3.2.0",
    "pyfakefs>=4.5.0"
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
    license='Apache2',
    url=TEMPLATE_HANDLER_URL,
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    entry_points={
        'sceptre.template_handlers': [
            f"{TEMPLATE_HANDLER_TYPE}={TEMPLATE_HANDLER_MODULE_NAME}:{TEMPLATE_HANDLER_CLASS}"
        ]
    },
    include_package_data=True,
    zip_safe=False,
    keywords="sceptre, sceptre-template-handler, sam, aws, cloudformation",
    classifiers=[
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Environment :: Console",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9"
    ],
    test_suite="tests",
    install_requires=install_requirements,
    tests_require=test_requirements,
    setup_requires=setup_requirements,
    python_requires='>=3.6',
    extras_require={
        "test": test_requirements,
        'sam': ['aws-sam-cli']
    }
)
