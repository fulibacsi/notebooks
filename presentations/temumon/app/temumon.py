"""Monster Battle Cards - Streamlit App

Upload a monster PDF and find out which existing monster defeats it!
"""
import os
import re
from databricks.sdk import WorkspaceClient

import streamlit as st
import pandas as pd

from utils import slugify, parse_file, extract_stats, load_roster
from battle import find_winner, narrate_battle
from pdf_generator import generate_card_pdf

TYPE_ADVANTAGE = {
    "Fire": "Ice",
    "Ice": "Earth",
    "Earth": "Storm",
    "Storm": "Shadow",
    "Shadow": "Light",
    "Light": "Void",
    "Void": "Poison",
    "Poison": "Fire",
}

# Ensure environment variable is set
assert os.getenv('DATABRICKS_WAREHOUSE_ID'), "DATABRICKS_WAREHOUSE_ID must be set in app.yaml."
w = WorkspaceClient()


def process_uploaded_pdf(uploaded_file):
    """Process uploaded PDF and run battle simulation."""
    try:
        # Parse PDF
        with st.spinner("📄 Parsing uploaded PDF..."):
            file_bytes = uploaded_file.read()
            parsed = parse_file(file_bytes)
        
        # Extract stats
        with st.spinner("🔍 Extracting monster stats..."):
            challenger = extract_stats(parsed)
        
        # Display extracted stats before battle (transposed, no header)
        st.subheader("📊 Extracted Challenger Stats")
        challenger_df = pd.DataFrame([challenger]).T
        challenger_df.columns = ['Value']
        st.table(challenger_df)
        
        # Find best opponent
        challenger_name = challenger.get('name', 'Unknown')
        with st.spinner(f"⚔️ Finding the best opponent for {challenger_name}..."):
            roster_df = load_roster()
            roster = roster_df.to_dict('records')
            battle_result, best_opponent = find_winner(challenger, roster)
        
        # Generate narrative
        with st.spinner("📖 Generating battle narrative..."):
            narrative = narrate_battle(battle_result)
        
        return challenger, battle_result, best_opponent, narrative
        
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None, None, None, None


# ============================================================================
# Streamlit UI Configuration
# ============================================================================

st.set_page_config(
    page_title="Monster Battle Cards",
    page_icon="⚔️",
    layout="wide"
)

# Header
st.title("⚔️ Monster Battle Cards")
st.markdown("Upload a monster PDF and find out which existing monster defeats it!")

# Create tabs
tab1, tab2 = st.tabs(["🎮 Battle Arena", "🎨 Create Monster"])

# ============================================================================
# Tab 1: Battle Arena
# ============================================================================

