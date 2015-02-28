from . import RustFFIGenerator

ENTRY = 'ffi-type'


class Proxy(object):

    # convert function must be of the form:
    #   (writer, expr) -> result expr
    def __init__(self, name, convert):
        self.name = name
        self.convert = convert

    def __call__(self, *args, **kwargs):
        return self.convert(*args, **kwargs)

    def __bool__(self):
        return self.convert is not None


class RustFFITypeGenerator(RustFFIGenerator):

    def __init__(self, parent, ty):
        super().__init__(parent)
        self.ty = ty

    def typegen(self, ty):
        Generator = self.registry(ENTRY)[ty]
        return Generator(self.parent, ty)

    def proxy(self, root=[], out=False):
        return Proxy(self.ffi_name(root), None)

    def ffi_name(self, root=[]):
        raise NotImplementedError('RustFFITypeGenerator.ffi_name')

    def rust_name(self, root=[], out=False):
        return self.proxy(root, out=out).name

    @property
    def flat_name(self):
        raise NotImplementedError('RustFFITypeGenerator.ffi_name')


class BuiltinTypeGenerator(RustFFITypeGenerator):
    NAMES = {
        'void':     ('c_void',   '()'),

        'char':     ('c_char',   'i8'),
        'int':      ('c_int',    'isize'),
        'uchar':    ('c_uchar',  'u8'),
        'uint':     ('c_uint',   'usize'),
        'size':     ('size_t',   'usize'),

        'int8':     ('int8_t',   'i8'),
        'int16':    ('int16_t',  'i16'),
        'int32':    ('int32_t',  'i32'),
        'int64':    ('int64_t',  'i64'),
        'uint8':    ('uint8_t',  'u8'),
        'uint16':   ('uint16_t', 'u16'),
        'uint32':   ('uint32_t', 'u32'),
        'uint64':   ('uint64_t', 'u64'),

        'double':   ('c_double', 'f64'),
        'float':    ('c_float',  'f32'),

        # Boolean type is represented as int in
        # order to provide compatibility.
        # 1 - true
        # 0 - false
        'bool':     ('c_int',    'bool'),
    }

    def proxy(self, root=[], out=False):
        name = self.NAMES[self.ty.ty.name][1]

        def convert(writer, expr):
            dest_ty = name if out else self.ffi_name(root)

            if self.ty.ty.name == 'bool':
                if out:
                    expr = '%s != 0' % (expr)
                else:
                    expr = 'if %s { 1 } else { 0 }' % (expr)
            elif self.ty.ty.name != 'void':
                expr = '%s as %s' % (expr, dest_ty)

            return expr

        return Proxy(name, convert)

    def ffi_name(self, root=[]):
        name = self.NAMES[self.ty.ty.name][0]
        path = root + ['libc', name]
        return self.gen_rust_name(path)

    @property
    def flat_name(self):
        return self.ty.ty.name


class StringTypeGenerator(RustFFITypeGenerator):

    def generate_def(self, writer):
        from bindgen.ast import SizeTy

        data_ty = self.typegen(self.data_type)
        size_ty = self.typegen(SizeTy)

        writer.writeln()
        writer.attr('repr(C)')
        writer.struct_def(self.ffi_name(), [
            (data_ty.ffi_name(), 'data', True),
            (size_ty.ffi_name(), 'length', True),
        ], pub=True)

    @property
    def data_type(self):
        from bindgen.ast import Pointer, Char
        return Pointer(Char, const=self.ty.const)

    def proxy(self, root=[], out=False):
        from bindgen.ast import SizeTy

        name = self.ffi_name(root) if out else '&str'

        size_ty = self.typegen(SizeTy)
        size_proxy = size_ty.proxy(root, out=out)

        def convert_in(writer, expr):
            data = '%s.as_ptr()' % (expr)
            data = 'unsafe { ::std::mem::transmute(%s) }' % (data)

            length = size_proxy(writer, '%s.len()' % (expr))

            return writer.gen.struct_init(self.ffi_name(root), [
                ('data', data),
                ('length', length),
            ])

        # TODO: Implement this
        def convert_out(writer, expr):
            return expr

        return Proxy(name, convert_out if out else convert_in)

    def ffi_name(self, root=[]):
        name = 'std_string'
        if self.ty.const:
            name += '_const'
        return self.gen_rust_name(root + [name])

    @property
    def flat_name(self):
        return self.ffi_name


