#!/usr/bin/env python3
# pylint: skip file

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="understanding-bias-hunter",
    version="0.0.1",
    description=('Modified version of code for ', 
                 '"Understanding Bias in Word Embeddings", ',
                 'updated for Hunter College CSCI795 class project, ',
                 '2021'),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=('https://github.com/morganwl/csci795_intersections-of-bias/',
         'tree/main/proposal'),
    scripts=['scripts/make_plots.py',
             'scripts/make_wiki_corpus.py',
             'scripts/make_nyt_corpus.py'],
    packages=setuptools.find_packages(),
    install_requires=['boto',
                      'boto3',
                      'bz2file',
                      'certifi',
                      'chardet',
                      'docutils',
                      'gensim',
                      'idna',
                      'jmespath',
                      'numpy',
                      'python-dateutil',
                      'requests',
                      's3transfer',
                      'scipy',
                      'six',
                      'smart-open',
                      'urllib3',
                      ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS X",
    ],
    python_requires='>=3.7',
)
