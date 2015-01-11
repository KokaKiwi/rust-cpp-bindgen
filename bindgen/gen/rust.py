from . import BindingGenerator, CodeGenerator, CodeWriter
from . import utils as gen_utils
from collections import OrderedDict
from contextlib import contextmanager

class RustCodeGenerator(CodeGenerator):
    def __init__(self, root):
        super().__init__(root)

        self.pub = True

    def declare_var(self, name, ty=None, init=None, **kwargs):
        if kwargs.get('static', False):
            text = 'static '
        else:
            text = 'let '
        if not kwargs.get('const', True):
            text += 'mut '
        text += name
        if ty is not None:
            text += ': %s' % (ty)
        if init is not None:
            text += ' = %s' % (init)
        text += ';'

        return text

    def declare_function(self, name, ret_ty=None, args=[], **kwargs):
        ret_ty = '()' if ret_ty is None else ret_ty

        text = ''
        if kwargs.get('pub', self.pub):
            text += 'pub '
        if kwargs.get('unsafe', False):
            text += 'unsafe '
        text += 'fn %s' % (name)
        ty_params = kwargs.get('ty_params')
        if ty_params is not None and len(ty_params) > 0:
            text += '<%s>' % (', '.join(ty_params))
        text += '('
        for (i, arg) in enumerate(args):
            if isinstance(arg, tuple):
                (arg_ty, arg_name) = arg
                arg = '%s: %s' % (arg_name, arg_ty)
            if i > 0:
                text += ', '
            text += arg
        text += ')'
        if ret_ty != '()':
            text += ' -> %s' % (ret_ty)

        return text

    def typedef(self, name, ty, **kwargs):
        pub = 'pub ' if kwargs.get('pub', self.pub) else ''
        return '%stype %s = %s;' % (pub, name, ty)

    def struct(self, name, members=[], **kwargs):
        text = ''
        if kwargs.get('pub', self.pub):
            text += 'pub '
        text += 'struct %s' % (name)
        if len(members) > 0:
            text += ' {\n'
            for (member_ty, member_name) in members:
                text += ' '*4
                if member_name.startswith('priv:'):
                    member_name = member_name[5:]
                else:
                    text += 'pub '
                text += '%s: %s,\n' % (member_name, member_ty)
            text += '}'
        else:
            text += ';'

        return text

    def enum(self, name, values=[], **kwargs):
        text = ''
        if kwargs.get('pub', self.pub):
            text += 'pub '
        text += 'enum %s {\n' % (name)
        for value in values:
            text += ' '*4
            if isinstance(value, tuple):
                (value_name, value_val) = value
                text += '%s = %d,\n' % (value_name, value_val)
            else:
                text += '%s,\n' % (value)
        text += '}'

        return text

    def trait(self, name, bases=[], **kwargs):
        text = ''
        if kwargs.get('pub', self.pub):
            text += 'pub '
        text += 'trait %s' % (name)
        for (i, base) in enumerate(bases):
            if i == 0:
                text += ': '
            else:
                text += ' + '
            text += base

        return text

    def impl(self, ty, trait=None, **kwargs):
        text = ''
        if kwargs.get('unsafe', False):
            text += 'unsafe '
        if trait is None:
            text += 'impl %s' % (ty)
        else:
            text += 'impl %s for %s' % (trait, ty)

        return text

    def cast(self, expr, ty):
        return '%s as %s' % (expr, ty)

    def init_struct(self, name, values=[]):
        text = '%s {\n' % (name)
        for (value_name, value_val) in values:
            text += '    %s: %s,\n' % (value_name, value_val)
        text += '}'

        return text

    def assign_var(self, name, value):
        return '%s = %s;' % (name, value)

    def call(self, name, args=[]):
        return '%s(%s)' % (name, ', '.join(list(args)))

    def comment(self, text):
        lines = text.splitlines()

        if len(lines) > 1:
            text = '/*\n'
            for line in lines:
                text += ' * ' + line + '\n'
            text += '*/'
        else:
            text = '// ' + lines[0]

        return text

    def ret(self, expr):
        return 'return %s;' % (value)

    def member(self, expr, name, static=False):
        sep = '::' if static else '.'
        return '%s%s%s' % (expr, sep, name)

    def attr(self, name, args, **kwargs):
        g = '!' if kwargs.get('glob', False) else ''

        text = '#%s[%s' % (g, name)
        if len(args) > 0:
            text += '('
            for (i, arg) in enumerate(args):
                if i > 0:
                    text += ', '
                text += arg
            text += ')'
        text += ']'

        return text

    def link_attr(self, name, **kwargs):
        args = {
            'name': name
        }
        args.update(kwargs)
        args = ['%s = "%s"' % (key, value) for (key, value) in args.items()]
        return self.attr('link', args)

    def extern(self, abi):
        return 'extern "%s"' % (abi)

    def mod(self, name, **kwargs):
        pub = 'pub ' if kwargs.get('pub', self.pub) else ''
        return '%smod %s' % (pub, name)

    def extern_crate(self, name, alias=None):
        text = 'extern crate %s' % (name)
        if alias is not None:
            text += ' as %s' % (alias)
        text += ';'

        return text

    def use(self, path, **kwargs):
        text = ''
        if kwargs.get('pub', self.pub):
            text += 'pub '
        text += 'use %s' % ('::'.join(path))
        if kwargs.get('alias', None) is not None:
            text += ' as %s' % (kwargs.get('alias'))
        text += ';'

        return text

    def unsafe(self, expr=None):
        text = 'unsafe'
        if expr is not None:
            text += ' { %s }' % (expr)

        return text

    def expr(self, expr, discard=False):
        if discard:
            return '%s;' % (expr)
        return expr

    def borrow(self, expr):
        return '&%s' % (expr)

