"""Compares WEAT sets to the vocab for a given embedding and produces a
report."""

import argparse
import itertools
import json
import pathlib
import os
import sys

DEFAULT_DATA_DIR = pathlib.Path(__file__).parents[1] / 'data'
DEFAULT_WEAT_FILENAME = 'weat-word-sets.json'
DEFAULT_WEAT_PATH = DEFAULT_DATA_DIR / DEFAULT_WEAT_FILENAME

class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    @classmethod
    def bold(cls, text):
        return cls.BOLD + text + cls.END

    def hl():
        return '-' * 25

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('vocab_path')
    parser.add_argument('-w', '--weat', dest='weat_path',
                        default=DEFAULT_WEAT_PATH)
    return vars(parser.parse_args())

def import_vocab(vocab_path):
    """Reads in a vocab file and returns a dictionary of vocab
    occurrence counts."""
    vocab = {}
    with open(vocab_path) as file:
        for line in file:
            word, count = line.split(' ')
            vocab[word] = int(count)
    return vocab

def vocab_statistics(vocab, weat_sets):
    for ws in weat_sets.values():
        min_occ = None
        max_occ = 0
        for cat in ws.values():
            if not isinstance(cat, dict):
                continue
            vocab_occ = []
            for word in (word.lower() for word in cat['vocab']):
                if word in vocab:
                    count = vocab[word]
                else:
                    count = 0
                vocab_occ.append((word, count))
                if min_occ is None or min_occ > count:
                    min_occ = count
                if max_occ < count:
                    max_occ = count
            cat['vocab'] = vocab_occ
        ws['min_occ'] = min_occ
        ws['max_occ'] = max_occ
    return weat_sets

def get_missing(weat_sets):
    return list(ws for ws in weat_sets if weat_sets[ws]['min_occ'] == 0)

def missing_report(weat_sets):
    buffer = []
    buffer.append(color.hl())
    buffer.append(color.bold('MISSING REPORT'))
    subhead = '{} has missing vocab:'
    row = '  {:32} {}'
    for ws in (ws for ws in weat_sets if weat_sets[ws]['min_occ'] == 0):
        buffer.append(subhead.format(ws))
        vocab = itertools.chain(*(cat['vocab'] for cat in
                                weat_sets[ws].values() if
                                isinstance(cat, dict)))
        for word, count in vocab:
            if count == 0:
                #buffer.append(row.format(word, count))
                pass
    return '\n'.join(buffer)

def main(vocab_path, weat_path=DEFAULT_WEAT_PATH):
    vocab = import_vocab(vocab_path)
    with open(weat_path) as weat_file:
        weat_sets = json.load(weat_file)
    weat_sets = vocab_statistics(vocab, weat_sets)
    print(missing_report(weat_sets))

if __name__ == '__main__':
    main(**parse_args())
