# Databricks notebook source
# DBTITLE 1,Parse Documents - Extract Raw Text
# MAGIC %md
# MAGIC # Parse Documents - Extract Raw Text with AI
# MAGIC
# MAGIC This notebook uses `ai_parse_document()` to extract raw text from monster PDF cards.
# MAGIC
# MAGIC **Input**: PDF files in `/Volumes/workspace/monsters/dropzone/raw_pdfs/`  
# MAGIC **Output**: `workspace.monsters.raw_text` table with extracted text
# MAGIC
# MAGIC ## What is ai_parse_document()?
# MAGIC
# MAGIC `ai_parse_document()` is a Databricks SQL function that:
# MAGIC * Extracts text from PDFs, images, and other documents
# MAGIC * Uses AI/ML models for OCR and layout understanding
# MAGIC * Returns unstructured text that needs further parsing
# MAGIC * Available in Databricks SQL and PySpark via spark.sql()
# MAGIC
# MAGIC In the next notebook, we'll use `ai_extract()` to turn this raw text into structured data.

# COMMAND ----------

# DBTITLE 1,Set default schema
from pyspark.sql import functions as F

# Set the current catalog and schema
spark.catalog.setCurrentCatalog("workspace")
spark.catalog.setCurrentDatabase("monsters")

print("✓ Using workspace.monsters schema")

# COMMAND ----------

# DBTITLE 1,Define volume path
# Path to the PDF files
volume_path = "/Volumes/workspace/monsters/dropzone/raw_pdfs/"
print(f"Reading PDFs from: {volume_path}")

# COMMAND ----------

# DBTITLE 1,Parse PDFs with ai_parse_document
# MAGIC %md
# MAGIC ## Extract Raw Text from PDFs
# MAGIC
# MAGIC We'll use `ai_parse_document()` to extract text from each PDF file.  
# MAGIC The function takes the binary file content and returns extracted text.
# MAGIC
# MAGIC **Note**: This may take several minutes depending on the number of PDFs and AI function throughput.

# COMMAND ----------

# DBTITLE 1,Parse documents and create table
# Parse all PDFs and save to raw_text table
# Using CREATE OR REPLACE to make this operation idempotent

print("Parsing PDFs with ai_parse_document()...")
print("This may take 2-5 minutes for 80 PDFs...\n")

# Read binary files from volume
files_df = (
    spark.read
    .format("binaryFile")
    .load(volume_path)
)

# Parse documents and extract metadata
raw_text_df = (
    files_df
    .filter(F.col("_metadata.file_name").like("%.pdf"))
    .select(
        F.col("_metadata.file_path").alias("source_file"),
        F.col("_metadata.file_name").alias("filename"),
        F.expr("ai_parse_document(content, map('version', '2.0'))").alias("raw_text"),
        F.current_timestamp().alias("parsed_at")
    )
)

# Write to Delta table
raw_text_df.write.mode("overwrite").saveAsTable("workspace.monsters.raw_text")

print("✓ PDF parsing complete!")
print("✓ Results saved to workspace.monsters.raw_text")

# COMMAND ----------

# DBTITLE 1,Count parsed documents
# Check how many documents were successfully parsed
raw_text_table = spark.table("workspace.monsters.raw_text")
total = raw_text_table.count()

print(f"\nTotal documents parsed: {total}")

# COMMAND ----------

# DBTITLE 1,Preview Raw Text
# MAGIC %md
# MAGIC ## Preview Extracted Text
# MAGIC
# MAGIC Let's look at a few examples of the raw text extracted from PDFs.  
# MAGIC Notice that the text is unstructured - we'll parse it into columns in the next notebook.

# COMMAND ----------

# DBTITLE 1,Show sample of raw text
# Display first 3 parsed documents
sample_df = (
    spark.table("workspace.monsters.raw_text")
    .select(
        F.col("filename"),
        F.expr("LEFT(raw_text, 500)").alias("text_preview"),
        F.length("raw_text").alias("text_length"),
        F.col("parsed_at")
    )
    .orderBy("filename")
    .limit(3)
)

display(sample_df)

# COMMAND ----------

# DBTITLE 1,Verification
# MAGIC %md
# MAGIC ## Verification
# MAGIC
# MAGIC Let's verify the table schema and check for any parsing failures.

# COMMAND ----------

# DBTITLE 1,Check for empty or null raw_text
# Check if any documents failed to parse (null or empty text)
failed_df = (
    spark.table("workspace.monsters.raw_text")
    .select(
        F.col("filename"),
        F.when(F.col("raw_text").isNull(), F.lit("NULL"))
         .when(F.length("raw_text") == 0, F.lit("EMPTY"))
         .when(F.length("raw_text") < 50, F.lit("TOO_SHORT"))
         .otherwise(F.lit("OK"))
         .alias("status"),
        F.length("raw_text").alias("text_length")
    )
    .filter(
        F.col("raw_text").isNull() |
        (F.length("raw_text") == 0) |
        (F.length("raw_text") < 50)
    )
)

failed_count = failed_df.count()

if failed_count > 0:
    print(f"⚠️ WARNING: {failed_count} documents may have parsing issues:")
    display(failed_df)
else:
    print("✅ All documents parsed successfully with sufficient text!")

# COMMAND ----------

# DBTITLE 1,Next Steps
# MAGIC %md
# MAGIC ## Next Steps
# MAGIC
# MAGIC Now that we have raw text extracted from PDFs:
# MAGIC
# MAGIC 1. **Run notebook 03_extract_stats.py** to parse structured monster stats using `ai_extract()`
# MAGIC 2. The stats will be extracted into typed columns: name, lore, type, weakness, atk, def, spd, hp
# MAGIC 3. Results will be saved to `workspace.monsters.stats` table
# MAGIC
# MAGIC **Key difference**:  
# MAGIC * `ai_parse_document()` = unstructured text extraction (what we just did)
# MAGIC * `ai_extract()` = structured data extraction with JSON schema (next step)