class RustCodeWriter(CodeWriter):
    def _gen_proxy(name):
        def proxy(self, *args, **kwargs):
            m = getattr(self.gen, name)
            self.writeln(m(*args, **kwargs))
        return proxy

    @contextmanager
    def function(self, *args, **kwargs):
        self.write(self.gen.declare_function(*args, **kwargs))
        self.write(' ')
        with self.block():
            yield

    @contextmanager
    def extern(self, *args, **kwargs):
        self.write(self.gen.extern(*args, **kwargs))
        self.write(' ')
        with self.block():
            yield

    @contextmanager
    def trait(self, *args, **kwargs):
        self.write(self.gen.trait(*args, **kwargs))
        self.write(' ')
        with self.block():
            yield

    @contextmanager
    def impl(self, *args, **kwargs):
        self.write(self.gen.impl(*args, **kwargs))
        self.write(' ')
        with self.block():
            yield

    @contextmanager
    def mod(self, *args, **kwargs):
        self.write(self.gen.mod(*args, **kwargs))
        self.write(' ')
        with self.block():
            yield

    @contextmanager
    def unsafe(self, *args, **kwargs):
        self.write(self.gen.unsafe(*args, **kwargs))
        self.write(' ')
        with self.block():
            yield

    @contextmanager
    def block(self):
        self.writeln('{')
        with self.indent():
            yield
        self.writeln('}')

    def call(self, *args, **kwargs):
        self.writeln('%s;' % (self.gen.call(*args, **kwargs)))

    def declare_function(self, *args, **kwargs):
        self.writeln('%s;' % (self.gen.declare_function(*args, **kwargs)))

    def declare_mod(self, *args, **kwargs):
        self.writeln('%s;' % (self.gen.mod(*args, **kwargs)))

    declare_var = _gen_proxy('declare_var')
    typedef = _gen_proxy('typedef')
    struct = _gen_proxy('struct')
    enum = _gen_proxy('enum')
    assign_var = _gen_proxy('assign_var')
    comment = _gen_proxy('comment')
    ret = _gen_proxy('ret')
    attr = _gen_proxy('attr')
    extern_crate = _gen_proxy('extern_crate')
    use = _gen_proxy('use')
    expr = _gen_proxy('expr')
    link_attr = _gen_proxy('link_attr')
    init_struct = _gen_proxy('init_struct')

