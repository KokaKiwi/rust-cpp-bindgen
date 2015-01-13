from . import RustLibConstants
from .codegen import RustCodeGenerator
from .codewriter import RustCodeWriter
from .tree import make_tree
from .utils import get_inner, get_inner_static
from .. import BindingGenerator

def camelcase_to_underscore(name):
    import re

    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

camel_case_convert = camelcase_to_underscore

def underscore_to_camelcase(name):
    def title(s):
        s = s[0].upper() + s[1:]
        return s
    return "".join(title(x) if x else '_' for x in name.split("_"))

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
            writer.attr('experimental', glob=True)
            writer.attr('allow', ['unstable'], glob=True)
            writer.writeln()
            writer.extern_crate('libc')
            writer.writeln()
            writer.declare_mod('ffi')
            writer.declare_mod('traits')
            self._generate_tree_def(writer, tree)

        # Generate tree
        self._generate_tree(tree, dest)

        # Generate traits file
        path = dest / 'traits.rs'
        self.makedir(path.parent)

        with path.open('w+') as f:
            writer = RustCodeWriter(self.gen, f)
            self._generate_traits(writer, tree)

    def _generate_traits(self, writer, tree):
        from bindgen.ast import objects as obj
        from .tree import item_key

        for (name, subtree) in tree.subtrees.items():
            self._generate_traits(writer, subtree)

        for item in sorted(tree.items, key=item_key):
            if isinstance(item.item, obj.Class):
                self._generate_trait(writer, item)

    def _generate_trait(self, writer, item):
        cls = item.item
        trait_name = RustLibConstants.TRAIT_NAME.format(name=cls.name)

        path = [''] + item.path + [trait_name]
        name = '::'.join(path)

        writer.use([name])

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
        from .tree import ty_filter, item_key

        def sorted_filter(_filter, key, items):
            return sorted(filter(_filter, items), key=key)

        # Write classes
        for item in sorted_filter(ty_filter(obj.Enum), item_key, tree.items):
            self._generate_tree_enum(writer, tree, item.item)

        for item in sorted_filter(ty_filter(obj.Class), item_key, tree.items):
            self._generate_tree_class(writer, tree, item)

        for item in sorted_filter(ty_filter(obj.Function), item_key, tree.items):
            self._generate_tree_function(writer, tree, item.item, pub=True)

    def _generate_tree_enum(self, writer, tree, enum):
        from bindgen.ast import objects as obj

        enum_name = enum.name
        ffi_enum_name = enum.ffi_name('rust', path=['', 'ffi'])

        # Writer enum
        values = []
        for value in enum.values:
            if isinstance(value, tuple):
                (name, value) = value
                values.append(name)
            else:
                values.append(value)
        values = [underscore_to_camelcase(value) for value in values]

        writer.attr('derive', ['Copy'])
        writer.enum(enum_name, values)

        # Impl enum
        with writer.impl(enum_name):
            # Convert from FFI
            with writer.function('from_ffi', enum_name, [(ffi_enum_name, 'value')]):
                with writer.match('value'):
                    patterns = []
                    for value in enum.values:
                        if isinstance(value, tuple):
                            (name, value) = value

                            if isinstance(value, str):
                                continue
                        else:
                            name = value

                        patterns.append((name, name))

                    for (name, ffi_name) in patterns:
                        name = '%s::%s' % (enum_name, underscore_to_camelcase(name))
                        ffi_name = '%s::%s' % (ffi_enum_name, ffi_name)

                        mpattern = writer.gen.match_pattern(ffi_name, name)
                        writer.writeln('%s,' % (mpattern))

            # Convert to FFI
            with writer.function('to_ffi', ffi_enum_name, ['self']):
                with writer.match('self'):
                    patterns = []
                    for value in enum.values:
                        if isinstance(value, tuple):
                            (name, value) = value
                            ffi_name = name

                            if isinstance(value, str):
                                ffi_name = value
                        else:
                            name = ffi_name = value

                        patterns.append((name, ffi_name))

                    for (name, ffi_name) in patterns:
                        name = '%s::%s' % (enum_name, underscore_to_camelcase(name))
                        ffi_name = '%s::%s' % (ffi_enum_name, ffi_name)

                        mpattern = writer.gen.match_pattern(name, ffi_name)
                        writer.writeln('%s,' % (mpattern))

    def _generate_tree_class(self, writer, tree, item):
        from bindgen.ast import objects as obj

        cls = item.item
        trait_name = RustLibConstants.TRAIT_NAME.format(name=cls.name)
        struct_name = RustLibConstants.STRUCT_NAME.format(name=cls.name)
        inner_name = RustLibConstants.INNER_NAME.format(name=cls.name)

        # Generate enums
        for it in sorted(cls.items, key=lambda item: item.name):
            if isinstance(it, obj.Enum):
                self._generate_tree_enum(writer, tree, it)

        # Generate inner type
        ffi_typename = '::ffi::%s' % (cls.ffi_name('rust'))
        ffi_ptr_typename = '*mut %s' % (inner_name)
        raw_inner_method_name = 'inner_%s' % (cls.flat_name())

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
            writer.attr('allow', ['non_snake_case'])
            writer.declare_function(raw_inner_method_name, ffi_ptr_typename, ['&self'], pub=False)

            writer.writeln()
            with writer.function('inner', ffi_ptr_typename, ['&self'], pub=False):
                inner_method = writer.gen.member('self', raw_inner_method_name)
                writer.expr(writer.gen.call(inner_method))

            # Class methods
            for it in sorted(cls.items, key=lambda item: item.name):
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
            base_inner_method_name = 'inner_%s' % (base.item.flat_name())

            with writer.impl(struct_name, base_name):
                with writer.function(base_inner_method_name, '*mut %s' % (base_ffi_typename), ['&self'], pub=False):
                    with writer.unsafe():
                        writer.expr(writer.gen.call('::std::mem::transmute', ['self.inner']))

        # Implement class trait
        with writer.impl(struct_name, trait_name):
            with writer.function(raw_inner_method_name, ffi_ptr_typename, ['&self'], pub=False):
                writer.expr('self.inner')

        # Implement some specific methods
        with writer.impl(struct_name):
            with writer.function('from_inner', struct_name, [(ffi_ptr_typename, 'inner')], unsafe=True):
                writer.init_struct(struct_name, [
                    ('inner', 'inner'),
                ])

            # Static methods
            for it in sorted(filter(lambda item: isinstance(item, obj.StaticMethod), cls.items), key=lambda item: item.name):
                self._generate_tree_function(writer, tree, it, pub=True)

        # Implement extra traits
        destructor = cls.destructor
        if destructor is not None:
            with writer.impl(struct_name, 'Drop'):
                with writer.function('drop', args=['&mut self'], pub=False):
                    cls_path = destructor.path[:-1]
                    ffi_name = '::ffi' + '%s_%s' % ('::'.join(cls_path), destructor.name)
                    call_name = ffi_name
                    inner = get_inner_static(tree, writer, obj.Pointer(destructor.parent), 'self')
                    call = writer.gen.call(call_name, [inner])
                    with writer.unsafe():
                        writer.expr(call, discard=True)
        else:
            with writer.impl(struct_name, 'Copy'):
                pass

    def _generate_tree_function(self, writer, tree, func, **kwargs):
        from bindgen.ast import objects as obj

        # Some util functions
        name = camel_case_convert(func.name)
        ret_tyname = tree.resolve_type(func.ret_ty, impl=True)
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
            arg_tyname = tree.resolve_type(arg_ty)

            if obj.is_class_type(arg_ty):
                arg_tyname = '&%s' % (arg_tyname)

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

                        value = arg_ty.convert_to_ffi(writer, 'rust', arg_name, get_inner=get_inner)
                        writer.declare_var(c_arg_name, init=value)

                        call_args.append(c_arg_name)
                    elif obj.is_class_type(arg_ty):
                        call_args.append(get_inner(writer, arg_ty, arg_name))
                    else:
                        call_args.append(arg_name)

                call_args = [arg_ty.transform('rustlib', arg_name) for ((arg_ty, _), arg_name) in zip(arg_tys, call_args)]

                if isinstance(func, obj.Method):
                    cls = func.parent
                    ffi_typename = '::ffi::%s' % (cls.ffi_name('rust'))
                    self_arg = get_inner(writer, obj.Pointer(cls), 'self')
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
                    ret = func.ret_ty.convert_from_ffi(writer, 'rust', 'ret', get_inner=get_inner)

                ret = func.ret_ty.transform('rustlib', ret, out=True)

                if obj.is_class_type(func.ret_ty):
                    name = RustLibConstants.STRUCT_NAME.format(name=tree.resolve_type(func.ret_ty.subtype))
                    ret_ffi_typename = '::ffi::%s' % (func.ret_ty.subtype.ffi_name('rust'))
                    from_inner = writer.gen.member(name, 'from_inner', static=True)
                    if func.ret_ty.const:
                        ret = writer.gen.cast(ret, '*mut %s' % (ret_ffi_typename))
                    ret = writer.gen.call(from_inner, [ret])

                discard = func.ret_ty == obj.Void
                writer.expr(ret, discard=discard)
