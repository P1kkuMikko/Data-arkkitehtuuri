"""Datan muuntaminen: siivous ja uusien muuttujien laskeminen."""

import pandas as pd


def toi_to_minutes(toi):
    """Muuttaa peliajan '18:45' -> 18.75 minuuttia."""
    try:
        minutes, seconds = toi.split(":")
        return int(minutes) + int(seconds) / 60
    except (AttributeError, ValueError):
        return None


def transform_teams(raw_teams):
    rows = [
        {
            "team_abbrev": t["teamAbbrev"]["default"],
            "team_name": t["teamName"]["default"],
            "conference": t["conferenceName"],
            "division": t["divisionName"],
            "games_played": t["gamesPlayed"],
            "wins": t["wins"],
            "losses": t["losses"],
            "goal_for": t["goalFor"],
            "goal_against": t["goalAgainst"],
            "points": t["points"],
        }
        for t in raw_teams
    ]
    df = pd.DataFrame(rows).drop_duplicates("team_abbrev")
    # Laskettu muuttuja: maaliero per ottelu
    df["goal_diff_per_game"] = ((df["goal_for"] - df["goal_against"]) / df["games_played"]).round(2)
    return df


def transform_players(raw_players):
    rows = [
        {
            "player_id": p["id"],
            "name": f"{p['firstName']['default']} {p['lastName']['default']}",
            "position": p["positionCode"],
            "team_abbrev": p["teamAbbrev"],
        }
        for p in raw_players
    ]
    return pd.DataFrame(rows).drop_duplicates("player_id")


def transform_profiles(raw_profiles):
    """Rikastus: ikä, BMI ja draft-tiedot pelaajaprofiileista (landing-reitti)."""
    today = pd.Timestamp.today()
    rows = []
    for p in raw_profiles:
        birth = pd.to_datetime(p.get("birthDate"), errors="coerce")
        height_m = p.get("heightInCentimeters", 0) / 100
        weight = p.get("weightInKilograms")
        draft = p.get("draftDetails") or {}  # puuttuu draftaamattomilta
        rows.append(
            {
                "player_id": p["playerId"],
                "birth_date": p.get("birthDate"),
                "birth_city": (p.get("birthCity") or {}).get("default"),
                "height_cm": p.get("heightInCentimeters"),
                "weight_kg": weight,
                "age": round((today - birth).days / 365.25, 1) if pd.notna(birth) else None,
                "bmi": round(weight / height_m**2, 1) if weight and height_m else None,
                "draft_year": draft.get("year"),
                "draft_overall_pick": draft.get("overallPick"),
                "undrafted": 0 if draft else 1,
            }
        )
    return pd.DataFrame(rows).drop_duplicates("player_id")


def transform_game_logs(raw_logs):
    """raw_logs: lista (player_id, ottelulista) -pareja."""
    rows = []
    for player_id, games in raw_logs:
        for g in games:
            rows.append(
                {
                    "game_id": g["gameId"],
                    "player_id": player_id,
                    "game_date": g["gameDate"],
                    "opponent": g["opponentAbbrev"],
                    "home": 1 if g["homeRoadFlag"] == "H" else 0,
                    "goals": g["goals"],
                    "assists": g["assists"],
                    "points": g["points"],
                    "shots": g["shots"],
                    "plus_minus": g["plusMinus"],
                    "toi_min": toi_to_minutes(g["toi"]),
                }
            )
    df = pd.DataFrame(rows)

    # Siivous: duplikaatit ja puuttuvat arvot
    before = len(df)
    df = df.drop_duplicates(["game_id", "player_id"])
    df = df.dropna(subset=["toi_min"])
    print(f"Siivous: poistettiin {before - len(df)} riviä (duplikaatit / tyhjä peliaika)")

    # Uudet laskennalliset muuttujat
    df = df.sort_values(["player_id", "game_date"]).reset_index(drop=True)
    df["points_per_60"] = df["points"] / df["toi_min"].where(df["toi_min"] > 0) * 60
    df["rolling_points_5"] = (
        df.groupby("player_id")["points"].transform(lambda s: s.rolling(5, min_periods=1).mean())
    )
    df["cumulative_points"] = df.groupby("player_id")["points"].cumsum()
    return df