# Rust FFI generator
class RustFFIBindingGenerator(BindingGenerator):
    def generate(self, dest):
        path = dest / 'ffi.rs'

        self.makedir(path.parent)

        with path.open('w+') as f:
            gen = RustCodeGenerator(self.root)
            gen.pub = True
            writer = RustCodeWriter(gen, f)
            self._generate(writer)

    def _generate(self, writer):
        from bindgen.ast import objects as obj

        # Write types
        def traverse_types():
            for item in self.root.traverse():
                if isinstance(item, obj.Function):
                    yield item.ret_ty

                    for (arg_ty, arg_name) in item.arg_tys:
                        yield arg_ty
                elif isinstance(item, obj.Class):
                    yield item

        types = set()
        for ty in traverse_types():
            ty_name = ty.ffi_name('rust')
            if ty_name not in types:
                ty.write_def('rust', writer)
                types.add(ty_name)

        # FFI functions
        writer.writeln()
        with writer.mod('raw', pub=False):
            with writer.extern('C'):
                for item in self.root.traverse():
                    if isinstance(item, obj.Function):
                        self._generate_ffi_function(writer, item)

        self._generate_mod(writer, self.root)
        self.root.extra('rust', writer)

    def _generate_ffi_function(self, writer, func):
        name = gen_utils.c_name(func.path)
        ret_ty = func.ret_ty.ffi_name('rust', path=['super'])

        args = []
        for (arg_ty, arg_name) in func.arg_tys:
            arg_ty = arg_ty.ffi_name('rust', path=['super'])

            args.append((arg_ty, arg_name))

        writer.declare_function(name, ret_ty, args)

    def _generate_mod(self, writer, mod):
        from bindgen.ast import objects as obj

        for item in mod.items:
            if isinstance(item, obj.Namespace):
                writer.writeln()
                with writer.mod(item.name):
                    writer.use(['super', 'raw'], pub=False)

                    self._generate_mod(writer, item)
            elif isinstance(item, obj.Module):
                self._generate_mod(writer, item)
            elif isinstance(item, obj.Function):
                writer.writeln()
                self._generate_function(writer, item)

    def _generate_function(self, writer, func):
        from bindgen.ast import objects as obj

        path = func.namespace.path[1:]
        super = ['super'] * len(path)
        writer.comment(gen_utils.cpp_name(func.path))

        name = func.name
        if isinstance(func, (obj.Method, obj.StaticMethod)):
            name = gen_utils.c_name(func.path[-2:])

        if func.ret_ty == obj.Bool:
            ret_ty = 'bool'
        else:
            ret_ty = func.ret_ty.ffi_name('rust', path=super)

        args = []
        for (arg_ty, arg_name) in func.arg_tys:
            if arg_ty == obj.Bool:
                arg_ty = 'bool'
            else:
                arg_ty = arg_ty.ffi_name('rust', path=super)

            args.append((arg_ty, arg_name))

        writer.attr('inline', ['always'])
        with writer.function(name, ret_ty, args, unsafe=True):
            # Call function
            call_args = [arg_ty.transform('rust', arg_name) for (arg_ty, arg_name) in func.arg_tys]

            call_name = 'raw::%s' % (gen_utils.c_name(func.path))
            ret = writer.gen.call(call_name, call_args)
            ret = func.ret_ty.transform('rust', ret, out=True)
            writer.expr(ret)

# Rust lib generator
def camel_case_convert(name):
    import re

    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

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
            elif isinstance(item, (obj.Function, obj.Class)):
                yield item

    for item in items(root):
        if item == root:
            continue

        path = get_modpath(item)
        add_item(path, item)

    return tree

class RustLibConstants:
    TRAIT_NAME = '{name}Ext'
    STRUCT_NAME = '{name}'
    INNER_NAME = '{name}Inner'

