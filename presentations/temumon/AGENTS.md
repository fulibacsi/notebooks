# TemuMon — Workshop Project

## What this is

A 60-minute guided coding workshop for ~10 data science students (1st–5th year) using **Databricks Free Edition**. Students upload monster stat cards as PDFs to a Unity Catalog Volume, parse and extract structured stats using Databricks AI functions, implement a hybrid battle agent (rule engine + LLM narration), and deploy a Databricks App where any user can upload a new monster PDF and find out which existing monster defeats it.

There is no local development. Everything runs inside Databricks Free Edition notebooks and apps.

---

## Project structure

```
temumon/
├── AGENTS.md                          ← this file
├── README.md                          ← student-facing setup guide
│
├── data/
│   └── monsters.json                  ← source data for all 80 seed monsters
│
├── notebooks/
│   ├── 00_setup                       ← create catalog/schema/volume + generate PDFs
│   ├── 01_upload_check                ← LIST volume, verify uploads (PySpark)
│   ├── 02_parse_documents             ← ai_parse_document() on all PDFs (PySpark)
│   ├── 03_extract_stats               ← ai_extract() → structured Delta table (PySpark)
│   ├── 04_battle_logic                ← rule engine + LLM narration (Python)
│   ├── 05_student_exercise            ← guided exercise: extract your own monster
│   └── 06_deploy.py                   ← deploy job + Streamlit app
│
└── app/
    ├── app.yaml                       ← app configuration file for deployment
    ├── baseline_app.py                ← baseline streamlit app with sql and upload capabilities
    ├── battle.py                      ← implementation of the TemuMon fights
    ├── pdf_generator.py               ← monster generator script for the app
    ├── requirements.txt               ← python dependencies
    ├── temumon.py                     ← final Databricks App (Streamlit)
    └── utils.py                       ← utility functions for the app
```

**Key changes from original design:**
- PDF generation is now integrated into `00_setup.py` (cells 6-10) rather than being a separate script
- `monsters.json` location: `data/monsters.json` (moved from `data/seed_monsters/`)
- `generate_monsters.py` is obsolete but kept for reference

---

## TemuMon card schema

Every monster PDF contains exactly these fields. All notebooks and app code must treat this as the canonical schema.

```
NAME        string       — monster name, unique
LORE        string       — one-sentence flavour text
TYPE        string       — one of: Fire, Ice, Shadow, Storm, Earth, Poison, Light, Void
WEAKNESS    string       — one of the same TYPE values
ATK         integer      — 1–100
DEF         integer      — 1–100
SPD         integer      — 1–100
HP          integer      — 1–100
```

Type advantage table (deterministic layer of the battle engine):

```
Fire     beats  Ice
Ice      beats  Earth
Earth    beats  Storm
Storm    beats  Shadow
Shadow   beats  Light
Light    beats  Void
Void     beats  Poison
Poison   beats  Fire
```

If TYPE beats WEAKNESS, the attacker deals 1.5x damage in the battle formula. No advantage if types are neutral.

Battle format:
- Faster monster starts the round, in case of draw, randomly selected
- First monster attacks, damage formula:
  ```
  damage = ATK * type_bonus - opponent_DEF
  ```
- If second monster still alive, they attack
- Repeat until one of the monster faints
- Score is the percentage of the remaining life of the surviving monster

---

## Databricks environment conventions

- **Catalog**: `workspace` (created in `00_setup.py`)
- **Schema**: `monsters`
- **Volume path**: `/Volumes/workspace/monsters/dropzone/raw_pdfs`
- **Delta tables**:
  - `workspace.monsters.raw_text` — output of `ai_parse_document()`
  - `workspace.monsters.stats` — output of `ai_extract()`, one row per monster
- **Model Serving endpoint**: use `databricks-meta-llama-3-1-70b-instruct` (available in Free Edition) for all LLM calls
- All notebooks use PySpark DataFrame API, not SQL strings (except for AI function calls via `F.expr()`)

---

## Notebook specifications

### `00_setup.py`
Creates the catalog, schema, and volume. Must be idempotent (`CREATE IF NOT EXISTS` everywhere). **Now includes PDF generation (cells 6-10):**

**Cells 1-5:** Standard setup (catalog, schema, volume creation)
**Cells 6-10:** PDF generation
- Cell 6: Markdown intro for PDF generation
- Cell 7: Install reportlab (`%pip install reportlab --quiet`)
- Cell 8: Define helper functions (slugify, draw_ascii_monster, draw_stat_block_*, generate_card)
- Cell 9: Cleanup existing PDFs
- Cell 10: Generate all 80 PDFs from `data/monsters.json`
- Cell 11+: Volume verification and next steps

**Key pattern:** Reads from `/Workspace/Users/{current_user}/temumon/data/monsters.json` and writes PDFs to volume.

### `01_upload_check.py`
Lists all files in the volume using PySpark DataFrame API. Shows file count, names, sizes. Students run this after notebook 00 to confirm all 80 PDFs were generated. Include a simple count assertion.

