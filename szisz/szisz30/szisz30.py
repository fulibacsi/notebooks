# encoding: utf-8

import random
from copy import deepcopy
from collections import Counter
from itertools import product

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier

import matplotlib.pyplot as plt
import seaborn as sns

from ipywidgets import widgets


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
    transform_map = {'z': [0, 0, 0],
                     'k': [1, 0, 0], 
                     'p': [0, 1, 0],
                     'o': [0, 0, 1]}

    def __init__(self, mode='naive', seed=None, memsize=1):
        random.seed(seed)
        self.mode = mode
        self.seed = seed
        self.pool = ['k', 'p', 'o']
        self.game_log = []
        if self.mode == 'stateful':
            self.memsize = min(memsize, 3)
            self.pool = self.generate_stateful_pool()
            self.state = None
        if self.mode == 'neural':
            self.mlp = MLPClassifier(random_state=self.seed)
            # all zero previous games
            self.state = {'player': ['z'] * 5,
                          'ai': ['z'] * 5}
    
    def generate_stateful_pool(self):
        keys = []
        for i in range(self.memsize):
            variations = [''.join(pair) 
                          for pair in product('kpo', repeat=i + 1)]
            keys += variations
        return {key: ['k', 'p', 'o'] for key in keys}

    def reset(self):
        self.pool = ['k', 'p', 'o']
        self.game_log = []
        if self.mode == 'stateful':
            self.pool = self.generate_stateful_pool()
            self.state = None
        if self.mode == 'neural':
            self.mlp = MLPClassifier(random_state=self.seed)
            # all zero previous games
            self.state = {'player': ['z'] * 5,
                          'ai': ['z'] * 5}

    def new(self):
        return self.__class__(self.mode, self.seed)

    def copy(self):
        return deepcopy(self)

    def play(self, player, plot=False):
        if len(player) == 1:
            return self.play_one(player)
        return self.play_multiple(player, plot)

    def play_one(self, player):
        ai = self.beat[self.predict()]
        result = self.result(ai, player)

        self.log_game(ai, player, result)
        self.learn(ai, player)

        return result

    def play_multiple(self, player, plot=False):
        results = [self.play_one(p) for p in player]
        return self.plot_win_ratio() if plot else results

    def result(self, ai, player):
        if ai == player:
            return 0
        return 1 if self.beat[ai] == player else -1

    def random(self):
        return random.choice(['k', 'p', 'o'])

    def predict(self):
        if self.mode == 'null':
            return self.random()
        elif self.mode == 'naive':
            return random.choice(self.pool)
        elif self.mode == 'stateful':
            if self.state is not None:
                return random.choice(self.pool[self.state])
        elif self.mode == 'neural':
            if hasattr(self.mlp, 'coefs_'):
                X = self.process_history()
                prediction = self.mlp.predict(X)
                return prediction[0]
        return self.random()

    def process_history(self):
        """Transforms historical hand data into a concatenated vector."""
        ai = [self.transform_map[hand] for hand in self.state['ai']]
        player = [self.transform_map[hand] for hand in self.state['player']]
        X = [sum(ai + player, [])]
        return X

    def update_state(self, ai, player):
        if self.mode == 'stateful':
            state = (self.state or '') + player
            return state[-self.memsize:]
        elif self.mode == 'neural':
            ai = self.state['ai'] + [ai]
            player = self.state['player'] + [player]
            state = {'ai': ai[1:],
                     'player': player[1:]}
            return state

    def learn(self, ai, player):
        if self.mode == 'naive':
            self.pool.append(player)
        elif self.mode == 'stateful':
            if self.state is not None:
                self.pool[self.state].append(player)
            self.state = self.update_state(ai, player)
        elif self.mode == 'neural':
            X = self.process_history()
            y = [player]
            self.mlp.partial_fit(X, y, classes=self.pool)
            self.state = self.update_state(ai, player)

    def log_game(self, ai, player, result):
        log = {'ai': ai,
               'player': player,
               'result': result}
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
        wins = sum([game['result'] == 1 for game in self.game_log])
        ties = sum([game['result'] == 0 for game in self.game_log])
        losses = sum([game['result'] == -1 for game in self.game_log])
        score = sum([game['result'] * -1 for game in self.game_log])

        stats = pd.DataFrame([{'Number of games': len(self.game_log),
                               'Number of player wins': wins,
                               'Number of ties': ties,
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
        wins = sum([game['result'] == 1 for game in self.game_log])
        ties = sum([game['result'] == 0 for game in self.game_log])
        losses = sum([game['result'] == -1 for game in self.game_log])

        rects = ax.bar(range(3), [wins, ties, losses], align='center')
        autolabel(rects, ax)

        plt.setp(ax, xticks=range(3),
                 xticklabels=['player wins', 'ties', 'ai wins'])
        ax.set_title('Outcome')

        return fig


class Simulate(object):

    beat = {'k': 'p',
            'p': 'o',
            'o': 'k'}

    def __init__(self, p1, p2, rounds=1000, p1static=False, p2static=False):
        self.orig_p1 = p1.copy()
        self.orig_p2 = p2.copy()

        self.p1 = self.orig_p1.copy()
        self.p2 = self.orig_p2.copy()

        self.p1static = p1static
        self.p2static = p2static

        self.rounds = rounds
        self.game_log = []

    def reset(self):
        self.p1 = self.orig_p1.copy()
        self.p2 = self.orig_p2.copy()
        self.game_log = []

    def play(self, plot=False):
        for game in range(self.rounds):
            self.play_one()
        return self.plot() if plot else self.evaluate()

    def play_one(self):
        p1hand = self.beat[self.p1.predict()]
        p2hand = self.beat[self.p2.predict()]

        result = self.result(p1hand, p2hand)
        self.log(p1hand, p2hand, result)

        if not self.p1static:
            self.p1.learn(p2hand)
        if not self.p2static:
            self.p2.learn(p1hand)

    def result(self, p1, p2):
        if p1 == p2:
            return 'tie'
        if self.beat[p1] == p2:
            return 'p2'
        return 'p1'

    def log(self, p1, p2, result):
        self.game_log.append({'p1': p1,
                              'p2': p2,
                              'result': result})

    def evaluate(self):
        p1wins = sum([game['result'] == 'p1' for game in self.game_log])
        p2wins = sum([game['result'] == 'p2' for game in self.game_log])
        
        return {'p1wins': p1wins,
                'p2wins': p2wins,
                'p1score': p1wins - p2wins,
                'p2score': p2wins - p1wins,
                'games': len(self.game_log),
                'ties': len(self.game_log) - p1wins - p2wins}

    def plot(self):
        evaluation = self.evaluate()
        results = [evaluation[value] for value in ['p1wins', 'ties', 'p2wins']]
        fig, ax = plt.subplots()
        rects = ax.bar(range(3), results, align='center')
        autolabel(rects, ax)

        plt.setp(ax, xticks=range(3),
                 xticklabels=['p1 wins', 'ties', 'p2 wins'])
        ax.set_title('Outcome')

        return fig


def generate_interface(ai):

    def play(hand):
        def func(button):
            result = ai.play_one(hand)
            if result == 0:
                text = u"<b style='background-color:yellow'>döntetlen</b>"
            elif result == -1:
                text = u"<b style='background-color:red'>vereség</b>"
            else:
                text = u"<b style='background-color:green'>győzelem</b>"
            result_box.value = text
        return func

    result_box = widgets.HTML(
        placeholder=u"<b style='background-color:grey'>Kő-papír-olló!</b>")

    rock_button = widgets.Button(description='ko')
    rock_button.on_click(play('k'))

    paper_button = widgets.Button(description='papir')
    paper_button.on_click(play('p'))

    scissors_button = widgets.Button(description='ollo')
    scissors_button.on_click(play('o'))

    button_container = widgets.HBox()
    button_container.children = [rock_button, paper_button, scissors_button]

    container = widgets.VBox()
    container.children = [button_container, result_box]

    return container