class RustLibBindingGenerator(BindingGenerator):
    def __init__(self, root):
        super().__init__(root)

        self.gen = RustCodeGenerator(root)
        self.gen.pub = True

    def generate(self, dest):
        tree = make_tree(self.root)

        # Generate entry file
        path = dest / 'lib.rs'
        self.makedir(path.parent)

        with path.open('w+') as f:
            writer = RustCodeWriter(self.gen, f)
            writer.attr('allow', ['non_camel_case_types', 'non_snake_case', 'raw_pointer_derive', 'unstable'], glob=True)
            writer.writeln()
            writer.extern_crate('libc')
            writer.writeln()
            writer.declare_mod('ffi')
            writer.writeln()
            self._generate_tree_def(writer, tree)

        self._generate_tree(tree, dest)

    def _generate_tree_def(self, writer, tree):
        for name in tree.subtrees.keys():
            writer.declare_mod(name)

    def _generate_tree(self, tree, path):
        for (name, subtree) in tree.subtrees.items():
            subpath = path / name
            self._generate_tree(subtree, subpath)

        if len(tree.items) > 0:
            if len(tree.subtrees) > 0:
                fpath = path / 'mod.rs'
            else:
                fpath = path.with_suffix('.rs')
            self.makedir(fpath.parent)

            with fpath.open('w+') as f:
                writer = RustCodeWriter(self.gen, f)
                self._generate_tree_def(writer, tree)
                self._generate_tree_items(writer, tree)

    def _generate_tree_items(self, writer, tree):
        from bindgen.ast import objects as obj

        for item in tree.items:
            if isinstance(item.item, obj.Class):
                self._generate_tree_class(writer, tree, item)
            elif isinstance(item.item, obj.Function):
                self._generate_tree_function(writer, tree, item.item, pub=True)

    def _generate_tree_class(self, writer, tree, item):
        from bindgen.ast import objects as obj

        cls = item.item
        trait_name = RustLibConstants.TRAIT_NAME.format(name=cls.name)
        struct_name = RustLibConstants.STRUCT_NAME.format(name=cls.name)
        inner_name = RustLibConstants.INNER_NAME.format(name=cls.name)

        # Generate inner type
        ffi_typename = '::ffi::%s' % (cls.ffi_name('rust'))
        ffi_ptr_typename = '*mut %s' % (inner_name)

        writer.typedef(inner_name, ffi_typename)

        # Generate trait
        def base_cmp(base):
            def _cmp(item):
                return item.item == base
            return _cmp
        bases = [tree.root.find(base_cmp(base)) for base in cls.bases]
        bases = [[''] + base.fullpath for base in bases]
        bases = ['::'.join(base) for base in bases]
        bases = [RustLibConstants.TRAIT_NAME.format(name=base) for base in bases]

        writer.writeln()
        with writer.trait(trait_name, bases):
            writer.writeln()
            writer.declare_function('inner', ffi_ptr_typename, ['&self'], pub=False)

            # Class methods
            for it in cls.items:
                if isinstance(it, obj.Function) and not isinstance(it, (obj.StaticMethod, obj.Destructor)):
                    self._generate_tree_function(writer, tree, it)

        # Generate struct
        writer.writeln()
        writer.struct(struct_name, [
            ('*mut %s' % (inner_name), 'priv:inner'),
        ])

        # Implement bases
        def find_bases_tree(cls):
            bases = []

            for base in cls.bases:
                if bases in bases:
                    continue

                bases += find_bases_tree(base)
                bases.append(base)

            return bases
        bases = find_bases_tree(cls)
        bases = [tree.root.find(base_cmp(base)) for base in bases]

        for base in bases:
            base_path = [''] + base.fullpath
            base_name = '::'.join(base_path)
            base_name = RustLibConstants.TRAIT_NAME.format(name=base_name)

            base_ffi_typename = '::ffi::%s' % (base.item.ffi_name('rust'))

            with writer.impl(struct_name, base_name):
                with writer.function('inner', '*mut %s' % (base_ffi_typename), ['&self'], pub=False):
                    with writer.unsafe():
                        writer.expr(writer.gen.call('::std::mem::transmute', ['self.inner']))

        # Implement class trait
        with writer.impl(struct_name, trait_name):
            with writer.function('inner', ffi_ptr_typename, ['&self'], pub=False):
                writer.expr('self.inner')

        # Implement some specific methods
        with writer.impl(struct_name):
            with writer.function('from_inner', struct_name, [(ffi_ptr_typename, 'inner')], unsafe=True):
                writer.init_struct(struct_name, [
                    ('inner', 'inner'),
                ])

            # Static methods
            for it in cls.items:
                if isinstance(it, obj.StaticMethod):
                    self._generate_tree_function(writer, tree, it, pub=True)

        # Implement extra traits
        def is_class_type(ty):
            return isinstance(ty, (obj.Pointer, obj.Ref)) and isinstance(ty.subtype, obj.Class)

        def resolve_type(ty, impl=False):
            if is_class_type(ty):
                name = resolve_type(ty.subtype)
                if impl:
                    fmt = RustLibConstants.STRUCT_NAME
                else:
                    fmt = RustLibConstants.TRAIT_NAME
                return fmt.format(name=name)
            return ty.lib_name('rust', tree=tree)

        def get_inner(cls, expr):
            name = resolve_type(cls)
            meth = writer.gen.member(name, 'inner', static=True)
            return writer.gen.call(meth, [expr])

        destructor = cls.destructor
        if destructor is not None:
            with writer.impl(struct_name, 'Drop'):
                with writer.function('drop', args=['&mut self'], pub=False):
                    cls_path = destructor.path[:-1]
                    ffi_name = '::ffi' + '%s_%s' % ('::'.join(cls_path), destructor.name)
                    call_name = ffi_name
                    inner = get_inner(obj.Pointer(destructor.parent), 'self')
                    call = writer.gen.call(call_name, [inner])
                    with writer.unsafe():
                        writer.expr(call, discard=True)
        else:
            with writer.impl(struct_name, 'Copy'):
                pass

    def _generate_tree_function(self, writer, tree, func, **kwargs):
        from bindgen.ast import objects as obj

        # Some util functions
        def is_class_type(ty):
            return isinstance(ty, (obj.Pointer, obj.Ref)) and isinstance(ty.subtype, obj.Class)

        def resolve_type(ty, impl=False):
            if is_class_type(ty):
                name = resolve_type(ty.subtype)
                if impl:
                    fmt = RustLibConstants.STRUCT_NAME
                else:
                    fmt = RustLibConstants.TRAIT_NAME
                return fmt.format(name=name)
            return ty.lib_name('rust', tree=tree)

        def get_inner(cls, expr):
            name = resolve_type(cls)
            meth = writer.gen.member(name, 'inner', static=True)
            return writer.gen.call(meth, [expr])

        name = camel_case_convert(func.name)
        ret_tyname = resolve_type(func.ret_ty, impl=True)
        ty_params = []
        args = []

        # Build args list
        arg_tys = func.arg_tys
        if isinstance(func, obj.Method):
            if func.const:
                arg = '&self'
            else:
                arg = '&mut self'
            args.append(arg)
            arg_tys = arg_tys[1:]

        for (i, (arg_ty, arg_name)) in enumerate(arg_tys):
            arg_name = camel_case_convert(arg_name)
            arg_tyname = resolve_type(arg_ty)

            if is_class_type(arg_ty):
                param_name = 'A%d' % (i + 1)
                ty_param = '%s: %s' % (param_name, arg_tyname)
                ty_params.append(ty_param)

                arg_tyname = param_name

            args.append((arg_tyname, arg_name))

        # Write function
        writer.writeln()
        with writer.function(name, ret_tyname, args, ty_params=ty_params, pub=kwargs.get('pub', False)):
            with writer.unsafe():
                call_args = []
                for (arg_ty, arg_name) in arg_tys:
                    arg_name = camel_case_convert(arg_name)
                    if isinstance(arg_ty, obj.ConvertibleType):
                        c_arg_name = 'c_%s' % (arg_name)

                        value = arg_ty.convert_to_ffi(writer, 'rust', arg_name)
                        writer.declare_var(c_arg_name, init=value)

                        call_args.append(c_arg_name)
                    elif is_class_type(arg_ty):
                        call_args.append(get_inner(arg_ty, writer.gen.borrow(arg_name)))
                    else:
                        call_args.append(arg_name)

                call_args = [arg_ty.transform('rustlib', arg_name) for ((arg_ty, _), arg_name) in zip(arg_tys, call_args)]

                if isinstance(func, obj.Method):
                    cls = func.parent
                    ffi_typename = '::ffi::%s' % (cls.ffi_name('rust'))
                    self_arg = get_inner(obj.Pointer(cls), 'self')
                    if func.const:
                        self_arg = writer.gen.cast(self_arg, '*const %s' % (ffi_typename))
                    call_args.insert(0, self_arg)

                ffi_name = '::'.join(func.path)
                if isinstance(func, (obj.Method, obj.StaticMethod)):
                    cls_path = func.path[:-1]
                    ffi_name = '%s_%s' % ('::'.join(cls_path), func.name)
                ffi_name = '::ffi' + ffi_name
                call_name = ffi_name

                ret = writer.gen.call(call_name, call_args)

                if isinstance(func.ret_ty, obj.ConvertibleType):
                    writer.declare_var('ret', init=ret)
                    ret = func.ret_ty.convert_from_ffi(writer, 'rust', 'ret')

                ret = func.ret_ty.transform('rustlib', ret, out=True)

                if is_class_type(func.ret_ty):
                    name = RustLibConstants.STRUCT_NAME.format(name=resolve_type(func.ret_ty.subtype))
                    ret_ffi_typename = '::ffi::%s' % (func.ret_ty.subtype.ffi_name('rust'))
                    from_inner = writer.gen.member(name, 'from_inner', static=True)
                    if func.ret_ty.const:
                        ret = writer.gen.cast(ret, '*mut %s' % (ret_ffi_typename))
                    ret = writer.gen.call(from_inner, [ret])

                discard = func.ret_ty == obj.Void
                writer.expr(ret, discard=discard)

# Generators
GENERATORS = [
    RustFFIBindingGenerator,
    RustLibBindingGenerator,
]
