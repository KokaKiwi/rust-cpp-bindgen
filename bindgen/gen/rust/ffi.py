from .codegen import RustCodeGenerator
from .codewriter import RustCodeWriter
from .. import BindingGenerator, CodeBuilder
from .. import utils as gen_utils

class RustFFICodeBuilder(CodeBuilder):
    def generate_ffi_function(self, func):
        self._generate_ffi_function(self.writer, func)

    def generate_function(self, func):
        self._generate_function(self.writer, func)

    def generate_mod(self, mod):
        self._generate_mod(self.writer, mod)

    def _generate_ffi_function(self, writer, func):
        name = gen_utils.c_name(func.path)
        ret_ty = func.ret_ty.ffi_name('rust', path=['super'])

        args = []
        for (arg_ty, arg_name) in func.arg_tys:
            arg_ty = arg_ty.ffi_name('rust', path=['super'])

            args.append((arg_ty, arg_name))

        writer.declare_function(name, ret_ty, args)

    def _generate_mod(self, writer, mod):
        from bindgen.ast import objects as obj

        for item in sorted(mod.items, key=lambda item: item.name):
            if isinstance(item, obj.Namespace):
                writer.writeln()
                with writer.mod(item.name):
                    writer.use(['super', 'raw'])

                    self.generate_mod(item)
            elif isinstance(item, obj.Module):
                self.generate_mod(item)
            elif isinstance(item, obj.Function):
                writer.writeln()
                self.generate_function(item)
            elif isinstance(item, obj.RawFunction):
                writer.writeln()
                item.generate(self, 'rust_ffi')

    def _generate_function(self, writer, func):
        from bindgen.ast import objects as obj

        path = func.namespace.path[1:]
        super = ['super'] * len(path)
        writer.comment(gen_utils.cpp_name(func.path))

        name = func.name
        if isinstance(func, (obj.Method, obj.StaticMethod)):
            name = gen_utils.c_name(func.path[-2:])

        if func.ret_ty == obj.Bool:
            ret_ty = 'bool'
        else:
            ret_ty = func.ret_ty.ffi_name('rust', path=super)

        args = []
        for (arg_ty, arg_name) in func.arg_tys:
            if isinstance(arg_ty, obj.Option):
                arg_ty = arg_ty.subtype

            if arg_ty == obj.Bool:
                arg_ty = 'bool'
            else:
                arg_ty = arg_ty.ffi_name('rust', path=super)

            args.append((arg_ty, arg_name))

        writer.attr('inline', ['always'])
        with writer.function(name, ret_ty, args, unsafe=True):
            # Call function
            call_args = [arg_ty.transform('rust', arg_name) for (arg_ty, arg_name) in func.arg_tys]

            call_name = 'raw::%s' % (gen_utils.c_name(func.path))
            ret = writer.gen.call(call_name, call_args)
            ret = func.ret_ty.transform('rust', ret, out=True)
            writer.expr(ret)

class RustFFIBindingGenerator(BindingGenerator):
    def generate(self, dest):
        path = dest / 'ffi.rs'

        self.makedir(path.parent)

        with path.open('w+') as f:
            gen = RustCodeGenerator(self.root)
            gen.pub = True
            writer = RustCodeWriter(gen, f)
            builder = RustFFICodeBuilder(writer)
            self._generate(builder)

    def _generate(self, builder):
        from bindgen.ast import objects as obj

        writer = builder.writer

        # Writer header
        writer.attr('allow', ['non_camel_case_types', 'non_snake_case', 'unstable'], glob=True)
        writer.writeln()

        # Write types
        def traverse_types():
            for item in sorted(self.root.traverse(), key=lambda item: item.name):
                if isinstance(item, obj.Function):
                    yield item.ret_ty

                    for (arg_ty, arg_name) in item.arg_tys:
                        yield arg_ty
                elif isinstance(item, obj.Class):
                    yield item
                elif isinstance(item, obj.Module):
                    yield from item.types
                elif isinstance(item, obj.Enum):
                    yield item

        types = set()
        for ty in traverse_types():
            ty_name = ty.ffi_name('rust')
            if ty_name not in types:
                ty.write_def('rust', writer)
                types.add(ty_name)

        # FFI functions
        writer.writeln()
        with writer.mod('raw', pub=False):
            with writer.extern('C'):
                for item in sorted(self.root.traverse(), key=lambda item: item.name):
                    if isinstance(item, obj.Function):
                        builder.generate_ffi_function(item)
                    elif isinstance(item, obj.RawFunction):
                        item.generate(builder, 'rust_ffi', decl=True)

        builder.generate_mod(self.root)
        self.root.extra('rust', writer)
