from bindgen.ast.objects import *
from ..ns import llvm

@llvm.body
class llvm_body:
    _includes_ = ['llvm/ADT/ArrayRef.h']

def is_class_type(ty):
    return isinstance(ty, (Pointer, Ref)) and isinstance(ty.subtype, Class)

class ArrayRef(ConvertibleType):
    def __init__(self, subtype):
        super().__init__()

        self.subtype = subtype

    def write_def(self, lang, writer):
        if lang == 'rust':
            writer.attr('repr', ['C'])
            writer.attr('derive', ['Copy'])

        writer.struct(members=[
            (ptr(self.subtype, const=True).ffi_name(lang), 'data'),
            (SizeTy.ffi_name(lang), 'length'),
        ], name=self.flat_name())

    def flat_name(self):
        return 'llvm_ArrayRef_%s' % (self.subtype.flat_name())

    def ffi_name(self, lang, **kwargs):
        if lang == 'c++':
            return '::llvm::ArrayRef<%s>' % (self.subtype.ffi_name('c', **kwargs))
        elif lang == 'rust':
            path = kwargs.get('path', []) + [self.flat_name()]
            return '::'.join(path)

        return self.flat_name()

    def lib_name(self, lang, **kwargs):
        if lang == 'rust':
            from bindgen.gen.rust import RustLibConstants

            name = self.subtype.lib_name(lang, trait=True, **kwargs)
            return '&[%s]' % (name)

        return super().lib_name(lang, **kwargs)

    def convert_from_ffi(self, writer, lang, expr, **kwargs):
        if lang == 'c':
            args = [writer.gen.member(expr, 'data'), writer.gen.member(expr, 'length')]
            return writer.gen.call(self.ffi_name('c++'), args)
        elif lang == 'rust':
            return expr

        return super().convert_from_ffi(writer, lang, expr, **kwargs)

    def convert_to_ffi(self, writer, lang, expr, **kwargs):
        if lang == 'c':
            members = [
                ('data', writer.gen.member(expr, writer.gen.call('data'))),
                ('length', writer.gen.member(expr, writer.gen.call('size'))),
            ]
            return writer.gen.init_struct(members)
        elif lang == 'rust':
            data = expr

            if is_class_type(self.subtype):
                data_name = '_tmp_%s' % (expr)

                data_vec = '%s.iter().map(|ty| ty.inner()).collect()' % (data)
                writer.declare_var(data_name, 'Vec<_>', data_vec)
                data = data_name

            struct_name = '::ffi::%s' % (self.ffi_name(lang))
            data_ptr = writer.gen.call(writer.gen.member(data, 'as_ptr'))
            return writer.gen.init_struct(struct_name, [
                ('data', data_ptr),
                ('length', writer.gen.cast(writer.gen.call(writer.gen.member(expr, 'len')), SizeTy.ffi_name(lang))),
            ])

        return super().convert_to_ffi(writer, lang, expr, **kwargs)
