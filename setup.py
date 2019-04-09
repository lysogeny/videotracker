#!/usr/bin/env python3
"""Setup file for tracker"""

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

#with open('LICENSE') as f:
#    license = f.read()

setup(
    name='videotracker',
    version='0.0.0',
    description='Modular video tracker with a Qt interface',
    long_description=readme,
    author='Jooa Hooli',
    author_email='code@jooa.xyz',
    url='https://github.com/lysogeny/videotracker',
    #license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
