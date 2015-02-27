from . import RustFFIGenerator

ENTRY = 'ffi-function'


class RustFFIFunctionGenerator(RustFFIGenerator):

    def __init__(self, parent, func):
        super().__init__(parent)
        self.func = func

    def typegen(self, ty):
        from . import ty as gen_ty

        Generator = self.registry(gen_ty.ENTRY)[ty.__class__]
        return Generator(self.parent, ty)

    def generate_raw(self, writer, root=[]):
        from bindgen.ast import Void

        ret_tyname = self.typegen(self.ret_ty).ffi_name(root)
        if self.ret_ty is Void:
            ret_tyname = None

        args = []
        for (arg_ty, arg_name) in self.arg_tys:
            arg_tyname = self.typegen(arg_ty).ffi_name(root)

            args.append((arg_tyname, arg_name))

        writer.declare_function(self.ffi_name(), ret_tyname, *args, pub=True)

    def generate_proxy(self, writer, root=[]):
        from bindgen.ast import Void

        ret_tygen = self.typegen(self.ret_ty)
        ret_proxy = ret_tygen.proxy(root, out=True)

        ret_tyname = ret_proxy.name
        if self.ret_ty is Void:
            ret_tyname = None

        args = []
        for (arg_ty, arg_name) in self.arg_tys:
            arg_tyname = self.typegen(arg_ty).rust_name(root)

            args.append((arg_tyname, arg_name))

        with writer.function(self.func.name, ret_tyname, *args, pub=True):
            call_args = []
            for (arg_ty, arg_name) in self.arg_tys:
                arg_tygen = self.typegen(arg_ty)
                proxy = arg_tygen.proxy(root)

                if proxy:
                    value = proxy(writer, arg_name)
                    writer.declare_var(arg_name, init=value)

                call_args.append(arg_name)

            call_name = self.ffi_name(root + ['raw'])
            ret = writer.gen.call(call_name, *call_args)

            if ret_proxy:
                ret = ret_proxy(writer, ret)

            with writer.unsafe():
                writer.writeln(ret)

    @property
    def ret_ty(self):
        return self.func.ret_ty

    @property
    def arg_tys(self):
        return self.func.arg_tys

    def ffi_name(self, root=[]):
        name = self.gen_c_name(self.func.path)
        return self.gen_rust_name(root + [name])


class FunctionGenerator(RustFFIFunctionGenerator):
    pass


class StaticMethodGenerator(RustFFIFunctionGenerator):
    pass


class MethodGenerator(RustFFIFunctionGenerator):

    @property
    def arg_tys(self):
        self_arg = (self.func.self_ty, 'inst')
        return [self_arg] + super().arg_tys


class ConstructorGenerator(RustFFIFunctionGenerator):

    @property
    def ret_ty(self):
        from bindgen.ast import Pointer
        return Pointer(self.func.parent, owned=True)


class DestructorGenerator(RustFFIFunctionGenerator):

    @property
    def arg_tys(self):
        self_arg = (self.func.self_ty, 'inst')
        return [self_arg]


def register(reg):
    from bindgen.ast import Function, StaticMethod
    from bindgen.ast import Method, Constructor, Destructor

    reg[Function] = FunctionGenerator

    reg[StaticMethod] = StaticMethodGenerator
    reg[Method] = MethodGenerator

    reg[Constructor] = ConstructorGenerator
    reg[Destructor] = DestructorGenerator
