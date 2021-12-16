"""Outputs the documents with the greatest differential bias from an
understanding-bias results file, formatted as html."""

import argparse
import datetime
import json
import os
import sys
from textwrap import TextWrapper

import pandas as pd
import matplotlib.pyplot as plt

def parse_args():
    """parse command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('results_file')
    parser.add_argument('corpus_file')
    parser.add_argument('html_file', nargs='?', default=None)
    parser.add_argument('-n', type=int, default=50)
    parser.add_argument('-b', '--bias-only', dest='effect_direction',
                        action='store_const', const='positive',
                        default=argparse.SUPPRESS)
    parser.add_argument('-d', '--debias-only', action='store_true',
                        default=argparse.SUPPRESS)
    return vars(parser.parse_args())



def select_results(results, n, effect_direction):
    """Returns the n documents with the greatest effect size, one
    DataFrame for each direction of effect size, per WEAT set.)"""
    selects = {}
    # get the names of the differential columns
    diff_cols = set(results.columns.difference(['pid','doc_num']))

    for col in diff_cols:
        selects[col] = []
        sorted_results = results.sort_values(col, ascending=False)
        if effect_direction in ('positive', 'both'):
            selects[col].append(pd.DataFrame(sorted_results.head(n)[col]))
        if effect_direction in ('negative', 'both'):
            # select the last n rows and reverse them
            selects[col].append(pd.DataFrame(sorted_results.tail(n)[::-1][col]))
    return selects

def merge_selects(selects):
    """Merges a nested list of selects into one single DataFrame, sorted
    by document number."""
    documents = pd.DataFrame()
    for weat in selects.values():
        for df in weat:
            documents = documents.merge(df, how='outer', left_index=True,
                                        right_index=True)
    return documents

def merge_text(selects, documents, fields):
    """Adds the text column from a DataFrame of documents to a nested
    list of selects, by matching index."""
    for weat in selects:
        selects[weat] = list(
            df.join(documents[fields]).rename(
                columns={weat:'differential bias'}) for df in selects[weat])
    return selects

def get_documents(selects, corpus_file):
    """Gets the matching documents from a nested list of selects."""

    # read in metadata
    meta_file = corpus_file.replace('.txt', '.meta.json')
    with open(meta_file) as meta_object:
        metadata = json.load(meta_object)

    # create a single documents DataFrame
    documents = merge_selects(selects)

    # create the new columns to be populated
    fields = metadata['fields'] + ['text']
    for field in fields:
        documents.loc[:,field] = None

    select_i = 0
    doc_i = documents.index[select_i]

    with open(corpus_file) as corpus_object:
        for read_i, line in enumerate(corpus_object):
            if read_i == doc_i:
                documents.loc[doc_i, 'text'] = line.strip()
                for field in metadata['fields']:
                    documents.loc[doc_i, field] = metadata['index'][doc_i][field]
                
                # incremement counters
                select_i += 1
                if select_i == len(documents):
                    break
                doc_i = documents.index[select_i]
    selects = merge_text(selects, documents, fields)
    return selects

def metadata_to_string(row, fields=None, labels=None):
    # very quick and dirty differentiation between Simplewiki and
    # nytimes corpora
    if row.index[1] == 'id':
        metadata = {
            'differential bias': '{:.04}'.format(row['differential bias']),
            'article': row['name'],
            'doc no': row['line'] + 1
        }
    else:
        date = row['date']
        date = datetime.date(int(date[0:4]), int(date[4:6]), int(date[6:8]))
        metadata = {
            'differential bias': '{:.04}'.format(row['differential bias']),
            'headline': row['headline'],
            'date': date.strftime('%a, %b %d, %Y'),
            'byline': row['nbyline'],
            'doc no': row['line'] + 1
        }
    buffer = []
    buffer.append('<div class="metadata">')
    for field, value in metadata.items():
        buffer.append('<div class="cell"><em>{}:</em> {}</div>'.format(
            field, value))
    buffer.append('</div>')
    return '\n  '.join(buffer)

def rows_to_string(df, key):
    """Returns the rows of a df as a string buffer."""
    buffer = []
    wrapper = TextWrapper()
    buffer.append('<div class="group">')
    for index, row in df.iterrows():
        buffer.append(metadata_to_string(row, [key, 'headline', 'date',
                                         'nbyline', 'line']))
        buffer.append('<div class="doctext">')
        buffer.append('\n  '.join(wrapper.wrap(row['text'])))
        buffer.append('</div>')
    buffer.append('</div>')
    return '\n  '.join(buffer)

def write_html(selects, html_file):
    """Writes an html file containing all selected documents."""
    buffer = []
    # header
    buffer.append('<html>\n<link rel="stylesheet" href="style.css">\n<body>')
    for key, weat in selects.items():
        buffer.extend(['<h2>', key, '</h2>'])
        for df in weat:
            buffer.append('<hl>')
            buffer.append(rows_to_string(df, key))
    buffer.append('</body></html>')
    with open(html_file, 'w') as fh:
        fh.write('\n'.join(buffer))

def format_table_row(cols):
    buffer = ['<tr>']
    for col in cols:
        buffer.append('<p>{}</p>'.format(col))
    buffer.append('</tr>\n')
    return ''.join(buffer)

def print_statistics(results):
    """Print some statistics about the overall results."""
    print(results.describe())
    print('Maximum gradient:')
    print(results.max().to_string())
    print('Minimum gradient:')
    print(results.min().to_string())
    print('Standard deviation:')
    print(results.std().to_string())
    print(results.quantile([.8, .9, .95, .96, .97, .98, .99, .995,
                            .9995, .99995]))

def main(results_file, corpus_file, n=50, effect_direction='both',
         html_file=None, **kwargs):
    results = pd.read_csv(results_file, skipinitialspace=True)
    results = results.drop(columns=['pid', 'doc_num'])
    print_statistics(results)
    selects = select_results(results, n, effect_direction)
    selects = get_documents(selects, corpus_file)
    if html_file is None:
        html_file = results_file.replace('.csv', '_selects.html')
    write_html(selects, html_file)


if __name__ == '__main__':
    main(**parse_args())
