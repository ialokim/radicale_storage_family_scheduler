#!/usr/bin/env python3

from setuptools import setup

setup(
    name="radicale_storage_family_scheduler",
    version='0.0.1',
    description='Basic scheduling for users on the same server',
    url='https://github.com/ialokim/radicale_storage_family_scheduler',
    license='CC-BY-SA-4.0',
    keywords='radicale storage scheduling caldav python',
    author='ialokim',

    install_requires=['radicale'],
    packages=["radicale_storage_family_scheduler"]
)
