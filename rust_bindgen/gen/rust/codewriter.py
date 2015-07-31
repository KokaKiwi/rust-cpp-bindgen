from contextlib import contextmanager
from ..codewriter import CodeWriter
from .codegen import RustCodeGenerator


class RustCodeWriter(CodeWriter):
    gen_classes = (RustCodeGenerator,)

    use = CodeWriter.proxy('use')
    extern_crate = CodeWriter.proxy('extern_crate')
    attr = CodeWriter.proxy('attr')
    typedef = CodeWriter.proxy('typedef')
    declare_var = CodeWriter.proxy('declare_var')
    assign_var = CodeWriter.proxy('assign_var')
    declare_function = CodeWriter.proxy('declare_function', fmt='{};')
    call = CodeWriter.proxy('call', fmt='{};')
    comment = CodeWriter.proxy('comment')
    ret = CodeWriter.proxy('ret')
    struct_def = CodeWriter.proxy('struct_def')
    enum_def = CodeWriter.proxy('enum_def')
    mod_decl = CodeWriter.proxy('mod', fmt='{};')

    @contextmanager
    def block(self, newline=True):
        self.writeln('{')
        with self.indent():
            yield
        self.write('}')
        if newline:
            self.writeln()

    @contextmanager
    def unsafe(self, *args, **kwargs):
        self.write('unsafe ')
        with self.block(*args, **kwargs):
            yield

    @contextmanager
    def extern(self, *args, **kwargs):
        self.write(self.gen.extern(*args, **kwargs) + ' ')
        with self.block():
            yield

    @contextmanager
    def function(self, *args, **kwargs):
        self.write(self.gen.declare_function(*args, **kwargs) + ' ')
        with self.block():
            yield

    @contextmanager
    def mod(self, *args, **kwargs):
        self.write(self.gen.mod(*args, **kwargs) + ' ')
        with self.block():
            yield

    @contextmanager
    def impl(self, *args, **kwargs):
        self.write(self.gen.impl(*args, **kwargs) + ' ')
        with self.block():
            yield
