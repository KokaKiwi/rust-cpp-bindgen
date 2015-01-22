
def get_inner(tree, writer, ptr, expr):
    return get_inner_static(tree, writer, ptr, expr)

def get_inner_static(tree, writer, ptr, expr):
    from bindgen.ast import objects as obj

    inner_method_name = 'inner'

    name = tree.resolve_type(ptr)

    if isinstance(ptr, obj.Pointer) and ptr.owned:
        expr = '&%s' % (expr)

    meth = writer.gen.member(name, inner_method_name, static=True)
    return writer.gen.call(meth, [expr])
