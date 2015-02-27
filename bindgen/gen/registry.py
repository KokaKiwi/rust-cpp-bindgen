import enum
import inspect
from collections import defaultdict


class Entries(object):

    def __init__(self):
        self.entries = {}

    def get(self, cls, default=None):
        try:
            return self[cls]
        except KeyError:
            return default

    def __getitem__(self, cls):
        mro = inspect.getmro(cls)

        for cls in mro:
            entry = self.entries.get(cls, None)
            if entry is not None:
                return entry

        raise KeyError(cls)

    def __setitem__(self, cls, value):
        self.entries[cls] = value

    def __contains__(self, cls):
        try:
            entry = self[cls]
            return True
        except KeyError:
            return False

    def __repr__(self):
        return repr(self.entries)


class Registry(object):

    def __init__(self, parent=None):
        self.parent = parent

        self.mapping = defaultdict(lambda: defaultdict(Entries))

    def register(self, entry, lang, cls, value):
        self.mapping[entry][lang][cls] = value

    # The searching algorithm is the following:
    # 1 - Search in the entries for specified lang.
    # 2 - Search in the entries for `None` lang.
    # 3 - Search in the parent registry
    def get(self, entry, lang, cls):
        if not inspect.isclass(cls):
            raise TypeError('Expected Python class, got object <%s>' % (cls))

        value = self.mapping[entry][lang].get(cls)
        if value is None:
            value = self.mapping[entry][None].get(cls)
        if value is None and self.parent is not None:
            value = self.parent.get(entry, lang, cls)

        return value

    def map(self, lang):
        return LangRegistry(self, lang)


class LangRegistry(object):

    def __init__(self, registry, lang):
        assert isinstance(registry, Registry)

        self.registry = registry
        self.lang = lang

    def get(self, entry, cls):
        return self.registry.get(entry, self.lang, cls)

    def register(self, entry, cls, value):
        self.registry.register(entry, self.lang, cls, value)

    def map(self, entry):
        return MappedRegistry(self, entry)


class MappedRegistry(object):

    def __init__(self, registry, entry):
        assert isinstance(registry, LangRegistry)

        self.registry = registry
        self.entry = entry

    def get(self, cls):
        return self.registry.get(self.entry, cls)

    def register(self, cls, value):
        self.registry.register(self.entry, cls, value)

    def __getitem__(self, cls):
        value = self.get(cls)

        if value is None:
            raise KeyError(cls)

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
