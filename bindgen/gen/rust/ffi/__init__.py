from bindgen.ast.visit import Aggregator, EntityVisitor
from .. import RustBindingGenerator
from ..codegen import RustCodeGenerator
from ..codewriter import RustCodeWriter
from ... import BindingGenerator


class LinkNamesAggregator(EntityVisitor, Aggregator):

    def __init__(self, *args, **kwargs):
        EntityVisitor.__init__(self, *args, **kwargs)
        Aggregator.__init__(self)

    def visit_Entity(self, entity):
        linknames = entity.attrs.get('rust-linknames', [])
        self.items += linknames

        return True


class RustFFIBindingGenerator(BindingGenerator):
    LANG = RustBindingGenerator.LANG

    def generate(self, dest):
        self.makedir(dest)
        gen = RustCodeGenerator()

        # Generate FFI
        path = dest / 'ffi.rs'

        with path.open('w+') as f:
            writer = RustCodeWriter(gen, f)
            self._generate(writer)

    def _generate(self, writer):
        from .gen import ty, func

        types = self.create_type_aggregator()
        types(self.root)

        linknames = LinkNamesAggregator()
        linknames(self.root)

        types_registry = self.registry(ty.ENTRY)

        # Generate module attributes
        def allow(name):
            writer.attr('allow(%s)' % (name), glob=True)
        allow('dead_code')
        allow('non_camel_case_types')
        allow('non_snake_case')

        # Generate module imports
        writer.extern_crate('libc')

        # Generate type definitions
        if len(types) > 0:
            writer.writeln()
        for ty in types:
            Generator = types_registry[ty.__class__]
            gen = Generator(self, ty)

            if hasattr(gen, 'generate_def'):
                gen.generate_def(writer)

        self._generate_raw(writer)
        self._generate_proxy(writer)

    # Generate raw FFI functions
    def _generate_raw(self, writer):
        from .gen import func

        linknames = LinkNamesAggregator()
        linknames(self.root)

        functions = self.create_function_aggregator()
        functions(self.root)

        functions_registry = self.registry(func.ENTRY)

        writer.writeln()
        with writer.mod('raw', pub=True):
            for linkname in linknames:
                name = linkname
                kind = None

                if ':' in linkname:
                    (name, kind) = linkname.split(':', 2)

                args = {
                    'name': name,
                }
                if kind is not None:
                    args['kind'] = kind

                args = ['%s = "%s"' % (key, value)
                        for (key, value) in args.items()]
                writer.attr('link(%s)' % (', '.join(args)))

            with writer.extern('C'):
                for func in functions:
                    Generator = functions_registry[func.__class__]
                    gen = Generator(self, func)

                    gen.generate_raw(writer, ['super'])

    # Generate proxy FFI functions
    def _generate_proxy(self, writer):
        writer.writeln()
        self._generate_proxy_mod(writer, self.root)

    def _generate_proxy_mod(self, writer, mod, root=[]):
        from bindgen.ast import Module, Function
        from .gen import func

        functions_registry = self.registry(func.ENTRY)

        items = []
        items += [item for item in sorted(
            mod, key=lambda item: item.name) if isinstance(item, Module)]
        items += [item for item in sorted(
            mod, key=lambda item: item.name) if isinstance(item, Function)]

        for (i, item) in enumerate(items):
            if i > 0:
                writer.writeln()

            if isinstance(item, Module):
                with writer.mod(item.name, pub=True):
                    self._generate_proxy_mod(
                        writer, item, root=root + ['super'])
            elif isinstance(item, Function):
                Generator = functions_registry[item.__class__]
                gen = Generator(self, item)

                gen.generate_proxy(writer, root)

    def create_registry(self):
        from . import gen

        reg = super().create_registry()
        gen.register(reg)
        return reg

    def create_type_aggregator(self):
        from bindgen.ast import Class, Enum

        visitor = super().create_type_aggregator()
        visitor.add_class_segment(Class)
        visitor.add_class_segment(Enum)
        visitor.sorter = lambda ty: ty.tyname
        return visitor

    def create_function_aggregator(self):
        from bindgen.ast import Function

        visitor = super().create_function_aggregator()
        visitor.add_segment(lambda fn: fn.__class__ is Function)
        visitor.sorter = lambda fn: '_'.join(fn.path)
        return visitor
