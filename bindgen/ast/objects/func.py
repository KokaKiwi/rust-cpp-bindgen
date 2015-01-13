import enum
from .entity import Entity
from .ns import Namespace
from .ty import *

class Function(Entity):
    def __init__(self, ret_ty=Void, *arg_tys):
        super().__init__()
        self.ret_ty = ret_ty
        self.arg_tys = Function.convert_arg_tys(*arg_tys)

        self._call_name = None

    @property
    def namespace(self):
        current = self.parent

        while not isinstance(current, Namespace):
            current = current.parent

        return current

    @property
    def call_name(self):
        if self._call_name is not None:
            return self._call_name
        return self.name

    @call_name.setter
    def call_name(self, name):
        self._call_name = name

    def convert_arg_tys(*arg_tys):
        def convert_arg_ty(i, arg_ty):
            arg_name = 'arg_%d' % (i + 1)

            if isinstance(arg_ty, tuple):
                (arg_ty, arg_name) = arg_ty

            return (arg_ty, arg_name)

        return [convert_arg_ty(i, arg_ty) for (i, arg_ty) in enumerate(arg_tys)]

    def with_call_name(self, name):
        self._call_name = name
        return self

class Method(Function):
    def __init__(self, ret_ty=Void, *arg_tys, const=False):
        Entity.__init__(self)
        self.ret_ty = ret_ty
        self._arg_tys = Function.convert_arg_tys(*arg_tys)
        self.const = const

        self._call_name = None

    @property
    def arg_tys(self):
        return [(ptr(self.parent, const=self.const), 'inst')] + self._arg_tys

    @arg_tys.setter
    def args_tys(self, value):
        self._arg_tys = value

class StaticMethod(Function):
    pass

class Constructor(StaticMethod):
    class Null(enum.Enum):
        nothrow = 1
        catch = 2

    def __init__(self, *arg_tys, null=Null.nothrow):
        Entity.__init__(self)
        self.arg_tys = Function.convert_arg_tys(*arg_tys)

        self._call_name = None
        self.null = null

    @property
    def ret_ty(self):
        return ptr(self.parent, null=Pointer.Null.panic)

class Destructor(Method):
    pass
