"""Datan sisäänluku: hakee datan NHL:n avoimesta API:sta."""

import time

import requests

BASE_URL = "https://api-web.nhle.com/v1"


def get_json(path) -> dict:
    """Hakee yhden API-reitin ja palauttaa JSON:n."""
    for attempt in range(6):
        response = requests.get(f"{BASE_URL}/{path}", timeout=15)
        if response.status_code == 429:  # liikaa pyyntöjä -> odotetaan ja yritetään uudelleen
            time.sleep(10 * (attempt + 1))
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"API palautti toistuvasti virheen 429 (liikaa pyyntöjä): {path}")


def fetch_teams():
    """Joukkueet ja sarjataulukko."""
    data = get_json("standings/now")
    return data["standings"]


def fetch_finnish_players(team_abbrevs, country="FIN"):
    """Käy läpi joukkueiden kokoonpanot ja palauttaa valitun maan kenttäpelaajat."""
    players = []
    for abbrev in team_abbrevs:
        roster = get_json(f"roster/{abbrev}/current")
        for group in ("forwards", "defensemen"):
            for p in roster.get(group, []):
                if p.get("birthCountry") == country:
                    p["teamAbbrev"] = abbrev
                    players.append(p)
        time.sleep(0.1)  # ollaan kohteliaita API:a kohtaan
    return players


def fetch_player_profile(player_id):
    """Pelaajan profiili (pituus, paino, syntymäaika, varaustiedot) toisesta API-reitistä."""
    data = get_json(f"player/{player_id}/landing")
    time.sleep(1)
    return data


def fetch_game_log(player_id):
    """Pelaajan kuluvan kauden ottelukohtaiset tilastot."""
    data = get_json(f"player/{player_id}/game-log/now")
    time.sleep(1)
    return data.get("gameLog", [])
