from ..codegen import CodeGenerator


class RustCodeGenerator(CodeGenerator):

    def pub(self, stmt):
        return 'pub %s' % (stmt)

    def unsafe(self, expr, block=True):
        text = 'unsafe '

        if block:
            text += '{ %s }' % (expr)
        else:
            text += expr

        return text

    def attr(self, data, **kwargs):
        text = '#!' if kwargs.get('glob', False) else '#'
        text += '[%s]' % (data)

        return text

    def use(self, path, **kwargs):
        if isinstance(path, list):
            if isinstance(path[-1], list):
                path[-1] = '{%s}' % (', '.join(path[-1]))

            path = '::'.join(path)

        text = 'use %s;' % (path)
        if kwargs.get('pub', False):
            text = self.pub(text)

        return text

    def mod(self, name, **kwargs):
        text = 'mod %s' % (name)

        if kwargs.get('pub', False):
            text = self.pub(text)

        return text

    def extern_crate(self, name, **kwargs):
        text = 'extern crate '

        alias = kwargs.get('alias')
        if alias is None:
            text += name
        else:
            text += '"%s" as %s' % (name, alias)

        text += ';'
        return text

    def extern(self, abi=None, **kwargs):
        text = 'extern'

        if abi is not None:
            text += ' "%s"' % (abi)

        return text

    def typedef(self, name, ty, **kwargs):
        text = 'type %s = %s;' % (name, ty)
        if kwargs.get('pub', False):
            text = self.pub(text)
        return text

    def declare_var(self, name, ty=None, **kwargs):
        if kwargs.get('static', False):
            assert kwargs.get('ty') is not None
            assert kwargs.get('init') is not None
            text = 'static '
        elif kwargs.get('const', False):
            assert kwargs.get('ty') is not None
            assert kwargs.get('init') is not None
            text = 'const '
        else:
            text = 'let '

        text += name

        if ty is not None:
            text += ': %s' % (ty)

        init = kwargs.get('init')
        if init is not None:
            text += ' = %s' % (init)

        text += ';'
        return text

    def assign_var(self, name, value):
        return '%s = %s;' % (name, value)

    def declare_function(self, name, ret_ty=None, *args, **kwargs):
        text = 'fn %s' % (name)

        # Handle type params
        ty_params = kwargs.get('ty_params', [])
        if len(ty_params) > 0:
            param_strs = []
            for ty_param in ty_params:
                param_bases = []
                param_default = None

                if isinstance(ty_param, tuple):
                    if len(ty_param) == 2:
                        (param_name, param_bases) = ty_param
                    elif len(ty_param) == 3:
                        (param_name, param_bases, param_default) = ty_param
                else:
                    param_name = ty_param

                if isinstance(param_bases, str):
                    param_bases = [param_bases]

                param_str = param_name
                if len(param_bases) > 0:
                    param_str += ': %s' % (' + '.join(param_bases))
                if param_default is not None:
                    param_str += ' = %s' % (param_default)

                param_strs.append(param_str)
            text += '<%s>' % (', '.join(param_strs))

        # Handle args
        arg_strs = []
        for (arg_ty, arg_name) in args:
            arg_str = '%s: %s' % (arg_name, arg_ty)
            arg_strs.append(arg_str)
        text += '(%s)' % (', '.join(arg_strs))

        # Handle ret
        if ret_ty not in ('()', None):
            text += ' -> %s' % (ret_ty)

        # Handle attrs
        if kwargs.get('pub', False):
            text = self.pub(text)

        if kwargs.get('unsafe', False):
            text = self.unsafe(text, block=False)

        return text

    def call(self, expr, *args, **kwargs):
        return '%s(%s)' % (expr, ', '.join(args))

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
        return '%s.%s' % (expr, name)

    def struct_def(self, name, members=[], **kwargs):
        text = 'struct %s' % (name)

        if len(members) > 0:
            text += ' '
            text += '{\n'
            for member in members:
                member_name = None
                member_ty = None
                member_pub = False

                if len(member) == 2:
                    (member_ty, member_name) = member
                elif len(member) == 3:
                    (member_ty, member_name, member_pub) = member

                text += ' ' * 4
                if member_pub:
                    text += 'pub '
                text += '%s: %s,\n' % (member_name, member_ty)
            text += '}'
        else:
            text += ';'

        if kwargs.get('pub', False):
            text = self.pub(text)

        return text

    def struct_init(self, name, values=[], **kwargs):
        text = name

        if len(values) > 0:
            text += ' '
            text += '{\n'
            for (val_name, val_value) in values:
                text += '    %s: %s,\n' % (val_name, self.indent(val_value))
            text += '}'

        return text

    def enum_def(self, name, values=[], **kwargs):
        text = 'enum %s {' % (name)

        if len(values) > 0:
            text += '\n'
        for value in values:
            value_name = value
            value_value = None
            if isinstance(value):
                (value_name, value_value) = value

            text += '    %s' % (value_name)
            if value_value is not None:
                text += ' = %s' % (value_value)
            text += ',\n'

        text += '}'

        if kwargs.get('pub', False):
            text = self.pub(text)

        return text

    def impl(self, name):
        return 'impl %s' % (name)

    def ternary(self, cond_value, then_value, else_value):
        return 'if %s { %s } else { %s }' % (cond_value, then_value, else_value)
