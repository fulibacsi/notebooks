# encoding: utf-8
# Utility file for the Python101

# ============ imports ============
import os
import re
import time
import string
import random


# ============ functions ============


# fake download function
def download_series(_name='super_series',
                    _seasons=7,
                    _episodes=24,
                    _mismatch=False):
    """Download the specified series into a directory.
    One should wear sunglasses to avoid injuries caused by this awesome
    function!

    Arguments:
        _name: name of the series. default: 'super_series'
        _seasons: the number of seasons. default: 7
        _episodes: the number of episodes in a season. default: 24
        _mismatch: does the subtitle names matches?
    Returns:
        Log text.
    """
    seasons = range(1, _seasons+1)
    episodes = range(1, _episodes+1)
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
        filename = ('{filename}'
                    '{sep1}'
                    'S{season}'
                    'E{episode}'
                    '{sep2}'
                    '{obfuscation}'
                    '.{extension}')
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
def rename_subtitle(original, new, target_dir='.'):
    """Renames the specified file to a new name.
    Arguments:
        original: original filename
        new: new filename
        target_dir: subdirectory
    Returns:
        -
    """
    if len(target_dir):
        if not target_dir[-1] == '/':
            target_dir = target_dir + '/'
    if original in os.listdir(target_dir):
        os.rename(target_dir + original, target_dir + new)


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
    distortion = range(strength - 1)
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


# BALL WIDGET
from ipywidgets import widgets
from time import sleep


class BouncyBallSimulator(object):

    def __init__(self, ball, emptychar=' '):
        self.ball = ball

        self.height = self.ball.max_x
        self.width = self.ball.max_y

        self.emptychar = emptychar

        self.widget = self.init_widgets()

    def init_widgets(self):
        # iter slider
        numiter = widgets.IntSlider(value=50, min=1, step=1)
        # start button
        startbutton = widgets.Button(description='start')
        startbutton.on_click(lambda x: self.play(numiter.value))

        # pack iterslider and start button together
        buttonbox = widgets.HBox()
        buttonbox.children = [startbutton, numiter]

        # draw area
        self.textarea = widgets.Textarea()

        # packed widget
        container = widgets.VBox()
        container.children = [buttonbox, self.textarea]

        return container

    def show(self):
        return self.widget

    def draw(self, i, j):
        field = [[self.emptychar for _ in range(self.width)]
                 for _ in range(self.height)]
        field[i][j] = 'o'

        fieldstr = '\n'.join([''.join(char) for char in field])
        self.textarea.value =  fieldstr

    def step(self):
        self.ball.step()
        i, j = self.ball.x, self.ball.y
        self.draw(i, j)

    def play(self, numiter=50):
        # draw init position
        i, j = self.ball.x, self.ball.y
        self.draw(i, j)

        for _ in range(numiter):
            self.step()
            sleep(.1)


class DemoBall(object):

    def __init__(self, x, y, vx=1, vy=1, max_x=5, max_y=7):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.max_x = max_x
        self.max_y = max_y

    def step(self):
        nextx = self.x + self.vx
        nexty = self.y + self.vy
        if nextx >= self.max_x or nextx < 0:
            self.vx *= -1
            nextx = self.x + self.vx
        if nexty >= self.max_y or nexty < 0:
            self.vy *= -1
            nexty = self.y + self.vy
        self.x = nextx
        self.y = nexty


# ============== KIVY APP FOR RPS GAME ==============

from kivy.app import App

from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button


class RPSApp(App):
    """
    Requires a Game class with a play method.
    Game class should:
    - store the available moves in the hands attribute
    - have a play method which
        - stores the ai's move in the ai attribute
        - returns the result of a play
    """

    def __init__(self, Game):
        super().__init__()
        self.test_game(Game)
        self.game = Game()

    @staticmethod
    def test_game(Game):
        game = Game()

        attribs = dir(game)
        if 'play' not in attribs:
            raise ValueError('Provided class does not have `play` method!')

        if 'hands' not in attribs:
            raise ValueError('Provided class does not have `hands` attribute!')

        hands_length = len(game.hands)
        result = game.play(game.hands[0])
        attribs = dir(game)
        if 'ai' not in attribs:
            raise ValueError('Provided class does not save ai moves '
                             'to `ai` attribute!')

        if hands_length == len(game.hands):
            raise ValueError('Provided class does not update `hands` '
                             'attribute with the trump hands!')

    def play(self, hand, widget):
        """Play one round of the game and updates the widget text"""
        result = self.game.play(hand)
        widget.text = (f'PLAYER: {hand} | {result} | AI: {self.game.ai}')

    def build(self):
        """
        Builds the following grid for playing the game:
        +-------------------------------+
        |          result label         |
        +------------+-----+------------+
        | hand_1_btn | ... | hand_n_btn |
        +------------+-----+------------+

        """
        # result label
        result_label = Label(text='')

        # buttons
        button_layout = GridLayout(cols=len(self.game.hands))
        for hand in self.game.hands:
            button = Button(text=hand,
                            on_press=lambda btn: self.play(btn.text,
                                                           result_label))
            button_layout.add_widget(button)

        # final grid
        layout = GridLayout(rows=2)
        layout.add_widget(result_label)
        layout.add_widget(button_layout)

        return layout


class ExampleRPS:

    trumps = {'r': 'p',
              'p': 's',
              's': 'r'}

    def __init__(self):
        self.hands = ['r', 'p', 's']

    def move(self):
        return random.choice(self.hands)

    def play(self, hand):
        self.ai = self.move()
        self.hands.append(self.trumps[hand])

        print(f'LOG > P:{hand} AI:{self.ai}')
        if self.ai == hand:
            return 'draw'

        elif self.trumps[self.ai] == hand:
            return 'win'

        else:
            return 'lose'
