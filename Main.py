import os
from dotenv import load_dotenv
from pathlib import Path
env_path = "/Users/arvind/Downloads/VS CODE-Files/Cricbuzz project /_env"
load_dotenv(dotenv_path=env_path)
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

import streamlit as st
import mysql.connector
import pandas as pd
import os
import requests
import math
import re

# 📂 Folder where your pickle files are stored
DATA_DIR = "/Users/arvind/Downloads/VS CODE-Files/Cricbuzz project /Data"

# ✅ SQL Questions list
questions = [
    "1. All players who represent India",
    "2. Cricket matches that were played in the last Few days",
    "3. List the top 10 highest run scorers in ODI cricket",
    "4. Cricket grounds with a seating capacity greater than 30,000",
    "5. Matches each team has won, team name and total number of wins and teams with the most wins first",
    "6. Players role and count of players for each role.",
    "7. Highest individual batting score achieved in each cricket formatand the highest score for that format.",
    "8. Cricket series- started 2024 and include series name, host country, match type, start date, and total number of matches planned",
    "9. All-rounder players with more than 1000 runs and 50 wickets. Display player name, total runs, total wickets, and most played format.",
    "10. Last 20 completed matches. Show match description, both team names, winning team, victory margin, victory type (runs/wickets), and venue name. Most recent first.",
    "11. Compare each player's performance across different formats. Show total runs in Test, ODI, T20I and overall batting average for players who played at least 2 formats.",
    "12. Analyze international teams' performance home vs away. Count wins for each team in home and away matches.",
    "13. Identify batting partnerships where two consecutive batsmen scored 100+ runs in same innings. Show both player names, combined runs, and innings number.",
    "14. Examine bowling performance at different venues. For bowlers with ≥3 matches at same venue and ≥4 overs per match, calculate avg economy rate, total wickets, and matches played.",
    "15. Identify players performing well in close matches (<50 runs or <5 wickets). Calculate average runs, total close matches played, and matches won when batting.",
    "16. Track players' batting performance over years since 2020. Show avg runs per match and avg strike rate per year for players with ≥5 matches in a year.",
    "17. Analyze toss advantage. Calculate % of matches won by toss-winning team, broken down by toss decision (bat first/bowl first).",
    "18. Most economical bowlers in ODI and T20. Calculate overall economy rate and total wickets for bowlers with ≥10 matches and ≥2 overs per match on avg.",
    "19. Most consistent batsmen since 2022. Calculate avg runs and std deviation for players with ≥10 balls per innings. Lower std deviation = more consistent.",
    "20. Matches played and batting averages per player across formats. Show Test, ODI, T20 match counts and respective batting averages for players with ≥20 total matches.",
    "21_1. Comprehensive player ranking combining batting, bowling, and fielding performance. Test Score.",
    "21_2. Comprehensive player ranking combining batting, bowling, and fielding performance. ODI Score.",
    "21_3. Comprehensive player ranking combining batting, bowling, and fielding performance. T20 Score.",
    "21_4. Comprehensive player ranking combining batting, bowling, and fielding performance. IPL Score.",
    "22_1. Head-to-head match analysis. For team pairs with ≥5 matches in last 3 years",
    "22_2. Venue analysis. For team pairs with ≥5 matches in last 3 years",
    "23. Recent player form analysis. For each player's last 10 batting performances, calculate avg runs in last 5 vs last 10 matches, recent strike rate trends, #scores above 50, consistency score, categorize form.",
    "24. Study successful batting partnerships. For pairs batting consecutively ≥5 times, calculate avg partnership runs, count of 50+ partnerships, highest partnership, success rate, rank best combinations.",
    "25. Time-series analysis of player performance evolution. Track quarterly avg runs & strike rate, compare with previous quarter, identify trends, categorize career phase. Include players with ≥6 quarters and ≥3 matches per quarter."
]

# ✅ Build pickle_dict properly
pickle_dict = {}
for q in questions:
    q_num = q.split(".")[0]
    base_num = q_num.split("_")[0]
    pickle_dict[q] = {}
    for candidate in [q_num, base_num]:
        for suffix in ["", "_test", "_odi", "_t20", "_ipl", "_1", "_2"]:
            filename = f"dfqn_{candidate}{suffix}.pkl"
            filepath = os.path.join(DATA_DIR, filename)
            if os.path.exists(filepath):
                key_name = suffix.replace("_", "") if suffix != "" else "base"
                pickle_dict[q][key_name] = filepath

