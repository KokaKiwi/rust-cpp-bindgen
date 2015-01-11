from .entity import Entity
from .ty import _Type
from bindgen.gen import utils as gen_utils

class Enum(Entity, _Type):
    def __init__(self, name=None, values=[]):
        Entity.__init__(self)
        _Type.__init__(self)

        self.name = None
        self.values = values

    def write_def(self, lang, writer):
        if lang == 'rust':
            writer.attr('repr', ['C'])
            writer.attr('derive', ['Copy'])
            writer.enum(self.flat_name(), self.values)
        else:
            super().write_def(lang, writer)

    def flat_name(self):
        return gen_utils.c_name(self.path)

    def ffi_name(self, lang, **kwargs):
        if lang == 'c':
            return gen_utils.cpp_name(self.path)
        elif lang == 'rust':
            path = kwargs.get('path', []) + [self.flat_name()]
            return '::'.join(path)

        return super().ffi_name(lang)

    def lib_name(self, lang, **kwargs):
        if lang == 'rust':
            return '::ffi::%s' % (self.flat_name())

        return super().lib_name(lang, **kwargs)
