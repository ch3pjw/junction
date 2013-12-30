# Copyright (C) 2013 Paul Weaver <p.weaver@ruthorn.co.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].

import os
from setuptools import setup

__version__ = None
# Populate __version__ using the jcn._version module, without importing
this_dir_path = os.path.dirname(__file__)
version_module_path = os.path.join(this_dir_path, 'jcn', '_version.py')
exec(open(version_module_path).read())

readme_path = os.path.join(this_dir_path, 'README.md')
long_description = open(readme_path).read()

kwargs = dict(
    name='jcn',
    description='Junction: A Python-based command-line UI framework',
    long_description=long_description,
    url='https://github.com/ch3pjw/junction/',
    author='Paul Weaver',
    author_email='p.weaver@ruthorn.co.uk',
    license='GPLv3',
    platforms=[
        'Linux'],
    version=__version__,
    packages=[
        'jcn'],
    install_requires=[
        'blessings',
        'asyncio'],
    extras_require={
        'dev': [
            'pep8',
            'mock',
            'nose',
            'nose-progressive',
            'coverage'],
        'docs': [
            'Sphinx',
            'sphinx_bootstrap_theme']},
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Software Development :: Widget Sets']
)

if __name__ == '__main__':
    setup(**kwargs)
