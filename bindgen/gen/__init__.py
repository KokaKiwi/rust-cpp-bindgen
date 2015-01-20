from . import utils as gen_utils
from contextlib import contextmanager

class CodeGenerator(object):
    def __init__(self, root):
        self.root = root

class CodeWriter(object):
    def __init__(self, gen, file):
        self.gen = gen
        self.file = file

        self._indent = 0
        self._indent_text = ' ' * 4

        self._newline = True

    @contextmanager
    def indent(self, amount=1):
        self._indent += amount
        yield
        self._indent -= amount

    def raw_write(self, data=''):
        self.file.write(data)

    def write(self, data=''):
        for (i, line) in enumerate(data.splitlines()):
            if i > 0:
                self.raw_write('\n')
                self._newline = True

            if self._newline and len(line) > 0:
                indent = self._indent_text * self._indent
                self.raw_write(indent)
                self._newline = False

            self.raw_write(line)

    def writeln(self, data=''):
        self.write(data)
        self.raw_write('\n')

        self._newline = True

class CodeBuilder(object):
    def __init__(self, writer):
        self.writer = writer

    def c_name(self, path):
        return gen_utils.c_name(path)

    def cpp_name(self, path):
        return gen_utils.cpp_name(path)

class BindingGenerator(object):
    def __init__(self, root):
        self.root = root

    def generate(self, dest):
        pass

    def makedir(self, path):
        if not path.exists():
            path.mkdir(parents=True)

from . import c, rust, utils

GENERATORS = []
GENERATORS += c.GENERATORS
GENERATORS += rust.GENERATORS
