import sys
import json
from os import path
from gensim.corpora.wikicorpus import WikiCorpus

WIKI_FILENAME = 'simplewiki-20171103-pages-articles-multistream.xml.bz2'
MAX_WC = 20_000_000
ARTICLE_MIN_WC = 200
ARTICLE_MAX_WC = 10000


def get_articles(base_dir, wiki_path):
    # dict=True avoids making vocab
    wiki = WikiCorpus(wiki_path, dictionary=True)
    wiki.metadata = True  # Want article titles
    print("Loading Wikipedia archive (this may take a few minutes)... ",
          end="")
    articles = list(wiki.get_texts())
    print("Done.")
    print("Total Number of Articles:", len(articles))
    return articles

def output_corpus(articles, outname):
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
            if art_len >= ARTICLE_MIN_WC and art_len <= ARTICLE_MAX_WC:
                text = " ".join(article)
                wc += art_len
                ac += 1
                pos = f.tell()
                index.append({"id": id, "name": name, "wc": art_len,
                              "line": line, "byte": pos})
                f.write(text)
                f.write("\n")
                line += 1

            if wc >= MAX_WC:
                break
    print("Selected", ac, "documents. (", wc, "words )")
    return index, ac, wc

def write_metadata(index, ac, wc, outname):
    metadata = {
        "source": wiki_filename,
        "document_min_wc": ARTICLE_MIN_WC,
        "document_max_wc": ARTICLE_MAX_WC,
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

def main(wiki_filename, rebuild=False):
    # identify input and output files relative to location of this
    # script
    base_dir = path.join(path.dirname(path.realpath(__file__)),
                         path.pardir)
    wiki_path = path.join(base_dir, 'corpora', wiki_filename)
    outname = path.join(base_dir, 'corpora', 'simplewikiselect')
    
    if path.exists(outname + '.txt' and not rebuild):
        print(outname + '.txt', 'already exists. To forcibly remake',
        'corpus, use --rebuild option.')
        return

    articles = get_articles(base_dir, WIKI_FILENAME)
    index, ac, wc = output_corpus(articles, base_dir, WIKI_FILENAME)
    write_metadata(index, ac, wc, outname)

if __name__ == '__main__':
    if '--rebuild' in sys.argv:
        rebuild = True
    else:
        rebuild = False
    main(WIKI_FILENAME, rebuild)
