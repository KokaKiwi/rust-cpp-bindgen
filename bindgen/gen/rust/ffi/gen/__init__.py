from ...gen import RustGenerator


class RustFFIGenerator(RustGenerator):
    pass


def register(reg):
    from . import ty, func

    ty.register(reg.map(ty.ENTRY))
    func.register(reg.map(func.ENTRY))
