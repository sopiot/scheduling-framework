from setuptools import setup, find_packages
import codecs
import re
import os

VERSION_RE = re.compile(r'''.*__version__ = ["'](.*?)['"]''', re.S)
PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))


def _load_readme():
    readme_path = os.path.join(PROJECT_DIR, 'README.md')
    with codecs.open(readme_path, 'r', 'utf-8') as f:
        return f.read()


def _load_version():
    init_path = os.path.join(PROJECT_DIR, 'simulation_framework', '__init__.py')
    with open(init_path) as fp:
        return VERSION_RE.match(fp.read()).group(1)


setup(
    name="simulation-framework",
    version=_load_version(),
    description="SoPIoT Thing SDK",
    long_description=_load_readme(),
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
    author="caplab",
    author_email="caplab94@gmail.com",
    url="https://iris.snu.ac.kr",
    license="MysMax Inc.",
    install_requires=[
        'big-thing-py',
        'pyyaml',
        'paramiko',
        'termcolor',
        'tabulate'],
    packages=find_packages(exclude=[]),
)
