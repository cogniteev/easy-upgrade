import inspect
import logging
import operator

import pkg_resources

from .toolbox import temp_dir


def parse_version(version):
    if version is None:
        return version
    version = version.lstrip('v')
    return pkg_resources.parse_version(version)


class Action(dict):
    actions = {}
    bases = ['Fetcher', 'Installer', 'PostInstaller']

    def __init__(self, provider, release, config):
        super(Action, self).__init__(config)
        self.provider = provider
        self.release = release

    @classmethod
    def clear(cls):
        cls.actions.clear()

    def jinja_eval(self, text):
        # FIXME
        return text

    class __metaclass__(type):
        def __new__(mcs, name, bases, attrs):
            new_type = type.__new__(mcs, name, bases, attrs)
            if name != 'Action' and name not in Action.bases:
                action_name = Action.get_action_name(new_type, attrs)
                providers = Action.get_action_providers(new_type, attrs)
                basename = Action.get_action_basename(new_type)
                Action.register(basename, new_type, action_name, providers)
            return new_type

    @classmethod
    def get_action_basename(cls, new_type):
        classes = list(new_type.__bases__)
        candidates = []
        while any(classes):
            clazz = classes.pop()
            if clazz.__name__ in cls.bases:
                candidates.append(clazz)
            classes += clazz.__bases__
        if not(any(candidates)):
            raise Exception(
                "Action class must extend one of those classes: " +
                ", ".join(cls.bases)
            )
        elif len(candidates) != 1:
            raise Exception(
                "Action class must extend exactly one of those classes: " +
                ", ".join(cls.bases)
            )
        return candidates[0].__name__

    @classmethod
    def get_action_name(cls, new_type, attrs):
        if 'name' not in attrs:
            raise Exception(
                "class '{}' misses 'name' static member".format(
                    new_type.__name__))
        return attrs['name']

    @classmethod
    def get_action_providers(cls, new_type, attrs):
        providers = attrs.get('providers')
        if 'providers' not in attrs:
            classes = [new_type]
            while providers is None and any(classes):
                clazz = classes.pop()
                if hasattr(clazz, 'providers'):
                    providers = getattr(clazz, 'providers')
                    break
                classes += clazz.__bases__
        return providers

    @classmethod
    def get_action(cls, base, name, provider):
        if isinstance(provider, ReleaseProvider):
            provider = provider.name
        base = base.__name__ if inspect.isclass(base) else base
        actions = cls.actions.get(base, {})
        providers, action = actions.get(name, (None, None))
        if action is None:
            raise Exception("Unknown {} action {}".format(base, name))
        if providers is None:
            return action
        elif provider in providers:
            return action
        else:
            raise Exception(
                "{} Action '{}' is not available in provider '{}'".format(
                    base, name, provider)
            )

    @classmethod
    def register(cls, base_name, action_cls, name, providers):
        if name in cls.actions.get(base_name, {}):
            raise Exception("Action '{}' is already registered".format(name))
        if isinstance(providers, basestring):
            providers = (providers,)
        elif isinstance(providers, list):
            providers = tuple(providers)
        elif providers and not isinstance(providers, tuple):
            raise Exception(
                "Error in class {}".format(name) +
                ", 'providers' static member must be either "
                "a string, a list, or a tuple")
        cls.actions.setdefault(base_name, {})[name] = (providers, action_cls)


class Fetcher(Action):
    def candidate_version(self):
        """returns the version the fetcher would like to install"""
    def fetch(self, output_directory):
        pass


class Installer(Action):
    def installed_version(self):
        raise NotImplementedError()

    def install(self, fetched_items_path, version):
        raise NotImplementedError


class PostInstaller(Action):
    def execute(self, fetched_items_path, version):
        raise NotImplementedError


