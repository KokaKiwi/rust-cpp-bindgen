from .mod import Module
from .ty import _Type
from bindgen.gen import utils as gen_utils

class Class(Module, _Type):
    def __init__(self, name, *bases):
        Module.__init__(self)
        _Type.__init__(self)

        self.name = name
        self.cpp_name = self.name
        self.bases = list(bases)
        self.upclasses = self.bases
        self.downclasses = list()

        for base in self.upclasses:
            base.downclasses.append(self)

    @property
    def methods(self):
        return self.functions

    @property
    def constructor(self):
        from .func import Constructor

        for item in self.items:
            if isinstance(item, Constructor):
                return item

        return None

    @property
    def destructor(self):
        from .func import Destructor

        for item in self.items:
            if isinstance(item, Destructor):
                return item

        for base in self.bases:
            destructor = base.destructor
            if destructor is not None:
                return destructor

        return None

    @property
    def self_type(self):
        from .ty import ptr

        return ptr(self)

    def add_body_item(self, name, item):
        if name == '_realname_':
            self.cpp_name = item
        else:
            super().add_body_item(name, item)

    def all_downclasses(self):
        for down in self.downclasses:
            yield down
            yield from down.all_downclasses()

    def all_upclasses(self):
        for up in self.upclasses:
            yield up
            yield from up.all_upclasses()

    def all_casts(self):
        yield from self.all_downclasses()
        yield from self.all_upclasses()

    def write_def(self, lang, writer):
        if lang == 'rust':
            writer.attr('repr', ['C'])
            writer.attr('derive', ['Copy'])
            writer.struct(self.flat_name())
        else:
            super().write_def(lang, writer)

    def flat_name(self):
        return gen_utils.c_name(self.path)

    def ffi_name(self, lang, **kwargs):
        if lang == 'c':
            path = self.path
            path[-1] = self.cpp_name
            return gen_utils.cpp_name(path)
        elif lang == 'rust':
            path = kwargs.get('path', []) + [self.flat_name()]
            return '::'.join(path)

        return super().ffi_name(lang)

    def lib_name(self, lang, **kwargs):
        if lang == 'rust':
            from bindgen.gen.rust import RustLibConstants

            tree = kwargs['tree']
            item = tree.root.find(lambda item: item.item == self)
            path = [''] + item.fullpath
            name = '::'.join(path)

            if kwargs.get('trait', False):
                name = RustLibConstants.INNER_TRAIT_NAME.format(name=name)
            elif kwargs.get('impl', False):
                name = RustLibConstants.STRUCT_NAME.format(name=name)
            elif kwargs.get('inner', False):
                name = RustLibConstants.INNER_NAME.format(name=name)

            return name

        return super().lib_name(lang, **kwargs)
