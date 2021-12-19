"""Creates a new, smaller corpus randomly sampled from a larger
corpus."""

import argparse
import json
import os
from zlib import crc32

import numpy as np

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('corpus')
    parser.add_argument('new_corpus_path', nargs='?', default=None)
    parser.add_argument('-r', '--ratio', type=float, default=0.2)
    parser.add_argument('-s', '--seed', type=int, default=1)
    return vars(parser.parse_args())

def in_subset(identifier, ratio):
    return crc32(np.int64(identifier)) & 0xffffffff < ratio * 2 **32

def sample_corpus(corpus, metadata, ratio):
    """Creates a subset of a corpus with corresponding metadata."""
    new_corpus = []
    new_index = []
    num_documents = 0
    num_words = 0
    num_bytes = 0
    with open(corpus) as corpus_file:
        for line, meta in zip(corpus_file, metadata['index']):
            if in_subset(meta['line'], ratio):
                meta = meta.copy()
                meta['line'] = len(new_corpus)
                meta['byte'] = num_bytes
                new_corpus.append(line)
                new_index.append(meta)
                num_documents += 1
                num_words += len(line.split(' '))
                num_bytes += len(line.encode('utf-8'))
    new_metadata = {
        'num_documents': num_documents,
        'num_words': num_words,
        'index': new_index,
    }
    return new_corpus, new_metadata

def merge_metadata(metadata, new_metadata):
    """Adds unchanged fields from old metadata to new metadata."""
    for key in metadata:
        if key not in new_metadata:
            new_metadata[key] = metadata[key]
    return new_metadata

def write_corpus(corpus, metadata, corpus_path):
    """Writes a corpus and corresponding metadata to files."""
    with open(corpus_path, 'w') as file:
        file.writelines(corpus)
    with open(corpus_path.replace('.txt', '.meta.json'), 'w') as file:
        json.dump(metadata, file, indent=4)
    with open(corpus_path.replace('.txt', '.meta.txt'), 'w') as file:
        for key, value in metadata.items():
            if key == 'index':
                continue
            file.write('{}: {}\n'.format(key, str(value)))

def main(corpus, new_corpus_path=None, ratio=0.2, seed=1, **kwargs):
    meta_json_path = corpus.replace('.txt', '.meta.json')
    meta_txt_path = corpus.replace('.txt', '.meta.txt')
    if new_corpus_path is None:
        new_corpus_path = corpus.replace('.txt',
                                    '_subset_{:.03}.txt'.format(ratio))
    with open(meta_json_path) as meta_json:
        metadata = json.load(meta_json)
    new_corpus, new_metadata = sample_corpus(corpus, metadata, ratio)
    new_metadata = merge_metadata(metadata, new_metadata)
    write_corpus(new_corpus, new_metadata, new_corpus_path)
    print('{} documents written to {}.'.format(
        new_metadata['num_documents'], new_corpus_path))

if __name__ == '__main__':
    main(**parse_args())
