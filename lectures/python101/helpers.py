"""Helper utilities for the Python 101 course.

The notebooks import from here with either

    from helpers import import_from_csv, encrypt

or, in the earlier chapters, with

    from helpers import *

Everything listed in ``__all__`` below is meant for you to use. Every public
function has a docstring, so you can always ask python what it does:

    help(download_series)

...or, in VS Code, hover over the name or press [shift]+[tab] inside its
brackets.
"""

import collections
import csv
import random
import re
import string
from functools import reduce
from pathlib import Path

import IPython.display

__all__ = [
    # display
    "print_image",
    # csv
    "import_from_csv",
    "export_to_csv",
    # files
    "list_files",
    "download_series",
    "rename_subtitle",
    "find_episode_number",
    # text
    "encrypt",
    # teaching toys
    "FakeMapReduce",
    "DemoBall",
    "BouncyBallSimulator",
    "ExampleRPS",
    "RPSApp",
    "test_game",
]


# =========================================================================
# Display
# =========================================================================

def print_image(source, _type="img", width=None, height=None):
    """Display an image inside a notebook.

    Arguments:
        source: where the image comes from - a path, or a URL if
            ``_type='net'``.
        _type: what kind of image it is. One of:
            - ``'img'``: a file on your computer (the default)
            - ``'net'``: a URL
            - ``'svg'``: an svg file on your computer
        width: display width in pixels. Optional.
        height: display height in pixels. Optional.

    Returns:
        Nothing - it draws the picture as the cell's output.
    """
    if _type == "net":
        image = IPython.display.Image(url=source, width=width, height=height)
    elif _type == "img":
        image = IPython.display.Image(filename=source, width=width, height=height)
    elif _type == "svg":
        # SVG() takes no width/height, so wrap it if a size was asked for
        image = IPython.display.SVG(filename=source)
    else:
        raise ValueError(f"Unknown _type {_type!r}. Use 'img', 'net' or 'svg'.")

    IPython.display.display(image)


# =========================================================================
# CSV
# =========================================================================
# Note the `encoding` and `newline` arguments below. They are not decoration:
# without `encoding='utf-8'` python uses whatever the operating system happens
# to prefer, which on Windows cannot represent 'ű' or 'ő'; and without
# `newline=''` the csv module's line endings get doubled on Windows, so every
# second row of the file comes out empty.

def import_from_csv(filename, delimiter=","):
    """Read a csv file and return its rows.

    Arguments:
        filename: the file to read.
        delimiter: the character between two values. Default: ``','``.

    Returns:
        A list of rows, where every row is a list of strings.
    """
    with open(filename, "r", encoding="utf-8", newline="") as csvfile:
        return list(csv.reader(csvfile, delimiter=delimiter))


def export_to_csv(filename, data, delimiter=","):
    """Write rows into a csv file.

    Arguments:
        filename: the file to write to. ``.csv`` is appended if missing.
        data: a list of rows, where every row is a list of values.
        delimiter: the character to put between two values. Default: ``','``.

    Returns:
        The path that was written, as a string.
    """
    path = Path(filename)
    if path.suffix.lower() != ".csv":
        path = path.with_suffix(".csv")

    with open(path, "w", encoding="utf-8", newline="") as csvfile:
        csv.writer(csvfile, delimiter=delimiter).writerows(data)

    return str(path)


# =========================================================================
# Files
# =========================================================================

def list_files(target_dir=""):
    """Collect the filenames from a directory (folders are left out).

    Arguments:
        target_dir: the directory to look in. Default: the working directory.
            Both relative (``'pics'``, ``'./pics/'``) and absolute paths work.

    Returns:
        A list of filenames (without the directory part).
    """
    directory = Path(target_dir) if target_dir else Path(".")
    return sorted(item.name for item in directory.iterdir() if item.is_file())


