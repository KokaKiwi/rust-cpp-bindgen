
class CodeGenerator(object):

    def indent(self, text, indent=' ' * 4, first=False):
        lines = text.splitlines()
        text = ''
        for (i, line) in enumerate(lines):
            if i > 0 or first:
                text += indent
            text += line
            if i < len(lines) - 1:
                text += '\n'
        return text
