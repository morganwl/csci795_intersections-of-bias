"""Front-end for understanding-bias tools."""

import argparse
from pathlib import Path
import re
import subprocess

DEFAULT_EMBEDDING='vectors-C0-V20-W8-D25-R0.05-E15-S1.bin'

BASE_DIR = (Path(__file__).parents[1])
UNDERSTANDING_BIAS = BASE_DIR / 'code' / 'understanding-bias'
CORPORA_DIR = UNDERSTANDING_BIAS / 'corpora'
EMBEDDING_DIR = UNDERSTANDING_BIAS / 'embeddings'
RESULTS_DIR = UNDERSTANDING_BIAS / 'results'
JULIA_DIR = UNDERSTANDING_BIAS / 'src'

CORPORA = {
    'C0': {
        'documents': 'simplewikiselect.txt',
    },
    'C1': {
        'documents': 'nytselect.txt',
    },
    'C2': {
        'documents': 'nytselect_subset_0.2.txt',
    },
    'C3': {
        'documents': 'nytselect_subset_0.5.txt',
    }
}


class Corpora:
    def __init__(self):
        self.corpora = CORPORA

    def from_embedding(self, embedding):
        corpus = re.match(r'vectors-(\w+)-', embedding.stem).group(1)
        return CORPORA_DIR / self.corpora[corpus]['documents']

def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    diff_parser = subparsers.add_parser('diff')
    diff_parser.add_argument('embedding', default=DEFAULT_EMBEDDING)
    diff_parser.add_argument('results', nargs='?', default=None)
    diff_parser.add_argument('-f', '--first', default=1)
    diff_parser.add_argument('-l', '--last', default=None)
    diff_parser.add_argument('--overwrite', action='store_true')
    diff_parser.add_argument('-c', '--corpus', default=None)
    diff_parser.add_argument('-w', '--wordset', type=string_to_list,
                             default=None)
    return vars(parser.parse_args())

def string_to_list(s):
    """Parses a single string as a list of comma or space delimited
    integers."""
    s = s.lstrip('[(')
    s = s.rstrip('])')
    return [w.strip() for w in s.split(',')]

def build_julia(prog, julia_dir=JULIA_DIR, project_dir=UNDERSTANDING_BIAS):
    return ['julia', '--project=' + str(project_dir), Path(julia_dir) / prog]

def expand_embedding(embedding, embedding_dir=EMBEDDING_DIR):
    if Path(embedding).exists():
        return embedding
    ecode = re.match(r'(?:vectors-)?(.*)', embedding).group(1)
    found = []
    found =  [file for file in Path(embedding_dir).glob('vectors-' +
                                                        ecode + '*')]
    if len(found) == 1:
        return found[0]
    raise FileNotFoundError

def expand_results(results, embedding=None, wordset=None,
                   subdir=None, results_dir=RESULTS_DIR):
    if results is None:
        buffer = [] 
        if embedding is not None:
            buffer.append(embedding.stem.replace('vectors-', ''))
        if wordset:
            buffer.append('_'.join(wordset)) 
        buffer.append('.csv')
        results = ''.join(buffer)
    results = Path(results)
    if str(results.parent) == '.':
        results = results_dir / subdir / results
    if not results.parent.exists():
        results.mkdir(parents=True, exist_ok=True)
    return results

def run_differential_bias(embedding, corpus=None, results=None,
                          wordset=None, overwrite=False, first=1,
                          last=None, **kwargs):
    embedding = expand_embedding(embedding)
    corpora = Corpora()
    if corpus is None:
        corpus = corpora.from_embedding(embedding)
    else:
        corpus = corpora.expand(corpus)
    results = expand_results(results, embedding, subdir='diff_bias')
    if not overwrite:
        while results.exists():
            parts = results.stem.rsplit('.', 1)
            try:
                parts[1] = '{:02}'.format(int(parts[1]) + 1)
            except:
                parts.append('01')
            results = results.with_stem('.'.join(parts))
    args = (build_julia('differential_bias.jl') +
        [embedding, corpus, results, '--first', str(first)])
    if wordset is not None:
        args.extend(['--wordset', ','.join(wordset)])
    if last is not None:
        args.extend(['--last', str(last)])
    for arg in args:
        if isinstance(arg, Path):
            arg = arg.relative_to(Path.cwd())
        print(arg)
    print(' '.join(map(str, args)))
    print(subprocess.run(args))

def main(command, **kwargs):
    if command == 'diff':
        run_differential_bias(**kwargs)

if __name__ == '__main__':
    main(**parse_args())
