from .. import AggregateBindingGenerator


class RustBindingGenerator(AggregateBindingGenerator):
    LANG = 'rust'

    def __init__(self, root):
        from ..c import CBindingGenerator
        from .ffi import RustFFIBindingGenerator
        from .lib import RustLibBindingGenerator

        super().__init__(
            root, CBindingGenerator, RustFFIBindingGenerator, RustLibBindingGenerator)
