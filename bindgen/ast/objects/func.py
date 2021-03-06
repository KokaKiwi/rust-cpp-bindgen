import enum
from .entity import Entity
from .ns import Namespace
from .ty import *

def raw(cls):
    func = cls()
    func.name = cls.__name__

    return func

class RawFunction(Entity):
    def generate(self, builder, lang, **kwargs):
        meth_name = self.gen_meth_name(lang, **kwargs)
        meth = getattr(self, meth_name, None)

        if meth is not None:
            meth(builder, **kwargs)

    def gen_meth_name(self, lang, **kwargs):
        name = 'generate_%s' % (lang)
        if kwargs.get('decl'):
            name += '_decl'
        return name

class Function(Entity):
    def __init__(self, ret_ty=Void, *arg_tys):
        super().__init__()
        self.ret_ty = ret_ty
        self.arg_tys = Function.convert_arg_tys(*arg_tys)

        self._call_name = None

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

fn = Function

class RawMethod(RawFunction):
    def gen_meth_name(self, lang, **kwargs):
        name = super().gen_meth_name(lang, **kwargs)

        if kwargs.get('static', False):
            name += '_static'

        return name

class Method(Function):
    def __init__(self, ret_ty=Void, *arg_tys, const=False):
        Entity.__init__(self)
        self.ret_ty = ret_ty
        self._arg_tys = Function.convert_arg_tys(*arg_tys)
        self.const = const

        self._call_name = None

        if isinstance(self.ret_ty, Option):
            raise Exception('Optionnable type not allowed for function return type.')

    @property
    def arg_tys(self):
        return [(ptr(self.parent, const=self.const), 'inst')] + self._arg_tys

    @arg_tys.setter
    def args_tys(self, value):
        self._arg_tys = value

meth = Method

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

ctor = Constructor

class Destructor(Method):
    pass

dtor = Destructor
