import json
from pathlib import Path
import sys

def main(corpus_path):
    json_path = corpus_path.with_suffix('.meta.json')
    backup = json_path
    while backup.exists():
        backup = backup.with_name(backup.name + '.bak')
    with open(json_path) as metafile:
        metadata = json.load(metafile)
    with open(corpus_path) as corpus:
        bytec = 0
        for doc, index in zip(corpus, metadata['index']):
            index['byte'] = bytec
            bytec += len(doc.encode('utf-8'))
    with open(json_path, 'w') as metafile:
        json.dump(metadata, metafile, indent=4)


if __name__ == '__main__':
    main(Path(sys.argv[1]))
