from . import RustLibConstants
from .codegen import RustCodeGenerator
from .codewriter import RustCodeWriter
from .tree import make_tree
from .utils import get_inner, get_inner_static
from .. import BindingGenerator

def camel_case_convert(name):
    import re

    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

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

        def sorted_filter(_filter, key, items):
            return sorted(filter(_filter, items), key=key)

        # Write classes
        for item in sorted_filter(lambda item: isinstance(item.item, obj.Class), lambda item: item.item.name, tree.items):
            self._generate_tree_class(writer, tree, item)

        for item in sorted_filter(lambda item: isinstance(item.item, obj.Function), lambda item: item.item.name, tree.items):
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
            writer.writeln()
            writer.declare_function(raw_inner_method_name, ffi_ptr_typename, ['&self'], pub=False)

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
                """
                param_name = 'A%d' % (i + 1)
                ty_param = '%s: %s' % (param_name, arg_tyname)
                ty_params.append(ty_param)

                arg_tyname = param_name
                """

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
