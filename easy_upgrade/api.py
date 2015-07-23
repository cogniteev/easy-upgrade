class Action(object):
    actions = {}

    @classmethod
    def clear(cls):
        cls.actions.clear()

    class __metaclass__(type):
        def __new__(mcs, name, bases, attrs):
            new_type = type.__new__(mcs, name, bases, attrs)
            if name not in ['Action', 'Fetcher', 'Installer', 'PostInstaller']:
                if 'name' not in attrs:
                    raise Exception(
                        "class '{}' misses 'name' static member".format(name)
                    )
                action_name = attrs['name']
                providers = attrs.get('providers')
                if 'providers' not in attrs:
                    classes = [new_type]
                    while providers is None and any(classes):
                        clazz = classes.pop()
                        if hasattr(clazz, 'providers'):
                            providers = getattr(clazz, 'providers')
                            break
                        classes += clazz.__bases__
                Action.register(new_type, action_name, providers)
            return new_type

    @classmethod
    def get(cls, name, provider):
        providers, action = cls.actions.get(name, (None, None))
        if action is None:
            raise Exception("Unknown action {}".format(name))
        if providers is None:
            return action
        elif provider.name in providers:
            return action
        else:
            raise Exception(
                "Action '{}' is not available in provider '{}'".format(
                    name, provider.name)
            )

    def __call__(self, config, release, provider, prev_result=None):
        raise NotImplementedError()

    def cleanup(self):
        pass

    @classmethod
    def register(cls, type, name, providers):
        if name in cls.actions:
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
        if providers is None:
            providers = (None,)
        for p in providers:
            cls.actions[name] = (providers, type())


class Fetcher(Action):
    pass


class Installer(Action):
    pass


class PostInstaller(Action):
    pass


class Release(dict):
    def __init__(self, name, config):
        super(Release, dict).__init__(config)
        self.name = name
        self.actions = config.get('actions')

    def install(self, provider):
        for action in self.actions:
            assert len(action) == 1
            name = action.keys()[0]
            pipeline = action.values()[0]
            self.install_step(name, pipeline, provider)

    def install_step(self, name, pipeline, provider):
        actions = [Action.get(p.keys()[0]) for p in pipeline]
        configs = [p.values()[0] for p in pipeline]

        def _execute(i):
            if i == 0:
                return self.execute_action(action[i], configs[i], provider)
            else:
                result = self.execute_action(action[i - 1], configs[i - 1])
                return self.execute_action(
                    action[i], configs[i], provider, result
                )
        try:
            return _execute(len(pipeline))
        finally:
            for action in reversed(actions):
                action.cleanup()

    def execute_action(self, action, config, provider, prev_result=None):
        return action(config, self, provider, prev_result)


class ReleaseProvider(object):
    def __init__(self, config, name, release_cls):
        self.name = name
        self.config = config
        self.pconfig = config.get(name)
        self.release_cls = release_cls

    def releases(self):
        return map(self.release_cls, self.pconfig.get('releases', {}).items())
