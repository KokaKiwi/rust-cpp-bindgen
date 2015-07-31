from ..ast.visit import TypeAggregator, FunctionAggregator, ClassAggregator, TYPE_VISIT_ENTRY, FUNCTION_VISIT_ENTRY
from .registry import sub_registry


class BindingGenerator(object):
    LANG = None

    def __init__(self, root):
        self.root = root

        self._registry = None

    def generate(self, dest):
        raise NotImplemented('BindingGenerator.generate')

    def makedir(self, path):
        if not path.exists():
            path.mkdir(parents=True)

    def registry(self, entry):
        if self._registry is None:
            self._registry = self.create_registry()

        return self._registry.map(entry)

    def create_registry(self):
        registry = sub_registry()
        return registry.map(self.__class__.LANG)

    def create_type_aggregator(self):
        types_registry = self.registry(TYPE_VISIT_ENTRY)
        return TypeAggregator(types_registry)

    def create_class_aggregator(self):
        types_registry = self.registry(TYPE_VISIT_ENTRY)
        return ClassAggregator(types_registry)

    def create_function_aggregator(self):
        functions_registry = self.registry(FUNCTION_VISIT_ENTRY)
        return FunctionAggregator(functions_registry)


class AggregateBindingGenerator(BindingGenerator):

    def __init__(self, root, *gens):
        super().__init__(root)

        self.gens = [Generator(root) for Generator in gens]

    def generate(self, dest):
        for gen in self.gens:
            gen.generate(dest)