# --- DB CONNECTION ---
def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,  
        database=DB_NAME
    )

# ----------------- DB helper functions -----------------
def fetch_players():
    conn = get_connection()
    try:
        query = """
        SELECT 
            player_id,
            name AS player_name,
            playing_role,
            battingstyle,
            bowlingstyle
        FROM all_players_role_details
        WHERE team_id = 2
        ORDER BY player_id;
        """
        df = pd.read_sql(query, conn)
    finally:
        conn.close()
    return df

def get_next_player_id():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COALESCE(MAX(player_id), 0) + 1 FROM all_players_role_details WHERE team_id = 2")
        row = cursor.fetchone()
        return int(row[0]) if row and row[0] is not None else 1
    finally:
        cursor.close()
        conn.close()

def add_player(player_id, name, role, battingstyle, bowlingstyle):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO all_players_role_details
            (player_id, name, playing_role, battingstyle, bowlingstyle, team_id)
            VALUES (%s, %s, %s, %s, %s, 2)
        """, (player_id, name, role, battingstyle, bowlingstyle))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def update_player(player_id, role, battingstyle, bowlingstyle):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE all_players_role_details
            SET playing_role=%s, battingstyle=%s, bowlingstyle=%s
            WHERE player_id=%s AND team_id=2
        """, (role, battingstyle, bowlingstyle, player_id))
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()

