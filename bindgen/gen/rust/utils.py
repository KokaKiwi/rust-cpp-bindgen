
def get_inner(tree, writer, ptr, expr):
    return get_inner_static(tree, writer, ptr, expr)

    # cls = ptr.subtype
    # inner_method_name = 'inner_%s' % (cls.flat_name())

    # meth = writer.gen.member(expr, inner_method_name)
    # return writer.gen.call(meth)

def get_inner_static(tree, writer, ptr, expr):
    # cls = ptr.subtype

    # inner_method_name = 'inner_%s' % (cls.flat_name())
    inner_method_name = 'inner'

    name = tree.resolve_type(ptr)

    meth = writer.gen.member(name, inner_method_name, static=True)
    return writer.gen.call(meth, [expr])
