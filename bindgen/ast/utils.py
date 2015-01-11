
def get_parent_modpath(item):
    from bindgen.ast import objects as obj

    if isinstance(item, obj.Class) and len(item.bases) > 0:
        return get_modpath(item.bases[0])
    return get_modpath(item.parent)

def get_modpath(item):
    if hasattr(item, 'modpath'):
        modpath = item.modpath
        if hasattr(modpath, '__call__'):
            modpath = modpath(item)
        return modpath
    return get_parent_modpath(item)

def submodpath(path):
    def modpath(item):
        return get_parent_modpath(item) + path
    return modpath
