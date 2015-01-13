from collections import OrderedDict

class ModTree(object):
    def __init__(self):
        self.subtrees = OrderedDict()
        self.items = []

    def get(self, name, default=None):
        return self.subtrees.get(name, default)

    def add(self, item):
        self.items.append(ModItem(self, item))

    def find(self, pred):
        for item in self.items:
            if pred(item):
                return item
        for (name, subtree) in self.subtrees.items():
            item = subtree.find(pred)
            if item is not None:
                return item
        return None

    def resolve_type(self, ty, impl=False):
        from . import RustLibConstants
        from bindgen.ast import objects as obj

        if obj.is_class_type(ty):
            name = self.resolve_type(ty.subtype)
            if impl:
                fmt = RustLibConstants.STRUCT_NAME
            else:
                fmt = RustLibConstants.TRAIT_NAME
            return fmt.format(name=name)
        return ty.lib_name('rust', tree=self)

    @property
    def path(self):
        if hasattr(self, 'parent'):
            return self.parent.path + [self.name]
        return []

    @property
    def root(self):
        if hasattr(self, 'parent'):
            return self.parent.root
        return self

    def __getitem__(self, name):
        subtree = self.get(name)
        if subtree is None:
            subtree = ModTree()
            subtree.name = name
            subtree.parent = self

            self.subtrees[name] = subtree
        return subtree

class ModItem(object):
    def __init__(self, parent, item):
        self.parent = parent
        self.item = item

    @property
    def path(self):
        return self.parent.path

    @property
    def fullpath(self):
        return self.path + [self.item.name]

def make_tree(root):
    from bindgen.ast import objects as obj
    from bindgen.ast.utils import get_modpath

    tree = ModTree()

    def add_item(path, value):
        current = tree

        for name in path:
            current = current[name]

        current.add(value)

    def items(mod):
        for item in mod.items:
            if isinstance(item, obj.Namespace):
                yield from items(item)
            elif isinstance(item, (obj.Function, obj.Class, obj.Enum)):
                yield item

    for item in items(root):
        if item == root:
            continue

        path = get_modpath(item)
        add_item(path, item)

    return tree
