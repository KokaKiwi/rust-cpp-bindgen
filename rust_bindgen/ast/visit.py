import inspect


class Visitor(object):

    def __init__(self):
        self.visited = set()

    def visit(self, node):
        if hash(node) in self.visited:
            return
        self.visited.add(hash(node))

        self.visit_class(node.__class__, node)

    __call__ = visit

    def visit_class(self, cls, node):
        bases = inspect.getmro(cls)
        meth_names = ['visit_%s' % (base.__name__) for base in bases]
        meths = [getattr(self, meth_name, None) for meth_name in meth_names]
        meths = [meth for meth in meths if meth is not None]

        if len(meths) == 0:
            meths = [self.visit_unknown]

        for meth in meths:
            if not meth(node):
                return

    def visit_unknown(self, node):
        pass

    def unknown_node(self, node):
        raise Exception('Unknown node visited: %s' % (node.__class__.__name__))


class VisitorGenerator(object):

    def __init__(self, visitor):
        self.visitor = visitor

    def visit(self, node):
        return True

TYPE_VISIT_ENTRY = 'type_visit'
FUNCTION_VISIT_ENTRY = 'function_visit'


class RegistryVisitor(Visitor):

    def __init__(self, registry=None):
        super().__init__()
        self.registry = registry

    def visit_class(self, cls, node):
        if self.registry is not None:
            bases = inspect.getmro(cls)

            for base in bases:
                Generator = self.registry.get(base)
                if Generator is not None:
                    gen = Generator(self)
                    if not gen.visit(node):
                        break

        super().visit_class(cls, node)


class EntityVisitor(RegistryVisitor):

    def visit_Module(self, mod):
        for item in mod.items:
            self.visit(item)

        return True


class TypeVisitor(EntityVisitor):

    def visit_Function(self, func):
        self.visit(func.ret_ty)

        for (arg_ty, arg_name) in func.arg_tys:
            self.visit(arg_ty)

        return True

    def visit_Constructor(self, func):
        for (arg_ty, arg_name) in func.arg_tys:
            self.visit(arg_ty)
        return True

    def visit_Optionnable(self, ty):
        self.visit(ty.subtype)
        return True

    def visit_Pointer(self, ty):
        self.visit(ty.subtype)
        return True

    def visit_Ref(self, ty):
        self.visit(ty.subtype)
        return True


class Aggregator(object):

    def __init__(self, container_cls=list):
        self.items = container_cls()
        self.segments = []
        self.sorter = None
        self.filter = None

    def add_segment(self, filter_fn):
        self.segments.append(filter_fn)

    def add_class_segment(self, cls):
        self.add_segment(lambda item: isinstance(item, cls))

    @property
    def items_iterator(self):
        iterator = iter(self.items)
        if self.filter is not None:
            iterator = filter(self.filter, iterator)
        if self.sorter is not None:
            iterator = sorted(iterator, key=self.sorter)
        return iterator

    def __iter__(self):
        for filter_fn in self.segments:
            yield from filter(filter_fn, self.items_iterator)

        filter_fn = lambda item: not any(f(item) for f in self.segments)
        yield from filter(filter_fn, self.items_iterator)

    def __len__(self):
        return len(self.items)


class TypeAggregator(TypeVisitor, Aggregator):

    def __init__(self, *args, **kwargs):
        TypeVisitor.__init__(self, *args, **kwargs)
        Aggregator.__init__(self)

    def visit_Type(self, ty):
        self.items.append(ty)
        return True


class ClassAggregator(TypeVisitor, Aggregator):

    def __init__(self, *args, **kwargs):
        TypeVisitor.__init__(self, *args, **kwargs)
        Aggregator.__init__(self)

    def visit_Class(self, cls):
        self.items.append(cls)
        return True


class FunctionAggregator(EntityVisitor, Aggregator):

    def __init__(self, *args, **kwargs):
        EntityVisitor.__init__(self, *args, **kwargs)
        Aggregator.__init__(self)

    def visit_Function(self, func):
        self.items.append(func)
        return True
