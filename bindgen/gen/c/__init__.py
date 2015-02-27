from bindgen.ast.visit import EntityVisitor, Aggregator
from .. import BindingGenerator
from ..registry import MappedRegistry, sub_registry
from .codegen import CCodeGenerator
from .codewriter import CCodeWriter


class IncludeAggregator(EntityVisitor, Aggregator):

    def __init__(self):
        EntityVisitor.__init__(self)
        Aggregator.__init__(self, set)

        self.sorter = lambda include: include

    def visit_Entity(self, entity):
        includes = entity.attrs.get('includes', set())
        self.items |= includes

        return True

    @property
    def includes(self):
        yield from self


class CBindingGenerator(BindingGenerator):
    LANG = 'c'

    def generate(self, dest):
        self.makedir(dest)
        gen = CCodeGenerator()

        # Create header
        path = dest / 'ffi.h'

        with path.open('w+') as f:
            writer = CCodeWriter(gen, f)
            self._generate_header(writer)

        # Create source
        path = dest / 'ffi.cpp'

        with path.open('w+') as f:
            writer = CCodeWriter(gen, f)
            self._generate_source(writer)

    def _generate_header(self, writer):
        from .gen import ty, func

        writer.cpp_ifndef('FFI_H_')
        writer.cpp_define('FFI_H_')
        writer.writeln()

        writer.cpp_ifdef('__cplusplus')
        # Generate includes
        visitor = IncludeAggregator()
        visitor(self.root)

        for include in visitor:
            writer.include(include)
        writer.cpp_endif('__cplusplus')

        # Generate type definitions
        visitor = self.create_type_aggregator()
        visitor(self.root)

        types_registry = self.registry(ty.ENTRY)
        for ty in visitor:
            Generator = types_registry[ty.__class__]
            gen = Generator(self, ty)

            if hasattr(gen, 'generate_def'):
                writer.writeln()
                gen.generate_def(writer)

        # Generate function definitions
        visitor = self.create_function_aggregator()
        visitor(self.root)

        functions_registry = self.registry(func.ENTRY)
        for func in visitor:
            Generator = functions_registry[func.__class__]
            gen = Generator(self, func)

            writer.writeln()
            gen.generate_def(writer)

        writer.writeln()
        writer.cpp_endif('FFI_H_')

    def _generate_source(self, writer):
        from .gen import ty, func

        # Generate includes
        visitor = IncludeAggregator()
        visitor(self.root)

        for include in visitor:
            writer.include(include)

        writer.include('ffi.h')

        # Generate function implementations
        visitor = self.create_function_aggregator()
        visitor(self.root)

        functions_registry = self.registry(func.ENTRY)
        for func in visitor:
            Generator = functions_registry[func.__class__]
            gen = Generator(self, func)

            writer.writeln()
            gen.generate_impl(writer)

    def create_registry(self):
        from .gen import register

        reg = super().create_registry()
        register(reg)
        return reg

    def create_type_aggregator(self):
        from bindgen.ast import Class, Enum

        visitor = super().create_type_aggregator()
        visitor.add_class_segment(Class)
        visitor.add_class_segment(Enum)
        return visitor

    def create_function_aggregator(self):
        from bindgen.ast import Function

        visitor = super().create_function_aggregator()
        visitor.add_segment(lambda fn: fn.__class__ is Function)
        visitor.sorter = lambda fn: fn.real_path
        return visitor
