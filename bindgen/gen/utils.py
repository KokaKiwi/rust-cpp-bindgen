
def c_name(path):
    path = path[1:] if path[0] == '' else path
    return '_'.join(path)

def cpp_name(path):
    return '::'.join(path)

def run(*args):
    import subprocess

    output = subprocess.check_output(list(args), universal_newlines=True)
    return output
