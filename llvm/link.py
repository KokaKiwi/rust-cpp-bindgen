from bindgen.gen.utils import run

LLVM_CONFIG = 'llvm-config'
STATIC_DEFAULT = False

def llconfig_run(*args):
    return run(LLVM_CONFIG, *args)

def write_link(lang, writer, static=STATIC_DEFAULT):
    if lang == 'rust':
        version = llconfig_run('--version').strip()

        args = ['--libs']
        if version >= '3.5':
            args.append('--system-libs')

        writer.writeln()

        flags = llconfig_run(*args).strip().replace('\n', ' ').split(' ')
        for flag in flags:
            libname = flag.strip()[2:]

            attr_args = {
                'name': libname,
            }

            if 'LLVM' in libname and static:
                attr_args['kind'] = 'static'
            writer.link_attr(**attr_args)

        flags = llconfig_run('--ldflags').strip().split(' ')
        for flag in flags:
            if flag.startswith('-l'):
                libname = flag[2:]

                writer.link_attr(name=libname)

        out = llconfig_run('--cxxflags')
        if static:
            assert('stdlib=libc++' not in out)
            writer.link_attr(name='stdc++', kind='static')
        else:
            if 'stdlib=libc++' in out:
                writer.link_attr(name='c++')
            else:
                writer.link_attr(name='stdc++')

        writer.writeln('extern "C" {}')
