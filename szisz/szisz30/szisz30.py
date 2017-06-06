import random
from collections import Counter

import matplotlib.pyplot as plt
import seaborn as sns


def plot_freqs(freqs):
    fig, ax = plt.subplots()
    ax.bar(range(len(freqs)), freqs.values(), align='center')
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
    
    win_map = {'k': 'p', 
               'p': 'o', 
               'o': 'k'}
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.choices = ['k', 'p', 'o']
        self.prev = None
        self.game_log = []
        
    def play(self, player):
        ai = random.choice(self.choices)
        player_won = self.win_map[ai] == player
        
        self.log_game(ai, player, player_won)
        
        # "LEARN"
        self.choices.append(self.win_map[player])
        self.prev = player # TODO: use this information for better prediction
        
        return player_won
    
    def log_game(self, ai, player, win):
        log = {'ai': ai, 
               'player': player, 
               'win': win}
        log = merge_dicts(log, self.generate_probs())
        self.game_log.append(log)
        
    def generate_probs(self):
        mem_length = float(len(self.choices))
        probs = dict(Counter(self.choices))
        return {'k': probs['k'] / mem_length,
                'p': probs['p'] / mem_length,
                'o': probs['o'] / mem_length}
        
    def stats(self):
        return {'Number of games': len(self.game_log),
                'Number of player wins': sum([game['win'] for game in self.game_log]),
                'Final probabilities': self.generate_probs()}
        
        
        
        