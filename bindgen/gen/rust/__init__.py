
class RustLibConstants:
    INNER_TRAIT_NAME = '{name}Obj'
    EXT_TRAIT_NAME = '{name}Ext'
    STRUCT_NAME = '{name}'
    INNER_NAME = '{name}Inner'

from .ffi import RustFFIBindingGenerator
from .lib import RustLibBindingGenerator

GENERATORS = [
    RustFFIBindingGenerator,
    RustLibBindingGenerator,
]
