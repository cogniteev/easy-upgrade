import os
import os.path as osp
import re
import shutil
import tempfile
import unittest

import yaml

from easy_upgrade.api import EasyUpgrade


class GithubTest(unittest.TestCase):
    YAML_CONFIG_FILE = osp.join(
        osp.dirname(__file__),
        os.path.splitext(__file__)[0] + '.yml'
    )

    @classmethod
    def setUpClass(cls):
        cls.register_temp_stow_dir()

    def test_outdated_packages(self):
        if osp.isdir(self.stow_root_dir):
            shutil.rmtree(self.stow_root_dir)
        eu = EasyUpgrade.from_yaml(self.YAML_CONFIG_FILE)
        outdated = list(eu.get_outdated_packages())
        self.assertEqual(len(outdated), 2)
        expected = [
            {
                'release': 'docker/machine',
                'provider': 'github',
                'versions': {
                    'candidate': {
                        'human': u'v0.3.1',
                        'tuple': (
                            u'00000000', u'00000003',
                            u'00000001', '*final'
                        )
                    }
                }
            },
            {
                'release': 'docker/compose',
                'provider': 'github',
                'versions': {
                    'candidate': {
                        'human': u'1.3.3',
                        'tuple': (
                            u'00000001', u'00000003',
                            u'00000003', '*final'
                        )
                    }
                }
            }
        ]
        for o in outdated:
            self.assertIn(o, expected)
        for e in expected:
            self.assertIn(e, outdated)

    def test_install_compose_only(self):
        if osp.isdir(self.stow_root_dir):
            shutil.rmtree(self.stow_root_dir)
        eu = EasyUpgrade.from_yaml(self.YAML_CONFIG_FILE)
        eu.providers['github'].install('docker/compose')
        compose_executable = osp.join(
            self.stow_root_dir,
            'stow',
            'compose-1.3.3',
            'bin',
            'docker-compose'
        )
        self.assertTrue(osp.isfile(compose_executable))

    @classmethod
    def tearDownClass(cls):
        if osp.isdir(cls.stow_root_dir):
            shutil.rmtree(cls.stow_root_dir)

    @classmethod
    def register_temp_stow_dir(cls):
        yaml_pattern = re.compile(r'^\<%= temp_stow_dir %\>$')
        cls.stow_root_dir = tempfile.mkdtemp(prefix='stow_root')
        yaml.add_implicit_resolver('!temp_stow_dir', yaml_pattern)

        def temp_stow_dir(loader, node):
            return cls.stow_root_dir
        yaml.add_constructor('!temp_stow_dir', temp_stow_dir)


if __name__ == '__main__':
    unittest.main()
