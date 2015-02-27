import enum
import inspect
from .entity import Entity
from .ty import Type


class EnumType(enum.Enum):

    def __new__(cls, value):
        if isinstance(value, (int,)):
            cls.__counter__ = value

        if value is None:
            value = cls.autovalue()

        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @classmethod
    def autovalue(cls):
        if not hasattr(cls, '__counter__'):
            cls.__counter__ = 0

        value = cls.__counter__
        cls.__counter__ += 1
        return value


class Enum(Type, Entity):

    def __init__(self, ty):
        assert inspect.isclass(ty) and issubclass(ty, EnumType)
        Type.__init__(self)
        Entity.__init__(self)

        self.ty = ty
        self.name = self.ty.__name__

    @property
    def tyname(self):
        return 'Enum %s' % (self.name)

    @property
    def values(self):
        return iter(self.ty)

    _hash = Entity._hash
