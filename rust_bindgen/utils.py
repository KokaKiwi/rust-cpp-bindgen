
def import_all(root, file):
    import os

    base = os.path.dirname(file)
    for fname in sorted(os.listdir(base)):
        is_python_script = fname.endswith('.py') or fname.endswith('.pyc')
        is_init_script = fname.startswith('__init__')
        is_directory = os.path.isdir(os.path.join(base, fname))
        is_python_module = is_directory and not fname.startswith('__')
        if (is_python_module or is_python_script) and not is_init_script:
            modname = os.path.basename(fname).rsplit('.', 1)[0]
            __import__('.'.join([root, modname]))
