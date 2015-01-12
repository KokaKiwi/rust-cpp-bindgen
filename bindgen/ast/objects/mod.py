from .entity import Entity

def isinstance_filter(cls):
    def _filter(item):
        return isinstance(item, cls)
    return _filter

class Module(Entity):
    def __init__(self):
        super().__init__()

        self.items = []
        self.includes = set()
        self.types = []

    def extra(self, lang, writer):
        pass

    def items_filter(self, cls):
        return filter(isinstance_filter(cls), self.items)

    def add_item(self, item):
        item.parent = self
        self.items.append(item)

    def new_item(self, cls, *args, **kwargs):
        item = cls(*args, **kwargs)
        self.add_item(item)
        return item

    def body(self, body):
        for (k, v) in body.__dict__.items():
            self.add_body_item(k, v)

        return self

    def add_body_item(self, name, item):
        if name == '_includes_' and isinstance(item, (set, list, tuple)):
            self.includes |= set(item)
        elif name == '_types_' and isinstance(item, (list)):
            self.types += item
        elif name.startswith('_'):
            attr_name = name[1:-1]
            setattr(self, attr_name, item)
        elif isinstance(item, Entity):
            if getattr(item, 'name', None) is None:
                item.name = name
            self.add_item(item)

    def traverse(self):
        yield from super().traverse()

        for item in sorted(self.items, key=lambda item: item.name):
            yield from item.traverse()

    def __getattr__(self, name):
        # Find subclasses
        for cls in Module.__subclasses__():
            def _wrapper(*args, **kwargs):
                return self.new_item(cls, *args, **kwargs)

            if cls.__name__ == name:
                return _wrapper

        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, name):
        # Find item
        for item in self.items:
            if getattr(item, 'name') == name:
                return item

        raise KeyError(name)

    def __iter__(self):
        return iter(self.items)

    def deep(self):
        for item in sorted(self.items, key=lambda item: item.name):
            yield item

            if isinstance(item, Module):
                yield from item.deep()

    @property
    def namespaces(self):
        from .ns import Namespace
        return self.items_filter(Namespace)

    @property
    def classes(self):
        from .cls import Class
        return self.items_filter(Class)

    @property
    def functions(self):
        from .func import Function
        return self.items_filter(Function)
