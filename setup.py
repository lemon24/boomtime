import re
import ast
from setuptools import setup

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('boomtime/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='boomtime',
    version=version,
    author='lemon24',
    url='https://github.com/lemon24/boomtime',
    packages=['boomtime'],
    install_requires=[
        'pytz',
        'python-dateutil>=2',
        'click>=5',
    ],
    description="",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)

