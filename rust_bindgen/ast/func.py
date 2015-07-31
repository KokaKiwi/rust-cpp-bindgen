import enum
from .entity import Entity
from .ty import Void, Pointer


class Function(Entity):
    ARG_NAME = 'arg_{no}'

    def __init__(self, ret_ty=Void, *arg_tys):
        super().__init__()

        self.ret_ty = ret_ty
        self.arg_tys = Function.convert_arg_tys(*arg_tys)

    @staticmethod
    def convert_arg_tys(*arg_tys):
        def convert(i, arg_ty):
            arg_name = Function.ARG_NAME.format(no=i + 1)

            if isinstance(arg_ty, tuple):
                (arg_ty, arg_name) = arg_ty

            return (arg_ty, arg_name)

        return [convert(i, arg_ty) for (i, arg_ty) in enumerate(arg_tys)]


class StaticMethod(Function):
    pass


class Method(Function):

    def __init__(self, *args, const=False, **kwargs):
        super().__init__(*args, **kwargs)

        self.const = const

    @property
    def self_ty(self):
        return Pointer(self.parent, const=self.const, nullable=False)


class Constructor(StaticMethod):

    class Null(enum.Enum):
        nothrow = 1
        catch = 2

    def __init__(self, *arg_tys, null=Null.nothrow):
        super().__init__(None, *arg_tys)

        if isinstance(null, str):
            null = Null[null]
        self.null = null


class Destructor(Method):
    pass
