from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='pystorz',
    version='0.1.11',
    author='wazofski',
    description='Python package for the Storz object store framework.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/wazofski/pystorz',
    packages=[
        "pystorz",
        "pystorz/internal",
        "pystorz/mgen",
        "pystorz/mgen/templates",
        "pystorz/sql",
        "pystorz/store",
    ],
    package_data={'': ['*.py']},
    # package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        "PyYAML",
        "jinja2",
        "black",
        "jsonpath-python",
        # "pysqlite3",
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.7",
    ],
    python_requires=">=3.6",
)