with tab1:
    # Main content area
    col1, col2 = st.columns([1, 2])

    # Left Column: File Upload
    with col1:
        st.subheader("📤 Upload Challenger")
        uploaded_file = st.file_uploader(
            "Select Monster PDF",
            type=['pdf'],
            help="Upload a monster card PDF to challenge the roster",
            key="battle_upload"
        )
        
        battle_btn = st.button("🎮 BATTLE!", type="primary", use_container_width=True)
        
        if battle_btn and uploaded_file:
            result = process_uploaded_pdf(uploaded_file)
            
            if result[0] is not None:
                challenger, battle_result, best_opponent, narrative = result
                # Store in session state for display
                st.session_state['challenger'] = challenger
                st.session_state['battle_result'] = battle_result
                st.session_state['best_opponent'] = best_opponent
                st.session_state['narrative'] = narrative

    # Right Column: Battle Results
    with col2:
        if 'battle_result' in st.session_state:
            st.subheader("🏆 Battle Results")
            
            # Get stored results
            battle_result = st.session_state['battle_result']
            challenger = st.session_state['challenger']
            winner = battle_result['winner']
            loser = battle_result['loser']
            
            # Winner announcement
            winner_name = winner.get('name', 'Unknown')
            winner_hp_pct = battle_result['score']
            total_rounds = battle_result['total_rounds']
            
            st.markdown(f"""
            <div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; margin-bottom: 20px;">
                <h2 style="margin: 0; color: white;">🏆 {winner_name} WINS!</h2>
                <p style="margin: 5px 0; font-style: italic; opacity: 0.9;">{winner.get('lore', '')}</p>
                <p style="margin: 5px 0; font-size: 14px; opacity: 0.8;">Victory in {total_rounds} rounds with {winner_hp_pct:.0f}% HP remaining</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Stats comparison
            col_a, col_b = st.columns(2)
            
            challenger_name = challenger.get('name', 'Unknown')
            opponent_name = st.session_state['best_opponent'].get('name', 'Unknown')
            
            with col_a:
                st.markdown(f"**Challenger: {challenger_name}**")
                st.markdown(f"Type: `{challenger['type']}` | Weakness: `{challenger['weakness']}`")
                stats_df = pd.DataFrame({
                    'Stat': ['ATK', 'DEF', 'SPD', 'HP'],
                    'Value': [challenger['atk'], challenger['def'], challenger['spd'], challenger['hp']]
                })
                st.dataframe(stats_df, hide_index=True, use_container_width=True)
            
            with col_b:
                opponent = st.session_state['best_opponent']
                st.markdown(f"**Opponent: {opponent_name}**")
                st.markdown(f"Type: `{opponent['type']}` | Weakness: `{opponent['weakness']}`")
                stats_df = pd.DataFrame({
                    'Stat': ['ATK', 'DEF', 'SPD', 'HP'],
                    'Value': [opponent['atk'], opponent['def'], opponent['spd'], opponent['hp']]
                })
                st.dataframe(stats_df, hide_index=True, use_container_width=True)
            
            # Battle narrative
            st.markdown("### 📖 Battle Narrative")
            st.info(st.session_state['narrative'])
            
            # Battle history (expandable)
            with st.expander("📜 View Battle History"):
                for round_info in battle_result['history']:
                    st.markdown(f"**Round {round_info['round']}:**")
                    for event in round_info['events']:
                        hp_pct = (event['defender_hp_after'] / event['defender_max_hp'] * 100) if event['defender_max_hp'] > 0 else 0
                        st.text(f"  {event['attacker']} → {event['defender']}: {event['damage']} damage "
                               f"({event['defender_hp_after']}/{event['defender_max_hp']} HP, {hp_pct:.0f}%)")
        
        else:
            st.info("👆 Upload a monster PDF and click BATTLE! to see results")

    # Monster Roster Display
    st.markdown("---")
    st.subheader("📋 Monster Roster")

    with st.expander("View All Monsters", expanded=False):
        roster_df = load_roster()
        
        # Add filters
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            type_filter = st.multiselect(
                "Filter by Type",
                options=roster_df['type'].unique(),
                default=[],
                key="battle_type_filter"
            )
        with filter_col2:
            search = st.text_input("Search by name", "", key="battle_search")
        
        # Apply filters
        filtered_df = roster_df.copy()
        if type_filter:
            filtered_df = filtered_df[filtered_df['type'].isin(type_filter)]
        if search:
            filtered_df = filtered_df[filtered_df['name'].str.contains(search, case=False, na=False)]
        
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400,
            column_config={
                "atk": st.column_config.NumberColumn("ATK", format="%d"),
                "def": st.column_config.NumberColumn("DEF", format="%d"),
                "spd": st.column_config.NumberColumn("SPD", format="%d"),
                "hp": st.column_config.NumberColumn("HP", format="%d"),
            }
        )
        
        st.caption(f"Showing {len(filtered_df)} of {len(roster_df)} monsters")

# ============================================================================
# Tab 2: Create Monster
# ============================================================================

with tab2:
    st.markdown("### 🎨 Design Your Own Monster")
    st.markdown("Create a custom monster card and download it as a PDF!")
    
    # Input form
    col_left, col_right = st.columns(2)
    
    with col_left:
        monster_name = st.text_input(
            "Monster Name*",
            placeholder="e.g., Sparkzilla",
            help="Choose a unique name for your monster"
        )
        
        monster_lore = st.text_area(
            "Lore*",
            placeholder="A fierce creature that roams the electric plains...",
            help="One-sentence flavor text describing your monster",
            height=80
        )
        
        type_options = ["Fire", "Ice", "Shadow", "Storm", "Earth", "Poison", "Light", "Void"]
        
        monster_type = st.selectbox(
            "Type*",
            options=type_options,
            help="Choose your monster's element type",
            key="monster_type_selector"
        )
        
        # Auto-update weakness when type changes, but allow manual override
        # Initialize session state for tracking type changes
        if 'last_selected_type' not in st.session_state:
            st.session_state['last_selected_type'] = monster_type
            st.session_state['auto_weakness'] = TYPE_ADVANTAGE.get(monster_type, "Fire")
        
        # Check if type changed
        if st.session_state['last_selected_type'] != monster_type:
            st.session_state['last_selected_type'] = monster_type
            st.session_state['auto_weakness'] = TYPE_ADVANTAGE.get(monster_type, "Fire")
        
        # Get the index of the auto-selected weakness
        auto_weakness = st.session_state['auto_weakness']
        weakness_index = type_options.index(auto_weakness) if auto_weakness in type_options else 0
        
        monster_weakness = st.selectbox(
            "Weakness*",
            options=type_options,
            index=weakness_index,
            help="Auto-selected based on type advantage, but you can change it"
        )
    
    with col_right:
        st.markdown("**Stats** (1-100)")
        
        monster_atk = st.slider("Attack (ATK)", 1, 100, 50, help="Offensive power")
        monster_def = st.slider("Defense (DEF)", 1, 100, 50, help="Defensive capability")
        monster_spd = st.slider("Speed (SPD)", 1, 100, 50, help="How fast your monster is")
        monster_hp = st.slider("Hit Points (HP)", 1, 100, 50, help="Health points")
        
        # Show total stats
        total_stats = monster_atk + monster_def + monster_spd + monster_hp
        st.metric("Total Stats", f"{total_stats} / 400")
    
    # Generate button
    st.markdown("---")
    
    generate_btn = st.button("🎨 Generate PDF Card", type="primary", use_container_width=True)
    
    if generate_btn:
        # Validate inputs
        if not monster_name or not monster_lore:
            st.error("⚠️ Please fill in all required fields (Name and Lore)")
        else:
            with st.spinner("✨ Generating your monster card..."):
                # Create monster dictionary
                custom_monster = {
                    'name': monster_name,
                    'lore': monster_lore,
                    'type': monster_type,
                    'weakness': monster_weakness,
                    'atk': monster_atk,
                    'def': monster_def,
                    'spd': monster_spd,
                    'hp': monster_hp
                }
                
                # Generate PDF
                try:
                    pdf_bytes = generate_card_pdf(custom_monster)
                    
                    # Store in session state
                    st.session_state['custom_monster'] = custom_monster
                    st.session_state['custom_pdf'] = pdf_bytes
                    
                    st.success("✅ Monster card generated successfully!")
                    
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
    
    # Display preview and download button
    if 'custom_monster' in st.session_state and 'custom_pdf' in st.session_state:
        st.markdown("---")
        st.markdown("### 🎉 Your Monster Card is Ready!")
        
        # Preview stats
        preview_col1, preview_col2 = st.columns(2)
        
        with preview_col1:
            st.markdown("**Monster Details:**")
            custom = st.session_state['custom_monster']
            st.markdown(f"**Name:** {custom['name']}")
            st.markdown(f"**Type:** `{custom['type']}` | **Weakness:** `{custom['weakness']}`")
            st.markdown(f"*{custom['lore']}*")
        
        with preview_col2:
            st.markdown("**Stats:**")
            stats_preview = pd.DataFrame({
                'Stat': ['ATK', 'DEF', 'SPD', 'HP'],
                'Value': [custom['atk'], custom['def'], custom['spd'], custom['hp']]
            })
            st.dataframe(stats_preview, hide_index=True, use_container_width=True)
        
        # Download button
        filename = f"{slugify(custom['name'])}.pdf"
        st.download_button(
            label="📥 Download PDF Card",
            data=st.session_state['custom_pdf'],
            file_name=filename,
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
