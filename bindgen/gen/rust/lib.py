from . import RustLibConstants
from .codegen import RustCodeGenerator
from .codewriter import RustCodeWriter
from .tree import make_tree
from .utils import get_inner, get_inner_static
from .. import BindingGenerator, CodeBuilder

def camelcase_to_underscore(name):
    import re

    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def underscore_to_camelcase(name):
    def title(s):
        s = s[0].upper() + s[1:]
        return s
    return "".join(title(x) if x else '_' for x in name.split("_"))

class RustLibCodeBuilder(CodeBuilder):
    def __init__(self, writer, tree):
        super().__init__(writer)

        self.tree = tree

    def generate_trait(self, item):
        self._generate_trait(self.writer, item)

    def generate_enum(self, enum):
        self._generate_tree_enum(self.writer, self.tree, enum)

    def generate_class(self, cls):
        self._generate_tree_class(self.writer, self.tree, cls)

    def generate_function(self, func, **kwargs):
        self._generate_tree_function(self.writer, self.tree, func, **kwargs)

    def camelcase_to_underscore(self, *args, **kwargs):
        return camelcase_to_underscore(*args, **kwargs)

    def underscore_to_camelcase(self, *args, **kwargs):
        return underscore_to_camelcase(*args, **kwargs)

    def get_inner(self, *args, **kwargs):
        return get_inner(*args, **kwargs)

    def get_inner_static(self, *args, **kwargs):
        return get_inner_static(*args, **kwargs)

    def _generate_trait(self, writer, item):
        cls = item.item

        inner_trait_name = RustLibConstants.INNER_TRAIT_NAME.format(name=cls.name)
        owned_trait_name = RustLibConstants.OWNED_TRAIT_NAME.format(name=cls.name)
        ext_trait_name = RustLibConstants.EXT_TRAIT_NAME.format(name=cls.name)

        base_path = [''] + item.path

        writer.use(base_path + [inner_trait_name])
        writer.use(base_path + [owned_trait_name])
        writer.use(base_path + [ext_trait_name])

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

        writer.simple_impl(enum_name, 'Copy')

    def _generate_tree_class(self, writer, tree, cls):
        from bindgen.ast import objects as obj

        inner_trait_name = RustLibConstants.INNER_TRAIT_NAME.format(name=cls.name)
        ext_trait_name = RustLibConstants.EXT_TRAIT_NAME.format(name=cls.name)
        owned_trait_name = RustLibConstants.OWNED_TRAIT_NAME.format(name=cls.name)
        struct_name = RustLibConstants.STRUCT_NAME.format(name=cls.name)
        inner_name = RustLibConstants.INNER_NAME.format(name=cls.name)

        destructor = cls.destructor

        # Generate enums
        for it in sorted(cls.items, key=lambda item: item.name):
            if isinstance(it, obj.Enum):
                self.generate_enum(it)

        # Generate inner type
        ffi_typename = '::ffi::%s' % (cls.ffi_name('rust'))
        ffi_ptr_typename = '*mut %s' % (inner_name)

        writer.typedef(inner_name, ffi_typename)

        # Generate traits
        def base_cmp(base):
            def _cmp(item):
                return item.item == base
            return _cmp
        bases = [tree.root.find(base_cmp(base)) for base in cls.bases]
        bases = [[''] + base.fullpath for base in bases]
        bases = ['::'.join(base) for base in bases]
        bases = [RustLibConstants.INNER_TRAIT_NAME.format(name=base) for base in bases]

        # Generate inner trait
        writer.writeln()
        with writer.trait(inner_trait_name, bases):
            writer.declare_function(RustLibConstants.GET_INNER_METHOD_NAME, ffi_ptr_typename, ['&self'], pub=False, unsafe=True)

        # Generate inner owned trait
        writer.writeln()
        with writer.trait(owned_trait_name, [inner_trait_name, '::core::marker::Sized']):
            writer.attr('inline', ['always'])
            with writer.function(RustLibConstants.MOVE_INNER_METHOD_NAME, ffi_ptr_typename, ['self'], pub=False, unsafe=True):
                get_inner_meth = writer.gen.member(inner_trait_name, RustLibConstants.GET_INNER_METHOD_NAME, static=True)
                inner = writer.gen.call(get_inner_meth, ['&self'])
                writer.declare_var('inner', init=inner)
                writer.call('::core::mem::forget', ['self'])
                writer.ret('inner')

        writer.writeln('impl<T> %s for T where T: %s + ::core::marker::Sized {}' % (owned_trait_name, inner_trait_name))

        # Generate ext trait
        writer.writeln()
        with writer.trait(ext_trait_name, [inner_trait_name]):
            for it in sorted(cls.items, key=lambda item: item.name):
                if isinstance(it, obj.Function) and not isinstance(it, (obj.StaticMethod, obj.Destructor)):
                    self.generate_function(it)
                elif isinstance(it, obj.RawFunction):
                    writer.writeln()
                    it.generate(self, 'rust')

        # Impl ext trait for all inner trait
        writer.writeln('impl<T> %s for T where T: %s {}' % (ext_trait_name, inner_trait_name))

        # Generate struct
        writer.writeln()

        members = [
            ('::core::nonzero::NonZero<*mut %s>' % (inner_name), 'priv:inner'),
        ]
        if destructor is not None:
            members.append(('bool', 'priv:owned'))
        writer.struct(struct_name, members)

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
            base_name = RustLibConstants.INNER_TRAIT_NAME.format(name=base_name)

            base_ffi_typename = '::ffi::%s' % (base.item.ffi_name('rust'))

            with writer.impl(struct_name, base_name):
                writer.attr('inline', ['always'])
                with writer.function(RustLibConstants.GET_INNER_METHOD_NAME, '*mut %s' % (base_ffi_typename), ['&self'], pub=False):
                    with writer.unsafe():
                        writer.expr(writer.gen.call('::core::mem::transmute', ['self.inner']))

        # Implement class trait
        with writer.impl(struct_name, inner_trait_name):
            writer.attr('inline', ['always'])
            with writer.function(RustLibConstants.GET_INNER_METHOD_NAME, ffi_ptr_typename, ['&self'], pub=False):
                writer.expr('*self.inner')

        # Implement some specific methods
        with writer.impl(struct_name):
            args = [(ffi_ptr_typename, 'inner')]
            members = [('inner', '::core::nonzero::NonZero::new(inner)')]
            if destructor is not None:
                args.append(('bool', 'owned'))
                members.append(('owned', 'owned'))

            writer.attr('inline', ['always'])
            with writer.function('from_inner', struct_name, args, unsafe=True):
                writer.init_struct(struct_name, members)

            # Static methods
            for it in sorted(cls.items, key=lambda item: item.name):
                if isinstance(it, obj.StaticMethod):
                    self.generate_function(it, pub=True)
                elif isinstance(it, obj.RawFunction):
                    writer.writeln()
                    it.generate(self, 'rust', static=True)

        # Implement extra traits
        if destructor is not None:
            with writer.impl(struct_name, 'Drop'):
                writer.attr('inline', ['always'])
                with writer.function('drop', args=['&mut self'], pub=False):
                    cls_path = destructor.path[:-1]
                    ffi_name = '::ffi' + '%s_%s' % ('::'.join(cls_path), destructor.name)
                    call_name = ffi_name
                    inner = get_inner_static(tree, writer, obj.Pointer(destructor.parent), 'self')
                    call = writer.gen.call(call_name, [inner])

                    writer.write('if self.owned ')
                    with writer.block():
                        with writer.unsafe():
                            writer.expr(call, discard=True)
        else:
            writer.simple_impl(struct_name, 'Copy')

    def is_null(self, ty, null=None):
        from bindgen.ast import objects as obj

        return isinstance(ty, obj.Pointer) and ty.null == null

    def check_ptr(self, ty, expr, name):
        from bindgen.ast import objects as obj

        writer = self.writer

        cond = '%s.is_null()' % (expr)
        if self.is_null(ty, obj.Pointer.Null.option):
            with writer.cond(cond):
                writer.ret('None')
        elif self.is_null(ty, obj.Pointer.Null.panic):
            with writer.cond(cond):
                writer.panic('%s returned a null pointer!' % (name))

    def _generate_tree_function(self, writer, tree, func, **kwargs):
        from bindgen.ast import objects as obj

        pub = kwargs.get('pub', False)

        # Some util functions
        is_null = self.is_null

        def get_inner_proxy(*args, **kwargs):
            return get_inner(tree, *args, **kwargs)

        name = camelcase_to_underscore(func.name)
        ret_tyname = tree.resolve_type(func.ret_ty, impl=True)
        ty_params = []
        args = []

        if is_null(func.ret_ty, obj.Pointer.Null.option):
            ret_tyname = 'Option<%s>' % (ret_tyname)

        # Build args list
        arg_tys = func.arg_tys
        if isinstance(func, obj.Method):
            if func.const:
                arg = '&self'
            else:
                arg = '&mut self'
            args.append(arg)
            arg_tys = arg_tys[1:]

        def get_tyname(ty):
            if isinstance(ty, obj.Option):
                tyname = get_tyname(ty.subtype)
                return 'Option<%s>' % (tyname)

            return tree.resolve_type(ty)

        def get_arg_tyname(ty, name):
            if isinstance(ty, obj.Option):
                tyname = get_arg_tyname(ty.subtype, name)
                return 'Option<%s>' % (tyname)

            return name

        for (i, (arg_ty, arg_name)) in enumerate(arg_tys):
            arg_name = camelcase_to_underscore(arg_name)

            if obj.is_class_type(arg_ty):
                cls = obj.get_class_type(arg_ty)
                cls_ptr = obj.get_class_ptr(arg_ty)
                cls_ref = obj.get_class_ref(arg_ty)
                cls_container = cls_ptr if cls_ptr is not None else cls_ref
                cls_tyname = tree.resolve_type(obj.Pointer(cls))
                cls_impl_tyname = tree.resolve_type(obj.Pointer(cls), impl=True)

                param_name = 'A%d' % (i + 1)
                ty_params.append((param_name, cls_tyname, cls_impl_tyname))

                arg_tyname = param_name
                if (cls_ptr is not None and not cls_ptr.owned) or cls_ref is not None:
                    # if destructor is not None:
                    if cls_container.const:
                        ref_str = '&'
                    else:
                        ref_str = '&mut '
                    arg_tyname = '%s%s' % (ref_str, arg_tyname)
                arg_tyname = get_arg_tyname(arg_ty, arg_tyname)
            else:
                arg_tyname = get_tyname(arg_ty)

            args.append((arg_tyname, arg_name))

        # Write function
        writer.writeln()
        with writer.function(name, ret_tyname, args, pub=pub, ty_params=ty_params):
            with writer.unsafe():
                call_args = []
                for (arg_ty, arg_name) in arg_tys:
                    arg_name = camelcase_to_underscore(arg_name)

                    if isinstance(arg_ty, obj.Option) and not obj.is_class_type(arg_ty.subtype):
                        value = '%s.unwrap_or(%s)' % (arg_name, arg_ty.default)
                        writer.declare_var(arg_name, init=value)
                        arg_ty = arg_ty.subtype

                    if isinstance(arg_ty, obj.ConvertibleType):
                        c_arg_name = 'c_%s' % (arg_name)

                        value = arg_ty.convert_to_ffi(writer, 'rust', arg_name, get_inner=get_inner_proxy)
                        writer.declare_var(c_arg_name, init=value)

                        call_args.append(c_arg_name)
                    elif isinstance(arg_ty, (obj.Pointer, obj.Ref)) and obj.is_class_type(arg_ty.subtype):
                        call_args.append(get_inner_proxy(writer, arg_ty, arg_name))
                    elif isinstance(arg_ty, obj.Option) and obj.is_class_container(arg_ty.subtype):
                        inner = get_inner_proxy(writer, arg_ty.subtype, arg_name)
                        if arg_ty.subtype.const:
                            null = '::std::ptr::null()'
                        else:
                            null = '::std::ptr::null_mut()'
                        arg = '%s.map(|%s| %s).unwrap_or(%s)' % (arg_name, arg_name, inner, null)
                        call_args.append(arg)
                    else:
                        call_args.append(arg_name)

                call_args = [arg_ty.transform('rustlib', arg_name) for ((arg_ty, _), arg_name) in zip(arg_tys, call_args)]

                if isinstance(func, obj.Method):
                    cls = func.parent
                    self_arg = get_inner_proxy(writer, obj.Pointer(cls), 'self')
                    if func.const:
                        ffi_typename = '::ffi::%s' % (cls.ffi_name('rust'))
                        self_arg = writer.gen.cast(self_arg, '*const %s' % (ffi_typename))
                    call_args.insert(0, self_arg)

                ffi_name = '::'.join(func.path)
                if isinstance(func, (obj.Method, obj.StaticMethod)):
                    cls_path = func.path[:-1]
                    ffi_name = '%s_%s' % ('::'.join(cls_path), func.name)
                ffi_name = '::ffi' + ffi_name
                call_name = ffi_name

                ret = writer.gen.call(call_name, call_args)

                # Do final transforms to return value
                if func.ret_ty == obj.Void:
                    writer.expr(ret, discard=True)
                    return

                if isinstance(func.ret_ty, obj.ConvertibleType):
                    writer.declare_var('ret', init=ret)
                    ret = func.ret_ty.convert_from_ffi(writer, 'rust', 'ret', get_inner=get_inner_proxy)

                ret = func.ret_ty.transform('rustlib', ret, out=True)

                writer.declare_var('ret', init=ret)
                ret = 'ret'

                self.check_ptr(func.ret_ty, ret, '::'.join(func.path))

                if obj.is_class_type(func.ret_ty):
                    cls = func.ret_ty.subtype

                    name = RustLibConstants.STRUCT_NAME.format(name=tree.resolve_type(cls))
                    from_inner = writer.gen.member(name, 'from_inner', static=True)
                    if func.ret_ty.const:
                        ret_ffi_typename = '::ffi::%s' % (cls.ffi_name('rust'))
                        ret = writer.gen.cast(ret, '*mut %s' % (ret_ffi_typename))

                    args = [ret]
                    if cls.destructor is not None:
                        owned = isinstance(func, obj.Constructor)
                        if isinstance(func.ret_ty, obj.Pointer):
                            owned |= func.ret_ty.owned

                        owned = 'true' if owned else 'false'
                        args.append(owned)

                    ret = writer.gen.call(from_inner, args)

                if is_null(func.ret_ty, obj.Pointer.Null.option):
                    ret = 'Some(%s)' % (ret)

                writer.expr(ret)

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
            builder = RustLibCodeBuilder(writer, tree)
            writer.attr('experimental', glob=True)
            writer.attr('allow', ['unstable'], glob=True)
            # writer.attr('no_std', glob=True)
            writer.writeln()
            writer.extern_crate('core')
            writer.extern_crate('libc')
            self._generate_tree_uses(builder)
            writer.writeln()
            writer.declare_mod('ffi')
            writer.declare_mod('traits')
            self._generate_tree_def(builder)

        # Generate tree
        self._generate_tree(tree, dest)

        # Generate traits file
        path = dest / 'traits.rs'
        self.makedir(path.parent)

        with path.open('w+') as f:
            writer = RustCodeWriter(self.gen, f)
            builder = RustLibCodeBuilder(writer, tree)
            self._generate_traits(builder, tree)

    def _generate_traits(self, builder, tree):
        from bindgen.ast import objects as obj
        from .tree import item_key

        writer = builder.writer

        for (name, subtree) in tree.subtrees.items():
            self._generate_traits(builder, subtree)

        for item in sorted(tree.items, key=item_key):
            if isinstance(item.item, obj.Class):
                builder.generate_trait(item)

    def _generate_tree_uses(self, builder):
        # writer.writeln()
        # writer.use(['', 'core', 'prelude', '*'])
        pass

    def _generate_tree_def(self, builder):
        writer = builder.writer
        tree = builder.tree

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
                builder = RustLibCodeBuilder(writer, tree)
                self._generate_tree_uses(builder)
                self._generate_tree_def(builder)
                self._generate_tree_items(builder)

    def _generate_tree_items(self, builder):
        from bindgen.ast import objects as obj
        from .tree import ty_filter, item_key

        writer = builder.writer
        tree = builder.tree

        def sorted_filter(_filter, key, items):
            return sorted(filter(_filter, items), key=key)

        # Write classes
        for item in sorted_filter(ty_filter(obj.Enum), item_key, tree.items):
            builder.generate_enum(item.item)

        for item in sorted_filter(ty_filter(obj.Class), item_key, tree.items):
            builder.generate_class(item.item)

        for item in sorted_filter(ty_filter((obj.Function, obj.RawFunction)), item_key, tree.items):
            if isinstance(item.item, obj.RawFunction):
                writer.writeln()
                item.item.generate(builder, 'rust')
            else:
                builder.generate_function(item.item, pub=True)
