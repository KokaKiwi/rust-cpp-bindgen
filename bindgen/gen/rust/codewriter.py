from .. import CodeWriter
from contextlib import contextmanager

class RustCodeWriter(CodeWriter):
    def _gen_proxy(name):
        def proxy(self, *args, **kwargs):
            m = getattr(self.gen, name)
            self.writeln(m(*args, **kwargs))
        return proxy

    @contextmanager
    def function(self, *args, **kwargs):
        self.write(self.gen.declare_function(*args, **kwargs))
        self.write(' ')
        with self.block():
            yield

    @contextmanager
    def extern(self, *args, **kwargs):
        self.write(self.gen.extern(*args, **kwargs))
        self.write(' ')
        with self.block():
            yield

    @contextmanager
    def trait(self, *args, **kwargs):
        self.write(self.gen.trait(*args, **kwargs))
        self.write(' ')
        with self.block():
            yield

    @contextmanager
    def impl(self, *args, **kwargs):
        self.write(self.gen.impl(*args, **kwargs))
        self.write(' ')
        with self.block():
            yield

    @contextmanager
    def mod(self, *args, **kwargs):
        self.write(self.gen.mod(*args, **kwargs))
        self.write(' ')
        with self.block():
            yield

    @contextmanager
    def unsafe(self, *args, **kwargs):
        self.write(self.gen.unsafe(*args, **kwargs))
        self.write(' ')
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

    def declare_function(self, *args, **kwargs):
        self.writeln('%s;' % (self.gen.declare_function(*args, **kwargs)))

    def declare_mod(self, *args, **kwargs):
        self.writeln('%s;' % (self.gen.mod(*args, **kwargs)))

    declare_var = _gen_proxy('declare_var')
    typedef = _gen_proxy('typedef')
    struct = _gen_proxy('struct')
    enum = _gen_proxy('enum')
    assign_var = _gen_proxy('assign_var')
    comment = _gen_proxy('comment')
    ret = _gen_proxy('ret')
    attr = _gen_proxy('attr')
    extern_crate = _gen_proxy('extern_crate')
    use = _gen_proxy('use')
    expr = _gen_proxy('expr')
    link_attr = _gen_proxy('link_attr')
    init_struct = _gen_proxy('init_struct')

