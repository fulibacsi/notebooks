# Databricks notebook source
# DBTITLE 1,Student Exercise: Extract Your Own Monster
# MAGIC %md
# MAGIC # Student Exercise: Extract Your Own Monster
# MAGIC
# MAGIC You've learned how to use Databricks AI functions in notebooks 02 and 03. Now it's your turn to apply them!
# MAGIC
# MAGIC **Your mission:**
# MAGIC 1. Pick one monster PDF from the volume
# MAGIC 2. Use `ai_parse_document()` to extract raw text
# MAGIC 3. Use `ai_extract()` to parse structured stats
# MAGIC 4. Battle your monster against the roster!
# MAGIC
# MAGIC **What you'll practice:**
# MAGIC * Reading files from Unity Catalog Volumes
# MAGIC * Calling `ai_parse_document()` via PySpark
# MAGIC * Calling `ai_extract()` with field names
# MAGIC * Converting between Spark DataFrames and Python dicts
# MAGIC
# MAGIC Let's get started!

# COMMAND ----------

# DBTITLE 1,Setup: Import libraries and set schema
from pyspark.sql import functions as F
import random

# Set the current catalog and schema
spark.catalog.setCurrentCatalog("workspace")
spark.catalog.setCurrentDatabase("monsters")

print("✓ Using workspace.monsters schema")

# COMMAND ----------

# DBTITLE 1,Step 1: Pick a random monster PDF
# Volume path where PDFs are stored
volume_path = "/Volumes/workspace/monsters/dropzone/raw_pdfs/"

# Read all PDFs from volume
files_df = (
    spark.read
    .format("binaryFile")
    .load(volume_path)
    .filter(F.col("_metadata.file_name").like("%.pdf"))
)

# Pick one random file
all_files = files_df.collect()
if len(all_files) == 0:
    raise Exception("No PDF files found in volume! Run 00_setup and generate_monsters.py first.")

random_file = random.choice(all_files)
selected_filename = random_file._metadata.file_name
selected_content = random_file.content

print(f"🎲 Randomly selected: {selected_filename}")
print(f"File size: {len(selected_content)} bytes")

# COMMAND ----------

# DBTITLE 1,Exercise Part 1: Extract Raw Text
# MAGIC %md
# MAGIC ## 📝 TODO: Extract raw text with ai_parse_document()
# MAGIC
# MAGIC In notebook 02, you learned how to use `ai_parse_document()` to extract text from PDFs.
# MAGIC
# MAGIC **Your task:**
# MAGIC 1. Create a DataFrame with the selected file's content
# MAGIC 2. Use `F.expr()` to call `ai_parse_document(content, map('version', '2.0'))`
# MAGIC 3. Extract the `raw_text` result
# MAGIC 4. Store it in a variable called `raw_text`
# MAGIC
# MAGIC **Hint**: Review notebook 02, cell 5 for the pattern. You'll need:
# MAGIC - `.select()` to add a column with the AI function call
# MAGIC - `.collect()[0]` to get the first row
# MAGIC - Access the column to get the raw text string

# COMMAND ----------

# DBTITLE 1,TODO: Your code here (Part 1)
# TODO: Extract raw text from selected_content using ai_parse_document()
# Store the result in a variable called: raw_text

# Hint: Create a DataFrame with the content, call ai_parse_document via F.expr(), collect the result

# Your code here:
raw_text = None  # Replace this!

# Verification (don't change this)
if raw_text is None:
    print("⚠️ You need to extract the raw text first!")
else:
    print(f"✓ Raw text extracted! Length: {len(raw_text)} characters")
    print(f"\nFirst 200 characters:\n{raw_text[:200]}...")

# COMMAND ----------

# DBTITLE 1,Exercise Part 2: Extract Structured Stats
# MAGIC %md
# MAGIC    
# MAGIC ## 📝 TODO: Extract structured stats with ai_extract()
# MAGIC
# MAGIC In notebook 03, you learned how to use `ai_extract()` to parse structured data from raw text.
# MAGIC
# MAGIC **Your task:**
# MAGIC 1. Call `ai_extract()` with the raw_text, a JSON string of field names, and options
# MAGIC 2. Parse the VARIANT response and extract the fields
# MAGIC 3. Convert to a Python dict with all 8 fields
# MAGIC 4. Store it in a variable called `monster_stats`
# MAGIC
# MAGIC **Hint**: Review notebook 03, cell 6 for the extraction pattern.
# MAGIC
# MAGIC **Remember**: `ai_extract()` signature is:
# MAGIC ```python
# MAGIC ai_extract(
# MAGIC     CAST(raw_text AS STRING),
# MAGIC     '["name", "lore", "type", "weakness", "atk", "def", "spd", "hp"]',
# MAGIC     map('instructions', 'Extract monster stats from this trading card...')
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC **Important**: The response is a VARIANT with nested structure. Access fields using:
# MAGIC ```python
# MAGIC parsed_json:response:name:value
# MAGIC parsed_json:response:atk:value
# MAGIC # etc.
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,TODO: Define the field list
# TODO: Define the list of fields to extract
# For ai_extract(), you'll pass these as a JSON string: '["field1", "field2", ...]'
# You need all 8 fields: name, lore, type, weakness, atk, def, spd, hp

