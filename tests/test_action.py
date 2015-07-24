import unittest

from easy_upgrade.api import (
    Action,
    Fetcher,
    Installer,
)


class TestDeclaration(unittest.TestCase):

    def test_fetcher_declaration(self):
        Action.clear()

        class Fetcher1(Fetcher):
            name = 'foo1'

        class Fetcher2(Fetcher):
            name = 'foo2'
            providers = ["foo"]

        class Fetcher3(Fetcher):
            name = 'foo3'
            providers = ('foo1', 'foo2')
        # test invalid provider type
        with self.assertRaises(Exception):
            class Fetcher4(Fetcher):
                name = 'foo4'
                providers = 42

    def test_fetcher_without_name(self):
        Action.clear()
        with self.assertRaises(Exception) as cm:

            class Foo42(Fetcher):
                pass
        self.assertEqual(
            cm.exception.message,
            "class 'Foo42' misses 'name' static member"
        )

    def test_fetcher_already_registered(self):
        Action.clear()

        class Fetch1(Fetcher):
            name = 'foo'
        with self.assertRaises(Exception) as cm:

            class Fetch2(Fetcher):
                name = 'foo'
        self.assertEqual(
            cm.exception.message,
            "Action 'foo' is already registered"
        )

    def test_action_miss_base_class(self):
        Action.clear()
        with self.assertRaises(Exception) as cm:

            class Fetch1(Action):
                name = 'pouet'
        self.assertEqual(
            cm.exception.message,
            "Action class must extend one of "
            "those classes: Fetcher, Installer, PostInstaller"
        )

    def test_action_extends_several_bases(self):
        Action.clear()
        with self.assertRaises(Exception) as cm:

            class Fetch(Fetcher, Installer):
                name = 'foo'
        self.assertEqual(
            cm.exception.message,
            "Action class must extend exactly one of those classes: "
            "Fetcher, Installer, PostInstaller"
        )


if __name__ == '__main__':
    unittest.main()
