from .mod import Module


class Namespace(Module):

    def __init__(self, name=''):
        super().__init__()

        self.name = name

    @property
    def Namespace(self):
        return self.item_constructor(Namespace)

    @property
    def Class(self):
        from .cls import Class
        return self.item_constructor(Class)

    @property
    def Enum(self):
        from .enum import Enum
        return self.item_constructor(Enum)

    @property
    def Function(self):
        from .func import Function
        return self.item_constructor(Function)