def download_series(name="super_series", seasons=7, episodes=24, mismatch=False):
    """Pretend to download a series, by creating a folder full of empty files.

    One should wear sunglasses to avoid injuries caused by this awesome
    function!

    For every episode it creates a video file (``.avi``) and a subtitle file
    (``.srt``). With ``mismatch=True`` the names get messy - random separators,
    random "release group" noise and random capitalisation - which is what the
    subtitle-renaming exercise is about.

    Arguments:
        name: the name of the series, also the folder name. Default:
            ``'super_series'``.
        seasons: how many seasons. Default: 7.
        episodes: how many episodes per season. Default: 24.
        mismatch: should the subtitle names differ from the video names?
            Default: False.

    Returns:
        A short log message.
    """
    noise = ["hdtv.xvid", "hdtv.fov", "720p-avg", "x264.eng", "BDRip"]
    separators = [".", " ", "_", " - ", "-"]

    directory = Path(name)
    directory.mkdir(exist_ok=True)

    created = 0
    for extension in ("avi", "srt"):
        for season in range(1, seasons + 1):
            for episode in range(1, episodes + 1):
                stem = f"{name}.S{season:02d}E{episode:02d}"

                if mismatch and extension == "srt":
                    stem = (f"{name}{random.choice(separators)}"
                            f"S{season:02d}E{episode:02d}"
                            f"{random.choice(separators)}{random.choice(noise)}")
                    if random.randint(0, 1):
                        stem = stem.lower()
                    elif random.randint(0, 1):
                        stem = stem.upper()

                path = directory / f"{stem}.{extension}"
                path.write_text(str(path), encoding="utf-8")
                created += 1

    return f"Creation successful: {created} files in {directory}/."


def rename_subtitle(original, new, target_dir=""):
    """Rename a file inside a directory.

    Arguments:
        original: the current filename.
        new: the filename you want instead.
        target_dir: the directory both files live in. Default: the working
            directory.

    Returns:
        True if the file was renamed, False if it was not found.
    """
    directory = Path(target_dir) if target_dir else Path(".")
    source = directory / original

    if not source.is_file():
        return False

    source.rename(directory / new)
    return True


def find_episode_number(filename):
    """Find the season-and-episode marker in a filename.

    Arguments:
        filename: a filename that hopefully contains something like
            ``S01E07``.

    Returns:
        The marker as it appears in the name (e.g. ``'S01E07'``), or None if
        there is none.
    """
    pattern = re.compile(r"[Ss]\d+[Ee]\d+")
    match = pattern.search(filename)
    return match.group(0) if match else None


# =========================================================================
# Text
# =========================================================================

def encrypt(text, strength=4, level=1):
    """"Encrypt" a text - badly, on purpose.

    Two things can happen, depending on ``level``:

    - level 1: ``strength - 1`` random letters are inserted after every
      character of the original text. So the original text is still in there,
      every ``strength``-th character.
    - level 2: the same, but the original characters are also shifted along the
      alphabet by ``strength`` positions first ('a' becomes 'c' if strength is
      2). The shift wraps around, so 'z' becomes 'b'.

    Arguments:
        text: the text to transform.
        strength: how much noise to add. Default: 4.
        level: 1 or 2, see above. Default: 1.

    Returns:
        The "encrypted" text as a string.
    """
    if level not in (1, 2):
        raise ValueError(f"level must be 1 or 2, got {level!r}")

    alphabet = string.ascii_letters
    noise_length = strength - 1

    pieces = []
    for character in text:
        if level == 2:
            character = _shift_letter(character, strength)
        noise = "".join(random.choice(alphabet) for _ in range(noise_length))
        pieces.append(character + noise)

    return "".join(pieces)


def _shift_letter(character, offset):
    """Move one letter along the alphabet, wrapping around at the end.

    Anything that is not an ascii letter is returned unchanged.
    """
    if character.islower() and character in string.ascii_lowercase:
        first = ord("a")
    elif character.isupper() and character in string.ascii_uppercase:
        first = ord("A")
    else:
        return character

    return chr(first + (ord(character) - first + offset) % 26)


