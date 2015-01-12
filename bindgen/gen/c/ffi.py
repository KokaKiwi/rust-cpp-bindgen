from .codegen import CCodeGenerator
from .codewriter import CCodeWriter
from .. import BindingGenerator

class CFFIBindingGenerator(BindingGenerator):
    def generate(self, dest):
        path = dest / 'ffi.cpp'

        self.makedir(path.parent)

        with path.open('w+') as f:
            gen = CCodeGenerator(self.root)
            writer = CCodeWriter(gen, f)
            self._generate(writer)

    def _generate(self, writer):
        from bindgen.ast import objects as obj

        # Includes
        includes = set()

        for item in self.root.traverse():
            if isinstance(item, obj.Module):
                includes |= item.includes

        writer.include('string', system=True)
        for include in sorted(includes):
            writer.include(include)
        writer.writeln()

        # Write types
        def traverse_types():
            for item in self.root.traverse():
                if isinstance(item, obj.Function):
                    yield item.ret_ty

                    for (arg_ty, arg_name) in item.arg_tys:
                        yield arg_ty
                elif isinstance(item, obj.Class):
                    yield item
                elif isinstance(item, obj.Module):
                    yield from item.types

        types = set()
        for ty in traverse_types():
            ty_name = ty.ffi_name('c')
            if ty_name not in types:
                ty.write_def('c', writer)
                types.add(ty_name)

        # Methods/Functions
        for item in self.root.traverse():
            if isinstance(item, obj.Function):
                writer.writeln()
                self._generate_function(writer, item)

    def _generate_function(self, writer, func):
        from bindgen.ast import objects as obj

        writer.comment(writer.gen.cpp_name(func.path))

        name = writer.gen.c_name(func.path)
        ret_ty = func.ret_ty.ffi_name('c')

        args = []
        for (arg_ty, arg_name) in func.arg_tys:
            if isinstance(arg_ty, obj.ConvertibleType):
                arg_name = '_' + arg_name

            arg_ty = arg_ty.ffi_name('c')

            args.append((arg_ty, arg_name))

        with writer.function(name, ret_ty, args):
            # Prepare arguments
            for (arg_ty, arg_name) in func.arg_tys:
                if isinstance(arg_ty, obj.ConvertibleType):
                    value = arg_ty.convert_from_ffi(writer, 'c', '_' + arg_name)
                    writer.declare_var('auto', arg_name, value)

            # Call function
            call_args = [arg_ty.transform('c', arg_name) for (arg_ty, arg_name) in func.arg_tys]

            if isinstance(func, obj.Constructor):
                call_name = 'new %s' % (writer.gen.cpp_name(func.parent.path))
            elif isinstance(func, obj.Destructor):
                this_arg = call_args[0]
                writer.delete(this_arg)
                return
            elif isinstance(func, obj.Method):
                this_arg = call_args[0]
                call_args = call_args[1:]

                call_name = '%s->%s' % (this_arg, func.call_name)
            else:
                path = func.path[:-1] + [func.call_name]
                call_name = writer.gen.cpp_name(path)

            ret = writer.gen.call(call_name, call_args)

            if isinstance(func.ret_ty, obj.ConvertibleType):
                writer.declare_var('auto', 'ret', ret)
                ret = func.ret_ty.convert_to_ffi(writer, 'c', 'ret')

            writer.ret(func.ret_ty.transform('c', ret, out=True))