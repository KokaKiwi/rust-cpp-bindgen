
class CGenerator(object):

    def __init__(self, parent):
        self.parent = parent

    def registry(self, entry):
        return self.parent.registry(entry)

    def typegen(self, ty):
        from . import ty as gen_ty

        Generator = self.registry(gen_ty.ENTRY)[ty.__class__]
        return Generator(self.parent, ty)

    def gen_c_name(self, path):
        while path[0] == '':
            path = path[1:]

        return '_'.join(path)

    def gen_cpp_name(self, path):
        return '::'.join(path)


def register(reg):
    from . import ty, func

    ty.register(reg.map(ty.ENTRY))
    func.register(reg.map(func.ENTRY))
