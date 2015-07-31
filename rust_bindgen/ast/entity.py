
class Entity(object):

    def __init__(self):
        self.parent = None
        self.name = None

        self.attrs = {}

    @property
    def path(self):
        path = []

        if self.parent is not None:
            path += self.parent.path
        if self.name is not None:
            path.append(self.name)

        return path

    @property
    def real_name(self):
        name = getattr(self, '_real_name', None)
        if name is not None:
            return name

        return self.name

    @real_name.setter
    def real_name(self, name):
        self._real_name = name

    def with_real_name(self, name):
        self.real_name = name
        return self

    @property
    def real_path(self):
        path = []

        if self.parent is not None:
            path += self.parent.real_path
        if self.name is not None:
            path.append(self.real_name)

        return path

    def add_attr(self, name, value):
        if isinstance(value, set):
            if name not in self.attrs.keys():
                self.attrs[name] = set()

            self.attrs[name] |= value
        elif isinstance(value, list):
            if name not in self.attrs.keys():
                self.attrs[name] = []

            self.attrs[name] += value
        else:
            self.set_attr(name, value)

    def set_attr(self, name, value):
        self.attrs[name] = value

    def get_attr(self, name, default=None):
        return self.attrs.get(name, default)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return self._hash()

    def _hash(self):
        return sum(map(hash, self.path + self.real_path))

    def __repr__(self):
        return '%s `%s`' % (self.__class__.__name__, self.name)
