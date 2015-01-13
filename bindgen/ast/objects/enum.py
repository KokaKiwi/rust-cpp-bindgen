from .cls import Class
from .entity import Entity
from .ty import _Type
from ..utils import get_modpath
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
            values = []
            for value in self.values:
                if isinstance(value, tuple):
                    (name, value) = value

                    if isinstance(value, int):
                        values.append((name, value))
                else:
                    values.append(value)
            writer.enum(self.flat_name(), values)
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
            path = [''] + get_modpath(self) + [self.name]
            return '::'.join(path)

        return super().lib_name(lang, **kwargs)

    def transform(self, lang, expr, out=False):
        if lang == 'rustlib':
            if out:
                ty_name = self.lib_name('rust')
                return '%s::from_ffi(%s)' % (ty_name, expr)
            else:
                return '%s.to_ffi()' % (expr)

        return super().transform(lang, expr, out)
