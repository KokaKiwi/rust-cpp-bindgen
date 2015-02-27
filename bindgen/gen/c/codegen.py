from ..codegen import CodeGenerator


class CCodeGenerator(CodeGenerator):

    def include(self, filename, **kwargs):
        c = '<>' if kwargs.get('system', False) else '""'
        return '#include %s%s%s' % (c[0], filename, c[1])

    def typedef(self, name, ty):
        return 'typedef %s %s;' % (ty, name)

    def declare_var(self, ty, name, **kwargs):
        text = ''

        if kwargs.get('static', False):
            text += 'static '

        text += '%s %s' % (ty, name)

        init = kwargs.get('init', None)
        if init is not None:
            text += ' = %s' % (init)

        text += ';'

        return text

    def assign_var(self, name, expr, **kwargs):
        text = '%s = %s' % (name, expr)
        return text

    def declare_function(self, name, ret_ty, *args, **kwargs):
        text = 'extern "C"\n'

        if kwargs.get('static', False):
            text += 'static '

        text += '%s %s(' % (ret_ty, name)

        for (i, (arg_ty, arg_name)) in enumerate(args):
            if i > 0:
                text += ', '
            text += '%s %s' % (arg_ty, arg_name)

        text += ')'

        return text

    def call(self, name, *args, **kwargs):
        return '%s(%s)' % (name, ', '.join(args))

    def comment(self, text):
        lines = text.splitlines()

        if len(lines) > 1:
            text = '/*\n'
            for line in lines:
                text += ' * ' + line + '\n'
            text += '*/'
        else:
            text = '// ' + lines[0]

        return text

    def ret(self, expr):
        return 'return %s;' % (expr)

    def member(self, expr, name, **kwargs):
        c = '->' if kwargs.get('ptr', False) else '.'
        return '%s%s%s' % (expr, c, name)

    def delete(self, expr):
        return 'delete %s;' % (expr)

    def struct_def(self, members=[], **kwargs):
        text = 'struct '

        name = kwargs.get('name')
        if name is not None:
            text += '%s ' % (name)

        text += '{'
        if len(members) > 0:
            text += '\n'
        for (member_ty, member_name) in members:
            text += '    %s %s;\n' % (member_ty, member_name)
        text += '}'

        return text

    def struct_init(self, values=[]):
        text = '{\n'
        for value in values:
            text += ' ' * 4

            if isinstance(value, tuple):
                (name, value) = value
                text += '.%s = %s,' % (name, value)
            else:
                text += '%s,' % (value)

            text += '\n'
        text += '}'

        return text

    def enum_def(self, values=[], **kwargs):
        text = 'enum '

        name = kwargs.get('name')
        if name is not None:
            text += '%s ' % (name)

        text += '{'
        if len(values) > 0:
            text += '\n'
        for (member_name, member_value) in values:
            if isinstance(member_value, (int,)):
                member_value = str(member_value)
            text += '    %s = %s,\n' % (member_name, member_value)
        text += '}'

        return text

    def ternary(self, cond_value, then_value, else_value):
        return '(%s) ? (%s) : (%s)' % (cond_value, then_value, else_value)

    def cpp_stmt(self, name, *args):
        text = '#%s' % (name)

        for arg in args:
            text += ' %s' % (arg)

        return text

    def cpp_if(self, cond):
        return self.cpp_stmt('if', cond)

    def cpp_ifdef(self, name):
        return self.cpp_stmt('ifdef', name)

    def cpp_ifndef(self, name):
        return self.cpp_stmt('ifndef', name)

    def cpp_else(self):
        return self.cpp_stmt('else')

    def cpp_endif(self, name=None):
        if name is None:
            return self.cpp_stmt('endif')
        else:
            return self.cpp_stmt('endif', '/* %s */' % (name))

    def cpp_define(self, name, value=None):
        if value is None:
            return self.cpp_stmt('define', name)

        return self.cpp_stmt('define', name, value)
