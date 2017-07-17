import os


def list_books(path):
    dirpath, subdirs, docs = list(os.walk('./docs/'))[0]
    return [dirpath + doc for doc in docs]