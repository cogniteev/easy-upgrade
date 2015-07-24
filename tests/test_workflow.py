import os.path as osp
import shutil
import unittest

from easy_upgrade.api import (
    EasyUpgrade,
    Fetcher,
    Installer,
    PostInstaller,
    ReleaseProvider,
)


class SimpleProvider(ReleaseProvider):
    def __init__(self, top_config):
        super(SimpleProvider, self).__init__(
            'simple-provider',
            top_config,
        )
        self.key1 = self.get('key1')


class SimpleFetcher(Fetcher):
    name = 'fetch1'

    def candidate_version(self):
        return '1.0.3'

    def fetch(self, fetched_items_path):
        with open(osp.join(fetched_items_path, 'version.txt'), 'w') as ostr:
            ostr.write('{}: {}'.format(
                self.release.name,
                self.candidate_version())
            )


class SimpleInstaller(Installer):
    name = 'install1'

    def installed_version(self):
        return getattr(self, '_installed_version', None)

    def install(self, fetched_items_path, version):
        self._installed_version = version
        shutil.copyfile(
            osp.join(fetched_items_path, 'version.txt'),
            osp.join(fetched_items_path, 'version2.txt')
        )


class SimplePostInstaller(PostInstaller):
    name = 'post-installer1'

    def execute(self, fetched_items_path, version):
        pass


class SimplePostInstaller2(PostInstaller):
    name = 'post-installer2'

    def execute(self, fetched_items_path, version):
        with open(osp.join(fetched_items_path, 'version2.txt')) as istr:
            file_content = istr.read()
        self.ut.assertEqual(
            file_content,
            '{}: {}'.format(self.release.name, version)
        )


class TestSimpleWorflow(unittest.TestCase):
    YML_CONFIG_PATH = osp.join(osp.dirname(__file__), 'simple-workflow.yml')

    def test_load_config(self):
        global_config = EasyUpgrade.load_yaml(self.YML_CONFIG_PATH)
        provider = SimpleProvider(global_config)
        self.assertEqual(provider.key1, 'value1')
        self.assertEqual(provider.get('key1'), 'value1')
        self.assertEqual(len(provider.releases), 1)
        release = provider.releases.values()[0]
        self.assertIsNotNone(release)
        self.assertEqual(release.name, 'cogniteev/docido')
        self.assertEqual(release.get('key2'), 'value2')
        self.assertIsNotNone(release.fetcher)
        self.assertEqual(release.fetcher.name, 'fetch1')
        self.assertEqual(release.fetcher.get('key3'), 'value3')
        self.assertIsNotNone(release.installer)
        self.assertEqual(release.installer.name, 'install1')
        self.assertEqual(release.installer.get('key4'), 'value4')
        self.assertIsNotNone(release.post_installers)
        self.assertEqual(len(release.post_installers), 3)
        pi1 = release.post_installers[0]
        self.assertEqual(pi1.name, 'post-installer1')
        self.assertEqual(pi1.get('key5'), 'value5')
        pi2 = release.post_installers[1]
        self.assertEqual(pi2.name, 'post-installer1')
        self.assertEqual(pi2.get('key6'), 'value6')
        pi3 = release.post_installers[2]
        self.assertEqual(pi3.name, 'post-installer2')
        self.assertEqual(pi3.get('key7'), 'value7')

    def test_installation(self):
        global_config = EasyUpgrade.load_yaml(self.YML_CONFIG_PATH)
        provider = SimpleProvider(global_config)
        release = provider.releases.values()[0]
        release.post_installers[2].ut = self
        self.assertTrue(provider.install('cogniteev/docido'))
        self.assertFalse(provider.install('cogniteev/docido'))

if __name__ == '__main__':
    unittest.main()
