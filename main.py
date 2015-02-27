#!/usr/bin/env python
import sys
from argparse import ArgumentParser
from pathlib import Path
from bindgen.gen.c import CBindingGenerator
from bindgen.gen.rust import RustBindingGenerator

GENERATORS = {
    'c': CBindingGenerator,
    'rust': RustBindingGenerator,
}

def generator(name):
    return GENERATORS[name]

def main(args):
    # Load module
    sys.path.insert(0, '.')
    mod = __import__(args.source)

    root = getattr(mod, 'root', None)
    if root is None:
        raise Exception('The source module (%s) does not have a `root` member.' % (args.source))

    dest = args.dest
    Generator = args.generator

    gen = Generator(root)
    gen.generate(dest)

# Main
parser = ArgumentParser()
parser.add_argument('-g', '--generator', type=generator, default='rust')
parser.add_argument('source')
parser.add_argument('dest', type=Path)

if __name__ == '__main__':
    main(parser.parse_args())
