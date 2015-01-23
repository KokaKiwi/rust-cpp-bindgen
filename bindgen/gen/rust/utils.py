from . import RustLibConstants

def get_inner(tree, writer, ptr, expr):
    return get_inner_static(tree, writer, ptr, expr)

def get_inner_static(tree, writer, ptr, expr):
    from bindgen.ast import objects as obj

    name = tree.resolve_type(ptr)
    inner_method_name = RustLibConstants.GET_INNER_METHOD_NAME

    if isinstance(ptr, obj.Pointer) and ptr.owned:
        name = tree.resolve_type(ptr, fmt=RustLibConstants.OWNED_TRAIT_NAME)
        inner_method_name = RustLibConstants.MOVE_INNER_METHOD_NAME

    meth = writer.gen.member(name, inner_method_name, static=True)
    return writer.gen.call(meth, [expr])
