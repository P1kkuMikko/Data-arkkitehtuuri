"""SQLite-tietokanta: taulujen luonti, tallennus ja luku."""

import sqlite3

DB_PATH = "nhl.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS teams (
    team_abbrev  TEXT PRIMARY KEY,
    team_name    TEXT NOT NULL,
    conference   TEXT,
    division     TEXT,
    games_played INTEGER,
    wins         INTEGER,
    losses       INTEGER,
    goal_for     INTEGER,
    goal_against INTEGER,
    points       INTEGER,
    goal_diff_per_game REAL
);
CREATE TABLE IF NOT EXISTS players (
    player_id   INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    position    TEXT,
    team_abbrev TEXT REFERENCES teams(team_abbrev)
);
CREATE TABLE IF NOT EXISTS player_profiles (
    player_id          INTEGER PRIMARY KEY REFERENCES players(player_id),
    birth_date         TEXT,
    birth_city         TEXT,
    height_cm          INTEGER,
    weight_kg          INTEGER,
    age                REAL,
    bmi                REAL,
    draft_year         INTEGER,
    draft_overall_pick INTEGER,
    undrafted          INTEGER
);
CREATE TABLE IF NOT EXISTS game_logs (
    game_id           INTEGER,
    player_id         INTEGER REFERENCES players(player_id),
    game_date         TEXT,
    opponent          TEXT,
    home              INTEGER,
    goals             INTEGER,
    assists           INTEGER,
    points            INTEGER,
    shots             INTEGER,
    plus_minus        INTEGER,
    toi_min           REAL,
    points_per_60     REAL,
    rolling_points_5  REAL,
    cumulative_points REAL,
    PRIMARY KEY (game_id, player_id)
);
"""


def get_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def save_all(teams, players, profiles, game_logs, db_path=DB_PATH):
    """Tyhjentää taulut ja tallentaa uuden datan (putki on ajettavissa uudelleen)."""
    conn = get_connection(db_path)
    # Pudotetaan vanhat taulut, jotta skeemamuutokset tulevat voimaan
    for table in ("game_logs", "player_profiles", "players", "teams"):
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.executescript(SCHEMA)
    teams.to_sql("teams", conn, if_exists="append", index=False)
    players.to_sql("players", conn, if_exists="append", index=False)
    profiles.to_sql("player_profiles", conn, if_exists="append", index=False)
    game_logs.to_sql("game_logs", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()


def load_game_logs(db_path=DB_PATH):
    """Hakee ottelulokit yhdistettynä pelaajiin ja joukkueisiin."""
    import pandas as pd

    query = """
        SELECT g.*, p.name, p.position, p.team_abbrev, t.team_name,
               t.goal_for, t.points AS team_points, t.goal_diff_per_game,
               pr.age, pr.bmi, pr.height_cm, pr.weight_kg, pr.draft_year,
               pr.draft_overall_pick, pr.undrafted, pr.birth_city
        FROM game_logs g
        JOIN players p ON p.player_id = g.player_id
        JOIN player_profiles pr ON pr.player_id = g.player_id
        JOIN teams t ON t.team_abbrev = p.team_abbrev
        ORDER BY g.game_date
    """
    conn = get_connection(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
