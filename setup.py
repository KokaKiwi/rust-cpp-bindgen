#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='rust_bindgen',
    version='0.1.0',

    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'rust-cpp-bindgen = rust_bindgen.main:entry',
        ],
    },
)
