"""
Import various WEAT sets pulled from other sources.
"""

import argparse
import json
import os
import sys

def parse_args():
    """parse command line args"""
    parser = argparse.ArgumentParser()
    parser.add_argument('inputfile')
    parser.add_argument('--link')
    parser.add_argument('--format', dest='source_format')
    parser.add_argument('--source')
    parser.add_argument('--combine')
    parser.add_argument('-r', '--replace', action='store_true')
    return vars(parser.parse_args())

def rename_key(d, old, new):
    d[new] = d.pop(old)

def parse_directory(inputdir, source, link, source_format):
    """Parse a directory of json files"""
    weat_sets = dict()
    for file in os.listdir(inputdir):
        if file.endswith('.json') or file.endswith('.jsonl'):
            with open(os.path.join(inputdir, file)) as fh:
                input_dict = json.load(fh)
            weat = dict()
            weat['source'] = str(source)
            weat['link'] = str(link)
            weat.update(input_dict)
            if os.path.basename(inputdir).rstrip('/') == 'social-biases':
                for child in weat.values():
                    if isinstance(child, dict):
                        rename_key(child, 'examples', 'vocab')
            weat_sets[os.path.splitext(file)[0]] = weat
    return weat_sets

def main(inputfile, source=None, link=None, source_format=None,
         combine=None, replace=False):
    weat_sets = dict()
    if os.path.isdir(inputfile):
        weat_sets = parse_directory(inputfile, source, link,
                                    source_format)
    if combine is not None:
        with open(combine) as fh:
            original = json.load(fh)
        original.update(weat_sets)
        weat_sets = original
    
    if replace:
        backup = combine + '.bak'
        i = 1
        while os.path.exists(backup):
            backup = 'combine.bak.{:02}'.format(i)
            i += 1
        os.rename(combine, backup)
        with open(combine, 'w') as fh:
            fh.write(json.dumps(weat_sets, indent=4))
    else:
        print(json.dumps(weat_sets, indent=4))

if __name__ == '__main__':
    parsed_args = parse_args()
    main(**parsed_args)
