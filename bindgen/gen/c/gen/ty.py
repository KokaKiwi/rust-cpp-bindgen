import enum
from . import CGenerator

ENTRY = 'type'


class TypeConvert(object):

    class Kind(enum.Enum):
        inline = 1
        complex = 2

    # convert function signature match kind:
    #   inline: (writer, expr) -> str
    #   complex: (writer, dest, expr)
    def __init__(self, kind, convert):
        if isinstance(kind, str):
            kind = TypeConvert.Kind[kind]

        self.kind = kind
        self.convert = convert

    def __call__(self, *args, **kwargs):
        return self.convert(*args, **kwargs)


class CTypeGenerator(CGenerator):

    def __init__(self, parent, ty):
        super().__init__(parent)
        self.ty = ty

    @property
    def cpp_name(self):
        raise NotImplementedError('CTypeGenerator.cpp_name')

    @property
    def ffi_name(self):
        raise NotImplementedError('CTypeGenerator.ffi_name')

    @property
    def flat_name(self):
        raise NotImplementedError('CTypeGenerator.flat_name')

    # Should return a TypeConvert object or None
    # if not a convertable type
    def convert(self, out=False):
        return None


class BuiltinTypeGenerator(CTypeGenerator):
    NAMES = {
        'void':     'void',

        'char':     'char',
        'int':      'int',
        'uchar':    'unsigned char',
        'uint':     'unsigned int',
        'size':     'size_t',

        'int8':     'int8_t',
        'int16':    'int16_t',
        'int32':    'int32_t',
        'int64':    'int64_t',
        'uint8':    'uint8_t',
        'uint16':   'uint16_t',
        'uint32':   'uint32_t',
        'uint64':   'uint64_t',

        'double':   'double',
        'float':    'float',

        # Boolean type is represented as int in
        # order to provide compatibility.
        # 1 - true
        # 0 - false
        'bool':     ('bool', 'int'),
    }

    @property
    def cpp_name(self):
        name = self.NAMES[self.ty.ty.name]
        if isinstance(name, tuple):
            name = name[0]
        return name

    @property
    def ffi_name(self):
        name = self.NAMES[self.ty.ty.name]
        if isinstance(name, tuple):
            name = name[1]
        return name

    @property
    def flat_name(self):
        return self.ty.ty.name

    def convert(self, out=False):
        if self.ty.ty.name == 'bool':
            def convert(writer, expr):
                if out:
                    return '(%s ? 1 : 0)' % (expr)
                else:
                    return '(%s == 1 ? true : false)' % (expr)

            return TypeConvert('inline', convert)

        return None


class StringTypeGenerator(CTypeGenerator):

    def generate_def(self, writer):
        data_ty = self.typegen(self.data_type)

        struct_def = writer.gen.struct_def([
            (data_ty.ffi_name, 'data'),
            ('size_t', 'length'),
        ])
        writer.typedef(self.ffi_name, struct_def)

    @property
    def data_type(self):
        from bindgen.ast import Pointer, Char
        return Pointer(Char, const=self.ty.const)

    @property
    def cpp_name(self):
        return 'std::string'

    @property
    def ffi_name(self):
        name = 'std_string'
        if self.ty.const:
            name += '_const'
        return name

    @property
    def flat_name(self):
        return self.ffi_name

    def convert(self, out=False):
        def convert_in(writer, dest, expr):
            data = writer.gen.member(expr, 'data')
            length = writer.gen.member(expr, 'length')

            writer.writeln('std::string %s(%s, %s);' % (dest, data, length))

        def convert_out(writer, expr):
            data_meth = writer.gen.member(expr, 'data')
            data = writer.gen.call(data_meth)

            length_meth = writer.gen.member(expr, 'length')
            length = writer.gen.call(length_meth)

            return writer.gen.struct_init([
                ('data', data),
                ('length', length),
            ])

        if out:
            return TypeConvert('inline', convert_out)
        else:
            return TypeConvert('complex', convert_in)


