"""Functions to hide complexity from the audience."""

import os

from collections import Counter

import matplotlib.pyplot as plt
import seaborn as sns

import numpy as np
import dask.array as da
import dask.bag as db


def list_books(path):
    dirpath, subdirs, docs = list(os.walk(path))[0]
    return [dirpath + doc for doc in docs]


def mean(iterable):
    if isinstance(iterable, list):
        return np.mean([len(book) for book in iterable])
    return iterable.mean(axis=0)[::100]


def plot_histogram(books):
    fig, ax = plt.subplots()
    ax.hist([len(book) for book in books], bins=1000)


def print_most_common(wordcount, precomputed=False):
    if not precomputed:
        wordcount = Counter(wordcount).most_common(10) 

    for word, cnt in wordcount:
        print word, cnt
        

def generate_random_matrix(size, distributed=False):
    if distributed:
        return da.random.normal(10, 0.1, size=size, chunks=(2000, 2000))
    return np.random.normal(10, 0.1, size=size)
        
        
def load_books(path):
    return db.read_text(path).repartition(32).persist()