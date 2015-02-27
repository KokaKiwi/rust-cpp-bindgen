
class RustGenerator(object):

    def __init__(self, parent):
        self.parent = parent

    def registry(self, entry):
        return self.parent.registry(entry)

    def gen_c_name(self, path):
        while path[0] == '':
            path = path[1:]

        return '_'.join(path)

    def gen_rust_name(self, path):
        while path[0] == '':
            path = path[1:]

        return '::'.join(path)
