
class RustLibConstants:
    TRAIT_NAME = '{name}Ext'
    STRUCT_NAME = '{name}'
    INNER_NAME = '{name}Inner'

from .ffi import RustFFIBindingGenerator
from .lib import RustLibBindingGenerator

GENERATORS = [
    RustFFIBindingGenerator,
    RustLibBindingGenerator,
]
