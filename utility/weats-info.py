"""Reads a weat wordsets file and returns prints some information."""

import json
import os
import sys

def get_set(fh):
    weat_set = []
    nest = []
    closing = { '(':')', '{':'}', '[':']', '\'':'\'', '"':'"' }
    line = next(fh, None)
    while line is not None:
        line = line.strip('\n')
        weat_set.append(line)
        for c in line:
            if nest and nest[-1] == c:
                nest.pop()
                continue
            if c in closing:
                nest.append(closing[c])
                continue
        if not nest:
            break
        line = next(fh, None)
    if nest:
        return None
    # remove trailing comma off weat_set
    if weat_set:
        weat_set[-1] = weat_set[-1].strip(',')
    return weat_set

def get_key(line):
    buffer = []
    open = False
    for c in line:
        if open:
            if c == '"':
                open = False
                continue
            buffer.append(c)
            continue
        if c == '"':
            open = True
            continue
        if buffer and c == ':':
            return ''.join(buffer)

def set_info(weat_set):
    buffer = []
    weat_set[0] = '{'
    weat_set = json.loads('\n'.join(weat_set))
    for key, value in weat_set.items():
        if key == 'source':
            buffer.append(' Source: ' + value)
        elif key == 'link':
            pass
        else:
            buffer.append('  ' + key + ': ' + vocab_info(value))
    return '\n'.join(buffer)
            
def vocab_info(vocab):
    return '{}, {} words.'.format(
        vocab['category'],
        len(vocab['vocab']),
        ','.join(vocab['vocab']))

def main(inputfile):
    sets = 0
    duplicates = {}
    with open(inputfile) as fh:
        next(fh)
        weat_set = get_set(fh)
        while weat_set:
            sets +=1
            set_name = get_key(weat_set[0])
            if set_name in duplicates:
                duplicates[set_name].append(weat_set)
            else:
                duplicates[set_name] = [weat_set]
            weat_set = get_set(fh)
    print('Total word sets:', sets)
    for key, sets in duplicates.items():
        if len(sets) > 1:
            print('Duplicates found for', key)
            for weat_set in sets:
                print(set_info(weat_set))


if __name__ == '__main__':
    main(sys.argv[1])
