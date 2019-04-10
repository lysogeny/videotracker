#!/usr/bin/env python3
"""Setup file for tracker"""

from setuptools import setup, find_packages

with open('README.md') as f:
    README = f.read()

with open('LICENSE') as f:
    LICENSE = f.read()

setup(
    name='videotracker',
    version='0.0.0',
    description='Modular video tracker with a Qt interface',
    long_description=README,
    author='Jooa Hooli',
    author_email='code@jooa.xyz',
    url='https://github.com/lysogeny/videotracker',
    license=LICENSE,
    packages=find_packages(exclude=('tests', 'docs')),
    #scripts=['bin/videotracker'],
    entry_points={
        'console_scripts': [
            'videotracker = videotracker.entrypoints:gui'
        ]
    }
)