### `02_parse_documents.py`
Reads all PDF files from the volume using `ai_parse_document()` via PySpark DataFrame API. Writes raw extracted text + filename + parse timestamp to `workspace.monsters.raw_text`. Uses `CREATE OR REPLACE TABLE` so it's safe to re-run. Show a preview of 3 rows at the end.

Key pattern implemented:
```python
parsed_df = (
    spark.read
    .format("binaryFile")
    .load(volume_path)
    .select(
        F.col("_metadata.file_name").alias("source_file"),
        F.expr("ai_parse_document(content, map('version', '2.0'))").alias("raw_text")
    )
)
```

### `03_extract_stats.py`
Reads from `raw_text`, calls `ai_extract()` to extract the structured schema fields into typed columns, writes to `workspace.monsters.stats`. All stat columns are INT. Show a final `SELECT *` with all columns visible.

**Critical: Correct ai_extract() signature:**
```python
F.expr("""
    ai_extract(
        CAST(raw_text AS STRING),
        '["name", "lore", "type", "weakness", "atk", "def", "spd", "hp"]',
        map('instructions', 'Extract monster stats from this trading card...')
    )
""")
```

**Key points:**
- Schema is a **JSON string** (e.g., `'["field1", "field2"]'`), NOT a SQL array
- Options use `map('instructions', '...')` format
- Response is a VARIANT with nested structure: `{"response": {"field": {"value": ...}}, "error_message": null}`
- Access fields using VARIANT `:` operator: `parsed_json:response:name:value`

**Field access pattern:**
```python
F.expr("parsed_json:response:name:value").cast("string").alias("name")
F.expr("parsed_json:response:atk:value").cast("int").alias("atk")
```

This is the key teaching moment — show the raw text vs. the structured output side by side. Add a markdown cell explaining what `ai_extract()` is doing.

### `04_battle_logic`
Python notebook. Implements:

1. `calculate_damage(attacker: dict, defender: dict) -> int` — pure Python, applies damage formula with type advantage
2. `battle(monster_a: dict, monster_b: dict) -> dict` — simulates full battle, returns dict with keys: winner, loser, winner_is_first_arg (bool), score (% HP remaining), history, total_rounds
3. `find_winner(challenger: dict, roster: List[dict]) -> Tuple[dict, dict]` — returns (best_battle_result, best_opponent) where best_opponent is the roster monster with highest performance score
4. Battle narrative via LLM (optional demonstration)

Include a test cell at the bottom: pick two monsters from the stats table and run a full battle. Print winner name + score.

### `05_student_exercise`
Guided exercise notebook where students apply what they've learned:

**Structure (12 cells):**
1. Markdown intro — mission and learning objectives
2. Setup — imports and catalog/schema selection (complete)
3. Pick random PDF — loads one random file from volume (complete)
4. Part 1 instructions — markdown explaining ai_parse_document()
5. TODO cell 1 — students implement ai_parse_document() extraction
6. Part 2 instructions — markdown explaining ai_extract() with **correct signature**
7. TODO cell 2 — students define field list (Python list converted to JSON string)
8. TODO cell 3 — students implement ai_extract() with JSON string schema and VARIANT field access
9. Bonus intro — battle simulation explanation
10. Battle functions — complete battle logic (provided)
11. Run battle — executes battle if monster_stats extracted
12. Completion — summary of learning outcomes

**Pedagogical design:**
- TODO sections with clear instructions and hints showing correct ai_extract() format
- Verification code checks if students completed each part
- References to notebooks 02-04 for pattern examples
- Bonus section connects all pieces (PDF → text → stats → battle)
- **Updated** to show JSON string schema format and VARIANT `:value` access pattern

### `06_deploy.py`
Python notebook for deployment automation. Uses Databricks SDK to:

1. Create a scheduled Job with 4 tasks (notebooks 00-03 in sequence)
2. Configure Serverless compute
3. Set schedule to daily at 8 AM (PAUSED by default)
4. Provide UI and CLI instructions for deploying the Streamlit app

**Key features:**
- Dynamic path resolution using `current_user` (no hardcoded usernames)
- Generic placeholders in markdown cells (`<your-username>`)
- Verification cells to confirm files exist before deployment
- Clear instructions for manual app deployment via Databricks UI

---

## App structure (`app/temumon.py`)

Streamlit app with:
- File upload component (accepts PDF)
- On upload: parse PDF text, extract stats, run battle logic, display result
- Output panel: winner's stat card (formatted table) + battle narrative text
- A "View all monsters" accordion showing the full roster from the Delta table
- Monster generator: create new random monsters on the fly

**Supporting files:**
- `battle.py` — battle engine implementation (calculate_damage, battle, find_winner)
- `utils.py` — utility functions for Streamlit UI
- `pdf_generator.py` — monster PDF card generator
- `requirements.txt` — Python dependencies (streamlit, reportlab, etc.)
- `app.yaml` — Databricks App configuration
- `baseline_app.py` — simpler reference version

---

## Seed monster data (`monsters.json`)

**Location:** `data/monsters.json`

