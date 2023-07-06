from setuptools import setup, find_packages
import os

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))


def _load_version():
    init_path = os.path.join(PROJECT_ROOT, 'simulation_framework', '__init__.py')
    with open(init_path) as fp:
        version = fp.read().split('__VERSION__ =')[1].strip(" ").strip('\n').strip("'").strip('"')
        return version


def _load_readme():
    readme_path = os.path.join(PROJECT_ROOT, 'README.md')
    with open(readme_path, 'r', encoding='utf-8') as f:
        readme = f.read()
        return readme


setup(
    name='simulation-framework',
    version=_load_version(),
    license=None,
    description='MySSIX Simulation Framework SDK',
    long_description=_load_readme(),
    long_description_content_type='text/markdown',
    author='MysMax Inc.',
    author_email='caplab94@gmail.com',
    url='https://github.com/sopiot/simulation-framework',
    packages=find_packages(include=['simulation_framework']),
    classifiers=[],
    install_requires=[
        'big-thing-py',
        'pyyaml',
        'anytree',
        'paramiko',
        'termcolor',
        'tabulate',
        'rich'],
    python_requires='>=3.7',
)
