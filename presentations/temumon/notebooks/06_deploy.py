# Databricks notebook source
# DBTITLE 1,Monster Battle Cards - Deployment
# MAGIC %md
# MAGIC # TemuMon - Deployment
# MAGIC
# MAGIC This notebook automates the deployment of:
# MAGIC 1. **Data Pipeline Job** - Runs notebooks 00-03 in sequence to process monster PDFs
# MAGIC 2. **Gradio App** - Deploys the battle app for end users
# MAGIC
# MAGIC ## Architecture
# MAGIC
# MAGIC **Data Pipeline (Job)**
# MAGIC - `00_setup` → Create catalog/schema/volume
# MAGIC - `01_upload_check` → Verify PDFs uploaded to volume
# MAGIC - `02_parse_documents` → Extract raw text with ai_parse_document()
# MAGIC - `03_extract_stats` → Parse structured stats with ai_extract()
# MAGIC
# MAGIC **Gradio App**
# MAGIC - File upload interface
# MAGIC - PDF parsing and stat extraction
# MAGIC - Battle engine + LLM narration
# MAGIC - Results display with winner stats
# MAGIC
# MAGIC This notebook uses the Databricks SDK to programmatically create and configure both components.

# COMMAND ----------

# DBTITLE 1,Prerequisites
# MAGIC %md
# MAGIC ## Prerequisites
# MAGIC
# MAGIC Before running this deployment:
# MAGIC 1. ✅ All notebooks (00-03) exist in `/Users/<your-username>/temumon/notebooks/`
# MAGIC 2. ✅ The app file exists at `/Users/<your-username>/temumon/app/temumon.py`
# MAGIC 3. ✅ Seed monster PDFs have been uploaded to `/Volumes/workspace/monsters/dropzone/raw_pdfs/`
# MAGIC 4. ✅ You have permissions to create jobs and apps in this workspace
# MAGIC
# MAGIC Let's verify these before proceeding.

# COMMAND ----------

# DBTITLE 1,Install dependencies
# Job name with timestamp to avoid conflicts
job_name = f"TemuMon - Data Pipeline"

print(f"Creating job: {job_name}")
print(f"Schedule: Daily at 8:00 AM (cron: 0 0 8 * * ? *)")
print(f"\nTask dependencies:")
print("  00_setup → 01_upload_check → 02_parse_documents → 03_extract_stats")

# COMMAND ----------

# DBTITLE 1,Import libraries and initialize SDK
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs
import os
import json
from datetime import datetime

# Initialize Databricks SDK client
w = WorkspaceClient()

# Get current user for path resolution
current_user = w.current_user.me().user_name
print(f"✓ Connected as: {current_user}")

# Define notebook base path
notebook_base_path = f"/Users/{current_user}/temumon/notebooks"
app_path = f"/Users/{current_user}/temumon/app/temumon.py"

print(f"✓ Notebook base path: {notebook_base_path}")
print(f"✓ App path: {app_path}")

# COMMAND ----------

# DBTITLE 1,Verify notebook files exist
# Verify all required notebooks exist
required_notebooks = [
    "00_setup",
    "01_upload_check",
    "02_parse_documents",
    "03_extract_stats"
]

print("Checking notebook files...")
missing = []

for nb in required_notebooks:
    nb_path = f"{notebook_base_path}/{nb}"
    try:
        w.workspace.get_status(nb_path)
        print(f"  ✓ {nb}")
    except Exception as e:
        print(f"  ✗ {nb} - NOT FOUND")
        missing.append(nb)

if missing:
    raise FileNotFoundError(f"Missing notebooks: {missing}. Please create them first.")

print("\n✓ All required notebooks found!")

# COMMAND ----------

# DBTITLE 1,Part 1: Create Data Pipeline Job
# MAGIC %md
# MAGIC ## Part 1: Create Data Pipeline Job
# MAGIC
# MAGIC We'll create a Databricks Job with 4 sequential tasks:
# MAGIC - Each task runs one notebook
# MAGIC - Tasks have dependencies (01 waits for 00, 02 waits for 01, etc.)
# MAGIC - Job runs on Serverless compute (no cluster config needed)
# MAGIC - **Schedule is PAUSED by default** — trigger manually via UI when needed
# MAGIC
# MAGIC ### Why Serverless?
# MAGIC - No cluster management overhead
# MAGIC - Auto-scales based on workload
# MAGIC - Cost-effective for small batch jobs
# MAGIC - Perfect for Free Edition workshops

