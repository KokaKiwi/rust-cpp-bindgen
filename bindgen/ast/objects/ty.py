import enum
from bindgen.gen import utils as gen_utils

class _Type(object):
    def __init__(self):
        pass

    def write_def(self, lang, writer):
        pass

    def flat_name(self):
        raise NotImplementedError('_Type.flat_name')

    def ffi_name(self, lang, **kwargs):
        raise NotImplementedError('_Type.ffi_name')

    def lib_name(self, lang, **kwargs):
        raise NotImplementedError('_Type.lib_name')

    def transform(self, lang, expr, out=False):
        return expr

class ConvertibleType(_Type):
    def convert_to_ffi(self, writer, lang, expr, **kwargs):
        raise NotImplementedError('ConvertibleType.convert_to_ffi')

    def convert_from_ffi(self, writer, lang, expr, **kwargs):
        raise NotImplementedError('ConvertibleType.convert_from_ffi')

class BoolType(_Type):
    def flat_name(self):
        return 'bool'

    def ffi_name(self, lang, **kwargs):
        if lang == 'c':
            return 'int'
        elif lang == 'rust':
            return _rust_tyname('c_int')

        return super().ffi_name(lang, **kwargs)

    def lib_name(self, lang, **kwargs):
        if lang == 'rust':
            return 'bool'

        return super().lib_name(lang, **kwargs)

    def transform(self, lang, expr, out=False):
        if lang == 'c':
            if out:
                expr = '(%s == true ? 1 : 0)' % (expr)
            else:
                expr = '(%s == 1 ? true : false)' % (expr)
        elif lang == 'rust':
            if out:
                expr = '%s != 0' % (expr)
            else:
                expr = 'if %s { 1 } else { 0 }' % (expr)

        return expr

Bool = BoolType()

class Option(_Type):
    def __init__(self, subtype, default):
        super().__init__()

        self.subtype = subtype
        self.default = default

    def write_def(self, lang, writer):
        self.subtype.write_def(lang, writer)

    def flat_name(self):
        return self.subtype.flat_name()

    def ffi_name(self, lang, **kwargs):
        return self.subtype.ffi_name(lang, **kwargs)

    def lib_name(self, lang, **kwargs):
        return self.subtype.lib_name(lang, **kwargs)

    def transform(self, lang, expr, out=False):
        return self.subtype.transform(lang, expr, out=out)

class BuiltinType(_Type):
    def __init__(self, cpp_name, rust_name, rust_lib_name=None):
        super().__init__()

        self.cpp_name = cpp_name
        self.rust_name = rust_name
        self.rust_lib_name = rust_lib_name

    def flat_name(self):
        return self.rust_name.replace('::', '_')

    def ffi_name(self, lang, **kwargs):
        if lang == 'c':
            return self.cpp_name
        elif lang == 'rust':
            return self.rust_name

        return super().ffi_name(lang, **kwargs)

    def lib_name(self, lang, **kwargs):
        if lang == 'rust':
            return self.rust_lib_name

        return super().lib_name(lang, **kwargs)

    def transform(self, lang, expr, out=False):
        if lang == 'rustlib' and self.rust_lib_name is not None:
            if out:
                expr = '%s as %s' % (expr, self.rust_lib_name)
            else:
                expr = '%s as %s' % (expr, self.rust_name)

        return expr

def _rust_tyname(name):
    return '::libc::%s' % (name)

Void = BuiltinType('void', _rust_tyname('c_void'))
Char = BuiltinType('char', _rust_tyname('c_char'), 'char')
Int = BuiltinType('int', _rust_tyname('c_int'), 'i32')
UnsignedChar = BuiltinType('unsigned char', _rust_tyname('c_uchar'), 'u8')
UnsignedInt = BuiltinType('unsigned int', _rust_tyname('c_uint'), 'u32')
SizeTy = BuiltinType('size_t', _rust_tyname('size_t'), 'usize')

Int8 = BuiltinType('int8_t', _rust_tyname('int8_t'), 'i8')
Int16 = BuiltinType('int16_t', _rust_tyname('int16_t'), 'i16')
Int32 = BuiltinType('int32_t', _rust_tyname('int32_t'), 'i32')
Int64 = BuiltinType('int64_t', _rust_tyname('int64_t'), 'i64')

UnsignedInt8 = BuiltinType('uint8_t', _rust_tyname('uint8_t'), 'u8')
UnsignedInt16 = BuiltinType('uint16_t', _rust_tyname('uint16_t'), 'u16')
UnsignedInt32 = BuiltinType('uint32_t', _rust_tyname('uint32_t'), 'u32')
UnsignedInt64 = BuiltinType('uint64_t', _rust_tyname('uint64_t'), 'u64')

