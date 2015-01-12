from . import BindingGenerator, CodeGenerator, CodeWriter
from contextlib import contextmanager

class CCodeGenerator(CodeGenerator):
    def declare_var(self, ty, name, init=None, **kwargs):
        text = ''
        if kwargs.get('static', False):
            text += 'static '
        text += '%s %s' % (ty, name)
        if init is not None:
            text += ' = %s' % (init)
        text += ';'

        return text

    def declare_function(self, name, ret_ty, args=[], **kwargs):
        text = 'extern "C"\n'
        if kwargs.get('static', False):
            text += 'static '
        text += '%s %s(' % (ret_ty, name)
        for (i, (arg_ty, arg_name)) in enumerate(args):
            if i > 0:
                text += ', '
            text += '%s %s' % (arg_ty, arg_name)
        text += ')'

        return text

    def typedef(self, name, ty):
        return 'typedef %s %s;' % (ty, name)

    def struct(self, members=[], name=None):
        text = 'struct'
        if name is not None:
            text += ' %s' % (name)
        text += ' {\n'
        for (member_ty, member_name) in members:
            text += '    %s %s;\n' % (member_ty, member_name)
        text += '}'

        return text

    def enum(self, values=[], name=None):
        text = 'enum'
        if name is not None:
            text += ' %s' % (name)
        text += '{\n'
        for value in values:
            if isinstance(value, tuple):
                (value_name, value_val) = value
                text += '%s = %d,' % (value_name, value_val)
            else:
                text += '%s,' % (value)
            text += '\n'
        text += '}'

        return text

    def init_struct(self, values=[]):
        text = '{\n'
        for value in values:
            text += ' '*4
            if isinstance(value, tuple):
                (value_name, value_value) = value
                text += '.%s = %s,' % (value_name, value_value)
            else:
                text += '%s,' % (value)
            text += '\n'
        text += '}'

        return text

    def assign_var(self, name, value):
        return '%s = %s' % (name, value)

    def call(self, name, args=[]):
        return '%s(%s)' % (name, ', '.join(list(args)))

    def include(self, filename, system=False):
        c = '<>' if system else '""'
        return '#include %c%s%c' % (c[0], filename, c[1])

    def comment(self, text):
        lines = text.splitlines()

        if len(lines) > 1:
            text = '/*\n'
            for line in lines:
                text += ' * ' + line + '\n'
            text += '*/'
        else:
            text = '// ' + lines[0]

        return text

    def ret(self, value):
        return 'return %s;' % (value)

    def delete(self, name):
        return 'delete %s;' % (name)

    def new(self, name, args=[]):
        return 'new %s' % (self.call(name, args))

    def member(self, expr, name, ptr=False):
        c = '->' if ptr else '.'
        return '%s%s%s' % (expr, c, name)

    def c_name(self, path):
        from . import utils
        return utils.c_name(path)

    def cpp_name(self, path):
        from . import utils
        return utils.cpp_name(path)

class CCodeWriter(CodeWriter):
    def _gen_proxy(name):
        def proxy(self, *args, **kwargs):
            m = getattr(self.gen, name)
            self.writeln(m(*args, **kwargs))
        return proxy

    def declare_function(self, *args, **kwargs):
        self.writeln('%s;' % (self.gen.declare_function(*args, **kwargs)))

    def assign_var(self, *args, **kwargs):
        self.writeln('%s;' % (self.gen.assign_var(*args, **kwargs)))

    @contextmanager
    def function(self, *args, **kwargs):
        self.writeln(self.gen.declare_function(*args, **kwargs))
        with self.block():
            yield

    @contextmanager
    def block(self):
        self.writeln('{')
        with self.indent():
            yield
        self.writeln('}')

    def call(self, *args, **kwargs):
        self.writeln('%s;' % (self.gen.call(*args, **kwargs)))

    def struct(self, *args, **kwargs):
        self.writeln('%s;' % (self.gen.struct(*args, **kwargs)))

    def enum(self, *args, **kwargs):
        self.writeln('%s;' % (self.gen.enum(*args, **kwargs)))

    declare_var = _gen_proxy('declare_var')
    include = _gen_proxy('include')
    typedef = _gen_proxy('typedef')
    comment = _gen_proxy('comment')
    ret = _gen_proxy('ret')
    delete = _gen_proxy('delete')
    new = _gen_proxy('new')

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

GENERATORS = [
    CFFIBindingGenerator,
]
