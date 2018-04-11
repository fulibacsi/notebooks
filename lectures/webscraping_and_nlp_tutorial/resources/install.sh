conda config --add channels conda-forge
conda create -y -n seminar python=3.6 requests selenium beautifulsoup4 nltk scikit-learn spacy gensim pandas matplotlib seaborn tqdm jupyter notebook
source activate seminar
python -m nltk.downloader stopwords
python -m spacy download en
python download.py
jupyter notebook --notebook-dir=~/Downloads/ --allow-root