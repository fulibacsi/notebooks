# Databricks notebook source
# DBTITLE 1,Setup - Create Catalog, Schema, and Volume
# MAGIC %md
# MAGIC # TemuMon - Setup
# MAGIC
# MAGIC This notebook creates the foundational Unity Catalog objects:
# MAGIC * **Catalog**: `workspace` - top-level container
# MAGIC * **Schema**: `monsters` - logical database for our tables
# MAGIC * **Volume**: `dropzone` - managed storage for PDF files
# MAGIC
# MAGIC All subsequent notebooks will reference these objects.

# COMMAND ----------

# DBTITLE 1,Create catalog
# Create the workspace catalog if it doesn't exist
spark.sql("CREATE CATALOG IF NOT EXISTS workspace")
print("✓ Catalog 'workspace' created")

# COMMAND ----------

# DBTITLE 1,Create schema
# Create the monsters schema within the workspace catalog
spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.monsters")
print("✓ Schema 'workspace.monsters' created")

# COMMAND ----------

# DBTITLE 1,Set default schema
# Set workspace.monsters as the default schema for subsequent queries
spark.sql("USE CATALOG workspace")
spark.sql("USE SCHEMA monsters")
print("✓ Default schema set to workspace.monsters")

# COMMAND ----------

# DBTITLE 1,Create volume for PDF storage
# Create a managed volume to store monster PDF files
spark.sql("CREATE VOLUME IF NOT EXISTS workspace.monsters.dropzone")
print("✓ Volume 'dropzone' created at /Volumes/workspace/monsters/dropzone")

# COMMAND ----------

# DBTITLE 1,Generate Monster PDFs
# MAGIC %md
# MAGIC ## Generate Monster PDFs
# MAGIC
# MAGIC Now we'll generate 80 monster trading card PDFs from the seed data. Each card will have a unique, intentionally varied layout to make the AI parsing more challenging and realistic.

# COMMAND ----------

# DBTITLE 1,Install reportlab for PDF generation
# Install reportlab if not already available
%pip install reportlab --quiet

# COMMAND ----------

# DBTITLE 1,Restart Python to apply pip install
%restart_python

# COMMAND ----------

# DBTITLE 1,Define PDF generation helper functions
import json
import random
import re
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter, A6
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def slugify(name: str) -> str:
    """Convert monster name to filename-safe slug."""
    return re.sub(r'[^\w\s-]', '', name.lower()).replace(' ', '-')


def draw_ascii_monster(c: canvas.Canvas, x: float, y: float, width: float, look: str) -> None:
    """Draw a simple ASCII art representation of the monster."""
    ascii_arts = [
        ["  ^___^", " (o o)", "  \\_/"],
        ["  /\\_/\\", " ( o.o )", "  > ^ <"],
        [" .-''''-.", "/ o  o \\", "\\  <>  /", " '.__.'"],
        ["  ___", " {o,o}", " |)__)", " -\"-\"-"],
        [" .--.", "/.---.\\", "|>.<|", "\\___/"],
    ]
    art = random.choice(ascii_arts)
    c.setFont("Courier", 10)
    c.setFillColor(colors.HexColor("#333333"))
    for i, line in enumerate(art):
        c.drawCentredString(x + width/2, y - i*12, line)


def draw_stat_block_2x2(c: canvas.Canvas, x: float, y: float, stats: dict) -> None:
    """Draw stats in 2x2 grid layout."""
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, f"ATK: {stats['atk']}")
    c.drawString(x + 80, y, f"DEF: {stats['def']}")
    c.drawString(x, y - 20, f"SPD: {stats['spd']}")
    c.drawString(x + 80, y - 20, f"HP: {stats['hp']}")


def draw_stat_block_1x4(c: canvas.Canvas, x: float, y: float, stats: dict) -> None:
    """Draw stats in 1x4 vertical layout."""
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, f"ATK: {stats['atk']}")
    c.drawString(x, y - 18, f"DEF: {stats['def']}")
    c.drawString(x, y - 36, f"SPD: {stats['spd']}")
    c.drawString(x, y - 54, f"HP: {stats['hp']}")


def draw_stat_block_4x1(c: canvas.Canvas, x: float, y: float, stats: dict) -> None:
    """Draw stats in 4x1 horizontal layout."""
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y, f"ATK:{stats['atk']}")
    c.drawString(x + 60, y, f"DEF:{stats['def']}")
    c.drawString(x + 120, y, f"SPD:{stats['spd']}")
    c.drawString(x + 180, y, f"HP:{stats['hp']}")


