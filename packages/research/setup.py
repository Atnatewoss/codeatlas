from setuptools import setup, find_packages

setup(
    name="codeatlas-research",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langgraph>=0.0.27",
        "langchain>=0.1.0",
        "langchain-openai>=0.0.2",
        "langchain-google-genai>=1.0.0",
        "langchain-anthropic>=0.1.0",
        "pydantic>=2.0.0",
        "networkx>=3.0",
    ],
)
