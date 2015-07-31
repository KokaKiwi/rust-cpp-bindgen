from .mod import Module
from .ty import Type


class Class(Type, Module):

    def __init__(self, name, *bases):
        Type.__init__(self)
        Module.__init__(self)

        self.name = name
        self.bases = list(bases)

        self.upclasses = self.bases
        self.downclasses = []

        for base in self.bases:
            base.downclasses.append(self)

    @property
    def Enum(self):
        from .enum import Enum
        return self.item_constructor(Enum)

    @property
    def StaticMethod(self):
        from .func import StaticMethod
        return self.item_constructor(StaticMethod)

    @property
    def Method(self):
        from .func import Method
        return self.item_constructor(Method)

    @property
    def Constructor(self):
        from .func import Constructor
        return self.item_constructor(Constructor)

    @property
    def Destructor(self):
        from .func import Destructor
        return self.item_constructor(Destructor)

    @property
    def tyname(self):
        path = self.path
        while path[0] == '':
            del path[0]
        return '_'.join(path)

    def _hash(self):
        from .entity import Entity
        return Entity._hash(self)
