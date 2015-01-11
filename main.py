#!/usr/bin/env python
import bindgen
from argparse import ArgumentParser
from pathlib import Path

def main(args):
    # Load module
    mod = __import__(args.source)

    if not hasattr(mod, 'root'):
        raise Exception('The source module (%s) does not have a `root` member.' % (args.source))
        exit(1)

    root = getattr(mod, 'root')
    dest = args.dest

    for Generator in bindgen.gen.GENERATORS:
        gen = Generator(root)
        gen.generate(dest)

# Main
parser = ArgumentParser()
parser.add_argument('source')
parser.add_argument('dest', type=Path)

if __name__ == '__main__':
    main(parser.parse_args())
