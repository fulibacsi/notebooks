# TemuMon — Workshop Setup Guide

Welcome to the **TemuMon** workshop! This is a hands-on 60-minute coding session where you'll:

* Parse PDFs using Databricks AI functions
* Extract structured data from unstructured text
* Build a hybrid battle engine (rules + LLM)
* Deploy a Streamlit app on Databricks

Everything runs inside Databricks — no local setup required!

---

## Prerequisites

* Basic Python and SQL knowledge
* A laptop with a web browser
* Enthusiasm for absurdly named monsters 🐉

---

## Step 1: Sign Up for Databricks Free Edition

1. Go to **[databricks.com/try-databricks](https://databricks.com/try-databricks)**
2. Select **"Get Free Edition"**
3. Create your account with email

You'll land in the Databricks workspace. This is where all the magic happens!

---

## Step 2: Configure Your Compute

Databricks Free Edition includes **Serverless** compute — no configuration needed!

* Serverless compute auto-starts when you run a cell
* No need to manually create or start clusters
* Supports Python and SQL notebooks

**Note**: Serverless compute may take 1-2 minutes to warm up on first run. This is normal.

---

## Step 3: Import the Workshop Files

### Option A: Clone from GitHub

1. In your workspace, click **"Workspace"** in the left sidebar
2. Click **Home** → **"Create"** → **"Git Folder"**
3. Enter the workshop repo URL
4. Click **"Clone"**

### Option B: Upload Files Manually

1. Download the workshop files as a ZIP
2. In your workspace, navigate to your Home folder: `/Users/your.email@domain.com/`
3. Click **"Create"** → **"Folder"** → Name it `temumon`
4. Upload all files and folders from the workshop ZIP, maintaining the directory structure

**Important**: Make sure you upload the `data/` folder, which contains:
* `monsters.json` — data for 80 monsters (used by the setup notebook to generate PDFs)


---

## Step 4: Run the Setup & Generate PDFs

Notebook `00_setup.py` handles everything: infrastructure setup AND PDF generation!

1. Open notebook `notebooks/00_setup.py`
2. Run all cells from top to bottom
3. **What this does:**
   - Creates catalog: `workspace`
   - Creates schema: `monsters`
   - Creates volume: `/Volumes/workspace/monsters/dropzone/`
   - Installs `reportlab` package
   - Reads `data/monsters.json` (80 monsters)
   - Generates 80 PDF cards with varied layouts
   - Saves PDFs to `/Volumes/workspace/monsters/dropzone/raw_pdfs/`
4. **Verify**: The final cell should show the volume contents with 80 PDFs

**Expected output**: `✓ All 80 monster cards generated`

---

## Step 5: Verify PDF Generation

Run notebook `notebooks/01_upload_check.py` to confirm all PDFs were created:

1. Open `notebooks/01_upload_check.py`
2. Run all cells
3. **Verify**: Should show 80 PDF files listed

---

## Step 6: Run the Data Pipeline Notebooks

Now run the remaining notebooks in order to build the data pipeline:

### **02_parse_documents.py**
* Uses `ai_parse_document()` to extract text from PDFs
* Implemented with **PySpark DataFrame API** (not SQL)
* Writes raw text to `workspace.monsters.raw_text` table
* **Verify**: Preview shows extracted text from multiple monsters

### **03_extract_stats.py**
* Uses `ai_extract()` to extract structured fields (name, type, stats)
* Implemented with **PySpark DataFrame API** 
* Writes structured data to `workspace.monsters.stats` table
* **Key teaching moment**: Compare raw text vs. structured output!
* **Verify**: Final cell shows 80 monsters with all stats visible

**Important Note on `ai_extract()`:**
The schema parameter must be a **JSON string**, not a SQL array:
```python
# Correct:
ai_extract(
    CAST(raw_text AS STRING),
    '["name", "lore", "type", "weakness", "atk", "def", "spd", "hp"]',
    map('instructions', 'Extract monster stats...')
)

# Response is VARIANT: {"response": {"field": {"value": ...}}, "error_message": null}
# Access fields with: parsed_json:response:name:value
```

### **04_battle_logic**
* Implements the battle damage formula
* Implements winner selection logic
* Demonstrates type advantage mechanics
* Runs a test battle at the end
* **Verify**: See a winner and battle score printed

---

## Step 7: Complete the Student Exercise

Try the hands-on exercise where you extract your own monster:

### **05_student_exercise**
* **Part 1**: Extract raw text from a random PDF using `ai_parse_document()`
* **Part 2**: Define the field list and extract structured stats using `ai_extract()` with JSON string schema
* **Bonus**: Battle your extracted monster against the roster!

**Goal**: Apply what you've learned in notebooks 02-04 to process a single monster end-to-end.

**Instructions**:
1. Open `notebooks/05_student_exercise`
2. Follow the TODO sections
3. Refer back to notebooks 02-04 for patterns and examples
4. Pay attention to the `ai_extract()` signature — schema is a JSON string, field access uses `:response:field:value`
5. Run the verification cells to check your work

---

## Step 8: Deploy the Application (Optional)

If you want to deploy the complete Streamlit app for others to use:

### **06_deploy.py**
* Creates a scheduled Job to run the data pipeline (notebooks 00-03)
* Provides instructions for deploying the Streamlit app via Databricks UI
* Schedule is **PAUSED by default** — trigger manually when needed

**What the app does:**
* Upload a new monster PDF
* Extract stats automatically using the pipeline you built
* Find the best opponent from the roster
* Display battle results with stats and narrative
* Generate new random monsters

**Deployment steps:**
1. Open `notebooks/06_deploy.py`
2. Run the job creation cells (creates the data pipeline job)
3. Follow the UI instructions to deploy the Streamlit app
4. Access the app URL and share with others!

---

## Troubleshooting

### **"ModuleNotFoundError: No module named 'reportlab'"**
* This is handled automatically in notebook `00_setup.py` (cell 7)
* If you still get this error, run `%pip install reportlab` in a cell
* Restart the kernel: `%restart_python`

### **"FileNotFoundError: monsters.json"**
* Make sure you imported the entire `data/` folder in Step 3
* The JSON file must be at `data/monsters.json` (relative to the temumon/ root)
* Check the file path in cell 10 of `00_setup.py`

### **"Volume 'dropzone' does not exist"**
* Run notebook `00_setup.py` first to create the volume
* Verify the volume exists by running: `display(spark.sql("SHOW VOLUMES IN workspace.monsters"))`

### **"Table workspace.monsters.stats not found"**
* Make sure you ran notebooks `00_setup.py` through `03_extract_stats.py` in order

### **"ai_parse_document is not a recognized function"**
* Ensure you're using **Databricks** and Serverless compute
* AI functions are available in Databricks Runtime 14.0+

### **"ai_extract schema error: expected STRING but got ARRAY"**
* The schema must be a JSON string like `'["field1", "field2"]'`, not a SQL array like `array('field1', 'field2')`
* Review notebook `03_extract_stats.py` cell 6 for the correct pattern

### **Serverless compute is slow**
* First run takes 1-2 minutes to warm up
* Subsequent runs are faster
* This is normal for Serverless compute

### **Student exercise verification fails**
* Check that you've defined all required fields (name, lore, type, weakness, atk, def, spd, hp)
* Verify your `ai_extract()` call uses a JSON string schema: `'["name", "lore", ...]'`
* Access VARIANT fields correctly: `parsed_json:response:name:value`
* Review notebooks 02-03 for the correct patterns

---

## Workshop Structure

* **Minutes 0-10**: Setup + PDF Generation (notebook 00-01)
* **Minutes 10-25**: Document Parsing (notebook 02)
* **Minutes 25-40**: Structured Extraction (notebook 03)
* **Minutes 40-50**: Battle Logic (notebook 04)
* **Minutes 50-60**: Student Exercise (notebook 05)
* **Optional**: Deployment (notebook 06) — instructor-led or take-home

---

## Key Concepts You'll Learn

1. **AI Functions with PySpark**: `ai_parse_document()` and `ai_extract()` for document intelligence
2. **PySpark DataFrame API**: Programmatic data transformations (not SQL strings)
3. **Unity Catalog Volumes**: Cloud-native file storage in Databricks
4. **Hybrid AI Systems**: Combining deterministic rules with LLM creativity
5. **Streamlit Apps**: Deploying interactive apps on Databricks
6. **Job Scheduling**: Automating data pipelines with Databricks Jobs
7. **VARIANT data type**: Working with semi-structured JSON data in Databricks

---

## Project Structure

```
temumon/
├── notebooks/
│   ├── 00_setup.py              # Create infrastructure + generate PDFs
│   ├── 01_upload_check.py       # Verify PDFs generated
│   ├── 02_parse_documents.py    # Extract text from PDFs
│   ├── 03_extract_stats.py      # Parse structured stats
│   ├── 04_battle_logic          # Battle engine implementation
│   ├── 05_student_exercise      # Hands-on guided exercise
│   └── 06_deploy.py             # Deploy job + app
│
├── app/
│   ├── temumon.py               # Complete Streamlit app
│   ├── battle.py                # Battle logic module
│   ├── utils.py                 # UI utilities
│   ├── pdf_generator.py         # Monster card generator
│   └── requirements.txt         # Python dependencies
│
└── data/
    └── monsters.json            # 80 monster definitions (used by 00_setup)
```

---

## Need Help?

* **Databricks Documentation**: [docs.databricks.com](https://docs.databricks.com)
* **AI Functions Guide**: Search for "Databricks AI Functions"
* **Instructor**: Raise your hand or ask in chat!

---

## What Makes This Workshop Unique?

* **Pokémon from Temu**: Hilariously bad knockoff monster names
* **Real AI functions**: Not mock data — actual document parsing with Databricks AI
* **End-to-end pipeline**: From PDF generation to deployed app
* **Hybrid intelligence**: Deterministic rules + LLM creativity working together
* **No local setup**: Everything runs in Databricks Free Edition
* **Integrated workflow**: PDF generation happens right in the setup notebook

---

## Credits

Workshop created for data science students to explore AI-powered data engineering on Databricks. "Pokémon from Temu" concept inspired by the absurdity of knockoff trading cards.

Built with ❤️ and questionable monster naming choices.

---

**Ready to forge some monsters?** 🔨⚔️

Head to notebook `notebooks/00_setup.py` and let's get started!