class Release(dict):
    def __init__(self, provider, name, config):
        super(Release, self).__init__(config)
        self.provider = provider
        self.name = name
        self.fetcher = self.__extract_action('fetch', Fetcher)
        self.installer = self.__extract_action('install', Installer)
        self.post_installers = self.__extract_action(
            'post-install', PostInstaller, unique=False, default=[]
        )
        self.logger = logging.getLogger('{}:{}'.format(
            self.provider.name,
            self.name
        ))

    def pkg_name(self):
        return self.name

    def get_versions(self):
        installed = self.installer.installed_version()
        candidate = self.fetcher.candidate_version()
        versions = dict()
        if installed:
            versions['installed'] = {
                'human': installed,
                'tuple': parse_version(installed),
            }
        if candidate:
            versions['candidate'] = {
                'human': candidate,
                'tuple': parse_version(candidate),
            }
        return versions

    def __version(self, version):
        if version:
            version_tuple = parse_version(version)
        else:
            version_tuple = None
        return version, version_tuple

    def __is_bidder_newer(self, installed, bidder, bidder_str):
        if installed:
            if installed == bidder:
                self.logger.info(
                    "candidate version ({}) ".format(bidder_str) +
                    "is already installed. Nothing to do."
                )
                return False
            elif installed > bidder:
                self.logger.info(
                    "installed version ({}) ".format(installed) +
                    "is more recent than " +
                    "candidate version ({})".format(bidder_str)
                )
                return False
        return True

    def install(self):
        _, version = self.__version(self.installer.installed_version())
        bidder_str, bidder = self.__version(self.fetcher.candidate_version())
        if not self.__is_bidder_newer(version, bidder, bidder_str):
            return False
        self.logger.info("starting installation of version {}".format(
            bidder_str
        ))
        top_config = self.provider.top_config
        cleanup_temp_dir = top_config.get('cleanup-temp-dir', True)
        with temp_dir(cleanup=cleanup_temp_dir) as d:
            self.logger.info("fetching release")
            self.fetcher.fetch(d)
            self.logger.info("installing release")
            self.installer.install(d, bidder_str)
            for post_installer in self.post_installers:
                post_installer.execute(d, bidder_str)
        return True

    def __get_raw_config(self, config_key, default, unique):
        raw_configs = self.get(config_key)
        if raw_configs is None:
            if default is not None:
                return default
            else:
                raise Exception(
                    "Expecting key '{}' in release configuration"
                    .format(config_key)
                )
        elif isinstance(raw_configs, list):
            if unique:
                if len(raw_configs) != 1:
                    raise Exception(
                        "Release config key '{}' ".format(config_key) +
                        "expect only one item"
                    )
        else:
            raw_configs = [raw_configs]
        return raw_configs

    def __instantiate_action(self, base_action_cls, name, config):
        action_cls = Action.get_action(
            base_action_cls,
            name,
            self.provider
        )
        return action_cls(self.provider, self, config)

    def __extract_action(self, config_key, base_action_cls,
                         unique=True, default=None):
        raw_configs = self.__get_raw_config(config_key, default, unique)
        actions = []
        for config in raw_configs:
            if not isinstance(config, dict):
                raise Exception(
                    "Release config key '{}' ".format(config_key) +
                    "expect dictionary values"
                )
            if len(config) != 1:
                raise Exception(
                    "Release config-key '{}' ".format(config_key) +
                    "expect a dictionary values of 1 element (name => config)"
                )
            action_name, action_config = config.items()[0]
            actions.append(self.__instantiate_action(
                base_action_cls,
                action_name,
                action_config
            ))
        if unique:
            return actions[0]
        return actions


class ReleaseProvider(dict):
    def __init__(self, name, top_config, release_cls=Release):
        self.name = name
        self.top_config = top_config
        super(ReleaseProvider, self).__init__(top_config.get(name))
        self.release_cls = release_cls
        self.releases = {}
        for name, raw_config in self.get('releases', {}).items():
            self.releases[name] = release_cls(self, name, raw_config)

    def install(self, *releases):
        if not any(releases):
            return reduce(
                operator.__and__,
                map(
                    lambda r: r.install(),
                    self.releases.values()
                )
            )
        else:
            return reduce(
                operator.__and__,
                map(
                    lambda r: r.install(),
                    [release for name, release in self.releases.items()
                     if name in releases]
                )
            )


class EasyUpgrade(object):
    @classmethod
    def from_yaml(cls, path):
        return EasyUpgrade(cls.load_yaml(path))

    @classmethod
    def load_yaml(cls, path):
        from yaml import load
        with open(path) as istr:
            return load(istr)

    def get_packages_version(self):
        for provider in self.providers.values():
            for release in provider.releases.values():
                yield {
                    'provider': provider.name,
                    'release': release.name,
                    'versions': release.get_versions()
                }

    def get_outdated_packages(self):
        for pkg in self.get_packages_version():
            versions = pkg['versions']
            outdated = False
            installed = versions.get('installed')
            if 'candidate' in versions:
                if installed:
                    if installed['tuple'] < versions['candidate']['tuple']:
                        outdated = True
                else:
                    outdated = True
            if outdated:
                yield pkg

    def __init__(self, config):
        self.config = config
        self.providers = {}
        _actions = 'easy_upgrade.actions'
        _providers = 'easy_upgrade.providers'
        for entrypoint in pkg_resources.iter_entry_points(group=_actions):
            entrypoint.load()
        for entrypoint in pkg_resources.iter_entry_points(group=_providers):
            provider = entrypoint.load()
            name = entrypoint.name
            if name in config:
                self.providers[name] = provider(name, config)
