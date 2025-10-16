from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='pystorz',
    version='0.6.2',
    author='wazofski',
    description='Python package for the Storz object store framework.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/wazofski/pystorz',
    packages=[
        "pystorz",
        "pystorz/internal",
        "pystorz/meta",
        "pystorz/mgen",
        "pystorz/mgen/templates",
        "pystorz/rest",
        "pystorz/sql",
        "pystorz/store",
        "pystorz/router",
        "pystorz/mongo",
        "pystorz/browse",
        "pystorz/browse/templates",
    ],
    package_data={'': ['*.py', '*.js', '*.template', '*.html']},
    # package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        "PyYAML",
        "jinja2",
        "black",
        "jsonpath-python",
        "cherrypy",
        "requests",
        "mysql-connector-python",
        "sqlparse",
        "pymongo",
        # "pysqlite3",
    ],
    extras_require={
        'dev': [
            # 'pytest -v test_mgen.py -cov',
            # 'pytest -v -k "thestore" test_common.py -cov',
            # 'flake8',
        ]
    },
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.7",
    ],
    python_requires=">=3.6",
)
