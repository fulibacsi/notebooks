import random
from collections import Counter

import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns


def autolabel(rects, ax):
    y_bottom, y_top = ax.get_ylim()
    y_height = y_top - y_bottom

    for rect in rects:
        height = rect.get_height()
        label_position = height - (y_height * 0.05)

        ax.text(rect.get_x() + rect.get_width() / 2.,
                label_position,
                '%.2f' % height if height < 1 else '%d' % int(height),
                ha='center', va='bottom',
                color='white', fontweight='bold')


def plot_freqs(freqs):
    fig, ax = plt.subplots()
    rects = ax.bar(range(len(freqs)), freqs.values(), align='center')
    autolabel(rects, ax)
    plt.xticks(range(len(freqs)), freqs.keys())
    return fig


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


class RPS(object):

    beat = {'k': 'p',
            'p': 'o',
            'o': 'k'}

    def __init__(self, mode='naive', seed=None):
        random.seed(seed)
        self.mode = mode
        self.reset()

    def reset(self):
        self.pool = ['k', 'p', 'o']
        self.game_log = []
        if self.mode == 'stateful':
            self.pool = {key: ['k', 'p', 'o'] for key in ['k', 'p', 'o']}
            self.state = None

    def play(self, player):
        ai = self.beat[self.predict()]
        result = self.result(ai, player)

        self.log_game(ai, player, result)
        self.learn(player)

        return result

    def result(self, ai, player):
        if ai == player:
            return 0
        if self.beat[ai] == player:
            return 1
        return -1

    def random(self):
        return random.choice(['k', 'p', 'o'])

    def predict(self):
        if self.mode == 'null':
            return self.random()
        elif self.mode == 'naive':
            return random.choice(self.pool)
        elif self.mode == 'stateful':
            if self.state is None:
                return self.random()
            return random.choice(self.pool[self.state])

    def learn(self, player):
        if self.mode == 'naive':
            self.pool.append(player)
        elif self.mode == 'stateful':
            if self.state is not None:
                self.pool[self.state].append(player)
            self.state = player

    def log_game(self, ai, player, win):
        log = {'ai': ai,
               'player': player,
               'win': win}
        log = merge_dicts(log, self.generate_probs())
        self.game_log.append(log)

    def generate_probs(self):
        probs = {}

        pools = self.pool
        if isinstance(pools, list):
            pools = {self.mode: pools}

        for hand, pool in pools.items():
            pool_length = float(len(pool))
            prob = dict(Counter(pool))
            probs[hand] = {'k': prob['k'] / pool_length,
                           'p': prob['p'] / pool_length,
                           'o': prob['o'] / pool_length}

        return probs

    def stats(self):
        wins = sum([game['win'] == 1 for game in self.game_log])
        draws = sum([game['win'] == 0 for game in self.game_log])
        losses = sum([game['win'] == -1 for game in self.game_log])
        score = sum([game['win'] for game in self.game_log])

        stats = pd.DataFrame([{'Number of games': len(self.game_log),
                               'Number of player wins': wins,
                               'Number of draws': draws,
                               'Number of ai wins': losses,
                               'AI score': score}])
        probs = pd.DataFrame(self.generate_probs())

        return stats, probs

    def plot_probs(self):
        probs = self.generate_probs()
        width = len(probs.keys())

        fig, ax = plt.subplots(ncols=width, sharey=True)
        if width == 1:
            ax = [ax]

        for i, (hand, pool) in enumerate(probs.items()):
            rects = ax[i].bar(range(len(pool)), pool.values(), align='center')
            autolabel(rects, ax[i])

            plt.setp(ax[i], xticks=range(len(pool)), xticklabels=pool.keys())
            ax[i].set_title(hand)

        return fig

    def plot_win_ratio(self):
        fig, ax = plt.subplots()
        wins = sum([game['win'] == 1 for game in self.game_log])
        draws = sum([game['win'] == 0 for game in self.game_log])
        losses = sum([game['win'] == -1 for game in self.game_log])

        rects = ax.bar(range(3), [wins, draws, losses], align='center')
        autolabel(rects, ax)

        plt.setp(ax, xticks=range(3),
                 xticklabels=['player wins', 'draws', 'ai wins'])
        ax.set_title('Outcome')

        return fig
