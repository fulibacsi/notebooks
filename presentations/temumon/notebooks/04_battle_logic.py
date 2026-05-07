# Databricks notebook source
# DBTITLE 1,Battle Logic: Turn-Based Combat + LLM Narration
# MAGIC %md
# MAGIC This notebook implements the hybrid battle system:
# MAGIC * **Turn-based combat engine** → simulates rounds of combat with speed-based initiative
# MAGIC * **Battle history tracking** → records every attack and damage dealt
# MAGIC * **LLM narration** → generates a dramatic battle story based on actual combat events
# MAGIC
# MAGIC The LLM never decides who wins — it only tells the story of a battle whose outcome is already determined by the combat simulation.

# COMMAND ----------

# DBTITLE 1,Type Advantage System
# MAGIC %md
# MAGIC Type advantages follow a rock-paper-scissors pattern:
# MAGIC * Fire beats Ice
# MAGIC * Ice beats Earth
# MAGIC * Earth beats Storm
# MAGIC * Storm beats Shadow
# MAGIC * Shadow beats Light
# MAGIC * Light beats Void
# MAGIC * Void beats Poison
# MAGIC * Poison beats Fire
# MAGIC
# MAGIC **Important**: Each monster has a `weakness` field that specifies which type they're weak against. Type advantage is checked by comparing the attacker's type to the defender's weakness field.

# COMMAND ----------

# DBTITLE 1,Import dependencies and define TYPE_ADVANTAGE
from typing import Dict, List, Tuple
import random

# Type advantage mapping (for reference)
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

# COMMAND ----------

# DBTITLE 1,Damage Calculation
# MAGIC %md
# MAGIC The damage formula:
# MAGIC * Base damage = `ATK * type_bonus - opponent_DEF`
# MAGIC * Type bonus = `1.5x` if attacker's type matches defender's weakness, otherwise `1.0x`
# MAGIC * Minimum damage is always 1 (even if DEF > ATK)

# COMMAND ----------

# DBTITLE 1,Define calculate_damage function
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
    atk = int(attacker.get('atk', 0) or 0)
    def_stat = int(defender.get('def', 0) or 0)
    
    # Type advantage: check if attacker's type matches defender's weakness
    dmg_bonus = 1.0
    attacker_type = attacker.get('type')
    defender_weakness = defender.get('weakness')
    
    if attacker_type and defender_weakness and attacker_type == defender_weakness:
        dmg_bonus = 1.5
    
    damage = int(atk * dmg_bonus - def_stat)
    return max(1, damage)  # Minimum 1 damage

# COMMAND ----------

# DBTITLE 1,Turn-Based Battle Simulation
# MAGIC %md
# MAGIC Combat rules:
# MAGIC * Faster monster attacks first (random on speed tie)
# MAGIC * Each round, both monsters attack (unless first attacker KOs the defender)
# MAGIC * Battle continues until one monster reaches 0 HP
# MAGIC * Returns winner, loser, score (% HP remaining), and complete battle history

# COMMAND ----------

