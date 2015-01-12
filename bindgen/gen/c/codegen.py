from .. import CodeGenerator

class CCodeGenerator(CodeGenerator):
    def declare_var(self, ty, name, init=None, **kwargs):
        text = ''
        if kwargs.get('static', False):
            text += 'static '
        text += '%s %s' % (ty, name)
        if init is not None:
            text += ' = %s' % (init)
        text += ';'

        return text

    def declare_function(self, name, ret_ty, args=[], **kwargs):
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

    def typedef(self, name, ty):
        return 'typedef %s %s;' % (ty, name)

    def struct(self, members=[], name=None):
        text = 'struct'
        if name is not None:
            text += ' %s' % (name)
        text += ' {\n'
        for (member_ty, member_name) in members:
            text += '    %s %s;\n' % (member_ty, member_name)
        text += '}'

        return text

    def enum(self, values=[], name=None):
        text = 'enum'
        if name is not None:
            text += ' %s' % (name)
        text += '{\n'
        for value in values:
            if isinstance(value, tuple):
                (value_name, value_val) = value
                text += '%s = %d,' % (value_name, value_val)
            else:
                text += '%s,' % (value)
            text += '\n'
        text += '}'

        return text

    def init_struct(self, values=[]):
        text = '{\n'
        for value in values:
            text += ' '*4
            if isinstance(value, tuple):
                (value_name, value_value) = value
                text += '.%s = %s,' % (value_name, value_value)
            else:
                text += '%s,' % (value)
            text += '\n'
        text += '}'

        return text

    def assign_var(self, name, value):
        return '%s = %s' % (name, value)

    def call(self, name, args=[]):
        return '%s(%s)' % (name, ', '.join(list(args)))

    def include(self, filename, system=False):
        c = '<>' if system else '""'
        return '#include %c%s%c' % (c[0], filename, c[1])

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

    def ret(self, value):
        return 'return %s;' % (value)

    def delete(self, name):
        return 'delete %s;' % (name)

    def new(self, name, args=[]):
        return 'new %s' % (self.call(name, args))

    def member(self, expr, name, ptr=False):
        c = '->' if ptr else '.'
        return '%s%s%s' % (expr, c, name)

    def c_name(self, path):
        from .. import utils
        return utils.c_name(path)

    def cpp_name(self, path):
        from .. import utils
        return utils.cpp_name(path)