# COMMAND ----------

# DBTITLE 1,Define job configuration
# Job name with timestamp to avoid conflicts
job_name = f"TemuMon - Data Pipeline"

print(f"Creating job: {job_name}")
print(f"Schedule: Daily at 8:00 AM (PAUSED - will not run automatically)")
print(f"\nTask dependencies:")
print("  00_setup → 01_upload_check → 02_parse_documents → 03_extract_stats")

# COMMAND ----------

# DBTITLE 1,Create job using Databricks SDK
# Define the job configuration
try:
    created_job = w.jobs.create(
        name=job_name,
        tasks=[
            jobs.Task(
                task_key="setup",
                description="Create catalog, schema, and volume",
                notebook_task=jobs.NotebookTask(
                    notebook_path=f"{notebook_base_path}/00_setup",
                    source=jobs.Source.WORKSPACE
                ),
                timeout_seconds=600  # 10 minutes
            ),
            jobs.Task(
                task_key="upload_check",
                description="Verify PDFs uploaded to volume",
                depends_on=[jobs.TaskDependency(task_key="setup")],
                notebook_task=jobs.NotebookTask(
                    notebook_path=f"{notebook_base_path}/01_upload_check",
                    source=jobs.Source.WORKSPACE
                ),
                timeout_seconds=600
            ),
            jobs.Task(
                task_key="parse_documents",
                description="Extract raw text with ai_parse_document",
                depends_on=[jobs.TaskDependency(task_key="upload_check")],
                notebook_task=jobs.NotebookTask(
                    notebook_path=f"{notebook_base_path}/02_parse_documents",
                    source=jobs.Source.WORKSPACE
                ),
                timeout_seconds=1800  # 30 minutes (AI functions can be slow)
            ),
            jobs.Task(
                task_key="extract_stats",
                description="Parse structured stats with ai_parse",
                depends_on=[jobs.TaskDependency(task_key="parse_documents")],
                notebook_task=jobs.NotebookTask(
                    notebook_path=f"{notebook_base_path}/03_extract_stats",
                    source=jobs.Source.WORKSPACE
                ),
                timeout_seconds=1800  # 30 minutes
            )
        ],
        schedule=jobs.CronSchedule(
            quartz_cron_expression="0 0 8 * * ? *",  # Daily at 8 AM
            timezone_id="America/Los_Angeles",
            pause_status=jobs.PauseStatus.PAUSED  # PAUSED - will not run automatically
        ),
        email_notifications=jobs.JobEmailNotifications(
            on_failure=[current_user],
            no_alert_for_skipped_runs=True
        ),
        max_concurrent_runs=1,  # Prevent overlapping runs
        timeout_seconds=7200  # 2 hours total job timeout
    )
    
    print(f"\n✓ Job created successfully!")
    print(f"  Job ID: {created_job.job_id}")
    print(f"  Job URL: {w.config.host}/#job/{created_job.job_id}")
    print(f"  Schedule status: PAUSED (will not run automatically)")
    
    # Store job ID for later reference
    job_id = created_job.job_id
    
except Exception as e:
    print(f"✗ Error creating job: {e}")
    print("\nTroubleshooting:")
    print("  - Check that you have permission to create jobs")
    print("  - Verify all notebook paths are correct")
    print("  - Try deleting any existing job with the same name")
    raise

# COMMAND ----------

# DBTITLE 1,Verify job creation
# Retrieve and display job details
try:
    job_details = w.jobs.get(job_id)
    
    print("Job Details:")
    print(f"  Name: {job_details.settings.name}")
    print(f"  Job ID: {job_details.job_id}")
    print(f"  Tasks: {len(job_details.settings.tasks)}")
    print(f"  Schedule: {job_details.settings.schedule.quartz_cron_expression}")
    print(f"  Timezone: {job_details.settings.schedule.timezone_id}")
    print(f"  Status: {job_details.settings.schedule.pause_status}")
    
    print("\nTask Configuration:")
    for task in job_details.settings.tasks:
        deps = ", ".join([d.task_key for d in task.depends_on]) if task.depends_on else "None"
        print(f"  • {task.task_key}")
        print(f"    - Notebook: {task.notebook_task.notebook_path}")
        print(f"    - Depends on: {deps}")
        print(f"    - Timeout: {task.timeout_seconds}s")
    
    print(f"\n✓ Job verification complete!")
    print(f"\nNext steps:")
    print(f"  1. View job: {w.config.host}/#job/{job_id}")
    print(f"  2. Trigger a test run manually via the UI")
    print(f"  3. Monitor the run to ensure all tasks complete successfully")
    
