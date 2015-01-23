
class RustLibConstants:
    INNER_TRAIT_NAME = '{name}Obj'
    OWNED_TRAIT_NAME = '{name}Owned'
    EXT_TRAIT_NAME = '{name}Ext'
    STRUCT_NAME = '{name}'
    INNER_NAME = '{name}Inner'

    GET_INNER_METHOD_NAME = 'get_inner'
    MOVE_INNER_METHOD_NAME = 'move_inner'

from .ffi import RustFFIBindingGenerator
from .lib import RustLibBindingGenerator

GENERATORS = [
    RustFFIBindingGenerator,
    RustLibBindingGenerator,
]
