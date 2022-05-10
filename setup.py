#!/usr/bin/env python

from setuptools import setup
from setuptools import find_packages


def readme():
    with open("README.rst") as f:
        return f.read()


setup(
    name="sol-view",
    version="1.0.2",
    description="A Module to plot data stored in hdf files",
    long_description=readme(),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
    author="Hugo Campos",
    author_email="hugohvlcampos96@gmail.com",
    url="https://github.com/lnls-sol/sol-view",
    install_requires=[
        "wheel",
        "pydm",
        "PyQt5",
        "silx",
        "numpy",
        "python-dateutil",
        "lmfit",
        "qdarkstyle",
        "pymca",
        "pandas",
    ],
    package_data={"sol_view": ["*.ui", "icons/*.png"]},
    packages=find_packages(exclude=["test", "test.*"]),
    entry_points={"console_scripts": ["sol_view=sol_view.scripts.run:run_sol_view"]},
)