fields = ['name', 'lore', 'type', 'weakness', 'atk', 'def', 'spd', 'hp']

print(f"Fields to extract: {', '.join(fields)}")
print(f"\nAs JSON string: {str(fields).replace("'", '\"')}")
print("\nYou'll use this JSON format in the ai_extract() call.")

# COMMAND ----------

# DBTITLE 1,TODO: Your code here (Part 2)
# TODO: Extract structured stats from raw_text using ai_extract()
# Store the result as a dict in: monster_stats

# Hint: 
# 1. Create a DataFrame with the raw_text: spark.createDataFrame([(raw_text,)], ['text'])
# 2. Use F.expr() to call ai_extract with JSON string schema:
#    ai_extract(
#        CAST(text AS STRING),
#        '["name", "lore", "type", "weakness", "atk", "def", "spd", "hp"]',
#        map('instructions', 'Extract monster stats...')
#    )
# 3. Access VARIANT fields using : operator and :value suffix:
#    F.expr("parsed_json:response:name:value").cast("string").alias("name")
#    F.expr("parsed_json:response:atk:value").cast("int").alias("atk")
# 4. Collect and convert to dict with .asDict()

# Your code here:
monster_stats = None  # Replace this!

# Verification (don't change this)
if monster_stats is None:
    print("⚠️ You need to extract the monster stats first!")
else:
    required_fields = ['name', 'lore', 'type', 'weakness', 'atk', 'def', 'spd', 'hp']
    missing = [f for f in required_fields if f not in monster_stats or monster_stats[f] is None]
    
    if missing:
        print(f"⚠️ Missing or null fields: {', '.join(missing)}")
    else:
        print(f"✓ Monster stats extracted successfully!")
        print(f"\n{monster_stats['name']} ({monster_stats['type']})")
        print(f"  ATK: {monster_stats['atk']}, DEF: {monster_stats['def']}, SPD: {monster_stats['spd']}, HP: {monster_stats['hp']}")
        print(f"  Weakness: {monster_stats['weakness']}")
        print(f"\nLore: {monster_stats['lore'][:100]}...")

# COMMAND ----------

# DBTITLE 1,Bonus: Battle Your Monster!
# MAGIC %md
# MAGIC ## 🎯 Bonus Challenge: Battle Your Extracted Monster
# MAGIC
# MAGIC Now that you've extracted your monster's stats, let's see how it performs in battle!
# MAGIC
# MAGIC We'll:
# MAGIC 1. Load the battle functions from notebook 04
# MAGIC 2. Load the full monster roster from the database
# MAGIC 3. Find your monster's best opponent
# MAGIC 4. Generate a battle narrative
# MAGIC
# MAGIC This demonstrates how all the pieces connect: PDF → text → stats → battle!

# COMMAND ----------

# DBTITLE 1,Load battle functions from notebook 04
# Import battle logic from notebook 04
# (In a real workshop, you'd %run notebook 04 or copy these functions)

from typing import Dict, List, Tuple
import random

# Type advantage mapping
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
    """Calculate damage for one attack."""
    atk = int(attacker.get('atk', 0) or 0)
    def_stat = int(defender.get('def', 0) or 0)
    
    dmg_bonus = 1.0
    attacker_type = attacker.get('type')
    defender_weakness = defender.get('weakness')
    
    if attacker_type and defender_weakness and attacker_type == defender_weakness:
        dmg_bonus = 1.5
    
    damage = int(atk * dmg_bonus - def_stat)
    return max(1, damage)

