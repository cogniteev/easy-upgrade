
import os
import os.path as osp
import shutil
import subprocess

from .. api import Installer, parse_version
from .. toolbox import find_executable, pushd


class StowInstaller(Installer):
    name = 'stow'

    def __init__(self, provider, release, config):
        super(StowInstaller, self).__init__(provider, release, config)
        self.path = config['path']
        self.pkg_path = osp.join(self.path, 'stow')
        self.activate = config.get('activate', True)
        self.executable = find_executable(
            *config.get('stow', ('stow', 'xstow'))
        )

    def release_dir_name(self, version=''):
        return '{}-{}'.format(self.release.pkg_name, version)

    def get_local_versions(self):
        versions = []
        if not osp.isdir(self.pkg_path):
            return versions
        for p in os.listdir(self.pkg_path):
            fp = osp.join(self.pkg_path, p)
            if osp.isdir(fp) and p.startswith(self.release_dir_name()):
                versions.append(p[len(self.release_dir_name()):])
        return versions

    def installed_version(self):
        """
        :return: most recent version available in stow packages directory.
        :rtype: string
        """
        installed_version = reduce(
            lambda a, b: a if a > b else b,
            map(
                lambda v: (parse_version(v), v),
                self.get_local_versions()
            ),
            (None, None)
        )
        return installed_version[1]

    def _stow(self, *args):
        with pushd(self.pkg_path):
            subprocess.check_call([self.executable] + list(args))

    def disable_package(self, version):
        self._stow('-D', self.release_dir_name(version))

    def enable_package(self, version):
        self._stow(self.release_dir_name(version))

    def install(self, fetched_items_path, version):
        rdir_name = self.release_dir_name(version)
        release_path = osp.join(self.pkg_path, rdir_name)
        if not osp.isdir(self.pkg_path):
            os.makedirs(self.pkg_path)
        elif osp.isdir(release_path):
            raise Exception(
                "Cannot install {}/{} in {}: directory exists".format(
                    self.provider.name,
                    self.release.name,
                    release_path
                )
            )
        shutil.copytree(fetched_items_path, release_path)
        if self.activate:
            versions_to_disable = set(self.get_local_versions())
            versions_to_disable.remove(version)
            for v in versions_to_disable:
                self.disable_package(v)
            self.enable_package(version)
