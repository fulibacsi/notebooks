# Databricks notebook source
# DBTITLE 1,Upload Check - Verify PDFs in Volume
# MAGIC %md
# MAGIC # Upload Check - Verify Monster PDFs
# MAGIC
# MAGIC This notebook verifies that monster PDF files have been uploaded to the Unity Catalog Volume.
# MAGIC
# MAGIC **Expected location**: `/Volumes/workspace/monsters/dropzone/raw_pdfs/`
# MAGIC
# MAGIC We'll check:
# MAGIC * Total number of PDF files
# MAGIC * List of all filenames
# MAGIC * File size statistics
# MAGIC * Any missing or corrupted uploads

# COMMAND ----------

# DBTITLE 1,Set volume path
# Define the volume path where PDFs should be uploaded
volume_path = "/Volumes/workspace/monsters/dropzone/raw_pdfs/"
print(f"Checking for PDFs at: {volume_path}")

# COMMAND ----------

# DBTITLE 1,Read files using binaryFile format
from pyspark.sql import functions as F

# Read all PDF files from the volume using binaryFile format
# This reads the file metadata without loading full content into memory
files_df = spark.read.format("binaryFile").load(volume_path)

print(f"✓ Successfully accessed volume path")
print(f"Schema: {files_df.schema}")

# COMMAND ----------

# DBTITLE 1,Count total files
# Count total number of PDF files uploaded
total_files = files_df.count()

print(f"\n{'='*60}")
print(f"UPLOAD SUMMARY")
print(f"{'='*60}")
print(f"Total PDF files found: {total_files}")
print(f"{'='*60}\n")

if total_files == 0:
    print("⚠️ WARNING: No PDF files found!")
    print("Please upload monster PDFs to the volume before continuing.")
else:
    print(f"✓ {total_files} PDF files ready for processing")

# COMMAND ----------

# DBTITLE 1,File List
# MAGIC %md
# MAGIC ## File List
# MAGIC
# MAGIC Display all uploaded files with their sizes, sorted by filename.

# COMMAND ----------

# DBTITLE 1,List all files with sizes
# Extract filename from path and show file sizes
files_list = files_df.select(
    F.regexp_extract(F.col("path"), r"([^/]+\.pdf)$", 1).alias("filename"),
    F.col("path"),
    F.col("length").alias("size_bytes"),
    (F.col("length") / 1024).cast("decimal(10,2)").alias("size_kb")
).orderBy("filename")

# Display the file list
display(files_list)

# COMMAND ----------

# DBTITLE 1,Statistics
# MAGIC %md
# MAGIC ## File Size Statistics
# MAGIC
# MAGIC Aggregate statistics to identify any outliers or corrupted uploads.

# COMMAND ----------

# DBTITLE 1,Calculate aggregate stats
# Calculate min, max, average file sizes
stats_df = files_df.agg(
    F.count("*").alias("total_files"),
    F.min("length").alias("min_size_bytes"),
    F.max("length").alias("max_size_bytes"),
    F.avg("length").cast("decimal(10,2)").alias("avg_size_bytes"),
    (F.avg("length") / 1024).cast("decimal(10,2)").alias("avg_size_kb")
)

display(stats_df)

# COMMAND ----------

# DBTITLE 1,Validation checks
# Perform validation checks
stats = stats_df.collect()[0]

print("\nValidation Checks:")
print("="*60)

# Check 1: At least some files exist
if stats["total_files"] > 0:
    print(f"✓ Files found: {stats['total_files']}")
else:
    print("✗ No files found - upload PDFs before continuing!")

# Check 2: No suspiciously small files (likely corrupted)
min_size = stats["min_size_bytes"]
if min_size > 1000:  # At least 1KB
    print(f"✓ Minimum file size OK: {min_size} bytes")
else:
    print(f"⚠️ WARNING: Suspiciously small file detected: {min_size} bytes")
    print("  Some PDFs may be corrupted or empty.")

# Check 3: No suspiciously large files
max_size = stats["max_size_bytes"]
if max_size < 5_000_000:  # Less than 5MB
    print(f"✓ Maximum file size OK: {max_size} bytes ({max_size/1024:.0f} KB)")
else:
    print(f"⚠️ WARNING: Very large file detected: {max_size} bytes")
    print("  This may slow down processing.")

print("="*60)

if stats["total_files"] > 0 and min_size > 1000:
    print("\n✅ All checks passed! Ready to proceed to document parsing.")
else:
    print("\n⚠️ Please review warnings before continuing.")

# COMMAND ----------

# DBTITLE 1,Next Steps
# MAGIC %md
# MAGIC ## Next Steps
# MAGIC
# MAGIC If all validation checks passed:
# MAGIC 1. **Run notebook 02_parse_documents.py** to extract raw text from PDFs using `ai_parse_document()`
# MAGIC 2. The raw text will be saved to `workspace.monsters.raw_text` table
# MAGIC
# MAGIC If files are missing or corrupted:
# MAGIC 1. Check the upload location: `/Volumes/workspace/monsters/dropzone/raw_pdfs/`
# MAGIC 2. Re-generate PDFs using `data/seed_monsters/generate_monsters.py`
# MAGIC 3. Re-run this notebook to verify