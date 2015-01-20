
# Module path utils
def get_parent_modpath(item):
    from bindgen.ast import objects as obj

    if isinstance(item, obj.Class) and len(item.bases) > 0:
        return get_modpath(item.bases[0])
    return get_modpath(item.parent)

def resolve_modpath(modpath, item):
    if hasattr(modpath, '__call__'):
        modpath = modpath(item)
    return modpath

def get_modpath(item):
    if hasattr(item, 'modpath'):
        return resolve_modpath(item.modpath, item)
    return get_parent_modpath(item)

def submodpath(path):
    def _modpath(item):
        return get_parent_modpath(item) + path
    return _modpath

def concatmodpaths(*paths):
    def _modpath(item):
        modpath = []
        for path in iter(paths):
            modpath += resolve_modpath(path, item)
        return modpath
    return _modpath

def copymodpath(item):
    def _modpath(it):
        return get_modpath(item)
    return _modpath
