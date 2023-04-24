from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='pystorz',
    version='0.0.3',
    author='wazofski',
    description='Python package for the Storz object store framework.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/wazofski/pystorz',
    packages=["pystorz"],
    # package_dir={'': 'src'},
    # include_package_data=True,
    install_requires=[
        "PyYAML",
        "jinja2",
        "black",
        "jsonpath-python",
        # "pysqlite3",
    ],
    classifiers=[
        "Development Status :: Beta",
        "Intended Audience :: Developers",
        "License :: MIT License",
        "Programming Language :: Python :: 3.7",
    ],
    python_requires=">=3.6",
)
