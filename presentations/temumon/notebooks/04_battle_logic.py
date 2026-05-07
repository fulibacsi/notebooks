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
def _init_combatant(monster: Dict) -> Dict:
    """Prepare a battle copy of a monster with HP tracking fields."""
    hp = int(monster.get('hp', 0) or 0)
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

    a_spd = int(a.get('spd', 0) or 0)
    b_spd = int(b.get('spd', 0) or 0)
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
    # Use ai_query to call the LLM endpoint
    return spark.sql(f"""
        SELECT ai_query(
            'databricks-meta-llama-3-3-70b-instruct',
            {repr(prompt)}
        ) AS narrative
    """).collect()[0]['narrative']

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
narrative = narrate_battle(battle_result)

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