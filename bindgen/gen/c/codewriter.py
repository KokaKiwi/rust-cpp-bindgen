from .. import CodeWriter
from contextlib import contextmanager

class CCodeWriter(CodeWriter):
    def _gen_proxy(name):
        def proxy(self, *args, **kwargs):
            m = getattr(self.gen, name)
            self.writeln(m(*args, **kwargs))
        return proxy

    def declare_function(self, *args, **kwargs):
        self.writeln('%s;' % (self.gen.declare_function(*args, **kwargs)))

    def assign_var(self, *args, **kwargs):
        self.writeln('%s;' % (self.gen.assign_var(*args, **kwargs)))

    @contextmanager
    def function(self, *args, **kwargs):
        self.writeln(self.gen.declare_function(*args, **kwargs))
        with self.block():
            yield

    @contextmanager
    def block(self):
        self.writeln('{')
        with self.indent():
            yield
        self.writeln('}')

    def call(self, *args, **kwargs):
        self.writeln('%s;' % (self.gen.call(*args, **kwargs)))

    def struct(self, *args, **kwargs):
        self.writeln('%s;' % (self.gen.struct(*args, **kwargs)))

    def enum(self, *args, **kwargs):
        self.writeln('%s;' % (self.gen.enum(*args, **kwargs)))

    declare_var = _gen_proxy('declare_var')
    include = _gen_proxy('include')
    typedef = _gen_proxy('typedef')
    comment = _gen_proxy('comment')
    ret = _gen_proxy('ret')
    delete = _gen_proxy('delete')
    new = _gen_proxy('new')
