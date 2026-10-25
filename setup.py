from setuptools import setup, find_packages

setup(
    name="sythonlab_kiu_rest_sdk",
    version="0.0.1",
    packages=find_packages(), install_requires=[
        "requests>=2.31",
    ],
    python_requires=">=3.9",
    url="https://github.com/sythonlab/SythonLab-Kiu-Rest-Sdk",
    author="José Angel Alvarez Abraira",
    author_email="sythonlab@gmail.com",
    description="Sython Lab KIU REST SDK",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
)
