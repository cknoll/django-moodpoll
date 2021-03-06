#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

from moodpoll.release import __version__

with open('README.md') as readme_file:
    readme = readme_file.read()


with open("requirements.txt") as requirements_file:
    requirements = requirements_file.read()

setup_requirements = []

test_requirements = []

setup(
    author="Carsten Knoll",
    author_email='carsten.knoll@poste.de',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Framework :: Django',
        'Programming Language :: Python :: 3',
    ],
    description="django-app to facilitate decision making",
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n',
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords='django, decision making',
    name='django-moodpoll',
    packages=find_packages(),
    setup_requires=setup_requirements,
    tests_require=test_requirements,
    # url='to be defined',
    version=__version__,
)
