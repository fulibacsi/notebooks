import os
import io
import base64

from databricks import sql
from databricks.sdk.core import Config
from databricks.sdk import WorkspaceClient

import streamlit as st
import pandas as pd


# Ensure environment variable is set correctly
assert os.getenv('DATABRICKS_WAREHOUSE_ID'), "DATABRICKS_WAREHOUSE_ID must be set in app.yaml."
w = WorkspaceClient()


def sqlQuery(query: str) -> pd.DataFrame:
    cfg = Config() # Pull environment variables for auth
    with sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{os.getenv('DATABRICKS_WAREHOUSE_ID')}",
        credentials_provider=lambda: cfg.authenticate
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall_arrow().to_pandas()


def parse_file(file_bytes):
    encoded_file = base64.b64encode(file_bytes).decode("utf-8")
        
    # Parse the PDF using ai_parse_document
    sql_parse = f"""
        SELECT ai_parse_document(
            unbase64('{encoded_file}'),
            MAP('version', '2.0')
        ) AS raw_text
    """
    results = sqlQuery(sql_parse)
    parsed = results.iloc[0]['raw_text']

    return parsed


def extract_stats(parsed_string):
    # Extract structured stats using ai_extract
    schema = """
    {
        "name": {"type": "string"},
        "lore": {"type": "string"},
        "type": {"type": "string"},
        "weakness": {"type": "string"},
        "atk": {"type": "integer"},
        "def": {"type": "integer"},
        "spd": {"type": "integer"},
        "hp": {"type": "integer"}
    }
    """
    
    sql_extract = f"""
        SELECT
            parsed:response:name:value::STRING AS name,
            parsed:response:lore:value::STRING AS lore,
            parsed:response:type:value::STRING AS type,
            parsed:response:weakness:value::STRING AS weakness,
            parsed:response:atk:value::INT AS atk,
            parsed:response:def:value::INT AS def,
            parsed:response:spd:value::INT AS spd,
            parsed:response:hp:value::INT AS hp
        FROM (
            SELECT ai_extract(
                {repr(parsed_string)},
                {repr(schema)},
                MAP('instructions', 'Extract monster stats from the card text')
            ) AS parsed
        )
    """
    
    extracted_df = sqlQuery(sql_extract)
    stats = extracted_df.iloc[0].to_dict()

    return stats


def process_file(uploaded_file):
    file_bytes = uploaded_file.read()
    parsed = parse_file(file_bytes)
    stats = extract_stats(parsed)
    return stats


st.set_page_config(layout="wide")

@st.cache_data(ttl=30)  # only re-query if it's been 30 seconds
def getData():
    return sqlQuery("select * from workspace.monsters.stats limit 5000")

data = getData()

st.header("TemuMon stat distribution :)")
col1, col2 = st.columns([3, 1])
with col1:
    st.scatter_chart(data=data, height=400, width=700, y="atk", x="def")
with col2:
    st.subheader("Analyse uploaded TemuMon")
    uploaded_file = st.file_uploader(label="Select file")
    st.write("## TemuMon stats")
    if st.button("Upload"):
        results = process_file(uploaded_file)
        st.write(results)
    

st.dataframe(data=data, height=600, use_container_width=True)