def generate_card(monster: dict, output_path: str) -> None:
    """Generate a single monster card PDF with randomized layout."""
    # Random page size
    page_size = random.choice([letter, A6, (6*inch, 8*inch)])
    c = canvas.Canvas(output_path, pagesize=page_size)
    width, height = page_size
    
    # Border
    border_color = random.choice([colors.black, colors.HexColor("#8B4513"), 
                                  colors.HexColor("#4B0082"), colors.HexColor("#2F4F4F")])
    c.setStrokeColor(border_color)
    c.setLineWidth(random.choice([3, 4, 5, 6]))
    c.rect(0.25*inch, 0.25*inch, width - 0.5*inch, height - 0.5*inch)
    
    # Monster name - randomize position and style
    name_y = random.choice([height - 0.7*inch, 0.6*inch])
    name_size = random.randint(16, 24)
    c.setFont(random.choice(["Helvetica-Bold", "Times-Bold", "Courier-Bold"]), name_size)
    name_color = random.choice([colors.black, colors.HexColor("#8B0000"), 
                                colors.HexColor("#000080"), colors.HexColor("#006400")])
    c.setFillColor(name_color)
    
    # Random text decoration
    name_x = width / 2
    if random.choice([True, False]):  # underline
        c.line(0.5*inch, name_y - 5, width - 0.5*inch, name_y - 5)
    
    c.drawCentredString(name_x, name_y, monster['name'])
    
    # Type and Weakness badges - random location
    badge_y = random.uniform(height * 0.4, height * 0.7)
    badge_x = random.uniform(0.5*inch, width * 0.3)
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.white)
    
    # Type badge
    type_colors = {
        "Fire": "#FF4500", "Ice": "#00CED1", "Shadow": "#483D8B",
        "Storm": "#FFD700", "Earth": "#8B4513", "Poison": "#9370DB",
        "Light": "#FFD700", "Void": "#000000"
    }
    c.setFillColor(colors.HexColor(type_colors.get(monster['type'], "#808080")))
    c.rect(badge_x, badge_y, 1.2*inch, 0.3*inch, fill=1)
    c.setFillColor(colors.white)
    c.drawCentredString(badge_x + 0.6*inch, badge_y + 0.08*inch, monster['type'])
    
    # Weakness badge
    c.setFillColor(colors.HexColor(type_colors.get(monster['weakness'], "#808080")))
    c.rect(badge_x + 1.4*inch, badge_y, 1.2*inch, 0.3*inch, fill=1)
    c.setFillColor(colors.white)
    c.drawCentredString(badge_x + 2.0*inch, badge_y + 0.08*inch, f"Weak: {monster['weakness']}")
    
    # Stats - random layout style
    stat_layout = random.choice([draw_stat_block_2x2, draw_stat_block_1x4, draw_stat_block_4x1])
    stat_y = random.uniform(height * 0.25, height * 0.5)
    c.setFillColor(colors.black)
    stat_layout(c, 0.5*inch, stat_y, monster)
    
    # Lore text - random position and style
    lore_y = random.choice([1.2*inch, height - 1.5*inch, stat_y - 0.8*inch])
    lore_font = random.choice(["Helvetica", "Times-Italic", "Helvetica-Oblique"])
    c.setFont(lore_font, 8)
    c.setFillColor(colors.HexColor("#555555"))
    
    # Wrap lore text
    max_width = width - 1*inch
    words = monster['lore'].split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        if c.stringWidth(test_line, lore_font, 8) > max_width:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    
    for i, line in enumerate(lines):
        c.drawCentredString(width / 2, lore_y - i*10, line)
    
    # ASCII monster art
    ascii_y = random.uniform(height * 0.35, height * 0.55)
    ascii_x = random.uniform(width * 0.6, width * 0.8)
    draw_ascii_monster(c, ascii_x, ascii_y, 1*inch, monster['look'])
    
    c.save()

print("✓ PDF generation functions defined")

# COMMAND ----------

# DBTITLE 1,Clean up existing PDFs (if any)
import shutil

# Output directory in the volume
output_dir = "/Volumes/workspace/monsters/dropzone/raw_pdfs"

# Remove existing PDFs if the directory exists
if Path(output_dir).exists():
    shutil.rmtree(output_dir)
    print(f"✓ Cleaned up existing PDFs in {output_dir}")
else:
    print(f"✓ No existing PDFs to clean up")

# Recreate the directory
Path(output_dir).mkdir(parents=True, exist_ok=True)
print(f"✓ Created fresh directory: {output_dir}")

# COMMAND ----------

# DBTITLE 1,Generate all monster PDFs
# Get current user for dynamic path resolution
current_user = spark.sql("SELECT current_user()").collect()[0][0]
base_path = f"/Workspace/Users/{current_user}/temumon"

# Path to monsters.json in the data folder
json_path = f"{base_path}/data/monsters.json"

# Output directory in the volume
output_dir = "/Volumes/workspace/monsters/dropzone/raw_pdfs"

print(f"Reading monster data from: {json_path}")

# Read monsters.json
with open(json_path, 'r') as f:
    monsters = json.load(f)

print(f"Generating {len(monsters)} monster PDFs...")

# Generate all PDFs
for i, monster in enumerate(monsters, 1):
    slug = slugify(monster['name'])
    output_path = f"{output_dir}/{slug}.pdf"
    generate_card(monster, output_path)
    
    if i % 10 == 0:
        print(f"  Generated {i}/{len(monsters)} PDFs...")

print(f"\n✓ All {len(monsters)} monster cards generated in {output_dir}/")
print(f"\nSample filenames:")
for i in range(min(5, len(monsters))):
    slug = slugify(monsters[i]['name'])
    print(f"  - {slug}.pdf")

# COMMAND ----------

# DBTITLE 1,Verification
# MAGIC %md
# MAGIC ## Verify Setup
# MAGIC
# MAGIC Let's confirm all objects were created successfully by listing volumes in the monsters schema.

# COMMAND ----------

# DBTITLE 1,Show volumes to verify
# Display all volumes in the monsters schema
display(spark.sql("SHOW VOLUMES IN workspace.monsters"))

# COMMAND ----------

# DBTITLE 1,Next Steps
# MAGIC %md
# MAGIC ## Next Steps
# MAGIC
# MAGIC Setup complete! You've successfully:
# MAGIC * Created the `workspace` catalog and `monsters` schema
# MAGIC * Created the `dropzone` volume for PDF storage
# MAGIC * Generated 80 monster PDFs with varied layouts
# MAGIC
# MAGIC All PDFs are now stored in:
# MAGIC ```
# MAGIC /Volumes/workspace/monsters/dropzone/raw_pdfs/
# MAGIC ```
# MAGIC
# MAGIC **Next**: Run notebook `01_upload_check` to verify all PDFs are accessible and ready for processing.