except Exception as e:
    print(f"✗ Error retrieving job: {e}")

# COMMAND ----------

# DBTITLE 1,Optional: Trigger test run
# Optionally trigger an immediate test run
# Uncomment to execute:

# try:
#     run = w.jobs.run_now(job_id)
#     print(f"✓ Test run triggered!")
#     print(f"  Run ID: {run.run_id}")
#     print(f"  Run URL: {w.config.host}/#job/{job_id}/run/{run.run_id}")
#     print(f"\nMonitor the run in the UI. This may take 10-30 minutes.")
# except Exception as e:
#     print(f"✗ Error triggering run: {e}")

print("To trigger a test run, uncomment the code above or use the UI.")
print(f"Job URL: {w.config.host}/#job/{job_id}")

# COMMAND ----------

# DBTITLE 1,Part 2: Deploy Gradio App
# MAGIC %md
# MAGIC ## Part 2: Deploy Streamlit App
# MAGIC
# MAGIC Databricks Apps let you deploy Python applications (like Streamlit, Gradio, Flask) that:
# MAGIC - Run continuously on serverless compute
# MAGIC - Are accessible via public URLs (no Databricks login required)
# MAGIC - Can read from Unity Catalog tables and volumes
# MAGIC - Auto-scale based on traffic
# MAGIC
# MAGIC ### Deployment Methods
# MAGIC
# MAGIC **Option A: UI Deployment (Recommended for Workshops)**
# MAGIC 1. Navigate to the Databricks workspace
# MAGIC 2. Click "Apps" in the left sidebar
# MAGIC 3. Click "Create App"
# MAGIC 4. Specify the app file path
# MAGIC 5. Configure settings and deploy
# MAGIC
# MAGIC **Option B: Databricks CLI (Programmatic)**
# MAGIC - Requires `databricks` CLI installed locally
# MAGIC - Good for CI/CD pipelines
# MAGIC - We'll provide the commands below

# COMMAND ----------

# DBTITLE 1,Verify app file exists
# Verify the app.py file exists and is valid
try:
    app_status = w.workspace.get_status(app_path)
    print(f"✓ App file found: {app_path}")
    print(f"  Object type: {app_status.object_type}")
    print(f"  Size: {app_status.size} bytes" if app_status.size else "  Size: Unknown")
    
    # Try to read the first few lines to verify it's a Streamlit app
    try:
        app_content = w.workspace.download(app_path).read().decode('utf-8')
        
        # Check for key indicators
        has_streamlit = 'streamlit' in app_content.lower()
        has_import = 'import streamlit' in app_content or 'import st' in app_content
        
        print(f"\nApp validation:")
        print(f"  • Contains 'streamlit': {'✓' if has_streamlit else '✗'}")
        print(f"  • Has Streamlit import: {'✓' if has_import else '✗'}")
        
        if has_streamlit and has_import:
            print(f"\n✓ App file looks valid!")
        else:
            print(f"\n⚠ Warning: App file may not be a valid Streamlit app")
            
    except Exception as e:
        print(f"\n⚠ Could not read app content: {e}")
    
except Exception as e:
    print(f"✗ App file not found: {app_path}")
    print(f"  Error: {e}")
    print(f"\nPlease create the app file first before deploying.")
    raise

# COMMAND ----------

