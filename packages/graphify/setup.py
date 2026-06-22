from setuptools import setup, find_packages

setup(
    name="codeatlas-graphify",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["graphifyy>=0.8.44", "networkx>=3.0"],
)
