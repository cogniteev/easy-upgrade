
import argparse
import logging
import os.path as osp

from . api import EasyUpgrade

DEFAULT_CONFIG_PATH = osp.expanduser('~/.config/easy_upgrade/config.yml')


def list_outdated_packages(config, all_packages=False, **kwargs):
    eu = EasyUpgrade.from_yaml(config)
    method = eu.get_outdated_packages
    if all_packages:
        method = eu.get_packages_version
    for pkg in method():
        if 'candidate' not in pkg['versions']:
            message = "{}:{}: no candidate".format(
                pkg['provider'],
                pkg['release']
            )
        else:
            message = "{}:{}: candidate {}".format(
                pkg['provider'],
                pkg['release'],
                pkg['versions']['candidate']['human']
            )
        installed = pkg['versions'].get('installed')
        if installed:
            message += ", currently installed: {}".format(installed['human'])
        else:
            message += ", not installed"
        print message


def install_outdated_packages(config, release=None, **kwargs):
    eu = EasyUpgrade.from_yaml(config)
    if len(release) == 0:
        for provider in eu.providers.values():
            provider.install()
    else:
        for r in release:
            try:
                provider, release = r.split(':', 1)
            except ValueError:
                raise Exception(
                    "Invalid syntax for release: {}".format(r) +
                    ". Expecting provider/release"
                )
            eu.providers[provider].install(release)


def run(args=None):
    parser = argparse.ArgumentParser(
    )
    from . import __version__
    version = '.'.join(map(str, __version__))
    parser.add_argument(
        '-V', '--version',
        action='version',
        version='%(prog)s ' + version,
    )
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help='Verbose mode, -vv for more details'
    )
    parser.add_argument(
        '-c', '--config',
        metavar='<file>',
        help='Specify custom configuration file. Default is %(default)s',
        default=DEFAULT_CONFIG_PATH
    )
    subparsers = parser.add_subparsers(help='sub-command help')
    list_parser = subparsers.add_parser(
        'list',
        help='List outdated packages'
    )
    list_parser.add_argument(
        '-a', '--all',
        dest='all_packages',
        action='store_true',
        help='List all packages'
    )
    list_parser.set_defaults(func=list_outdated_packages)

    install_parser = subparsers.add_parser(
        'install',
        help='Install outdated package(s)'
    )
    install_parser.add_argument(
        'release',
        nargs='*',
        help="Subset of releases to upgrade. Syntax: 'provider:release'"
    )
    install_parser.set_defaults(func=install_outdated_packages)
    if args is None:
        args = parser.parse_args()
    else:
        parser.parse_args(args)
    if args.verbose >= 1:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO
    logging.basicConfig(level=logging_level)
    if args.verbose < 1:
        for l in ['requests.packages.urllib3.connectionpool', ]:
            logging.getLogger(l).setLevel(logging.ERROR)
    args.func(**vars(args))
