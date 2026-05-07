"""Battle logic for Monster Battle Cards.

Implements turn-based combat system with battle history and LLM-powered narration.
"""
from typing import Dict, List, Tuple
import random

import pandas as pd

from utils import sqlQuery


# Type advantage mapping (for reference - actual combat uses the weakness field)
TYPE_ADVANTAGE = {
    "Fire": "Ice",
    "Ice": "Earth",
    "Earth": "Storm",
    "Storm": "Shadow",
    "Shadow": "Light",
    "Light": "Void",
    "Void": "Poison",
    "Poison": "Fire"
}


def calculate_damage(attacker: Dict, defender: Dict) -> int:
    """Calculate damage for one attack.
    
    Formula: damage = (ATK * dmg_bonus) - DEF
    - dmg_bonus = 1.5 if attacker's type matches defender's weakness, else 1.0
    - Minimum damage is 1
    
    Args:
        attacker: Attacking monster's stats
        defender: Defending monster's stats
        
    Returns:
        Damage amount (minimum 1)
    """
    atk = attacker.get('atk')
    atk = 0 if pd.isna(atk) else int(atk)
    
    def_stat = defender.get('def')
    def_stat = 0 if pd.isna(def_stat) else int(def_stat)
    
    # Type advantage: check if attacker's type matches defender's weakness
    dmg_bonus = 1.0
    attacker_type = attacker.get('type')
    defender_weakness = defender.get('weakness')
    
    if attacker_type and defender_weakness and attacker_type == defender_weakness:
        dmg_bonus = 1.5
    
    damage = int(atk * dmg_bonus - def_stat)
    return max(1, damage)  # Minimum 1 damage


def battle(monster_a: Dict, monster_b: Dict) -> Dict:
    """Simulate a turn-based battle between two monsters.
    
    Combat rules:
    - Faster monster attacks first (random on tie)
    - Each turn, both monsters attack (unless first attacker KOs defender)
    - Battle continues until one monster reaches 0 HP
    - Score = % HP remaining for winner
    
    Args:
        monster_a: First monster's stats
        monster_b: Second monster's stats
        
    Returns:
        Dict with keys:
        - winner: Dict of winning monster (includes original stats)
        - loser: Dict of losing monster
        - score: float (percentage HP remaining for winner, 0-100)
        - history: list of round dicts with battle events
    """
    # Create battle copies with current HP tracking
    a = {**monster_a}
    b = {**monster_b}
    
    # Initialize current HP (handle NaN)
    a_max_hp = a.get('hp')
    a_max_hp = 0 if pd.isna(a_max_hp) else int(a_max_hp)
    a['current_hp'] = a_max_hp
    a['max_hp'] = a_max_hp
    
    b_max_hp = b.get('hp')
    b_max_hp = 0 if pd.isna(b_max_hp) else int(b_max_hp)
    b['current_hp'] = b_max_hp
    b['max_hp'] = b_max_hp
    
    # Determine turn order based on speed
    a_spd = a.get('spd')
    a_spd = 0 if pd.isna(a_spd) else int(a_spd)
    
    b_spd = b.get('spd')
    b_spd = 0 if pd.isna(b_spd) else int(b_spd)
    
    if a_spd > b_spd:
        first, second = a, b
    elif b_spd > a_spd:
        first, second = b, a
    else:
        # Random on tie
        if random.random() < 0.5:
            first, second = a, b
        else:
            first, second = b, a
    
    history = []
    round_num = 0
    max_rounds = 100  # Safety limit to prevent infinite loops
    
    while first['current_hp'] > 0 and second['current_hp'] > 0 and round_num < max_rounds:
        round_num += 1
        round_events = []
        
        # First attacker attacks
        dmg = calculate_damage(first, second)
        second['current_hp'] -= dmg
        
        round_events.append({
            'attacker': first.get('name', 'Unknown'),
            'defender': second.get('name', 'Unknown'),
            'damage': dmg,
            'defender_hp_after': max(0, second['current_hp']),
            'defender_max_hp': second['max_hp']
        })
        
        # If second is still alive, they counter-attack
        if second['current_hp'] > 0:
            dmg = calculate_damage(second, first)
            first['current_hp'] -= dmg
            
            round_events.append({
                'attacker': second.get('name', 'Unknown'),
                'defender': first.get('name', 'Unknown'),
                'damage': dmg,
                'defender_hp_after': max(0, first['current_hp']),
                'defender_max_hp': first['max_hp']
            })
        
        history.append({
            'round': round_num,
            'events': round_events
        })
    
    # Determine winner and calculate score
    if first['current_hp'] > 0:
        winner = first
        loser = second
        score = (first['current_hp'] / first['max_hp']) * 100 if first['max_hp'] > 0 else 0
    else:
        winner = second
        loser = first
        score = (second['current_hp'] / second['max_hp']) * 100 if second['max_hp'] > 0 else 0
    
    return {
        'winner': winner,
        'loser': loser,
        'score': score,
        'history': history,
        'total_rounds': round_num
    }


