call conda config --add channels conda-forge
call conda create -y -n seminar python=3.6 requests selenium beautifulsoup4 nltk scikit-learn spacy gensim pandas matplotlib seaborn tqdm jupyter notebook
call activate seminar
call python -m nltk.downloader stopwords
call python -m spacy download en
call python download.py
call jupyter notebook --notebook-dir=%HOMEPATH%\Downloads\ --allow-root