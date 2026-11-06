"""Ajaa dataputken: Extract -> Transform -> Load (nhl.db)."""

from src import database, extract, transform


def main():
    print("1/3 Haetaan data NHL API:sta...")
    raw_teams = extract.fetch_teams()
    teams = transform.transform_teams(raw_teams)
    raw_players = extract.fetch_finnish_players(teams["team_abbrev"])
    players = transform.transform_players(raw_players)
    print(f"  {len(teams)} joukkuetta, {len(players)} suomalaista kenttäpelaajaa")

    raw_logs = []
    raw_profiles = []
    for pid in players["player_id"]:
        raw_logs.append((int(pid), extract.fetch_game_log(pid)))
        raw_profiles.append(extract.fetch_player_profile(pid))

    print("2/3 Muunnetaan ja siivotaan...")
    profiles = transform.transform_profiles(raw_profiles)
    game_logs = transform.transform_game_logs(raw_logs)

    print("3/3 Tallennetaan SQLiteen...")
    database.save_all(teams, players, profiles, game_logs)
    print(f"Valmis: {len(game_logs)} ottelulokiriviä tietokannassa.")


if __name__ == "__main__":
    main()
