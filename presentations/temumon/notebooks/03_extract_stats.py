# Databricks notebook source
# DBTITLE 1,Extract Stats - Structured Parsing
# MAGIC %md
# MAGIC # Extract Stats - Structured Data Extraction
# MAGIC
# MAGIC This notebook uses `ai_extract()` to extract structured monster stats from raw text.
# MAGIC
# MAGIC **Input**: `workspace.monsters.raw_text` table (unstructured text)  
# MAGIC **Output**: `workspace.monsters.stats` table (structured columns)
# MAGIC
# MAGIC ## What is ai_extract()?
# MAGIC
# MAGIC `ai_extract()` is a Databricks SQL function that:
# MAGIC * Takes unstructured text and a JSON schema as input
# MAGIC * Extracts structured data matching the schema
# MAGIC * Returns JSON that can be parsed into typed columns
# MAGIC * More precise than `ai_parse_document()` for extracting specific fields
# MAGIC
# MAGIC **Teaching moment**: This is the key difference between document parsing (raw text) and structured extraction (typed fields).

# COMMAND ----------

# DBTITLE 1,Set default schema
from pyspark.sql import functions as F

# Set the current catalog and schema
spark.catalog.setCurrentCatalog("workspace")
spark.catalog.setCurrentDatabase("monsters")

print("✓ Using workspace.monsters schema")

# COMMAND ----------

# DBTITLE 1,Define Schema
# MAGIC %md
# MAGIC ## Monster Card Schema
# MAGIC
# MAGIC Every monster card contains these exact fields:
# MAGIC
# MAGIC | Field | Type | Description | Example |
# MAGIC |-------|------|-------------|----------|
# MAGIC | name | string | Monster name | "Pokachu" |
# MAGIC | lore | string | Flavor text | "Charged to the fullest..." |
# MAGIC | type | string | Element type | "Fire" |
# MAGIC | weakness | string | Weak against | "Ice" |
# MAGIC | atk | integer | Attack stat (1-100) | 72 |
# MAGIC | def | integer | Defense stat (1-100) | 88 |
# MAGIC | spd | integer | Speed stat (1-100) | 41 |
# MAGIC | hp | integer | Hit points (1-100) | 95 |
# MAGIC
# MAGIC We'll provide this schema to `ai_extract()` to ensure accurate extraction.

# COMMAND ----------

# DBTITLE 1,Define JSON schema for ai_parse
# Fields we'll extract from the monster cards using ai_extract()
# The function takes an array of field names to extract from the raw text

fields = ['name', 'lore', 'type', 'weakness', 'atk', 'def', 'spd', 'hp']

print(f"Fields to extract: {', '.join(fields)}")
print("\nai_extract() will analyze the raw text and extract these fields automatically.")

# COMMAND ----------

# DBTITLE 1,Extract Structured Stats
# MAGIC %md
# MAGIC ## Parse Raw Text into Structured Columns
# MAGIC
# MAGIC We'll call `ai_extract()` on each row of raw text, then extract the JSON fields into typed columns.
# MAGIC
# MAGIC **This may take 5-10 minutes** for 80 monsters, as each row requires an AI inference call.

# COMMAND ----------

# DBTITLE 1,Parse and extract stats
# Extract structured stats from raw text using ai_extract()
from pyspark.sql import functions as F

print("Extracting structured stats with ai_extract()...")
print("This may take 5-10 minutes for 80 monsters...\n")

# Read raw text table
raw_text_df = spark.table("workspace.monsters.raw_text")

# Apply ai_extract to get structured JSON
# Note: Cast raw_text to STRING since ai_parse_document returns VARIANT
# Schema is passed as a JSON string (array of field names)
extracted_df = raw_text_df.select(
    F.col("filename"),
    F.expr("""
        ai_extract(
            CAST(raw_text AS STRING),
            '["name", "lore", "type", "weakness", "atk", "def", "spd", "hp"]',
            map('instructions', 'Extract monster stats from this trading card. ATK, DEF, SPD, and HP are integer values between 1-100. TYPE and WEAKNESS are element types like Fire, Ice, Shadow, Storm, Earth, Poison, Light, or Void.')
        )
    """).alias("parsed_json")
)

# Parse JSON fields into typed columns
# ai_extract returns VARIANT {"response": {"field": {"value": ...}, ...}, "error_message": null}
# Use : operator to access nested VARIANT fields
stats_df = extracted_df.select(
    F.col("filename"),
    F.expr("parsed_json:response:name:value").cast("string").alias("name"),
    F.expr("parsed_json:response:lore:value").cast("string").alias("lore"),
    F.expr("parsed_json:response:type:value").cast("string").alias("type"),
    F.expr("parsed_json:response:weakness:value").cast("string").alias("weakness"),
    F.expr("parsed_json:response:atk:value").cast("int").alias("atk"),
    F.expr("parsed_json:response:def:value").cast("int").alias("def"),
    F.expr("parsed_json:response:spd:value").cast("int").alias("spd"),
    F.expr("parsed_json:response:hp:value").cast("int").alias("hp"),
    F.current_timestamp().alias("extracted_at")
).filter(F.col("parsed_json").isNotNull())

# Write to Delta table
stats_df.write.mode("overwrite").saveAsTable("workspace.monsters.stats")

