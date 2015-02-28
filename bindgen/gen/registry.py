import enum
import inspect
from collections import defaultdict


class Registry(object):

    def __init__(self, parent=None):
        self.parent = parent

        self.mapping = defaultdict(lambda: defaultdict(dict))

    def register(self, entry, lang, key, value):
        self.mapping[entry][lang][key] = value

    # The searching algorithm is the following:
    # 1 - Search in the entries for specified lang.
    # 2 - Search in the entries for `None` lang.
    # 3 - Search in the parent registry
    def get(self, entry, lang, key):
        key_registry = getattr(key, '__registry', {})
        entry_registry = key_registry.get(entry, {})
        value = entry_registry.get(lang, None)
        if value is not None:
            return value

        def search(cls):
            value = self.mapping[entry][lang].get(cls)
            if value is None:
                value = self.mapping[entry][None].get(cls)
            if value is None and self.parent is not None:
                value = self.parent.get(entry, lang, cls)
            return value

        cls = key
        if not inspect.isclass(cls):
            cls = cls.__class__

        mro = inspect.getmro(cls)
        for base in mro:
            value = search(base)
            if value is None:
                continue

            return value

        return None

    def map(self, lang):
        return LangRegistry(self, lang)


class LangRegistry(object):

    def __init__(self, registry, lang):
        assert isinstance(registry, Registry)

        self.registry = registry
        self.lang = lang

    def get(self, entry, key):
        return self.registry.get(entry, self.lang, key)

    def register(self, entry, key, value):
        self.registry.register(entry, self.lang, key, value)

    def map(self, entry):
        return MappedRegistry(self, entry)


class MappedRegistry(object):

    def __init__(self, registry, entry):
        assert isinstance(registry, LangRegistry)

        self.registry = registry
        self.entry = entry

    def get(self, key):
        return self.registry.get(self.entry, key)

    def register(self, key, value):
        self.registry.register(self.entry, key, value)

    def __getitem__(self, key):
        value = self.get(key)

        if value is None:
            raise KeyError(key)

        return value

    __setitem__ = register

GLOBAL_REGISTRY = Registry()


def sub_registry():
    global GLOBAL_REGISTRY

    return Registry(GLOBAL_REGISTRY)


def register(entry, lang, value):
    global GLOBAL_REGISTRY

    def wrapper(cls):
        GLOBAL_REGISTRY.register(entry, lang, cls, value)
        return cls
    return wrapper
