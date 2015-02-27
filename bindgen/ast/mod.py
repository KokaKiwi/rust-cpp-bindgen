import inspect
from .entity import Entity
from .ty import Type


class Module(Entity):

    def __init__(self):
        super().__init__()

        self.items = []

    def body(self, body):
        for (name, item) in body.__dict__.items():
            self.add_body_item(name, item)

        return self

    def add_item(self, item):
        item.parent = self
        self.items.append(item)

    # TODO: This method should verify there's no other items with same name
    def new_item(self, cls, *args, **kwargs):
        item = cls(*args, **kwargs)
        self.add_item(item)
        return item

    def item_constructor(self, cls):
        def wrapper(*args, **kwargs):
            return self.new_item(cls, *args, **kwargs)
        return wrapper

    def add_body_item(self, name, item):
        from .enum import Enum

        if name.startswith('_') and not name.startswith('__'):
            name = name[1:-1]
            self.add_body_attr(name, item)
        elif isinstance(item, Entity):
            self[name] = item

    def add_body_attr(self, name, value):
        self.add_attr(name, value)

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def __getitem__(self, name):
        for item in self.items:
            if item.name == name:
                return item

        raise KeyError(name)

    def __setitem__(self, name, item):
        if getattr(item, 'name', None) is None:
            item.name = name

        self.add_item(item)

    def __iter__(self):
        return iter(self.items)