class OptionTypeGenerator(CTypeGenerator):

    @property
    def cpp_name(self):
        from bindgen.ast import Pointer

        ty = Pointer(self.ty.subtype)
        gen = self.typegen(ty)
        return gen.cpp_name

    @property
    def ffi_name(self):
        from bindgen.ast import Pointer

        ty = Pointer(self.ty.subtype)
        gen = self.typegen(ty)
        return gen.ffi_name

    @property
    def flat_name(self):
        subgen = self.typegen(self.ty.subtype)
        return 'opt_%s' % (subgen.flat_name)

    def convert(self, out=False):
        subgen = self.typegen(self.ty.subtype)

        def convert_in(writer, dest, expr):
            writer.declare_var(subgen.cpp_name, dest, init=self.ty.default)
            writer.write('if (%s != NULL)' % (expr))
            with writer.block():
                value = '*%s' % (expr)

                subconvert = subgen.convert()

                if subconvert is not None:
                    if subconvert.kind == TypeConvert.Kind.inline:
                        value = subconvert(writer, '(%s)' % (value))
                    elif subconvert.kind == TypeConvert.Kind.complex:
                        subconvert(writer, '__%s_value' %
                                   (dest), '(%s)' % (value))
                        value = '__%s_value' % (dest)

                writer.assign_var(dest, value)

        if out:
            raise NotImplementedError('OptionTypeGenerator.convert (out)')
        else:
            return TypeConvert('complex', convert_in)


class RefTypeGenerator(CTypeGenerator):

    @property
    def cpp_name(self):
        subgen = self.typegen(self.ty.subtype)

        name = subgen.cpp_name
        if self.ty.const:
            name += ' const'
        name += '&'

        return name

    @property
    def ffi_name(self):
        subgen = self.typegen(self.ty.subtype)

        name = subgen.ffi_name
        if self.ty.const:
            name += ' const'
        name += '*'

        return name

    @property
    def flat_name(self):
        subgen = self.typegen(self.ty.subtype)

        name = 'ref_%s' % (subgen.flat_name)
        if self.ty.const:
            name += '_const'

        return name

    def convert(self, out=False):
        def convert(writer, expr):
            c = '&' if out else '*'
            return '%s%s' % (c, expr)

        return TypeConvert('inline', convert)


class PointerTypeGenerator(CTypeGenerator):

    @property
    def cpp_name(self):
        subgen = self.typegen(self.ty.subtype)

        name = subgen.cpp_name
        if self.ty.const:
            name += ' const'
        name += '*'

        return name

    @property
    def ffi_name(self):
        subgen = self.typegen(self.ty.subtype)

        name = subgen.ffi_name
        if self.ty.const:
            name += ' const'
        name += '*'

        return name

    @property
    def flat_name(self):
        subgen = self.typegen(self.ty.subtype)

        name = 'ptr_%s' % (subgen.flat_name)
        if self.ty.const:
            name += '_const'

        return name


class ClassTypeGenerator(CTypeGenerator):

    def generate_def(self, writer):
        writer.cpp_ifdef('__cplusplus')
        writer.typedef(self.ffi_name, self.cpp_name)
        writer.cpp_else()
        writer.typedef(self.ffi_name, writer.gen.struct_def())
        writer.cpp_endif('__cplusplus')

    @property
    def cpp_name(self):
        return self.gen_cpp_name(self.ty.real_path)

    @property
    def ffi_name(self):
        return self.gen_c_name(self.ty.path)

    @property
    def flat_name(self):
        return self.ffi_name

# TODO: Implement enums


class EnumTypeGenerator(CTypeGenerator):

    def generate_def(self, writer):
        writer.cpp_ifdef('__cplusplus')
        writer.typedef(self.ffi_name, self.cpp_name)
        writer.cpp_else()
        values = []
        for entry in self.ty.values:
            name = '%s_%s' % (self.ty.name, entry.name)
            value = entry.value
            if isinstance(value, (str,)):
                value = '%s_%s' % (self.ty.name, value)
            values.append((name, value))
        writer.typedef(self.ffi_name, writer.gen.enum_def(values))
        writer.cpp_endif('__cplusplus')

    @property
    def cpp_name(self):
        return self.gen_cpp_name(self.ty.real_path)

    @property
    def ffi_name(self):
        return self.gen_c_name(self.ty.path)

    @property
    def flat_name(self):
        return self.ffi_name


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
