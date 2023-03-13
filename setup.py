import os

from setuptools import setup

def readme():
    with open('README.md', encoding='utf-8') as f:
        return f.read()

setup(
    name="pyDynamicRoutingUpdater",
    long_description_content_type='text/markdown',
    long_description=readme(),
    packages=["DynamicRoutingUpdater"],
    install_requires=[
        "netifaces>=0.11.0",
        "netaddr>=0.8.0"
    ],
    version="0.0.3",
    description="""
    A Python library to modify and alter the routing table in according to configuration passed
    """,
    python_requires=">=3.9.0",
    author="Brage Skjønborg",
    author_email="bskjon@outlook.com",
    url="https://github.com/bskjon/DynamicRoutingUpdater",
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Networking",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
