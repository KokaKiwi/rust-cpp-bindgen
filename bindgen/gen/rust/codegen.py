from .. import CodeGenerator

class RustCodeGenerator(CodeGenerator):
    def __init__(self, root):
        super().__init__(root)

        self.pub = True

    def declare_var(self, name, ty=None, init=None, **kwargs):
        if kwargs.get('static', False):
            text = 'static '
        else:
            text = 'let '
        if not kwargs.get('const', True):
            text += 'mut '
        text += name
        if ty is not None:
            text += ': %s' % (ty)
        if init is not None:
            text += ' = %s' % (init)
        text += ';'

        return text

    def declare_function(self, name, ret_ty=None, args=[], **kwargs):
        ret_ty = '()' if ret_ty is None else ret_ty

        text = ''
        if kwargs.get('pub', self.pub):
            text += 'pub '
        if kwargs.get('unsafe', False):
            text += 'unsafe '
        text += 'fn %s' % (name)
        ty_params = kwargs.get('ty_params')
        if ty_params is not None and len(ty_params) > 0:
            params = []
            for ty_param in ty_params:
                if isinstance(ty_param, tuple):
                    (name, bases) = ty_param
                    if isinstance(bases, list):
                        bases = ' + '.join(bases)
                    ty_param = '%s: %s' % (name, bases)
                params.append(ty_param)
            text += '<%s>' % (', '.join(params))
        text += '('
        for (i, arg) in enumerate(args):
            if isinstance(arg, tuple):
                (arg_ty, arg_name) = arg
                arg = '%s: %s' % (arg_name, arg_ty)
            if i > 0:
                text += ', '
            text += arg
        text += ')'
        if ret_ty != '()':
            text += ' -> %s' % (ret_ty)

        return text

    def typedef(self, name, ty, **kwargs):
        pub = 'pub ' if kwargs.get('pub', self.pub) else ''
        return '%stype %s = %s;' % (pub, name, ty)

    def struct(self, name, members=[], **kwargs):
        text = ''
        if kwargs.get('pub', self.pub):
            text += 'pub '
        text += 'struct %s' % (name)
        if len(members) > 0:
            text += ' {\n'
            for (member_ty, member_name) in members:
                text += ' '*4
                if member_name.startswith('priv:'):
                    member_name = member_name[5:]
                else:
                    text += 'pub '
                text += '%s: %s,\n' % (member_name, member_ty)
            text += '}'
        else:
            text += ';'

        return text

    def enum(self, name, values=[], **kwargs):
        text = ''
        if kwargs.get('pub', self.pub):
            text += 'pub '
        text += 'enum %s {\n' % (name)
        for value in values:
            text += ' '*4
            if isinstance(value, tuple):
                (value_name, value_val) = value
                text += '%s = %s,\n' % (value_name, value_val)
            else:
                text += '%s,\n' % (value)
        text += '}'

        return text

    def trait(self, name, bases=[], **kwargs):
        text = ''
        if kwargs.get('pub', self.pub):
            text += 'pub '
        text += 'trait %s' % (name)
        for (i, base) in enumerate(bases):
            if i == 0:
                text += ': '
            else:
                text += ' + '
            text += base

        return text

    def impl(self, ty, trait=None, **kwargs):
        text = ''
        if kwargs.get('unsafe', False):
            text += 'unsafe '
        if trait is None:
            text += 'impl %s' % (ty)
        else:
            text += 'impl %s for %s' % (trait, ty)

        return text

    def panic(self, msg=None, *args):
        text = 'panic!('
        if msg is not None:
            text += '"%s"' % (msg)

            for arg in iter(args):
                text += ', %s' % (arg)

        text += ')'
        return text

    def match(self, expr):
        return 'match %s' % (expr)

    def match_pattern(self, pattern, value=''):
        return '%s => %s' % (pattern, value)

    def cast(self, expr, ty):
        return '%s as %s' % (expr, ty)

    def init_struct(self, name, values=[]):
        text = '%s {\n' % (name)
        for (value_name, value_val) in values:
            text += '    %s: %s,\n' % (value_name, value_val)
        text += '}'

        return text

    def assign_var(self, name, value):
        return '%s = %s;' % (name, value)

    def call(self, name, args=[]):
        return '%s(%s)' % (name, ', '.join(list(args)))

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

    def cond(self, expr):
        return 'if %s' % (expr)

    def member(self, expr, name, static=False):
        sep = '::' if static else '.'
        return '%s%s%s' % (expr, sep, name)

    def attr(self, name, args=[], **kwargs):
        g = '!' if kwargs.get('glob', False) else ''

        text = '#%s[%s' % (g, name)
        if len(args) > 0:
            text += '('
            for (i, arg) in enumerate(args):
                if i > 0:
                    text += ', '
                text += arg
            text += ')'
        text += ']'

        return text

    def link_attr(self, name, **kwargs):
        args = {
            'name': name
        }
        args.update(kwargs)
        args = ['%s = "%s"' % (key, value) for (key, value) in args.items()]
        return self.attr('link', args)

    def extern(self, abi):
        return 'extern "%s"' % (abi)

    def mod(self, name, **kwargs):
        pub = 'pub ' if kwargs.get('pub', self.pub) else ''
        return '%smod %s' % (pub, name)

    def extern_crate(self, name, alias=None):
        text = 'extern crate %s' % (name)
        if alias is not None:
            text += ' as %s' % (alias)
        text += ';'

        return text

    def use(self, path, **kwargs):
        text = ''
        if kwargs.get('pub', self.pub):
            text += 'pub '
        text += 'use %s' % ('::'.join(path))
        if kwargs.get('alias', None) is not None:
            text += ' as %s' % (kwargs.get('alias'))
        text += ';'

        return text

    def unsafe(self, expr=None):
        text = 'unsafe'
        if expr is not None:
            text += ' { %s }' % (expr)

        return text

    def expr(self, expr, discard=False):
        if discard:
            return '%s;' % (expr)
        return expr

    def borrow(self, expr):
        return '&%s' % (expr)
