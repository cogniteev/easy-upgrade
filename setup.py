import os
from setuptools import setup, find_packages


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
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    "Programming Language :: Python :: 2.7",
]

setup(
    name='easy-upgrade',
    version=VERSION,
    author='Tristan Carel',
    author_email='tristan@{nospam}cogniteev.com',
    maintainer="Tristan Carel",
    maintainer_email="tristan@{nospam}cogniteev.com",
    url='https://github.com/cogniteev/easy_upgrade',
    download_url='https://github.com/cogniteev/easy_upgrade/tarball/master',
    license='Apache license version 2.0',
    include_package_data=True,
    packages=find_packages(),
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
    tests_require=[
    ],
    entry_points="""
        [console_scripts]
        easy_upgrade = easy_upgrade.cli:run
        [easy_upgrade.actions]
        github = easy_upgrade.lib.github
        stow = easy_upgrade.lib.stow
        [easy_upgrade.providers]
        github = easy_upgrade.lib.github:GitHubProvider
    """
)
