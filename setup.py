import os
import sys
from setuptools import setup, find_packages

# Hack to silence atexit traceback in new


def get_version(version_tuple):
    if not isinstance(version_tuple[-1], int):
        return '.'.join(map(str, version_tuple[:-1])) + version_tuple[-1]
    return '.'.join(map(str, version_tuple))

# Dirty hack to get version number from monogengine/__init__.py - we can't
# import it as it depends on PyMongo and PyMongo isn't installed until this
# file is read
init = os.path.join(os.path.dirname(__file__), 'easy_upgrade', '__init__.py')
version_line = list(filter(
    lambda l: l.startswith('__version__'),
    open(init)))[0]

VERSION = get_version(eval(version_line.split('=')[-1]))
DESCRIPTION = ""
LONG_DESCRIPTION = ""

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.2",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
]

extra_opts = {"packages": find_packages(exclude=["tests", "tests.*"])}
if sys.version_info[0] == 3:
    extra_opts['use_2to3'] = True
    extra_opts['tests_require'] = [
        'nose', 'coverage==3.7.1',
        'blinker', 'Pillow>=2.0.0'
    ]
    if "test" in sys.argv or "nosetests" in sys.argv:
        extra_opts['packages'] = find_packages()
        extra_opts['package_data'] = {
            "tests": ["fields/mongoengine.png", "fields/mongodb_leaf.png"]
        }
else:
    # coverage 4 does not support Python 3.2 anymore
    extra_opts['tests_require'] = [
        'nose', 'coverage==3.7.1',
        'blinker', 'Pillow>=2.0.0',
        'python-dateutil'
    ]
    if sys.version_info[0] == 2 and sys.version_info[1] == 6:
        extra_opts['tests_require'].append('unittest2')

setup(
    name='easy_upgrade',
    version=VERSION,
    author='Tristan Carel',
    author_email='tristan@{nospam}cogniteev.com',
    maintainer="Tristan Carel",
    maintainer_email="tristan@{nospam}cogniteev.com",
    url='https://github.com/cogniteev/easy_upgrade',
    download_url='https://github.com/cogniteev/easy_upgrade/tarball/master',
    license='MIT',
    include_package_data=True,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    platforms=['any'],
    classifiers=CLASSIFIERS,
    test_suite='nose.collector',
    setup_requires=['nose', 'rednose'],
    install_requires=[
        'PyYAML>=3.11',
        'requests>=2.7.0',
    ],
    **extra_opts
)
