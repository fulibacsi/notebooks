# encoding: utf-8
# Utility file for the Python101

# ============ imports ============
import os
import string
import operator
import collections
import csv
import codecs
import random
import time
import re
import IPython.display

#  ============ globals ============
OR = operator.or_
AND = operator.and_

# ============ functions ============

# Image print
def print_image(source, _type='img', width=None, height=None):
    """Display an image. (IPython notebook exclusive!)
    Arguments:
        source: image URI.
        _type: the type of the image. available values:
            - net: URL
            - svg: svg image
            - img: standard image
        _width: display width
        _height: display height
    """
    if _type == 'net':
        IPython.display.display(
            IPython.display.Image(url=source, width=width, height=height)
        )
    elif _type == 'img':
        IPython.display.display(
            IPython.display.Image(filename=source, width=width, height=height)
        )
    elif _type == 'svg':
        IPython.display.display(
            IPython.display.SVG(source, width, height)
        )

# CSV reader
def import_from_csv(filename):
    """Returns the rows from the specified csv file.
    Arguments:
        filename: the file to read.
    Returns:
        List of the rows (where the values in the row are in a list).
    """
    data = []
    with open(filename, 'r') as csvfile:
        CSV = csv.reader(csvfile, dialect='excel')
        for row in CSV:
            data.append(row)
    return data

# CSV writer
def export_to_csv(filename, data):
    """Writes the data lines into a csv file.
    Arguments:
        filename: the file to write the data to.
        data: the data to write.
    Returns:
        -
    """
    if '.csv' not in filename:
        filename += '.csv'
    with open(filename, 'w') as csvfile:
        CSV = csv.writer(csvfile, dialect='excel')
        for row in data:
            CSV.writerow(row)

# file listing
def list_files(target_dir=''):
    """Collect the filenames from the specified directory.
    Argument:
        target_dir: subdirectory name. default: working directory.
    Returns:
        Filenames from the specified directory as a list."""
    if len(target_dir):
        if not target_dir[0] == '/':
            target_dir = '/' + target_dir
    return [_file
        for _file in os.listdir('.' + target_dir)
        if os.path.isfile('.' + target_dir + '/' + _file)
    ]

# fake download function
def download(_name='super_series', _seasons=7, _episodes=24, _mismatch=False):
    """Download the specified series into a directory.
    One should wear sunglass to avoid injuries caused by this awesome function!

    Arguments:
        _name: name of the series. default: 'super_series'
        _seasons: the number of seasons. default: 7
        _episodes: the number of episodes in a season. default: 24
        _mismatch: does the subtitle names matches?
    Returns:
        Log text.
    """
    seasons = xrange(1, _seasons+1)
    episodes = xrange(1, _episodes+1)
    movie_ext = 'avi'
    subtitle_ext = 'srt'
    subdir = './' + _name
    obfuscation = ['hdtv.xvid', 'hdtv.fov', '720p-avg', 'x264.eng', 'BDRip']
    separators = ['.', ' ', '_', ' - ', '-']
    possible_items = [{'season': s, 'episode': e, 'extension': x}
                      for x in [movie_ext, subtitle_ext]
                      for e in episodes
                      for s in seasons]
    if _mismatch:
        filename = '{filename}{sep1}S{season}E{episode}{sep2}{obfuscation}.{extension}'
    else:
        filename = '{filename}.S{season}E{episode}.{extension}'

    try:
        os.mkdir(subdir)
    except Exception:
        pass

    try:
        for item in possible_items:
            if _mismatch:
                path = subdir + '/' + filename.format(
                    filename=_name,
                    season=str(item['season']).zfill(2),
                    episode=str(item['episode']).zfill(2),
                    sep1=random.choice(separators),
                    sep2=random.choice(separators),
                    obfuscation=random.choice(obfuscation),
                    extension=item['extension']
                )
                if random.randint(0,1):
                    path = path.lower()
                elif random.randint(0,1):
                    path = path.upper()
            else:
                path = subdir + '/' + filename.format(
                    filename=_name,
                    season=str(item['season']).zfill(2),
                    episode=str(item['episode']).zfill(2),
                    extension=item['extension']
                )
            # file creation
            open(path, 'w').write(path)
    except Exception as e:
        return 'Creation process failed, ERROR:', e.message
    else:
        return 'Creation successful.'

# rename erroneous subtitle
def rename_subtitle(original, new, target_dir):
    """Renames the specified file to a new name.
    Arguments:
        original: original filename
        new: new filename
    Returns:
        -
    """
    if len(target_dir):
        if not target_dir[0] == '/':
            target_dir = '/' + target_dir
        if not target_dir[-1] == '/':
            target_dir = target_dir + '/'
    if original in list_files(target_dir):
        os.rename('.' + target_dir + original, '.' + target_dir + new)

def find_episode_number(filename):
    """Finds the seasons and episode numbers.
    Arguments:
        filename: the filename containing the seasons and episode numbers
    Returns:
        The seasons-episode numbers (sXXeYY X in series numbers, Y in episode
        numbers) or None if the number was not found.
    """
    pattern = re.compile(r'(\S+)[\.|\ |\ -\ |_|\-]'
                          '(?P<number>[S|s][0-9]+[E|e][0-9]+)')
    match = re.search(pattern, filename)
    if match:
        return match.group('number')
    else:
        return None