class OptionTypeGenerator(RustFFITypeGenerator):

    def proxy(self, root=[], out=False):
        subgen = self.typegen(self.ty.subtype)
        subproxy = subgen.proxy(root, out=out)

        name = 'Option<%s>' % (subproxy.name)

        def convert_in(writer, expr):
            if subproxy:
                var_name = 'opt_hack_%s' % (str(abs(hash(expr)))[:6])
                value = subproxy(writer, 'value')
                writer.declare_var(var_name, init='%s.map(|value| %s)' % (expr, value))
                expr = var_name

            expr = '%s.as_ref().map(|value| value as *const _).unwrap_or(::std::ptr::null())' % (expr)
            return expr

        # TODO: Implement this
        def convert_out(writer, expr):
            return expr

        return Proxy(name, convert_out if out else convert_in)

    def ffi_name(self, root=[]):
        from bindgen.ast import Pointer

        ty = Pointer(self.ty.subtype, const=True)
        gen = self.typegen(ty)
        return gen.ffi_name(root)

    @property
    def flat_name(self):
        subgen = self.typegen(self.ty.subtype)
        return 'opt_%s' % (subgen.flat_name)


class RefTypeGenerator(RustFFITypeGenerator):

    def ffi_name(self, root=[]):
        subgen = self.typegen(self.ty.subtype)

        name = subgen.ffi_name(root)
        const = 'const' if self.ty.const else 'mut'

        return '*%s %s' % (const, name)

    @property
    def flat_name(self):
        subgen = self.typegen(self.ty.subtype)

        name = 'ref_%s' % (subgen.flat_name)
        if self.ty.const:
            name += '_const'

        return name


class PointerTypeGenerator(RustFFITypeGenerator):

    def ffi_name(self, root=[]):
        subgen = self.typegen(self.ty.subtype)

        name = subgen.ffi_name(root)
        const = 'const' if self.ty.const else 'mut'

        return '*%s %s' % (const, name)

    @property
    def flat_name(self):
        subgen = self.typegen(self.ty.subtype)

        name = 'ptr_%s' % (subgen.flat_name)
        if self.ty.const:
            name += '_const'

        return name


class ClassTypeGenerator(RustFFITypeGenerator):

    def generate_def(self, writer):
        writer.attr('repr(C)')
        writer.struct_def(self.ffi_name(), pub=True)

    def ffi_name(self, root=[]):
        c_name = self.gen_c_name(self.ty.path)
        return self.gen_rust_name(root + [c_name])

    @property
    def flat_name(self):
        return self.ffi_name()


# TODO: Implement enums
class EnumTypeGenerator(RustFFITypeGenerator):

    def generate_def(self, writer):
        writer.typedef(self.ffi_name(), 'libc::c_int', pub=True)

    def ffi_name(self, root=[]):
        c_name = self.gen_c_name(self.ty.path)
        return self.gen_rust_name(root + [c_name])

    @property
    def flat_name(self):
        return self.ffi_name()


def register(reg):
    from bindgen.ast.cls import Class
    from bindgen.ast.enum import Enum
    from bindgen.ast.ty import BuiltinType, String, Option, Ref, Pointer

    reg[BuiltinType] = BuiltinTypeGenerator
    reg[String] = StringTypeGenerator
    reg[Option] = OptionTypeGenerator
    reg[Ref] = RefTypeGenerator
    reg[Pointer] = PointerTypeGenerator

    reg[Class] = ClassTypeGenerator

    reg[Enum] = EnumTypeGenerator
