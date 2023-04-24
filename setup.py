from setuptools import setup, find_packages

setup(
    name='pystorz',
    version='0.0.1',
    description='Python package for the Storz object store framework.',
    author='wazofski',
    author_email='wazo@duck.com',
    url='https://github.com/wazofski/pystorz',
    packages=find_packages(),
    install_requires=[
        "PyYAML",
        "jinja2",
        "black",
        # "pysqlite3",
        "jsonpath-python",
    ],
)
