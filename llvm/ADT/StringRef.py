from bindgen.ast.objects import *
from ..ns import llvm

@llvm.body
class llvm_body:
    _includes_ = ['llvm/ADT/StringRef.h', 'llvm/ADT/Twine.h']

class _StringRef(ConvertibleType):
    def write_def(self, lang, writer):
        if lang == 'rust':
            writer.attr('repr', ['C'])
            writer.attr('derive', ['Copy'])

        writer.struct(members=[
            (ptr(Char, const=True).ffi_name(lang), 'data'),
            (SizeTy.ffi_name(lang), 'length'),
        ], name=self.flat_name())

    def flat_name(self):
        return 'llvm_StringRef'

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
            return writer.gen.call('::llvm::StringRef', args)
        elif lang == 'rust':
            data = writer.gen.borrow(writer.gen.member(expr, 'data'))
            length = writer.gen.cast(writer.gen.member(expr, 'length'), 'usize')
            slice = writer.gen.call('::std::slice::from_raw_buf', [data, length])
            slice = writer.gen.call('::std::mem::transmute', [slice])
            result = writer.gen.call('::std::str::from_utf8_unchecked', [slice])

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
            return writer.gen.init_struct(struct_name, [
                ('data', writer.gen.cast(writer.gen.call(writer.gen.member(expr, 'as_ptr')), ptr(Char, const=True).ffi_name(lang))),
                ('length', writer.gen.cast(writer.gen.call(writer.gen.member(expr, 'len')), SizeTy.ffi_name(lang))),
            ])

        return super().convert_to_ffi(writer, lang, expr, **kwargs)

StringRef = _StringRef()
