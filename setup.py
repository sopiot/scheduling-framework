from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()


setup(
    name="simulation-framework",
    version="0.1.0",
    description="Simulation Framework for Hierarchical Edge-based IoT system",
    author="caplab",
    author_email="caplab94@gmail.com",
    long_description=long_description,
    url="https://iris.snu.ac.kr",
    license="MIT",
    install_requires=[
        'big-thing-py',
        'pyyaml',
        'paramiko',
        'termcolor',
        'toml',
        'dataclasses',
        'tabulate'],
    packages=find_packages(exclude=[]),
)