def encrypt(text, strength=4, level=1):
    """"Encrypt" a text by inserting random character [strength] times
    (level=1), and by  sliding the letters by [strength] positions (level=2),
    eg. the input letter 'a' becomes 'c' if strength equals 2.

    Parameters:
    -----------
    text: string
        Input text to be transformed.
    strength: int
        Intensity parameter. It will be used to determine the number of
        distortion characters and the sliding intensity.
    level: [1, 2]
        Level of encription:
            1) Only distortion characters inserted
            2) Beside distortion characters, the characters of the input
               strings also slides.

    Returns:
    --------
    encrypted: string
        The encrypted text.

    """
    abc = string.ascii_letters
    distortion = xrange(strength - 1)
    if level == 1:
        encrypted = [
            char +
            ''.join([random.choice(abc) for i in distortion])
            for char in text
        ]
    elif level == 2:
        encrypted = [
            chr(ord(char)+strength) +
            ''.join([random.choice(abc) for i in distortion])
            for char in text
        ]

    return ''.join(encrypted)


# custom assert functions

def isstr(candidate):
    return isinstance(candidate, (str, unicode))
    

def isiter(candidate):
    return isinstance(candidate, (tuple, list, dict))
    
    
def islist(candidate):
    return isinstance(candidate, (tuple, list))
    

def isdict(candidate):
    return isinstance(candidate, dict)
    
    
def isnumber(candidate):
    return isinstance(candidate, (int, float))


def extract_from_dict(data):
    if len(data) == 1:
        (a, b), = data.items()
    elif len(data) == 2:
        (a_key, a_value), (b_key, b_value) = data.items()
        if isstr(a_key) and isstr(b_key):
            a, b = a_value, b_value
        else:
            a, b = a_key, b_key
    else:
        assert False, "Wrong dictionary format!"
    return a, b

        
def check_grocery_list(data):
    assert isdict(data), "Wrong data type!"
    assert len(data.items()) > 4, "Too short!"
    for key, value in data.items():
        assert isstr(key), "Wrong key type!"
        assert isnumber(value), "Wrong value type!"
    return data


def check_updated_grocery_list(data):
    assert isdict(data), "Wrong data type!"
    assert len(data.items()) > 4, "Too short!"
    for key, value in data.items():
        assert isstr(key), "Wrong key type!"
        assert isiter(value), "Wrong value type!"
        if islist(value):
            assert len(value) == 2, "Value size mismatch!"
            measure, quantity = value
        else:
            measure, quantity = extract_from_dict(value)
        if not isstr(measure):
            measure, quantity = quantity, measure
        assert isstr(measure), "Measurement type mismatch!"
        assert isnumber(quantity), "Quantity type mismatch!"
            
    return data

    
def check_decision_list(decision_list):
    assert islist(decision_list), "Wrong decision list type! ({})".format(decision_list)
    assert len(decision_list) > 0, "Empty decision list!"
    for item in decision_list:
        assert isiter(item), "Wrong decision list item type!"
        if islist(item):
            assert len(item) == 2, "Wrong decision list item size!"
            text, target = item
        else:
            text, target = extract_from_dict(item)
        if not isstr(text):
            text, target = target, text
        assert isstr(text), "Wrong decision text type! ({})".format(text)
        assert isinstance(target, (int, bool)), "Wrong decision target chapter type! ({})".format(target)

        
def check_chapter(chapter):
    assert isdict(chapter), "Wrong chapter type!"
    number, data = extract_from_dict(chapter)
    if not isnumber(number):
        number, data = data, number
    assert isnumber(number), "Wrong chapter number type! ({})".format(number)
    assert isiter(data), "Wrong chapter data type! ({})".format(data)
    if islist(data):
        assert len(data) == 2, "Wrong chapter data length!"
        text, decision_list = data
    else:
        text, decision_list = extract_from_dict(data)
    if not isstr(text):
        text, decision_list = decision_list, text
    assert isstr(text), "Wrong chapter text type! ({})".format(text)
    check_decision_list(decision_list)
        
        
def check_book(book):
    assert isiter(book), "Wrong book type!"
    if isdict(book):
        book = [{'number': number, 'data': data} for number, data in book.items()]
    for chapter in book:
        check_chapter(chapter)
    return book
        
    
class FakeMapReduce(object):
    """An untested, unreliable, unparallel, undistributed
    fake mapreduce "framework" for demonstration purposes only.
    """
    
    def __init__(self, data, default=int):
        self.data = data
        self.default = default
        
    def map(self, function):
        data = map(function, self.data)
        return FakeMapReduce(data, self.default)
        
    def flatMap(self, function):
        data = map(function, sum(self.data, []))
        return FakeMapReduce(data, self.default)
    
    def filter(self, function):
        data = filter(function, self.data)
        return FakeMapReduce(data, self.default)
        
    def reduce(self, function):
        data = reduce(function, 
                      self.data, 
                      collections.defaultdict(self.default)),
        return FakeMapReduce(data, self.default)
    
    def reduceByKey(self, function):
        key_value = collections.defaultdict(list)
        
        for key, value in self.data:
            key_value[key].append(value)
        
        for key, value in key_value.items():
            key_value[key] = reduce(function, value)
        
        return FakeMapReduce(key_value, self.default)
    
    def __str__(self):
        return "<{} with values {}>".format(self.__class__.__name__, self.data)
        
        
def slowadd(x, y):
    print 'executing {} + {}'.format(x, y)
    time.sleep(random.random())
    return x + y