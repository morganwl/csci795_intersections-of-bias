import sys
import json
from os import path
from gensim.corpora.wikicorpus import WikiCorpus

WIKI_FILENAME = 'simplewiki-20171103-pages-articles-multistream.xml.bz2'
MAX_WC = 20_000_000
ARTICLE_MIN_WC = 200
ARTICLE_MAX_WC = 10000


def get_articles(wiki_path):
    """Parses the wikimedia bz2 file and returns articles as a list of
    strings (one string per article) and a corresponding title index, in
    the form (list of str, (int, str))."""
    # dict=True avoids making vocab
    wiki = WikiCorpus(wiki_path, dictionary=True)
    wiki.metadata = True  # Want article titles
    print("Loading Wikipedia archive (this may take a few minutes)... ",
          end="")
    articles = list(wiki.get_texts())
    print("Done.")
    print("Total Number of Articles:", len(articles))
    return articles

def output_corpus(articles, outname, max_wc=None, min_wc=None,
                  total_max_wc=None):
    """Filters articles between min_wc and max_wc and saves them to a
    text file, one article per line. Stops if the total file size would
    exceed total_max_wc. Returns an index of selected articles, the
    article count and the word count."""
    if max_wc is None:
        max_wc = ARTICLE_MAX_WC
    if min_wc is None:
        min_wc = ARTICLE_MIN_WC
    if total_max_wc is None:
        total_max_wc = MAX_WC
    num_articles = len(articles)
    ac = 0
    wc = 0
    selected=[]
    index = []  # Save information about articles as they've been processed.

    with open(outname + ".txt", "w") as f:
        line = 0
        for i in range(num_articles):
            article, (id, name) = articles[i]
            art_len = len(article)
            if art_len >= min_wc and art_len <= max_wc:
                text = " ".join(article)
                wc += art_len
                ac += 1
                pos = f.tell()
                index.append({"id": id, "name": name, "wc": art_len,
                              "line": line, "byte": pos})
                f.write(text)
                f.write("\n")
                line += 1

            if wc >= total_max_wc:
                break
    print("Selected", ac, "documents. (", wc, "words )")
    return index, ac, wc

def write_metadata(index, ac, wc, outname, max_wc=None, min_wc=None):
    if max_wc is None:
        max_wc = ARTICLE_MAX_WC
    if min_wc is None:
        min_wc = ARTICLE_MIN_WC
    metadata = {
        "source": wiki_filename,
        "document_min_wc": min_wc,
        "document_max_wc": max_wc,
        "num_documents": ac,
        "num_words": wc,
        "fields": list(index[0].keys()),
        "index": index}

    with open(outname + ".meta.json", "w") as f:
        json.dump(metadata, f, indent=4)

    with open(outname + ".meta.txt", "w") as f:
        del metadata["index"]
        for key, val in metadata.items():
            f.write(key)
            f.write(": ")
            f.write(str(val))
            f.write("\n")

def main(wiki_filename, outname=None, rebuild=False):
    # identify input and output files relative to location of this
    # script
    base_dir = path.join(path.dirname(path.realpath(__file__)),
                         path.pardir)
    wiki_path = path.join(base_dir, 'corpora', wiki_filename)
    if outname is None:
        outname = path.join(base_dir, 'corpora', 'simplewikiselect')
    else:
        outname = path.join(base_dir, 'corpora', outname)
    
    if path.exists(outname + '.txt') and not rebuild:
        print(outname + '.txt', 'already exists. To forcibly remake',
        'corpus, use --rebuild option.')
        return

    articles = get_articles(wiki_path)
    index, ac, wc = output_corpus(articles, outname, ARTICLE_MAX_WC,
                                  ARTICLE_MIN_WC, MAX_WC)
    write_metadata(index, ac, wc, outname)

if __name__ == '__main__':
    if '--rebuild' in sys.argv:
        rebuild = True
        sys.argv.remove('--rebuild')
    else:
        rebuild = False
    if len(sys.argv) > 1:
        wiki_filename = sys.argv[1]
    else:
        wiki_filename = WIKI_FILENAME
    if len(sys.argv) > 2:
        outname = sys.argv[2]
    else:
        outname = None
    main(wiki_filename, outname, rebuild)
