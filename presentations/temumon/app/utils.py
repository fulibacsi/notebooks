"""Utility functions for Monster Battle Cards app.

Handles SQL queries, AI-powered PDF parsing, and data loading.
"""
import os
import re
import base64
from typing import Dict

from databricks import sql
from databricks.sdk.core import Config

import pandas as pd
import streamlit as st


def slugify(name: str) -> str:
    """Convert monster name to filename-safe slug."""
    return re.sub(r'[^\w\s-]', '', name.lower()).replace(' ', '-')


def sqlQuery(query: str) -> pd.DataFrame:
    """Execute SQL query using warehouse."""
    cfg = Config()
    with sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{os.getenv('DATABRICKS_WAREHOUSE_ID')}",
        credentials_provider=lambda: cfg.authenticate
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall_arrow().to_pandas()


def parse_file(file_bytes: bytes) -> str:
    """Parse PDF using ai_parse_document.
    
    Args:
        file_bytes: Raw PDF file bytes
        
    Returns:
        Extracted text content from the PDF
    """
    encoded_file = base64.b64encode(file_bytes).decode("utf-8")
    
    sql_parse = f"""
        SELECT ai_parse_document(
            unbase64('{encoded_file}'),
            MAP('version', '2.0')
        ) AS raw_text
    """
    results = sqlQuery(sql_parse)
    return results.iloc[0]['raw_text']


def extract_stats(parsed_string: str) -> Dict:
    """Extract structured stats using ai_extract.
    
    Args:
        parsed_string: Raw text extracted from PDF
        
    Returns:
        Dictionary with monster stats (name, lore, type, weakness, atk, def, spd, hp)
    """
    schema = '["name", "lore", "type", "weakness", "atk", "def", "spd", "hp"]'
    
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
    return extracted_df.iloc[0].to_dict()


@st.cache_data(ttl=300)
def load_roster() -> pd.DataFrame:
    """Load all monsters from the stats table.
    
    Returns:
        DataFrame with all monsters and their stats
    """
    return sqlQuery("SELECT name, lore, type, weakness, atk, def, spd, hp FROM workspace.monsters.stats ORDER BY name")
