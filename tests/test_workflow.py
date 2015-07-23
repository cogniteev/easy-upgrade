import os.path as osp
import unittest

from easy_upgrade.api import (
    Config,
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


class SimpleInstaller(Installer):
    name = 'install1'


class SimplePostInstaller(PostInstaller):
    name = 'post-installer1'


class SimplePostInstaller2(PostInstaller):
    name = 'post-installer2'


class TestSimpleWorflow(unittest.TestCase):
    YML_CONFIG_PATH = osp.join(osp.dirname(__file__), 'simple-workflow.yml')

    def test_load_config(self):
        global_config = Config.from_yaml(self.YML_CONFIG_PATH)
        provider = SimpleProvider(global_config)
        self.assertEqual(provider.key1, 'value1')
        self.assertEqual(provider.get('key1'), 'value1')
        self.assertEqual(len(provider.releases), 1)
        release = provider.releases[0]
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
