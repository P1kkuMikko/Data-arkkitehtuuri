# Suomalaiset NHL-pelaajat – dataputki

Dataputki NHL:n avoimesta API:sta (`api-web.nhle.com`) SQLiteen ja Streamlit + Plotly -visualisointiin.

## Rakenne
- `src/extract.py` – hakee joukkueet (`standings/now`), rosterit, pelaajaprofiilit (`landing`) ja suomalaisten kenttäpelaajien ottelulokit
- `src/transform.py` – siivous (duplikaatit, tyhjät) ja laskennalliset muuttujat (peliaika minuutteina, P/60, 5 ottelun liukuva keskiarvo, pistekertymä, ikä, BMI, maaliero/ottelu)
- `src/database.py` – SQLite-skeema (`teams`, `players`, `player_profiles`, `game_logs`) ja luku/tallennus
- `main.py` – ajaa putken (Extract → Transform → Load)
- `app.py` – Streamlit-sovellus

## Käyttö
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py          # luo nhl.db
streamlit run app.py
```
