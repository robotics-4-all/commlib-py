#!/usr/bin/env python3

"""The setup script."""
import importlib.metadata
import os
import sys

from setuptools import setup

this_dir = os.path.abspath(os.path.dirname(__file__))

VERSIONFILE = os.path.join(this_dir, "commlib", "__init__.py")
VERSION = None
for line in open(VERSIONFILE, "r").readlines():
    if line.startswith("__version__"):
        VERSION = line.split('"')[1]

if not VERSION:
    raise RuntimeError("No version defined in commlib.__init__.py")


if sys.argv[-1].startswith("publish"):
    if os.system("pip list | grep wheel"):
        print("wheel not installed.\nUse `pip install wheel`.\nExiting.")
        sys.exit()
    if os.system("pip list | grep twine"):
        print("twine not installed.\nUse `pip install twine`.\nExiting.")
        sys.exit()
    os.system("python setup.py sdist bdist_wheel")
    if sys.argv[-1] == "publishtest":
        os.system("twine upload -r test dist/*")
    else:
        os.system("twine upload dist/*")
        print("You probably want to also tag the version now:")
        print(
            "  git tag -a {0} -m 'version {0}'".format(
                importlib.metadata.version("commlib-py")
            )
        )
        print("  git push --tags")
    sys.exit()

setup(version=VERSION)