# =========================================================================
# A fake mapreduce, for the functional programming chapter
# =========================================================================

class FakeMapReduce:
    """An untested, unreliable, unparallel, undistributed fake mapreduce
    "framework" for demonstration purposes only.

    It exists so you can see what pyspark code *looks* like without installing
    spark. Every method returns a new FakeMapReduce, so calls can be chained.
    """

    def __init__(self, data, default=int):
        self.data = data
        self.default = default

    def map(self, function):
        """Apply `function` to every item."""
        return FakeMapReduce([function(item) for item in self.data], self.default)

    def flatMap(self, function):
        """Apply `function` to every item of every sub-list, flattened."""
        flattened = [item for sublist in self.data for item in sublist]
        return FakeMapReduce([function(item) for item in flattened], self.default)

    def filter(self, function):
        """Keep only the items `function` returns True for."""
        return FakeMapReduce([item for item in self.data if function(item)],
                             self.default)

    def reduce(self, function):
        """Squash every item into a single value."""
        result = reduce(function, self.data, collections.defaultdict(self.default))
        return FakeMapReduce(result, self.default)

    def reduceByKey(self, function):
        """Squash the values of each key into a single value.

        Expects the data to be (key, value) pairs.
        """
        grouped = collections.defaultdict(list)
        for key, value in self.data:
            grouped[key].append(value)

        reduced = {key: reduce(function, values) for key, values in grouped.items()}
        return FakeMapReduce(reduced, self.default)

    def collect(self):
        """Return the plain python value inside."""
        return self.data

    def __str__(self):
        return f"<{self.__class__.__name__} with values {self.data}>"

    __repr__ = __str__


# =========================================================================
# The bouncing ball widget, for the classes chapter
# =========================================================================

class DemoBall:
    """A worked example of the Ball class the exercise asks you to write.

    The ball sits at (`x`, `y`), moves by (`vx`, `vy`) every step, and bounces
    when it reaches 0 or the maximum on either axis.
    """

    def __init__(self, x, y, vx=1, vy=1, max_x=5, max_y=7):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.max_x = max_x
        self.max_y = max_y

    def step(self):
        """Advance the ball by one step, bouncing off the walls."""
        next_x = self.x + self.vx
        next_y = self.y + self.vy

        if next_x >= self.max_x or next_x < 0:
            self.vx *= -1
            next_x = self.x + self.vx

        if next_y >= self.max_y or next_y < 0:
            self.vy *= -1
            next_y = self.y + self.vy

        self.x = next_x
        self.y = next_y


class BouncyBallSimulator:
    """Draws a ball object bouncing around, inside a notebook.

    Give it anything with `x`, `y`, `max_x`, `max_y` and a `step()` method -
    either `DemoBall` or the `Ball` class you wrote yourself:

        BouncyBallSimulator(DemoBall(x=0, y=0, max_x=5, max_y=40)).show()
    """

    def __init__(self, ball, emptychar=" "):
        self.ball = ball
        self.height = ball.max_x
        self.width = ball.max_y
        self.emptychar = emptychar
        self.widget = self._build_widget()

    def _build_widget(self):
        """Assemble the start button, the step slider and the drawing area."""
        # imported here rather than at the top of the file, so that the rest of
        # helpers.py still works if ipywidgets is not installed
        from ipywidgets import widgets

        iterations = widgets.IntSlider(value=50, min=1, step=1)
        start = widgets.Button(description="start")
        start.on_click(lambda _: self.play(iterations.value))

        self.textarea = widgets.Textarea()

        return widgets.VBox(children=[
            widgets.HBox(children=[start, iterations]),
            self.textarea,
        ])

    def show(self):
        """Return the widget, so the notebook displays it."""
        return self.widget

    def draw(self, row, column):
        """Draw the playing field with the ball at (row, column)."""
        field = [[self.emptychar for _ in range(self.width)]
                 for _ in range(self.height)]
        field[row][column] = "o"
        self.textarea.value = "\n".join("".join(line) for line in field)

    def step(self):
        """Move the ball once and redraw."""
        self.ball.step()
        self.draw(self.ball.x, self.ball.y)

    def play(self, iterations=50):
        """Run the simulation for `iterations` steps."""
        import time

        self.draw(self.ball.x, self.ball.y)
        for _ in range(iterations):
            self.step()
            time.sleep(0.1)


