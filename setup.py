import os
from setuptools import setup

__version__ = None
# Populate __version__ using the junction._version module, without importing
this_dir_path = os.path.dirname(__file__)
version_module_path = os.path.join(this_dir_path, 'junction', '_version.py')
exec(open(version_module_path).read())

readme_path = os.path.join(this_dir_path, 'README.md')
long_description = open(readme_path).read()

setup(
    name='junction',
    description='A Python-based command-line UI framework',
    long_description=long_description,
    url='https://github.com/ch3pjw/junction/',
    author='Paul Weaver',
    author_email='p.weaver@ruthorn.co.uk',
    license='GPLv3',
    platforms=[
        'Linux'],
    version=__version__,
    packages=[
        'junction'],
    install_requires=[
        'blessings',
        'asyncio'],
    extras_require={
        'dev': [
            'pep8',
            'mock',
            'nose',
            'nose-progressive',
            'coverage']},
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Software Development :: Widget Sets']
)
