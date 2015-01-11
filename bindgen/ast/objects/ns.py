from .mod import Module

class Namespace(Module):
    def __init__(self, name=''):
        super().__init__()

        self.name = name
        self.modpath = []

        if self.name != '':
            self.modpath.append(self.name)