def delete_player_by_name(player_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM all_players_role_details
            WHERE name = %s AND team_id = 2
        """, (player_name,))
        affected = cursor.rowcount
        conn.commit()
        return affected
    finally:
        cursor.close()
        conn.close()

# ----------------------------
# 1️⃣ Functions with caching
# ----------------------------
url_matches = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
headers = {
        "x-rapidapi-key": "b028e64c8cmshfae4422be773909p1d30c5jsnbe85b8e5c9a1",  
        "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
    }

@st.cache_data(ttl=60)  # cache for 60 seconds
def fetch_live_matches():
        response = requests.get(url_matches, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()

@st.cache_data(ttl=60)
def fetch_scorecard(match_id):
        url_score = f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}/scard"
        headers = {
        "x-rapidapi-key": "b028e64c8cmshfae4422be773909p1d30c5jsnbe85b8e5c9a1",  
        "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
        }
        res = requests.get(url_score, headers=headers, timeout=15)
        res.raise_for_status()
        return res.json()

# 🎨 Sidebar navigation
st.sidebar.title("🏏 Cricket Dashboard")
page = st.sidebar.radio(
    "Choose a page:",
    [
        "🏠 Home Page",
        "📡 Live Match Page",
        "👤 Players Stat",
        "📊 SQL Queries & Analytics Page",
        "✍️ CRUD Operations Page"
    ]
)

# -------------------- HOME PAGE --------------------
if page == "🏠 Home Page":
    st.title("🏠 Cricket SQL Analytics Project")
    st.write("""
    Welcome to the Cricket SQL Analytics Dashboard!  

    ### 🔧 Tools Used
    - Streamlit
    - MySQL
    - Python (pandas, mysql.connector)
    - Cricbuzz API (for live data)

    ### 📌 Features
    - Live match updates  
    - Top player stats  
    - 25+ SQL queries & analytics  
    - CRUD operations on cricket data

    Use the **sidebar** to navigate between sections.
    """)

# -------------------- LIVE MATCH PAGE --------------------
elif page == "📡 Live Match Page":
    st.title("📡 Live Match Updates")
    try:
        data = fetch_live_matches()
        matches = []
        match_id_list = []
        match_info_map = {}

        for t in data.get("typeMatches", []):
            for sm in t.get("seriesMatches", []):
                if 'seriesAdWrapper' in sm:
                    for m in sm['seriesAdWrapper'].get("matches", []):
                        match_info = m['matchInfo']
                        team1 = match_info.get("team1", {}).get("teamName", "Team 1")
                        team2 = match_info.get("team2", {}).get("teamName", "Team 2")
                        match_desc = match_info.get("matchDesc", "")
                        title = f"🏏 {team1} vs {team2} - {match_desc}"
                        matches.append(title)
                        match_id_list.append(int(match_info.get("matchId")))

                        # store extra info
                        venue = match_info.get("venueInfo", {}).get("ground", "N/A")
                        city = match_info.get("venueInfo", {}).get("city", "N/A")
                        series_name = match_info.get("seriesName", "N/A")
                        match_format = match_info.get("matchFormat", "N/A")
                        match_info_map[int(match_info.get("matchId"))] = {
                            "venue": venue,
                            "city": city,
                            "series": series_name,
                            "format": match_format
                        }

        if not matches:
            st.warning("⚠ No live matches available right now.")
        else:
            selected_match = st.selectbox("Select a match to see details:", matches, key="match_select")
            selected_index = matches.index(selected_match)
            selected_match_id = match_id_list[selected_index]
            info = match_info_map[selected_match_id]

            st.markdown("---")
            st.subheader(f"🏏 {info['series']}")
            st.caption(f"📍 Venue : {info['venue']}, {info['city']} | Format: {info['format']}")

            match_data = fetch_scorecard(selected_match_id)
            scorecards = match_data.get("scorecard", [])

            for inn in scorecards:
                bat_team = inn.get("batteamname", "N/A")
                runs = inn.get("score", "N/A")
                wickets = inn.get("wickets", "N/A")
                overs = inn.get("overs", "N/A")
                runrate = inn.get("runrate", "N/A")
                extras_total = inn.get("extras", {}).get("total", "N/A")
                powerplay_runs = inn.get("pp", {}).get("powerplay", [{"run": "N/A"}])[0].get("run", "N/A")

                # --- Unique widget keys ---
                btn_batsmen_key = f"btn_batsmen_{selected_match_id}_{bat_team}"
                btn_bowlers_key = f"btn_bowlers_{selected_match_id}_{bat_team}"
                btn_partnerships_key = f"btn_partnerships_{selected_match_id}_{bat_team}"

                # --- Unique session_state flags ---
                flag_batsmen_key = f"flag_batsmen_{selected_match_id}_{bat_team}"
                flag_bowlers_key = f"flag_bowlers_{selected_match_id}_{bat_team}"
                flag_partnerships_key = f"flag_partnerships_{selected_match_id}_{bat_team}"

                # --- Display innings info ---
                st.markdown(f"### 🏏 {bat_team} Innings")
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                col1.metric("Runs", runs)
                col2.metric("Wickets", wickets)
                col3.metric("Overs", overs)
                col4.metric("Run Rate", runrate)
                col5.metric("Extras", extras_total)
                col6.metric("PP Runs", powerplay_runs)

                # --- Toggle buttons ---
                button_col1, button_col2, button_col3 = st.columns(3)
                with button_col1:
                    if st.button("🏏 Toggle Batsmen", key=btn_batsmen_key):
                        st.session_state[flag_batsmen_key] = not st.session_state.get(flag_batsmen_key, False)

                with button_col2:
                    if st.button("🎯 Toggle Bowlers", key=btn_bowlers_key):
                        st.session_state[flag_bowlers_key] = not st.session_state.get(flag_bowlers_key, False)

                with button_col3:
                    if st.button("🤝 Toggle Partnerships", key=btn_partnerships_key):
                        st.session_state[flag_partnerships_key] = not st.session_state.get(flag_partnerships_key, False)

                # --- Show/hide sections ---
                if st.session_state.get(flag_batsmen_key, False):
                    batsmen_data = [
                        [
                            b.get("name", "N/A"),
                            b.get("runs", "N/A"),
                            b.get("balls", "N/A"),
                            b.get("fours", "N/A"),
                            b.get("sixes", "N/A"),
                            b.get("strkrate", "N/A"),
                            b.get("outdec", "N/A")
                        ]
                        for b in inn.get("batsman", [])
                    ]
                    if batsmen_data:
                        st.markdown("#### 🏏 Batsmen")
                        st.table(pd.DataFrame(
                            batsmen_data,
                            columns=["Batsman", "R", "B", "4s", "6s", "SR", "Status"]
                        ))

                if st.session_state.get(flag_bowlers_key, False):
                    bowlers_data = [
                        [
                            b.get("name", "N/A"),
                            b.get("overs", "N/A"),
                            b.get("maidens", "N/A"),
                            b.get("runs", "N/A"),
                            b.get("wickets", "N/A"),
                            b.get("economy", "N/A")
                        ]
                        for b in inn.get("bowler", [])
                    ]
                    if bowlers_data:
                        st.markdown("#### 🎯 Bowlers")
                        st.table(pd.DataFrame(
                            bowlers_data,
                            columns=["Bowler", "O", "M", "R", "W", "Econ"]
                        ))

                if st.session_state.get(flag_partnerships_key, False):
                    partnerships = [
                        [
                            p.get("bat1name", "N/A"),
                            p.get("bat2name", "N/A"),
                            p.get("totalruns", "N/A"),
                            p.get("totalballs", "N/A")
                        ]
                        for p in inn.get("partnership", {}).get("partnership", [])
                    ]
                    if partnerships:
                        st.markdown("#### 🤝 Partnerships")
                        st.table(pd.DataFrame(
                            partnerships,
                            columns=["Batsman 1", "Batsman 2", "Runs", "Balls"]
                        ))
    except Exception as e:
        st.error(f"⚡ Error: {e}")


# -------------------- PLAYER STAT PAGE --------------------
elif page == "👤 Players Stat":
    st.title("👤 Cricket Player Profile & Stats")
    ## --- Player Search Box ---
    search_name = st.text_input("🔍 Search for a player by name:")

    if search_name:
        # --- DB CONNECTION ---
        def get_connection():
            return mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,  
                database=DB_NAME
            )

        def load_player_data():
            conn = get_connection()
            players_info = pd.read_sql("SELECT * FROM players_get_info_1", conn)
            players_bowling = pd.read_sql("SELECT * FROM players_bowling", conn)
            players_batting = pd.read_sql("SELECT * FROM players_batting", conn)
            conn.close()
            return players_info, players_bowling, players_batting

        players_info, players_bowling, players_batting = load_player_data()

        # Filter players by name
        filtered_players = players_info[players_info['name'].str.contains(search_name, case=False, na=False)]
        if filtered_players.empty:
            st.info("🔔 No players match that name. Try again!")
        else:
            player_selected = st.selectbox("🎯 Choose a player", filtered_players['name'].tolist())
            if player_selected:
                player_data = filtered_players[filtered_players['name'] == player_selected].iloc[0]

                # --- Helper function to handle NaN ---
                def display_value(val):
                    if val is None or (isinstance(val, float) and math.isnan(val)):
                        return " - "
                    return val

                st.subheader(f"*{display_value(player_data['name'])} — Profile Overview*")

                # --- Tabs for profile & stats ---
                tab1, tab2, tab3 = st.tabs(["*🧾 Profile", "🏏 Batting", "⚾ Bowling*"])

                # --- Player Profile ---
                with tab1:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"*Player ID:* {display_value(player_data.get('player_id'))}")
                        st.markdown(f"*Role:* {display_value(player_data.get('role'))}")
                        st.markdown(f"*Batting Style:* {display_value(player_data.get('bat'))}")
                        st.markdown(f"*Bowling Style:* {display_value(player_data.get('bowl'))}")
                        st.markdown(f"*International Team:* {display_value(player_data.get('intlTeam'))}")
                    with col2:
                        st.markdown(f"*Date of Birth:* {display_value(player_data.get('DoB'))}")
                        st.markdown(f"*Birth Place:* {display_value(player_data.get('birthPlace'))}")
                    with col3:
                        st.markdown(f"*Test Batting Rank:* {display_value(player_data.get('bat_testRank'))}")
                        st.markdown(f"*ODI Batting Rank:* {display_value(player_data.get('bat_odiRank'))}")
                        st.markdown(f"*T20 Batting Rank:* {display_value(player_data.get('bat_t20Rank'))}")

                    st.markdown(f"*Teams:* {display_value(player_data.get('Teams'))}")

                    # --- Display Bio ---
                    bio_html = player_data.get('bio', '-')
                    if bio_html is None or bio_html.strip() == "":
                        bio_text = "-"
                    else:
                        bio_text = re.sub('<[^<]+?>', '', bio_html)
                        bio_text = bio_text.replace('&nbsp;', ' ').replace('&amp;', '&').strip()

                    st.subheader("📝 *Player Bio*")
                    st.text_area("", bio_text, height=400)
                    web_url = display_value(player_data.get('webURL'))
                    st.markdown(f"[🔗 *Read More*]({web_url})")

                # --- Batting Stats ---
                with tab2:
                    st.subheader("🏏 *Batting Performance*")
                    batting_stats = players_batting[
                        players_batting['player_id'] == player_data['player_id']
                    ].fillna('-')

                    if not batting_stats.empty:
                        stats_dict = batting_stats.iloc[0].to_dict()
                        formats = {
                            "Test": ["matches_test", "innings_test", "runs_test", "balls_test", "highest_test", "average_test", "sr_test", "not_out_test", "fours_test", "sixes_test", "ducks_test", "50s_test", "100s_test"],
                            "ODI": ["matches_odi", "innings_odi", "runs_odi", "balls_odi", "highest_odi", "average_odi", "sr_odi", "not_out_odi", "fours_odi", "sixes_odi", "ducks_odi", "50s_odi", "100s_odi"],
                            "T20": ["matches_t20", "innings_t20", "runs_t20", "balls_t20", "highest_t20", "average_t20", "sr_t20", "not_out_t20", "fours_t20", "sixes_t20", "ducks_t20", "50s_t20", "100s_t20"],
                            "IPL": ["matches_ipl", "innings_ipl", "runs_ipl", "balls_ipl", "highest_ipl", "average_ipl", "sr_ipl", "not_out_ipl", "fours_ipl", "sixes_ipl", "ducks_ipl", "50s_ipl", "100s_ipl"],
                        }
                        label_map = {
                            "matches": "Matches", "innings": "Innings", "runs": "Runs",
                            "balls": "Balls Faced", "highest": "Highest Score",
                            "average": "Batting Avg", "sr": "Strike Rate", "not_out": "Not Outs",
                            "fours": "Fours", "sixes": "Sixes", "ducks": "Ducks",
                            "50s": "50s", "100s": "100s",
                        }
                        for fmt, stats in formats.items():
                            with st.expander(f"📊 *{fmt} Format*", expanded=False):
                                for i in range(0, len(stats), 3):
                                    cols = st.columns(3)
                                    for j, col in enumerate(cols):
                                        if i + j < len(stats):
                                            key = stats[i + j]
                                            value = stats_dict.get(key, "-")
                                            base = key.replace(f"_{fmt.lower()}", "")
                                            label = label_map.get(base, key)
                                            if isinstance(value, (int, float)):
                                                if "average" in key or "sr" in key:
                                                    value = f"{value:.2f}"
                                                else:
                                                    value = int(value)
                                            col.metric(label, value)
                    else:
                        st.info("ℹ️ *Batting data not available for this player.*")

                # --- Bowling Stats ---
                with tab3:
                    st.subheader("⚾ *Bowling Performance*")
                    bowling_stats = players_bowling[
                        players_bowling['player_id'] == player_data['player_id']
                    ].fillna('-')

                    if not bowling_stats.empty:
                        stats_dict = bowling_stats.iloc[0].to_dict()
                        formats = {
                            "Test": ["matches_test", "innings_test", "balls_test", "runs_test", "maidens_test", "wickets_test", "avg_test", "eco_test", "sr_test", "bbi_test", "bbm_test", "4w_test", "5w_test", "10w_test"],
                            "ODI": ["matches_odi", "innings_odi", "balls_odi", "runs_odi", "maidens_odi", "wickets_odi", "avg_odi", "eco_odi", "sr_odi", "bbi_odi", "bbm_odi", "4w_odi", "5w_odi", "10w_odi"],
                            "T20": ["matches_t20", "innings_t20", "balls_t20", "runs_t20", "maidens_t20", "wickets_t20", "avg_t20", "eco_t20", "sr_t20", "bbi_t20", "bbm_t20", "4w_t20", "5w_t20", "10w_t20"],
                            "IPL": ["matches_ipl", "innings_ipl", "balls_ipl", "runs_ipl", "maidens_ipl", "wickets_ipl", "avg_ipl", "eco_ipl", "sr_ipl", "bbi_ipl", "bbm_ipl", "4w_ipl", "5w_ipl", "10w_ipl"],
                        }
                        label_map = {
                            "matches": "Matches", "innings": "Innings", "balls": "Balls Bowled",
                            "runs": "Runs Conceded", "maidens": "Maidens", "wickets": "Wickets",
                            "avg": "Bowling Avg", "eco": "Economy Rate", "sr": "Strike Rate",
                            "bbi": "Best Bowling Innings", "bbm": "Best Bowling Match",
                            "4w": "4 Wickets", "5w": "5 Wickets", "10w": "10 Wickets",
                        }
                        for fmt, stats in formats.items():
                            with st.expander(f"🎯 *{fmt} Format*", expanded=False):
                                for i in range(0, len(stats), 3):
                                    cols = st.columns(3)
                                    for j, col in enumerate(cols):
                                        if i + j < len(stats):
                                            key = stats[i + j]
                                            value = stats_dict.get(key, "-")
                                            base = key.replace(f"_{fmt.lower()}", "")
                                            label = label_map.get(base, key)
                                            if isinstance(value, (int, float)):
                                                if "avg" in key or "eco" in key or "sr" in key:
                                                    value = f"{value:.2f}"
                                                else:
                                                    value = int(value)
                                            col.metric(label, value)
                    else:
                        st.info("ℹ️ *Bowling data not available for this player.*")

    st.markdown("---")


# -------------------- SQL QUERIES & ANALYTICS PAGE --------------------
elif page == "📊 SQL Queries & Analytics Page":
    st.title("📊 SQL Queries and Analytics")
    selected_question = st.selectbox("Select a question", questions)
    try:
        available_paths = list(pickle_dict[selected_question].values())
        if available_paths:
            file_path = available_paths[0]
            df = pd.read_pickle(file_path)
            st.dataframe(df)
        else:
            st.info("No pickle file found for this question.")
    except Exception as e:
        st.error(f"Failed to load data: {e}")

# -------------------- CRUD OPERATIONS PAGE --------------------
elif page == "✍️ CRUD Operations Page":
    st.title("✍️ CRUD - Indian Players")
    menu = ["➕ Create Player", "📖 Read Players", "✏️ Update Player", "🗑️ Delete Player"]
    choice = st.selectbox("Select Operation", menu)

    if choice == "➕ Create Player":
        st.subheader("Create Player")
        player_id = st.number_input("Player ID", step=1, min_value=1, value=get_next_player_id())
        name = st.text_input("Full Name")
        role = st.text_input("Playing Role")
        battingstyle = st.text_input("Batting Style")
        bowlingstyle = st.text_input("Bowling Style")
        if st.button("Create"):
            if name.strip():
                add_player(player_id, name.strip(), role.strip(), battingstyle.strip(), bowlingstyle.strip())
                st.success(f"✅ {name} (ID: {player_id}) added successfully!")
            else:
                st.error("Please enter the player's name.")

    elif choice == "📖 Read Players":
        st.subheader("All Indian Players")
        df = fetch_players()
        st.dataframe(df.reset_index(drop=True))

    elif choice == "✏️ Update Player":
        st.subheader("Update Player Details")
        df = fetch_players()
        if not df.empty:
            st.dataframe(df)
            player_id = st.number_input("Player ID to Update", step=1, min_value=1)
            role = st.text_input("New Role")
            battingstyle = st.text_input("New Batting Style")
            bowlingstyle = st.text_input("New Bowling Style")
            if st.button("Update"):
                rows = update_player(player_id, role, battingstyle, bowlingstyle)
                if rows:
                    st.success("✅ Player updated successfully!")
                else:
                    st.warning("No player updated (check player_id).")

    elif choice == "🗑️ Delete Player":
        st.subheader("Delete Player")
        df = fetch_players()
        if not df.empty:
            selected_name = st.selectbox("Select Player Name to Delete", df["player_name"].tolist())
            if st.button("Delete"):
                deleted = delete_player_by_name(selected_name)
                if deleted:
                    st.success(f"🗑️ Player '{selected_name}' deleted successfully! ({deleted} row(s))")
                else:
                    st.warning("No rows deleted.")