Double = BuiltinType('double', _rust_tyname('c_double'), 'f64')
Float = BuiltinType('float', _rust_tyname('c_float'), 'f32')

class String(ConvertibleType):
    def __init__(self, const=False):
        super().__init__()

        self.const = const

    def write_def(self, lang, writer):
        if lang == 'rust':
            writer.attr('repr', ['C'])
            writer.attr('allow', ['raw_pointer_derive'])

        writer.struct(members=[
            (ptr(Char, const=self.const).ffi_name(lang), 'data'),
            (SizeTy.ffi_name(lang), 'length'),
        ], name=self.flat_name())

        if lang == 'rust':
            writer.writeln('impl Copy for %s {}' % (self.flat_name()))

    def flat_name(self):
        const = '_const' if self.const else ''
        return 'std_string%s' % (const)

    def ffi_name(self, lang, **kwargs):
        path = kwargs.get('path', []) + [self.flat_name()]
        return '::'.join(path)

    def lib_name(self, lang, **kwargs):
        if lang == 'rust':
            return '&str'

        return super().lib_name(lang, **kwargs)

    def convert_from_ffi(self, writer, lang, expr, **kwargs):
        if lang == 'c':
            args = [writer.gen.member(expr, 'data'), writer.gen.member(expr, 'length')]
            return writer.gen.call('std::string', args)
        elif lang == 'rust':
            data = writer.gen.borrow(writer.gen.member(expr, 'data'))
            length = writer.gen.cast(writer.gen.member(expr, 'length'), 'usize')
            slice = writer.gen.call('::core::slice::from_raw_buf', [data, length])
            slice = writer.gen.call('::core::mem::transmute', [slice])
            result = writer.gen.call('::core::str::from_utf8_unchecked', [slice])

            return result

        return super().convert_from_ffi(writer, lang, expr, **kwargs)

    def convert_to_ffi(self, writer, lang, expr, **kwargs):
        if lang == 'c':
            members = [
                ('data', writer.gen.member(expr, writer.gen.call('data'))),
                ('length', writer.gen.member(expr, writer.gen.call('size'))),
            ]
            return writer.gen.init_struct(members)
        elif lang == 'rust':
            struct_name = '::ffi::%s' % (self.ffi_name(lang))
            data_ptr = writer.gen.call(writer.gen.member(expr, 'as_ptr'))
            data_len = writer.gen.call(writer.gen.member(expr, 'len'))
            return writer.gen.init_struct(struct_name, [
                ('data', writer.gen.cast(data_ptr, ptr(Char, const=self.const).ffi_name(lang))),
                ('length', writer.gen.cast(data_len, SizeTy.ffi_name(lang))),
            ])

        return super().convert_to_ffi(writer, lang, expr, **kwargs)

class OptionString(Option):
    def __init__(self, *args, **kwargs):
        super().__init__(String(*args, **kwargs), '""')

class Ref(_Type):
    def __init__(self, subtype, const=False):
        super().__init__()

        self.subtype = subtype
        self.const = const

    def flat_name(self):
        name = '%s_ref' % (self.subtype.flat_name())

        if self.const:
            name = 'const_%s' % (name)

        return name

    def ffi_name(self, lang, **kwargs):
        if lang == 'c':
            if self.const:
                fmt = '{subtype} const*'
            else:
                fmt = '{subtype}*'
        elif lang == 'rust':
            if self.const:
                fmt = '*const {subtype}'
            else:
                fmt = '*mut {subtype}'
        else:
            return super().ffi_name(lang, **kwargs)

        return fmt.format(subtype=self.subtype.ffi_name(lang, **kwargs))

    def lib_name(self, lang, **kwargs):
        if lang == 'rust':
            return '&%s' % (self.subtype.lib_name(lang, **kwargs))

        return super().lib_name(lang, **kwargs)

    def transform(self, lang, expr, out=False):
        if lang == 'c':
            if out:
                return '&(%s)' % (expr)
            else:
                return '*%s' % (expr)

        return super().transform(lang, expr)

ref = Ref

class Pointer(_Type):
    class Null(enum.Enum):
        option = 1
        panic = 2

    def __init__(self, subtype, const=False, owned=False, null=Null.option):
        super().__init__()

        self.subtype = subtype
        self.const = const
        self.owned = owned
        self.null = null

    def flat_name(self):
        name = '%s_ptr' % (self.subtype.flat_name())

        if self.const:
            name = 'const_%s' % (name)

        return name

    def ffi_name(self, lang, **kwargs):
        return Ref.ffi_name(self, lang, **kwargs)

    def lib_name(self, lang, **kwargs):
        if lang == 'rust':
            return '&%s' % (self.subtype.lib_name(lang, **kwargs))

        return super().lib_name(lang, **kwargs)

ptr = Pointer