print("✓ Structured extraction complete!")
print("✓ Results saved to workspace.monsters.stats")

# COMMAND ----------

# DBTITLE 1,Count extracted monsters
# Check how many monsters were successfully extracted
stats_table = spark.table("workspace.monsters.stats")
total = stats_table.count()

print(f"\nTotal monsters extracted: {total}")

if total == 0:
    print("⚠️ WARNING: No monsters extracted! Check if raw_text table has data.")
else:
    print(f"✓ Successfully extracted {total} monster stat cards!")

# COMMAND ----------

# DBTITLE 1,Preview Structured Data
# MAGIC %md
# MAGIC ## Preview Structured Monster Stats
# MAGIC
# MAGIC Notice how the data is now in clean, typed columns ready for analysis and battle logic!

# COMMAND ----------

# DBTITLE 1,Display sample monsters
# Show first 5 monsters with all stats
sample_df = (
    spark.table("workspace.monsters.stats")
    .select(
        F.col("name"),
        F.col("type"),
        F.col("weakness"),
        F.col("atk"),
        F.col("def"),
        F.col("spd"),
        F.col("hp"),
        F.expr("LEFT(lore, 100)").alias("lore_preview")
    )
    .orderBy("name")
    .limit(5)
)

display(sample_df)

# COMMAND ----------

# DBTITLE 1,Validation
# MAGIC %md
# MAGIC ## Data Quality Validation
# MAGIC
# MAGIC Let's check for any extraction issues:

# COMMAND ----------

# DBTITLE 1,Validate extracted data
# Check for data quality issues
stats_df = spark.table("workspace.monsters.stats")

# Define valid types
valid_types = ['Fire', 'Ice', 'Shadow', 'Storm', 'Earth', 'Poison', 'Light', 'Void']

val_df = stats_df.agg(
    F.count("*").alias("total"),
    F.countDistinct("name").alias("unique_names"),
    F.sum(F.when((F.col("name").isNull()) | (F.col("name") == ""), 1).otherwise(0)).alias("missing_names"),
    F.sum(F.when(~F.col("type").isin(valid_types), 1).otherwise(0)).alias("invalid_types"),
    F.sum(F.when((F.col("atk") < 1) | (F.col("atk") > 100), 1).otherwise(0)).alias("invalid_atk"),
    F.sum(F.when((F.col("def") < 1) | (F.col("def") > 100), 1).otherwise(0)).alias("invalid_def"),
    F.sum(F.when((F.col("spd") < 1) | (F.col("spd") > 100), 1).otherwise(0)).alias("invalid_spd"),
    F.sum(F.when((F.col("hp") < 1) | (F.col("hp") > 100), 1).otherwise(0)).alias("invalid_hp")
)

val_result = val_df.collect()[0]

print("\n" + "="*60)
print("DATA QUALITY REPORT")
print("="*60)
print(f"Total monsters: {val_result['total']}")
print(f"Unique names: {val_result['unique_names']}")
print(f"Missing names: {val_result['missing_names']}")
print(f"Invalid types: {val_result['invalid_types']}")
print(f"Invalid ATK values: {val_result['invalid_atk']}")
print(f"Invalid DEF values: {val_result['invalid_def']}")
print(f"Invalid SPD values: {val_result['invalid_spd']}")
print(f"Invalid HP values: {val_result['invalid_hp']}")
print("="*60)

issues = (
    val_result['missing_names'] + 
    val_result['invalid_types'] +
    val_result['invalid_atk'] +
    val_result['invalid_def'] +
    val_result['invalid_spd'] +
    val_result['invalid_hp']
)

if issues == 0:
    print("\n✅ All data validation checks passed!")
else:
    print(f"\n⚠️ Found {issues} data quality issues. Review the data above.")

# COMMAND ----------

# DBTITLE 1,Statistics by Type
# MAGIC %md
# MAGIC ## Monster Distribution by Type
# MAGIC
# MAGIC Let's see how monsters are distributed across element types:

# COMMAND ----------

# DBTITLE 1,Show type distribution
# Count monsters by type
type_dist = (
    spark.table("workspace.monsters.stats")
    .groupBy("type")
    .agg(
        F.count("*").alias("count"),
        F.round(F.avg("atk"), 1).alias("avg_atk"),
        F.round(F.avg("def"), 1).alias("avg_def"),
        F.round(F.avg("spd"), 1).alias("avg_spd"),
        F.round(F.avg("hp"), 1).alias("avg_hp")
    )
    .orderBy(F.col("count").desc(), "type")
)

display(type_dist)

# COMMAND ----------

# DBTITLE 1,Next Steps
# MAGIC %md
# MAGIC ## Next Steps
# MAGIC
# MAGIC Now that we have structured monster stats:
# MAGIC
# MAGIC 1. **Run notebook 04_battle_logic.py** to implement the battle scoring system
# MAGIC    * Rule-based winner calculation using ATK, DEF, SPD, type advantage
# MAGIC    * LLM-generated battle narratives for storytelling
# MAGIC
# MAGIC 2. **Run notebook 05_student_exercise** to apply what you've learned
# MAGIC    * Extract your own monster from a PDF
# MAGIC    * Battle it against the full roster
# MAGIC
# MAGIC **The data pipeline is complete!** All monster stats are ready for battle simulation.