# =========================================================================
# Rock - paper - scissors, for the classes chapter
# =========================================================================

class ExampleRPS:
    """A worked example of the rock-paper-scissors class.

    `hands` holds the possible moves, `play(hand)` plays one round and returns
    `'win'`, `'lose'` or `'draw'`, and the AI's move is left behind in `ai`.
    """

    trumps = {"r": "p", "p": "s", "s": "r"}

    def __init__(self):
        self.hands = ["r", "p", "s"]
        self.ai = None

    def move(self):
        """Pick a move for the AI."""
        return random.choice(self.hands)

    def play(self, hand):
        """Play one round against `hand`. Returns 'win', 'lose' or 'draw'."""
        self.ai = self.move()
        # remember what would have beaten the player - the cheating version
        # uses this to weight its own choices
        self.hands.append(self.trumps[hand])

        if self.ai == hand:
            return "draw"
        if self.trumps[self.ai] == hand:
            return "win"
        return "lose"


def test_game(game_class):
    """Check that a rock-paper-scissors class has everything RPSApp needs.

    Arguments:
        game_class: the class itself, not an instance of it.

    Raises:
        ValueError: with a message saying what is missing.
    """
    game = game_class()

    if not hasattr(game, "hands"):
        raise ValueError("Provided class does not have a `hands` attribute!")
    if not callable(getattr(game, "play", None)):
        raise ValueError("Provided class does not have a `play` method!")

    # `ai` is only set once a round has been played, so play one
    hands_before = len(game.hands)
    result = game.play(game.hands[0])

    if not hasattr(game, "ai"):
        raise ValueError("Provided class does not save the ai's move "
                         "to an `ai` attribute!")
    if result not in ("win", "lose", "draw"):
        raise ValueError("`play` should return 'win', 'lose' or 'draw', "
                         f"got {result!r}!")
    if len(game.hands) == hands_before:
        raise ValueError("Provided class does not update the `hands` "
                         "attribute with the trump hands!")

    return True


class RPSApp:
    """A little window to play your rock-paper-scissors class in.

    Give it your class (not an instance) and call `run()`:

        RPSApp(MyCheatingRPS).run()

    The layout is:

        +-------------------------------+
        |          result label         |
        +------------+-----+------------+
        | hand_1_btn | ... | hand_n_btn |
        +------------+-----+------------+

    Built on tkinter, which ships with python - nothing to install. Closing the
    window hands control back to the notebook.
    """

    def __init__(self, game_class):
        test_game(game_class)
        self.game = game_class()
        self.window = None
        self.result_label = None

    def play(self, hand):
        """Play one round and update the label."""
        result = self.game.play(hand)
        self.result_label["text"] = f"PLAYER: {hand} | {result} | AI: {self.game.ai}"

    def build(self):
        """Create the window and its widgets."""
        import tkinter as tk

        self.window = tk.Tk()
        self.window.title("Rock - Paper - Scissors")

        hands = self.game.hands
        self.window.columnconfigure(list(range(len(hands))), minsize=150)
        self.window.rowconfigure([0, 1], minsize=50)

        self.result_label = tk.Label(master=self.window, text="",
                                     font=("Courier", 24))
        self.result_label.grid(row=0, columnspan=len(hands))

        for column, hand in enumerate(hands):
            tk.Button(
                master=self.window, text=hand, width=12, height=4,
                command=lambda hand=hand: self.play(hand),
            ).grid(row=1, column=column)

        return self.window

    def run(self):
        """Build the window and wait until it is closed."""
        self.build()
        self.window.mainloop()
