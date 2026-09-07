"""Battle logic for Monster Battle Cards.

Implements turn-based combat system with battle history and LLM-powered narration.
"""
from typing import Dict, List, Tuple
import random

import pandas as pd

from utils import sqlQuery



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


def _safe_int(value) -> int:
    """Cast a potentially NaN or None stat value to int."""
    return 0 if value is None or pd.isna(value) else int(value)


def _init_combatant(monster: Dict) -> Dict:
    """Prepare a battle copy of a monster with HP tracking fields."""
    hp = _safe_int(monster.get('hp'))
    return {**monster, 'current_hp': hp, 'max_hp': hp}


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
        - winner: Dict of winning monster
        - loser: Dict of losing monster
        - score: float (percentage HP remaining for winner, 0-100)
        - history: list of round dicts with battle events
        - total_rounds: int (number of rounds fought)
    """
    a, b = _init_combatant(monster_a), _init_combatant(monster_b)

    a_spd, b_spd = _safe_int(a.get('spd')), _safe_int(b.get('spd'))
    first, second = (a, b) if a_spd > b_spd else \
                    (b, a) if b_spd > a_spd else \
                    random.choice([(a, b), (b, a)])

    history = []
    round_num = 0

    while first['current_hp'] > 0 and second['current_hp'] > 0 and round_num < 100:
        round_num += 1
        events = []

        for attacker, defender in [(first, second), (second, first)]:
            if attacker['current_hp'] <= 0:
                break
            dmg = calculate_damage(attacker, defender)
            defender['current_hp'] -= dmg
            events.append({
                'attacker': attacker.get('name', 'Unknown'),
                'defender': defender.get('name', 'Unknown'),
                'damage': dmg,
                'defender_hp_after': max(0, defender['current_hp']),
                'defender_max_hp': defender['max_hp'],
            })

        history.append({'round': round_num, 'events': events})

    winner, loser = (first, second) if first['current_hp'] > 0 else (second, first)
    winner['current_hp'] = max(0, winner['current_hp'])
    score = (winner['current_hp'] / winner['max_hp']) * 100 if winner['max_hp'] > 0 else 0

    return {
        'winner': winner,
        'loser': loser,
        'winner_is_first_arg': winner is a,
        'score': score,
        'history': history,
        'total_rounds': round_num,
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
        if not result['winner_is_first_arg']:
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


def _build_prompt(
    winner: Dict,
    loser: Dict,
    challenger_won: bool,
    history_text: str,
    final_hp_pct: float,
    total_rounds: int,
) -> str:
    """Build the LLM narration prompt from battle participants and result."""
    winner_role = "WINNER (CHALLENGER)" if challenger_won else "WINNER"
    loser_role = "LOSER" if challenger_won else "LOSER (CHALLENGER)"
    outcome = (
        f"The challenger {winner['name']} proved victorious!"
        if challenger_won else
        f"The challenger {loser['name']} was defeated by {winner['name']}."
    )
    return f"""You are narrating an epic monster battle. Write a dramatic 3-4 sentence narrative about this battle. Reference specific stats and battle events naturally (e.g., "With 87 DEF, {winner['name']} shrugged off the attack...").

{winner_role}: {winner['name']}
- Type: {winner['type']}
- ATK: {winner['atk']}, DEF: {winner['def']}, SPD: {winner['spd']}, HP: {winner['hp']}
- Lore: {winner.get('lore', '')}
- Final HP: {final_hp_pct:.0f}% remaining after {total_rounds} rounds

{loser_role}: {loser['name']}
- Type: {loser['type']}
- ATK: {loser['atk']}, DEF: {loser['def']}, SPD: {loser['spd']}, HP: {loser['hp']}
- Lore: {loser.get('lore', '')}

BATTLE PROGRESSION:
{history_text}

{outcome} Narrate the battle, reference specific stats or battle moments, keep it under 100 words, and make it feel organic. Do not reveal the damage formula."""


def narrate_battle(battle_result: Dict) -> str:
    """Generate a dramatic battle narrative using LLM.

    Args:
        battle_result: The battle result dict (includes winner, loser, history, score)

    Returns:
        A 3-4 sentence dramatic battle narrative
    """
    winner = battle_result['winner']
    loser = battle_result['loser']
    challenger_won = battle_result['winner_is_first_arg']
    prompt = _build_prompt(
        winner=winner,
        loser=loser,
        challenger_won=challenger_won,
        history_text=format_battle_history(battle_result['history']),
        final_hp_pct=battle_result['score'],
        total_rounds=battle_result['total_rounds'],
    )
    sql_query = f"""
        SELECT ai_query(
            'databricks-meta-llama-3-3-70b-instruct',
            {repr(prompt)}
        ) AS narrative
    """
    return sqlQuery(sql_query).iloc[0]['narrative']
