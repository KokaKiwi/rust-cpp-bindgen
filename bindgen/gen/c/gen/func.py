from contextlib import contextmanager
from . import ty as gen_ty
from . import CGenerator

ENTRY = 'function'


class CallingContext(object):

    def __init__(self, *args):
        self.args = list(args)
        self.ret = None


class CFunctionGenerator(CGenerator):

    def __init__(self, parent, func):
        super().__init__(parent)
        self.func = func

    def generate_def(self, writer):
        ret_tyname = self.typegen(self.ret_ty).ffi_name

        args = []
        for (arg_ty, arg_name) in self.arg_tys:
            arg_tyname = self.typegen(arg_ty).ffi_name

            args.append((arg_tyname, arg_name))

        writer.declare_function(self.ffi_name, ret_tyname, *args)

    def generate_impl(self, writer):
        from bindgen.ast import Void
        from .ty import TypeConvert

        ret_tygen = self.typegen(self.ret_ty)
        ret_tyname = ret_tygen.ffi_name

        args = []
        for (arg_ty, arg_name) in self.arg_tys:
            arg_tygen = self.typegen(arg_ty)
            arg_tyname = arg_tygen.ffi_name

            convert = arg_tygen.convert()
            if convert is not None and convert.kind == TypeConvert.Kind.complex:
                arg_name = '_%s' % (arg_name)

            args.append((arg_tyname, arg_name))

        with writer.function(self.ffi_name, ret_tyname, *args):
            # Prepare args
            call_args = []
            for (arg_ty, arg_name) in self.arg_tys:
                arg_tygen = self.typegen(arg_ty)
                convert = arg_tygen.convert()

                value = arg_name
                if convert is not None:
                    if convert.kind == TypeConvert.Kind.inline:
                        value = convert(writer, value)
                    elif convert.kind == TypeConvert.Kind.complex:
                        convert(writer, arg_name, '_%s' % (arg_name))

                call_args.append(value)

            # Call
            ctx = CallingContext(*call_args)
            self.generate_call(writer, ctx)

            if ctx.ret:
                ret = ctx.ret

                if self.ret_ty != Void:
                    convert = ret_tygen.convert(out=True)

                    if convert is not None:
                        if convert.kind == TypeConvert.Kind.inline:
                            ret = convert(writer, ret)
                        elif convert.kind == TypeConvert.Kind.complex:
                            convert(writer, '__ret', ret)
                            ret = '__ret'

                    writer.ret(ret)
                else:
                    writer.writeln('%s;' % (ret))

    def generate_call(self, writer, ctx):
        raise NotImplementedError('CFunctionGenerator.generate_call')

    @property
    def ret_ty(self):
        return self.func.ret_ty

    @property
    def arg_tys(self):
        return self.func.arg_tys

    @property
    def cpp_name(self):
        return self.gen_cpp_name(self.func.real_path)

    @property
    def ffi_name(self):
        return self.gen_c_name(self.func.path)


class FunctionGenerator(CFunctionGenerator):

    def generate_call(self, writer, ctx):
        call_name = self.cpp_name
        ctx.ret = writer.gen.call(call_name, *ctx.args)


class StaticMethodGenerator(CFunctionGenerator):

    def generate_call(self, writer, ctx):
        call_name = self.cpp_name
        ctx.ret = writer.gen.call(call_name, *ctx.args)


class MethodGenerator(CFunctionGenerator):

    def generate_call(self, writer, ctx):
        call_name = writer.gen.member('self', self.func.real_name, ptr=True)
        call_args = ctx.args[1:]

        ctx.ret = writer.gen.call(call_name, *call_args)

    @property
    def arg_tys(self):
        self_arg = (self.func.self_ty, 'self')
        return [self_arg] + super().arg_tys

# TODO: Make constructors return something else than a
#       pointer by default.


class ConstructorGenerator(CFunctionGenerator):

    def generate_call(self, writer, ctx):
        from bindgen.ast import Constructor

        ctor_name = self.gen_cpp_name(self.func.parent.real_path)

        if self.func.null == Constructor.Null.nothrow:
            call_name = 'new(std::nothrow) %s' % (ctor_name)
        else:
            call_name = 'new %s' % (ctor_name)

        ret = writer.gen.call(call_name, *ctx.args)

        if self.func.null == Constructor.Null.catch:
            ret_tygen = self.typegen(self.ret_ty)
            writer.declare_var(ret_tygen.cpp_name, '__ret_try')

            writer.write('try ')
            with writer.block():
                writer.assign_var('__ret_try', ret)
            writer.write(' catch(std::exception &) ')
            with writer.block():
                writer.assign_var('__ret_try', 'NULL')

            ret = '__ret_try'

        ctx.ret = ret

    @property
    def ret_ty(self):
        from bindgen.ast import Pointer
        return Pointer(self.func.parent, owned=True)


class DestructorGenerator(CFunctionGenerator):

    def generate_call(self, writer, ctx):
        writer.delete('self')

    @property
    def arg_tys(self):
        self_arg = (self.func.self_ty, 'self')
        return [self_arg]


def register(reg):
    from bindgen.ast import Function, StaticMethod, Method, Constructor, Destructor

    reg[Function] = FunctionGenerator

    reg[StaticMethod] = StaticMethodGenerator
    reg[Method] = MethodGenerator

    reg[Constructor] = ConstructorGenerator
    reg[Destructor] = DestructorGenerator