Contains 80 monsters. Requirements:
- 10 monsters per TYPE (all 8 types covered)
- Stats should be varied — avoid clustering everything around 50–70
- Some monsters should be obviously strong (high ATK+SPD), some defensive tanks (high HP+DEF), some glass cannons (high ATK, low DEF/HP)
- Names should be evocative and ridiculous rip-offs of the original Pokémon (the call word is "Pokémon from Temu"): `Pokachu`, `Slothking`, `Charlizard`, `Ratatatata` — mix epic and absurd
- LORE: one sentence each, flavour text only, no game mechanics
- LOOK: a description of how the monster looks

Format:
```json
[
  {
    "name": "Pokachu",
    "lore": "Charged to the fullest at a chinese factory after ripping off all of the trademarked features.",
    "look": "Yellow rat with a battery stuffed into its back",
    "type": "Storm",
    "weakness": "Earth",
    "atk": 72,
    "def": 88,
    "spd": 41,
    "hp": 95
  }
]
```

---

## PDF generation (integrated into `00_setup.py`)

**Previous approach:** Separate `generate_monsters.py` script  
**Current approach:** Integrated into `00_setup.py` notebook (cells 6-10)

Uses `reportlab` only (no external design dependencies). Each PDF should look like a monster trading card, but with variations so it feels like someone making these by hand and constantly forgets about their own rules:

Layout per PDF (A6 or letter, single page):
- Monster name — large, top or bottom, bold, italic, underlined, different colors
- TYPE badge and WEAKNESS badge side by side, random location on the card
- Stat block: ATK / DEF / SPD / HP as a grid with labels, but different layouts: 2x2, 1x4, 4x1
- Lore text — sometimes italic, bottom of card, sometimes above stats, sometimes below, sometimes on the side
- A simple decorative border (just a thick rect outline is fine)
- An ASCII representation of the monster, be creative
- Filename: `{slug(name)}.pdf` e.g. `pokachu.pdf`

Reads from `/Workspace/Users/{current_user}/temumon/data/monsters.json` and writes PDFs to Volume: `/Volumes/workspace/monsters/dropzone/raw_pdfs/`.

---

## Code style and quality rules

- All Python: type hints on all function signatures
- All Python: docstrings on every function (one-line summary is fine)
- PySpark: use DataFrame API, not SQL strings (except for AI functions via `F.expr()`)
- No hardcoded cluster IDs, workspace URLs, tokens, or usernames — use dynamic resolution
- Notebook markdown cells: write as if talking to a student. Explain the *why* before the *what*. Keep cells short.
- Every notebook must be runnable top-to-bottom without errors on a fresh cluster
- Defensive: if a Delta table already exists, don't fail — use `CREATE OR REPLACE` or conditional logic
- Use `display()` in notebooks for DataFrames, not `print()`

---

## Pedagogical constraints (do not violate these)

These are deliberate teaching choices — do not optimise them away:

1. **Show the raw text before the structured extraction.** In `03_extract_stats.py`, there must be a cell that displays the raw `ai_parse_document` output before the `ai_extract` cell. Students need to see the messy text to appreciate what extraction does.

2. **Keep the rule engine and LLM narration strictly separate.** The winner is always determined by the scoring formula. The LLM only narrates — it never decides the outcome. This is the conceptual point of the battle logic.

3. **The student exercise has exactly three TODO cells.** Not more. The goal is for students to connect pieces they've already built, not to write new logic.

4. **Notebook 04 includes a test battle with visible output.** Students must see a real winner + score before building the app. Don't skip the test cell.

5. **No LangChain.** This workshop deliberately uses Databricks-native AI functions (`ai_parse_document`, `ai_extract`, Model Serving SDK) to teach the platform, not an abstraction layer.

6. **PySpark DataFrame API throughout.** Notebooks 01-03 use PySpark DataFrame operations, not SQL strings. This teaches students the programmatic API.

7. **Correct ai_extract() signature is non-negotiable.** Schema must be a JSON string, not SQL array. Field access must use VARIANT `:` operator with `:value` suffix. This is the actual API behavior.

---

## Deliverable checklist

When complete, the following must exist and be runnable:

- [x] `monsters.json` with 80 monsters (location: `data/monsters.json`)
- [x] PDF generation integrated into `00_setup.py` (cells 6-10)
- [x] `00_setup.py` through `05_student_exercise` — all 6 notebooks
- [x] `06_deploy.py` — deployment automation notebook
- [x] `app/temumon.py` — complete Streamlit app
- [x] `app/battle.py`, `app/utils.py`, `app/pdf_generator.py` — supporting app modules
- [x] `app/requirements.txt`, `app/app.yaml` — deployment configuration
- [x] `app/baseline_app.py` — reference baseline version
- [x] `README.md` with setup instructions
- [x] Correct `ai_extract()` signature in notebooks 03 and 05

---

## What students will build

Students will:

1. **Run the data pipeline** (notebooks 00-03) to generate and process 80 monster PDFs
2. **Understand battle logic** (notebook 04) with rule-based scoring and LLM narration
3. **Complete the student exercise** (notebook 05) to extract their own monster and battle it
4. **Deploy the app** (notebook 06) to share with others
5. **Explore the Streamlit app** to upload new monsters and see battles in action

The focus is on connecting AI functions, data pipelines, and application deployment — not on building everything from scratch.
