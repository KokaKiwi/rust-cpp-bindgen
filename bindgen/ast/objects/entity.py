
class Entity(object):
    def __init__(self):
        self.parent = None
        self.name = None

    def with_name(self, name):
        self.name = name
        return self

    def traverse(self):
        yield self

    @property
    def namespace(self):
        from .ns import Namespace

        current = self.parent

        while not isinstance(current, Namespace):
            current = current.parent

        return current

    @property
    def path(self):
        path = []

        if self.parent is not None:
            path += self.parent.path
        if self.name is not None:
            path.append(self.name)

        return path