def find_winner(challenger: Dict, roster: List[Dict]) -> Tuple[Dict, Dict]:
    """Battle challenger against all roster monsters and find the best opponent.
    
    The "best opponent" is the roster monster that performed best:
    - If any roster monster wins, pick the one with highest remaining HP%
    - If challenger wins all battles, pick the roster monster that lasted longest
    
    Args:
        challenger: The uploaded monster's stats
        roster: List of all monsters from the database
        
    Returns:
        Tuple of (best_battle_result, best_opponent_from_roster)
    """
    best_result = None
    best_opponent = None
    best_performance = -1
    
    for monster in roster:
        result = battle(challenger, monster)
        
        # Calculate performance metric for this roster monster
        if result['winner'].get('name') == monster.get('name'):
            # Roster monster won - performance is their remaining HP%
            performance = result['score']
        else:
            # Challenger won - performance is how much HP% the roster monster took from challenger
            # (i.e., how close they came to winning)
            challenger_hp_lost = 100 - result['score']
            performance = challenger_hp_lost
        
        # Track the roster monster with best performance
        if best_result is None or performance > best_performance:
            best_performance = performance
            best_result = result
            best_opponent = monster
    
    return best_result, best_opponent


def format_battle_history(history: List[Dict]) -> str:
    """Format battle history into a readable string for the LLM prompt.
    
    Args:
        history: List of round dicts from battle simulation
        
    Returns:
        Formatted string describing the battle progression
    """
    lines = []
    for round_info in history:
        round_num = round_info['round']
        lines.append(f"Round {round_num}:")
        
        for event in round_info['events']:
            hp_pct = (event['defender_hp_after'] / event['defender_max_hp'] * 100) if event['defender_max_hp'] > 0 else 0
            lines.append(f"  - {event['attacker']} attacked {event['defender']} for {event['damage']} damage "
                        f"({event['defender']}: {event['defender_hp_after']}/{event['defender_max_hp']} HP, {hp_pct:.0f}%)")
    
    return "\n".join(lines)


def narrate_battle(challenger: Dict, battle_result: Dict) -> str:
    """Generate a dramatic battle narrative using LLM.
    
    Args:
        challenger: The uploaded monster's stats
        battle_result: The battle result dict (includes winner, loser, history, score)
        
    Returns:
        A 3-4 sentence dramatic battle narrative
    """
    winner = battle_result['winner']
    loser = battle_result['loser']
    history_text = format_battle_history(battle_result['history'])
    total_rounds = battle_result['total_rounds']
    final_hp_pct = battle_result['score']
    
    # Determine if challenger won or lost
    challenger_won = (challenger.get('name') == winner.get('name'))
    
    if challenger_won:
        prompt = f"""You are narrating an epic monster battle. Write a dramatic 3-4 sentence narrative about how the challenger triumphed. Reference specific stats and battle events naturally (e.g., "With 87 DEF, {challenger['name']} shrugged off the attack...").

CHALLENGER (WINNER): {challenger['name']}
- Type: {challenger['type']}
- ATK: {challenger['atk']}, DEF: {challenger['def']}, SPD: {challenger['spd']}, HP: {challenger['hp']}
- Lore: {challenger.get('lore', '')}
- Final HP: {final_hp_pct:.0f}% remaining after {total_rounds} rounds

OPPONENT: {loser['name']}
- Type: {loser['type']}
- ATK: {loser['atk']}, DEF: {loser['def']}, SPD: {loser['spd']}, HP: {loser['hp']}
- Lore: {loser.get('lore', '')}

BATTLE PROGRESSION:
{history_text}

The challenger {challenger['name']} proved victorious! Narrate their triumph, reference specific stats or battle moments, keep it under 100 words, and make it feel organic. Do not reveal the damage formula."""
    else:
        prompt = f"""You are narrating an epic monster battle. Write a dramatic 3-4 sentence narrative about this battle. Reference specific stats and battle events naturally (e.g., "With 87 DEF, Glacius shrugged off the attack...").

WINNER: {winner['name']}
- Type: {winner['type']}
- ATK: {winner['atk']}, DEF: {winner['def']}, SPD: {winner['spd']}, HP: {winner['hp']}
- Lore: {winner.get('lore', '')}
- Final HP: {final_hp_pct:.0f}% remaining after {total_rounds} rounds

CHALLENGER: {challenger['name']}
- Type: {challenger['type']}
- ATK: {challenger['atk']}, DEF: {challenger['def']}, SPD: {challenger['spd']}, HP: {challenger['hp']}
- Lore: {challenger.get('lore', '')}

BATTLE PROGRESSION:
{history_text}

The winner is {winner['name']}. Narrate the battle, reference specific stats or battle moments, keep it under 100 words, and make it feel organic. Do not reveal the damage formula."""
    
    sql_query = f"""
        SELECT ai_query(
            'databricks-meta-llama-3-3-70b-instruct',
            {repr(prompt)}
        ) AS narrative
    """
    
    result_df = sqlQuery(sql_query)
    return result_df.iloc[0]['narrative']