# DBTITLE 1,UI Deployment Instructions
# MAGIC %md
# MAGIC ### Option A: Deploy via Databricks UI
# MAGIC
# MAGIC **Step-by-step instructions:**
# MAGIC
# MAGIC 1. **Navigate to Apps**
# MAGIC    - Click "Apps" in the left sidebar of your Databricks workspace
# MAGIC    - Or go directly to: `<your-workspace-url>/apps`
# MAGIC
# MAGIC 2. **Create New App**
# MAGIC    - Click "Create App" button (top right)
# MAGIC    - App name: `temumon`
# MAGIC    - Description: `Workshop app for monster battle simulation`
# MAGIC
# MAGIC 3. **Configure App**
# MAGIC    - **Source file**: `/Users/<your-username>/temumon/app/temumon.py`
# MAGIC    - **Compute**: Select "Serverless" (recommended)
# MAGIC    - **Environment**: Default Python environment
# MAGIC    - **Dependencies**: The app should include a requirements.txt or install deps in the app.py
# MAGIC
# MAGIC 4. **Deploy**
# MAGIC    - Click "Deploy"
# MAGIC    - Wait 3-5 minutes for deployment
# MAGIC    - Status will change from "Starting" → "Running"
# MAGIC
# MAGIC 5. **Access the App**
# MAGIC    - Copy the app URL (e.g., `https://<workspace>.cloud.databricks.com/apps/temumon`)
# MAGIC    - Share with workshop participants
# MAGIC    - No Databricks login required for public apps!
# MAGIC
# MAGIC **Troubleshooting:**
# MAGIC - If deployment fails, check the app logs in the UI
# MAGIC - Ensure `streamlit` is installed in the app environment
# MAGIC - Verify the app has `st.write()` commands and proper Streamlit structure

# COMMAND ----------

# DBTITLE 1,CLI Deployment Instructions
# MAGIC %md
# MAGIC ### Option B: Deploy via Databricks CLI
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC ```bash
# MAGIC # Install Databricks CLI
# MAGIC pip install databricks-cli
# MAGIC
# MAGIC # Configure authentication
# MAGIC databricks configure --token
# MAGIC # Enter your workspace URL and personal access token
# MAGIC ```
# MAGIC
# MAGIC **Deployment commands:**
# MAGIC ```bash
# MAGIC # Create app configuration file (app.yaml)
# MAGIC cat > app.yaml << EOF
# MAGIC name: temumon
# MAGIC description: Workshop app for monster battle simulation
# MAGIC source_file: /Users/<your-username>/temumon/app/temumon.py
# MAGIC compute:
# MAGIC   type: serverless
# MAGIC EOF
# MAGIC
# MAGIC # Deploy the app
# MAGIC databricks apps create --config app.yaml
# MAGIC
# MAGIC # Check deployment status
# MAGIC databricks apps get temumon
# MAGIC
# MAGIC # View logs
# MAGIC databricks apps logs temumon --follow
# MAGIC ```
# MAGIC
# MAGIC **Note:** CLI deployment is more complex and requires local setup. For workshops, we recommend the UI approach.

# COMMAND ----------

# DBTITLE 1,Generate deployment summary
# Generate a summary for workshop participants
print("="*70)
print("TEMUMON - DEPLOYMENT SUMMARY")
print("="*70)

print("\n📊 DATA PIPELINE JOB")
print(f"  Status: ✓ Created")
print(f"  Job ID: {job_id}")
print(f"  Schedule: Daily at 8:00 AM Pacific (PAUSED)")
print(f"  Job URL: {w.config.host}/#job/{job_id}")
print(f"  ⚠ Schedule is PAUSED - trigger runs manually when needed")

print("\n🎮 STREAMLIT APP")
print(f"  Status: Ready for deployment")
print(f"  App file: {app_path}")
print(f"  Deployment method: Use Databricks UI (Apps → Create App)")
print(f"  Workspace apps URL: {w.config.host}/apps")

print("\n📋 NEXT STEPS")
print("  1. Trigger a test job run to populate the monsters.stats table")
print(f"     → Visit: {w.config.host}/#job/{job_id}")
print(f"     → Click 'Run Now' button (schedule is paused, so manual trigger required)")
print("\n  2. Deploy the Streamlit app via UI (see instructions above)")
print(f"     → Visit: {w.config.host}/apps")
print("     → Create App → Point to app/temumon.py")
print("\n  3. Share the app URL with workshop participants")
print("     → They can upload monster PDFs and battle them!")

print("\n⚙️  MAINTENANCE")
print("  • Schedule is PAUSED by default - no automatic runs")
print("  • To enable automatic runs: Go to Job UI → Edit Schedule → Change to UNPAUSED")
print("  • Trigger manually when needed via 'Run Now' button")
print("  • Monitor job runs in the UI for failures")
print("  • Check app logs if users report issues")

print("\n" + "="*70)
print("Deployment configuration complete! 🚀")
print("="*70)