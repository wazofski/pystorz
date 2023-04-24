from setuptools import setup, find_packages

setup(
    name='pystorz',
    version='0.0.3',
    description='Python package for the Storz object store framework.',
    author='wazofski',
    author_email='wazo@duck.com',
    url='https://github.com/wazofski/pystorz',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        "PyYAML",
        "jinja2",
        "black",
        "jsonpath-python",
        # "pysqlite3",
    ],
)
