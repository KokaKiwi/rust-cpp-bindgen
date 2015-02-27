from .. import RustBindingGenerator
from ..codegen import RustCodeGenerator
from ..codewriter import RustCodeWriter
from ... import BindingGenerator


class RustLibBindingGenerator(BindingGenerator):
    LANG = RustBindingGenerator.LANG

    def generate(self, dest):
        self.makedir(dest)
        gen = RustCodeGenerator()

        # Generate lib entry
        path = dest / 'lib.rs'

        with path.open('w+') as f:
            writer = RustCodeWriter(gen, f)
            self._generate_root(writer)

    def _generate_root(self, writer):
        writer.attr('feature(libc)', glob=True)

        writer.mod_decl('ffi', pub=True)