def battle(monster_a: Dict, monster_b: Dict) -> Dict:
    """Simulate a turn-based battle."""
    a = {**monster_a}
    b = {**monster_b}
    
    a_max_hp = int(a.get('hp', 0) or 0)
    a['current_hp'] = a_max_hp
    a['max_hp'] = a_max_hp
    
    b_max_hp = int(b.get('hp', 0) or 0)
    b['current_hp'] = b_max_hp
    b['max_hp'] = b_max_hp
    
    a_spd = int(a.get('spd', 0) or 0)
    b_spd = int(b.get('spd', 0) or 0)
    
    if a_spd > b_spd:
        first, second = a, b
    elif b_spd > a_spd:
        first, second = b, a
    else:
        if random.random() < 0.5:
            first, second = a, b
        else:
            first, second = b, a
    
    history = []
    round_num = 0
    max_rounds = 100
    
    while first['current_hp'] > 0 and second['current_hp'] > 0 and round_num < max_rounds:
        round_num += 1
        round_events = []
        
        dmg = calculate_damage(first, second)
        second['current_hp'] -= dmg
        
        round_events.append({
            'attacker': first.get('name', 'Unknown'),
            'defender': second.get('name', 'Unknown'),
            'damage': dmg,
            'defender_hp_after': max(0, second['current_hp']),
            'defender_max_hp': second['max_hp']
        })
        
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
    """Find the best opponent from the roster."""
    best_result = None
    best_opponent = None
    best_performance = -1
    
    for monster in roster:
        result = battle(challenger, monster)
        
        if result['winner'].get('name') == monster.get('name'):
            performance = result['score']
        else:
            challenger_hp_lost = 100 - result['score']
            performance = challenger_hp_lost
        
        if best_result is None or performance > best_performance:
            best_performance = performance
            best_result = result
            best_opponent = monster
    
    return best_result, best_opponent

print("✓ Battle functions loaded")

# COMMAND ----------

# DBTITLE 1,Run the battle (only if you completed Part 2)
# Only run this if you successfully extracted monster_stats!

if monster_stats is None:
    print("⚠️ Complete Part 2 first to extract your monster's stats!")
else:
    # Load the full roster from the database
    roster_df = spark.table("workspace.monsters.stats")
    roster = [row.asDict() for row in roster_df.collect()]
    
    print(f"Loaded {len(roster)} monsters from the roster")
    print(f"\nYour challenger: {monster_stats['name']} ({monster_stats['type']})")
    print(f"  ATK: {monster_stats['atk']}, DEF: {monster_stats['def']}, SPD: {monster_stats['spd']}, HP: {monster_stats['hp']}")
    print(f"\nFinding the best opponent...\n")
    
    # Find the best battle
    battle_result, best_opponent = find_winner(monster_stats, roster)
    
    winner = battle_result['winner']
    loser = battle_result['loser']
    
    print(f"🏆 Winner: {winner['name']} ({winner['type']})")
    print(f"  Final HP: {battle_result['score']:.0f}% after {battle_result['total_rounds']} rounds")
    print(f"\n📜 Battle Summary:")
    print(f"  {monster_stats['name']} vs {best_opponent['name']}")
    
    if winner['name'] == monster_stats['name']:
        print(f"\n🎉 Your monster won! Congrats!")
    else:
        print(f"\n💀 Your monster was defeated by {winner['name']}")
    
    print(f"\nBattle lasted {battle_result['total_rounds']} rounds")
    print(f"First 3 rounds:")
    for round_info in battle_result['history'][:3]:
        print(f"\n  Round {round_info['round']}:")
        for event in round_info['events']:
            hp_pct = (event['defender_hp_after'] / event['defender_max_hp'] * 100) if event['defender_max_hp'] > 0 else 0
            print(f"    {event['attacker']} → {event['defender']}: {event['damage']} damage ({event['defender_hp_after']}/{event['defender_max_hp']} HP)")

# COMMAND ----------

# DBTITLE 1,Exercise Complete!
# MAGIC %md
# MAGIC ## ✅ Exercise Complete!
# MAGIC
# MAGIC **What you learned:**
# MAGIC 1. How to read binary files from Unity Catalog Volumes
# MAGIC 2. How to use `ai_parse_document()` to extract text from PDFs
# MAGIC 3. How to use `ai_extract()` to parse structured data with a JSON schema
# MAGIC 4. How to connect the data pipeline to the battle system
# MAGIC
# MAGIC **Key takeaways:**
# MAGIC - `ai_parse_document()` handles unstructured text extraction (OCR, layout understanding)
# MAGIC - `ai_extract()` handles structured parsing (turning text into typed fields)
# MAGIC - The battle engine is deterministic — LLMs only narrate, they don't decide outcomes
# MAGIC - All pieces connect: Volume → PDF → Text → Stats → Battle → App
# MAGIC
# MAGIC **Next steps:**
# MAGIC - Check out the complete Streamlit app: `app/temumon.py`
# MAGIC - Try the bonus: create your own custom monster!
# MAGIC - Explore how the app uses these same functions in production