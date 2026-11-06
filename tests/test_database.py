"""Testit tietokantamoduulille (väliaikainen SQLite-tiedosto)."""

import sqlite3

import pytest

from src import database
from src.transform import (
    transform_game_logs,
    transform_players,
    transform_profiles,
    transform_teams,
)


def tee_testidata():
    joukkueet = transform_teams(
        [
            {
                "teamAbbrev": {"default": "FLA"},
                "teamName": {"default": "Florida Panthers"},
                "conferenceName": "Eastern",
                "divisionName": "Atlantic",
                "gamesPlayed": 20,
                "wins": 12,
                "losses": 8,
                "goalFor": 60,
                "goalAgainst": 50,
                "points": 24,
            }
        ]
    )
    pelaajat = transform_players(
        [
            {
                "id": 1,
                "firstName": {"default": "Aleksander"},
                "lastName": {"default": "Barkov"},
                "positionCode": "C",
                "teamAbbrev": "FLA",
            }
        ]
    )
    profiilit = transform_profiles(
        [
            {
                "playerId": 1,
                "birthDate": "1995-09-02",
                "heightInCentimeters": 191,
                "weightInKilograms": 97,
                "draftDetails": {"year": 2013, "overallPick": 2},
            }
        ],
        today="2026-09-02",
    )
    ottelut = [
        {
            "gameId": n,
            "gameDate": f"2026-10-0{n}",
            "opponentAbbrev": "TOR",
            "homeRoadFlag": "H",
            "goals": 1,
            "assists": 0,
            "points": 1,
            "shots": 3,
            "plusMinus": 0,
            "toi": "20:00",
        }
        for n in (1, 2, 3)
    ]
    lokit = transform_game_logs([(1, ottelut)])
    return joukkueet, pelaajat, profiilit, lokit


@pytest.fixture
def tietokanta(tmp_path):
    polku = str(tmp_path / "testi.db")
    database.save_all(*tee_testidata(), db_path=polku)
    return polku


def test_save_all_luo_kaikki_taulut(tietokanta):
    conn = sqlite3.connect(tietokanta)
    taulut = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert {"teams", "players", "player_profiles", "game_logs"} <= taulut


def test_load_game_logs_palauttaa_rivit_ja_sarakkeet(tietokanta):
    df = database.load_game_logs(tietokanta)
    assert len(df) == 3
    for sarake in ("name", "team_name", "age", "bmi", "goal_for", "points_per_60"):
        assert sarake in df.columns


def test_viiteavain_estaa_tuntemattoman_joukkueen(tietokanta):
    conn = database.get_connection(tietokanta)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO players (player_id, name, position, team_abbrev) VALUES (99, 'Testi', 'C', 'XXX')"
        )
    conn.close()


def test_uudelleenajo_ei_kasvata_rivimaaraa(tietokanta):
    database.save_all(*tee_testidata(), db_path=tietokanta)
    assert len(database.load_game_logs(tietokanta)) == 3
