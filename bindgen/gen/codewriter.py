from contextlib import contextmanager


class CodeWriter(object):
    gen_classes = ()

    def __init__(self, gen, out):
        self.gen = gen
        self.out = out

        if not any(isinstance(gen, cls) for cls in self.gen_classes):
            raise Exception('Bad generator class', gen.__class__)

        self._indent = 0
        self._indent_text = ' ' * 4

        self._newline = True

    def raw_write(self, data=''):
        if not isinstance(data, str):
            data = data.decode('utf-8')

        self.out.write(data)

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

    @contextmanager
    def indent(self, amount=1):
        self._indent += amount
        yield
        self._indent -= amount

    @staticmethod
    def proxy(name, fmt='{}', line=True):
        def proxy(self, *args, **kwargs):
            meth = getattr(self.gen, name)
            s = meth(*args, **kwargs)

            write = self.writeln if line else self.write
            write(fmt.format(s))
        return proxy
