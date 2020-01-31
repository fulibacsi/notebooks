# encoding: utf-8

import random
import sqlite3
from copy import deepcopy
from collections import Counter
from itertools import product

import pandas as pd
from sklearn.neural_network import MLPClassifier

import matplotlib.pyplot as plt
import seaborn as sns

from ipywidgets import widgets


def autolabel(rects, ax):
    """Append value labels to the top of the bar chart columns.

    Parameters:
    -----------
    rects : list of matplotlib figure elements
        The bar charts
    ax : matplotlib axis
        Axis containing the bars.

    Returns:
    --------
    None
    """
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
    """Plot frequencies from a dict containing frequencies.

    Parameters:
    -----------
    freqs : dict
        Frequency dict with the following format :
        {category: number_of_occurences}

    Returns:
    --------
    fig : matplotlib figure
        Figure containing the plot
    """
    fig, ax = plt.subplots()
    rects = ax.bar(range(len(freqs)), freqs.values(), align='center')
    autolabel(rects, ax)
    plt.xticks(range(len(freqs)), freqs.keys())
    return fig


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.

    Parameters:
    -----------
    *dict_args : tuple of dicts
        dicts to merge

    Returns:
    --------
    result : dict
        Merged dict
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


class RPS(object):
    """Rock-Paper-Scissors playing agent.

    Different agents are implemented to learn the player's playing pattern.
    Currently the following agents available:
    - null : pure random agent
    - naive : attempts to learn the opponents hand probability
    - stateful : attempts to learn the opponents state-transition probabilities
    - neural : multilayer perceptron based opponent with 3 layers:
        - the input layer accepts the played hands from the previous 5 game
          (both opponent's and the agent's).
        - the hidden layer contains 100 hidden neuron
        - the output layer contains 3 neuron, each represents the different
          hands

    Parameters:
    -----------
    mode : string
        Available modes are null, naive, stateful and neural
    seed : int or random.seed
        Initial random seed
    memsize : int
        Only available in stateful mode. The length of the states.
    """

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
        """Generate the states for the stateful agent."""
        keys = []
        for i in range(self.memsize):
            variations = [''.join(pair)
                          for pair in product('kpo', repeat=i + 1)]
            keys += variations
        return {key: ['k', 'p', 'o'] for key in keys}

    def reset(self):
        """Resets the agent."""
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
        """Returns a blank new instance from self."""
        return self.__class__(self.mode, self.seed)

    def copy(self):
        """Copies the current agent with the already set values."""
        return deepcopy(self)

    def play(self, player, plot=False):
        """Plays the game.

        Depending on the `player` parameter, which can be a string from
        {'k', 'p', 'o'} (roc[k], [p]aper, sciss[o]rs) or a sequence of such
        strings, one or more games are played.
        The results are either returned as a list of outcomes (-1 lose,
        0 tie, 1 win) or a matplotlib figure depending on the plot parameter.

        Parameters:
        -----------
        player : string or iterable of strings
            Player selected hand(s). Available hands are: roc[k], [p]aper,
            sciss[o]rs.
        plot : boolean
            Plot the results (available only if multiple games are played)
            or return them as a list.

        Returns:
        --------
        result : integer or dict or matplotlib figure
            The outcome of the game. Either integer (-1, 0, 1) or a list of
            ints or a plot of the results.
        """
        if len(player) == 1:
            return self.play_one(player)
        return self.play_multiple(player, plot)

    def play_one(self, player):
        """Plays one round of RPS game.

        Plays one round, logs the results and execute a learning step.

        Parameters:
        -----------
        player : string
            The selected hand. Available hands are: roc[k], [p]aper, sciss[o]rs

        Returns:
        --------
        result : integer
            The outcome (-1 lose, 0 tie, 1 win)
        """
        ai = self.beat[self.predict()]
        result = self.result(ai, player)

        self.log_game(ai, player, result)
        self.learn(ai, player)

        return result

    def play_multiple(self, player, plot=False):
        """Plays multiple RPS games.

        Parameters:
        -----------
        player : list of strings
            List of strings {'k', 'p', 'o'} (roc[k], [p]aper, sciss[o]rs)
        plot : boolean
            Set the result type.

        Returns:
        --------
        result : list of strings or matplotlib figure
            The result in list or in plot format
        """
        results = [self.play_one(p) for p in player]
        return self.plot_win_ratio() if plot else results

    def result(self, ai, player):
        """Decide the outcome of a game.

        Parameters:
        -----------
        ai : string
            First player's (agent) hand
        player : string
            Second player's (opponent) hand

        Returns:
        --------
        outcome : integer
            The outcome (-1 lose, 0 tie, 1 win)
        """
        if ai == player:
            return 0
        return 1 if self.beat[ai] == player else -1

    def random(self):
        """Returns a random hand.

        Parameters:
        -----------
        None

        Returns:
        --------
        hand : string
            The selected hand {'k', 'p', 'o'} (roc[k], [p]aper, sciss[o]rs)
        """
        return random.choice(['k', 'p', 'o'])

    def predict(self):
        """Make a prediction based on the learner agent's currnt model.

        Makes a prediction based on the selected mode:
        - null: uniform random hand
        - naive: weighted random hand (starts from uniform)
        - stateful: weighted random. weights comes from state-transition probs
        - neural: MLP based prediction
        If no model is initialized yet, retuns a random choice.

        Parameters:
        -----------
        None

        Returns:
        --------
        prediction : string
            Predicted hand for the opponent.
        """
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
        """Transforms historical hand data into a concatenated vector.

        Required for the neural agent.

        Parameters:
        -----------
        None

        Returns:
        --------
        X : list of ints
            The flattened encoded hand vectors from the previous 5 games.
        """
        ai = [self.transform_map[hand] for hand in self.state['ai']]
        player = [self.transform_map[hand] for hand in self.state['player']]
        X = [sum(ai + player, [])]
        return X

    def update_state(self, ai, player):
        """Set the agent state.

        In stateful mode the state is a memsize length sequence of the previous
        opponent hands.
        In neural mode the state is the agent's and the opponent's previous 5
        hands.

        Parameters:
        -----------
        ai : string
            agent's most recent played hand
        player : string
            opponent's most recent played hand

        Returns:
        --------
        state : list or dict
            Updated state
        """
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
        """Executes one learning step.

        In naive mode the opponent's played hand is added to the pool of hands.
        In stateful mode, the pool associated to the current state is extended
        by the opponent's current hand. The new state is also set.
        In neural mode, vectorize the current state (game history) and then
        execute one backpropagation learning step.

        Parameters:
        -----------
        ai : string
            Agent's hand
        player : string
            Opponent's hand

        Returns:
        --------
        None
        """
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
        """Add current turn's data to the game log.

        Stores the agent's and opponent's selected hands, the outcome, and the
        current transition probabilities where available.

        Parameters:
        -----------
        ai : string
            Agent's hand
        player : string
            Opponent's hand
        result : integer
            The outcome of the current round

        Returns:
        --------
        None
        """
        log = {'ai': ai,
               'player': player,
               'result': result}
        log = merge_dicts(log, self.generate_probs())
        self.game_log.append(log)

    def generate_probs(self):
        """Generate probabilities from the agent's pool.

        Parameters:
        -----------
        None

        Returns:
        --------
        probabilities : dict
            Probability of each hand from each state (where states available)
        """
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
        """Generate game stats from the previously played games.

        Stats includes wins, ties, losses and agent's score.

        Parameters:
        -----------
        None

        Returns:
        --------
        stats : tuple of pandas dataframes
            stat and probability dataframes"""
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
        """Plot hand probabilities.

        Parameters:
        -----------
        None

        Returns:
        --------
        fig : matplotlib figure
            Figure containing the barplots for each hand in each state.
        """
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
        """Plot winning ratio.

        Parameters:
        -----------
        None

        Returns:
        --------
        fig : matplotlib figure
            Figure containing the barplots for wins, ties and losses
        """
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
    """Simulate multiple rounds of rock-paper-scissors game between artificial
    agents.

    Parameters:
    -----------
    p1 : RPS object
        Artificial rps agent.
    p2 : RPS object
        Artificial rps agent.
    rounds : int
        Number of rounds to simulate
    p1static : boolean
        If p1 agent should learn or stay static (default: False)
    p2static : boolean
        If p1 agent should learn or stay static (default: False)
    """

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
        """Reset rps agents to their initial state."""
        self.p1 = self.orig_p1.copy()
        self.p2 = self.orig_p2.copy()
        self.game_log = []

    def play(self, plot=False):
        """Simulate rps rounds.

        Parameters:
        -----------
        plot : boolean
            Whether plot the results or returns as a dict.

        Returns:
        --------
        results : dict or fig
            game stats or plot of stats"""
        for game in range(self.rounds):
            self.play_one()
        return self.plot() if plot else self.evaluate()

    def play_one(self):
        """Simulate one round of RPS.

        Both agent's selects their hands than the result is decided and the
        round is logged. Learning steps are executed for the non-static agents.
        """
        p1hand = self.beat[self.p1.predict()]
        p2hand = self.beat[self.p2.predict()]

        result = self.result(p1hand, p2hand)
        self.log(p1hand, p2hand, result)

        if not self.p1static:
            self.p1.learn(p1hand, p2hand)
        if not self.p2static:
            self.p2.learn(p2hand, p1hand)

    def result(self, p1, p2):
        """Computes a round's outcome.

        Parameters:
        -----------
        p1 : string
            Selected hand by p1
        p2 : string
            Selected hand by p2

        Returns:
        --------
        result : string
            Either 'p1', 'p2' or 'tie"""
        if p1 == p2:
            return 'tie'
        if self.beat[p1] == p2:
            return 'p2'
        return 'p1'

    def log(self, p1, p2, result):
        """Log round results.

        Parameters:
        -----------
        p1 : string
            Selected hand by p1
        p2 : string
            Selected hand by p2
        result : string
            Result of the round

        Returns:
        --------
        None
        """
        self.game_log.append({'p1': p1,
                              'p2': p2,
                              'result': result})

    def evaluate(self):
        """Evaluate the played rounds.

        Compute agents' wins, scores, ties and number of ties.

        Parameters:
        -----------
        None

        Returns:
        --------
        stats : dict
            The computed statistics.
        """
        p1wins = sum([game['result'] == 'p1' for game in self.game_log])
        p2wins = sum([game['result'] == 'p2' for game in self.game_log])

        return {'p1wins': p1wins,
                'p2wins': p2wins,
                'p1score': p1wins - p2wins,
                'p2score': p2wins - p1wins,
                'games': len(self.game_log),
                'ties': len(self.game_log) - p1wins - p2wins}

    def plot(self):
        """Evaluate and plot the results of the played rounds.

        Parameters:
        -----------
        None

        Returns:
        --------
        fig : matplotlib figure
            Figure containing the p1wins, p2wins and ties as barcharts.
        """
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
    """Generate an interactive interface on a jupyter notebook to play against
    an agent.

    Parameters:
    -----------
    ai : RPS object
        Artificial rps agent.

    Returns:
    --------
    widget : Jupyter Notebook Widget
        Widget containing the interface.
    """

    def play(hand):
        def func(button):
            result = ai.play_one(hand)
            text = u"<br/><h1 style='background-color:{}'>{}</b>"
            if result == 0:
                text = text.format(u'yellow', u'döntetlen')
            elif result == -1:
                text = text.format(u'red', u'vereség')
            else:
                text = text.format(u'green', u'győzelem')
            result_box.value = text

            pics = {'k': u"<img src='pics/rock.gif' align='left'/>",
                    'p': u"<img src='pics/paper.gif' align='left'/>",
                    'o': u"<img src='pics/scissors.gif' align='left'/>"}
            ai_hand.value = (u'<center><b>AI:</b></center><br/>' +
                             pics[ai.game_log[-1]['ai']])
            player_hand.value = (u'<center><b>Ön:</b></center><br/>' +
                                 pics[hand])
        return func

    ai_hand = widgets.HTML()
    player_hand = widgets.HTML()
    result_box = widgets.HTML()

    result_container = widgets.HBox()
    result_container.children = [ai_hand, result_box, player_hand]

    rock_button = widgets.Button(description='ko')
    rock_button.on_click(play('k'))

    paper_button = widgets.Button(description='papir')
    paper_button.on_click(play('p'))

    scissors_button = widgets.Button(description='ollo')
    scissors_button.on_click(play('o'))

    button_container = widgets.HBox()
    button_container.children = [rock_button, paper_button, scissors_button]

    container = widgets.VBox()
    container.children = [button_container, result_container]

    return container


def get_results():
    db = sqlite3.connect('./data/results.db')
    results = pd.read_sql('select * from results', con=db)
    return results


def plot_wins(df):
    return plot_freqs(df.groupby('result').user.count().to_dict())


def plot_favourite_hand(df):
    return plot_freqs(df.groupby('user').result.count().to_dict())


def plot_area_by_turn(df, column='user'):
    fig, ax = plt.subplots()
    result = (df
              .groupby(['turn', column], as_index=False).count()
              .pivot('turn', column, 'ai')
              .fillna(0.)
              .plot.area(stacked=True, ax=ax))
    return fig
