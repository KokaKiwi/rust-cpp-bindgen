from contextlib import contextmanager
from ..codewriter import CodeWriter
from .codegen import CCodeGenerator


class CCodeWriter(CodeWriter):
    gen_classes = (CCodeGenerator,)

    include = CodeWriter.proxy('include')
    typedef = CodeWriter.proxy('typedef')
    declare_var = CodeWriter.proxy('declare_var')
    assign_var = CodeWriter.proxy('assign_var', fmt='{};')
    declare_function = CodeWriter.proxy('declare_function', fmt='{};')
    call = CodeWriter.proxy('call', fmt='{};')
    comment = CodeWriter.proxy('comment')
    ret = CodeWriter.proxy('ret')
    delete = CodeWriter.proxy('delete')
    struct_def = CodeWriter.proxy('struct_def', fmt='{};')
    struct_init = CodeWriter.proxy('struct_init')
    enum_def = CodeWriter.proxy('enum_def', fmt='{};')
    cpp_stmt = CodeWriter.proxy('cpp_stmt')
    cpp_if = CodeWriter.proxy('cpp_if')
    cpp_ifdef = CodeWriter.proxy('cpp_ifdef')
    cpp_ifndef = CodeWriter.proxy('cpp_ifndef')
    cpp_else = CodeWriter.proxy('cpp_else')
    cpp_endif = CodeWriter.proxy('cpp_endif')
    cpp_define = CodeWriter.proxy('cpp_define')

    @contextmanager
    def block(self, newline=True):
        self.writeln('{')
        with self.indent():
            yield
        self.write('}')
        if newline:
            self.writeln()

    @contextmanager
    def function(self, *args, **kwargs):
        self.writeln(self.gen.declare_function(*args, **kwargs))
        with self.block():
            yield
