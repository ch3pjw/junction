import os
from setuptools import setup

__version__ = None
# Populate __version__ using the junction._version module, without importing
this_dir_path = os.path.dirname(__file__)
version_module_path = os.path.join(this_dir_path, 'junction', '_version.py')
exec(open(version_module_path).read())

setup(
    name='junction',
    version=__version__,
    install_requires=[
        'blessings',
        'asyncio'],
    packages=[
        'junction'],
    extras_require={
        'development': [
            'pep8',
            'mock',
            'nose',
            'nose-progressive',
            'coverage']}
)