# DBTITLE 1,Define battle function
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
        - total_rounds: int (number of rounds fought)
    """
    # Create battle copies with current HP tracking
    a = {**monster_a}
    b = {**monster_b}
    
    # Initialize current HP
    a_max_hp = int(a.get('hp', 0) or 0)
    a['current_hp'] = a_max_hp
    a['max_hp'] = a_max_hp
    
    b_max_hp = int(b.get('hp', 0) or 0)
    b['current_hp'] = b_max_hp
    b['max_hp'] = b_max_hp
    
    # Determine turn order based on speed
    a_spd = int(a.get('spd', 0) or 0)
    b_spd = int(b.get('spd', 0) or 0)
    
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

# COMMAND ----------

# DBTITLE 1,Find Best Opponent
# MAGIC %md
# MAGIC Given a challenger and a roster, find the best performing opponent:
# MAGIC * If any roster monster wins, pick the one with highest remaining HP%
# MAGIC * If challenger wins all battles, pick the roster monster that dealt the most damage

# COMMAND ----------

# DBTITLE 1,Define find_winner function
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

# COMMAND ----------

# DBTITLE 1,Format Battle History
# MAGIC %md
# MAGIC Convert the battle history into a readable text format for the LLM prompt.

# COMMAND ----------

# DBTITLE 1,Define format_battle_history function
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

# COMMAND ----------

# DBTITLE 1,LLM Narration Function
# MAGIC %md
# MAGIC Uses Databricks AI functions to generate a dramatic battle narrative.
# MAGIC The LLM receives both stat cards AND the battle history, but doesn't decide the winner — it only narrates what happened.

# COMMAND ----------

# DBTITLE 1,Define narrate_battle function
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
    
    # Use ai_query to call the LLM endpoint
    result = spark.sql(f"""
        SELECT ai_query(
            'databricks-meta-llama-3-3-70b-instruct',
            {repr(prompt)}
        ) AS narrative
    """).collect()[0]['narrative']
    
    return result

# COMMAND ----------

# DBTITLE 1,Test Battle
# MAGIC %md
# MAGIC Let's run a real battle between two monsters from our stats table!

# COMMAND ----------

# DBTITLE 1,Load the monster roster
# Load the monster roster
roster_df = spark.table("workspace.monsters.stats")
roster = roster_df.collect()

# Convert to dictionaries
roster_dicts = [row.asDict() for row in roster]

print(f"Loaded {len(roster_dicts)} monsters from the stats table.")

# COMMAND ----------

# DBTITLE 1,Pick two monsters and find best opponent
# Pick two monsters for testing
challenger = roster_dicts[0]  # First monster in the roster
test_roster = roster_dicts[1:]  # All others

print(f"Challenger: {challenger['name']} ({challenger['type']})")
print(f"  ATK: {challenger['atk']}, DEF: {challenger['def']}, SPD: {challenger['spd']}, HP: {challenger['hp']}")
print(f"\nFinding the best opponent from {len(test_roster)} monsters...")

# COMMAND ----------

# DBTITLE 1,Run the battle and display winner
# Find the best opponent and get battle result
battle_result, best_opponent = find_winner(challenger, test_roster)

winner = battle_result['winner']
print(f"\n🏆 Winner: {winner['name']} ({winner['type']})")
print(f"  ATK: {winner['atk']}, DEF: {winner['def']}, SPD: {winner['spd']}, HP: {winner['hp']}")
print(f"  Final HP: {battle_result['score']:.0f}% after {battle_result['total_rounds']} rounds")

# COMMAND ----------

# DBTITLE 1,Display Battle History
# MAGIC %md
# MAGIC Let's see the round-by-round combat log!

# COMMAND ----------

# DBTITLE 1,Print battle history
print("📜 Battle History:\n")
for round_info in battle_result['history']:
    print(f"Round {round_info['round']}:")
    for event in round_info['events']:
        hp_pct = (event['defender_hp_after'] / event['defender_max_hp'] * 100) if event['defender_max_hp'] > 0 else 0
        print(f"  {event['attacker']} → {event['defender']}: {event['damage']} damage "
              f"({event['defender_hp_after']}/{event['defender_max_hp']} HP, {hp_pct:.0f}%)")

# COMMAND ----------

# DBTITLE 1,Generate Battle Narrative
# MAGIC %md
# MAGIC Now let's have the LLM narrate this battle based on the actual combat events!

# COMMAND ----------

# DBTITLE 1,Generate and display LLM narrative
narrative = narrate_battle(challenger, battle_result)

print(f"\n📖 Battle Narrative:\n")
print(narrative)

# COMMAND ----------

# DBTITLE 1,Battle System Complete
# MAGIC %md
# MAGIC ✅ **Battle system complete!**
# MAGIC
# MAGIC We've implemented:
# MAGIC * ✅ Turn-based combat simulation with speed-based initiative
# MAGIC * ✅ Damage formula with type advantage (1.5x multiplier)
# MAGIC * ✅ Battle history tracking (every attack, every round)
# MAGIC * ✅ Best opponent selection logic
# MAGIC * ✅ LLM-powered battle narration using actual combat events
# MAGIC
# MAGIC **Key insight**: The LLM never decides who wins — it only tells the story. The combat engine determines the outcome through deterministic rules, and the LLM narrates what actually happened. This is "hybrid AI" — combining deterministic simulation with generative storytelling.
# MAGIC
# MAGIC **Next**: Try the student exercise notebook to apply what you've learned, or check out the complete Streamlit app at `app/temumon.py`!