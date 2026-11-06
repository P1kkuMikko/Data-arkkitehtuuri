"""Testit muunnosfunktioille (ei vaadi verkkoyhteyttä)."""

import pandas as pd

from src.transform import (
    toi_to_minutes,
    transform_game_logs,
    transform_profiles,
    transform_teams,
)


def tee_ottelu(game_id, paiva, pisteet, toi: str | None = "15:00"):
    """Apufunktio: yksi ottelulokirivi API:n muodossa."""
    return {
        "gameId": game_id,
        "gameDate": paiva,
        "opponentAbbrev": "TOR",
        "homeRoadFlag": "H",
        "goals": 0,
        "assists": pisteet,
        "points": pisteet,
        "shots": 2,
        "plusMinus": 0,
        "toi": toi,
    }


def test_toi_to_minutes_muuntaa_minuuteiksi():
    assert toi_to_minutes("18:45") == 18.75


def test_toi_to_minutes_virheellinen_arvo_palauttaa_none():
    assert toi_to_minutes(None) is None
    assert toi_to_minutes("abc") is None


def test_game_logs_poistaa_duplikaatit():
    ottelut = [tee_ottelu(1, "2026-10-01", 1), tee_ottelu(1, "2026-10-01", 1)]
    df = transform_game_logs([(100, ottelut)])
    assert len(df) == 1


def test_game_logs_poistaa_rivit_ilman_peliaikaa():
    ottelut = [tee_ottelu(1, "2026-10-01", 1), tee_ottelu(2, "2026-10-03", 0, toi=None)]
    df = transform_game_logs([(100, ottelut)])
    assert list(df["game_id"]) == [1]


def test_game_logs_liukuva_keskiarvo():
    pisteet = [1, 0, 2, 0, 1, 3]
    ottelut = [tee_ottelu(i, f"2026-10-0{i}", p) for i, p in enumerate(pisteet, start=1)]
    df = transform_game_logs([(100, ottelut)])
    odotettu = [1.0, 0.5, 1.0, 0.75, 0.8, 1.2]
    assert list(df["rolling_points_5"].round(2)) == odotettu


def test_game_logs_kumulatiiviset_pisteet_pelaajittain():
    a = [tee_ottelu(1, "2026-10-01", 1), tee_ottelu(2, "2026-10-02", 2)]
    b = [tee_ottelu(3, "2026-10-01", 3)]
    df = transform_game_logs([(100, a), (200, b)])
    assert list(df[df["player_id"] == 100]["cumulative_points"]) == [1, 3]
    assert list(df[df["player_id"] == 200]["cumulative_points"]) == [3]


def test_game_logs_pisteet_per_60_minuuttia():
    df = transform_game_logs([(100, [tee_ottelu(1, "2026-10-01", 1, toi="30:00")])])
    assert df.loc[0, "points_per_60"] == 2.0


def test_profiilit_laskee_ian_ja_painoindeksin():
    raaka = [
        {
            "playerId": 1,
            "birthDate": "1995-09-02",
            "birthCity": {"default": "Tampere"},
            "heightInCentimeters": 191,
            "weightInKilograms": 97,
            "draftDetails": {"year": 2013, "overallPick": 2},
        }
    ]
    df = transform_profiles(raaka, today="2026-09-02")
    assert df.loc[0, "age"] == 31.0
    assert df.loc[0, "bmi"] == 26.6
    assert df.loc[0, "draft_overall_pick"] == 2
    assert df.loc[0, "undrafted"] == 0


def test_profiilit_varaamaton_pelaaja_merkitaan():
    raaka = [
        {
            "playerId": 2,
            "birthDate": "2000-01-01",
            "heightInCentimeters": 180,
            "weightInKilograms": 80,
        }
    ]
    df = transform_profiles(raaka, today="2026-01-01")
    assert df.loc[0, "undrafted"] == 1
    assert pd.isna(df.loc[0, "draft_year"])


def test_joukkueet_laskee_maalieron_per_ottelu():
    raaka = [
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
    df = transform_teams(raaka)
    assert df.loc[0, "goal_diff_per_game"] == 0.5
