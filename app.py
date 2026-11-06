"""Streamlit + Plotly -visualisointisovellus: suomalaiset NHL-pelaajat (data SQLitestä)."""

import plotly.express as px
import streamlit as st

from src.database import load_game_logs

st.set_page_config(page_title="Suomalaiset NHL-pelaajat", layout="wide")


@st.cache_data
def get_data():
    return load_game_logs()


df = get_data()

st.title("Suomalaiset NHL-pelaajat")

# Sivupalkin suodattimet
position = st.sidebar.radio("Pelipaikka", ["Kaikki", "Hyökkääjät", "Puolustajat"])
min_games = st.sidebar.slider("Min. otteluita", 1, int(df.groupby("player_id").size().max()), 5)
player = st.sidebar.selectbox("Pelaaja (kuntopuntari)", sorted(df["name"].unique()))

# Kaavio 1: peliaika vs. pisteet
data = df
if position == "Hyökkääjät":
    data = data[data["position"].isin(["C", "L", "R"])]
elif position == "Puolustajat":
    data = data[data["position"] == "D"]

summary = data.groupby(["name", "team_abbrev"], as_index=False).agg(
    games=("game_id", "count"),
    toi=("toi_min", "mean"),
    points=("points", "sum"),
    shots=("shots", "sum"),
    p60=("points_per_60", "mean"),
)
summary = summary[summary["games"] >= min_games]

fig1 = px.scatter(
    summary, x="toi", y="points", size="shots", color="team_abbrev", hover_name="name",
    hover_data=["games", "p60"],
    labels={"toi": "Keskim. peliaika (min)", "points": "Pisteet", "shots": "Laukaukset"},
    title="Peliaika vs. pisteet (pallon koko = laukaukset)",
)
st.plotly_chart(fig1, use_container_width=True)

# Kaavio 2: valitun pelaajan kuntopuntari
player_data = df[df["name"] == player]
fig2 = px.line(
    player_data, x="game_date", y=["cumulative_points", "rolling_points_5"], hover_name="opponent",
    labels={"value": "Pisteet", "game_date": "Pvm", "variable": "Mittari"},
    title=f"{player}: pistekertymä ja 5 ottelun liukuva keskiarvo",
)
st.plotly_chart(fig2, use_container_width=True)

# Kaavio 3: rikastettu data (profiili) – ikä vs. P/60
profile_summary = data.groupby(["name", "position"], as_index=False).agg(
    age=("age", "first"), bmi=("bmi", "first"), p60=("points_per_60", "mean"),
    draft_pick=("draft_overall_pick", "first"), games=("game_id", "count"),
)
profile_summary = profile_summary[profile_summary["games"] >= min_games]
fig3 = px.scatter(
    profile_summary, x="age", y="p60", color="position", size="bmi", hover_name="name",
    hover_data=["draft_pick"],
    labels={"age": "Ikä", "p60": "Pisteet / 60 min", "bmi": "BMI"},
    title="Ikä vs. pisteet per 60 min (pallon koko = BMI)",
)
st.plotly_chart(fig3, use_container_width=True)

# Kaavio 4: joukkuekonteksti (standings) – pelaajan osuus joukkueen maaleista
share = data.groupby(["name", "team_abbrev"], as_index=False).agg(
    points=("points", "sum"), goal_for=("goal_for", "first"),
    team_points=("team_points", "first"), games=("game_id", "count"),
)
share = share[share["games"] >= min_games]
share["goal_share_pct"] = (share["points"] / share["goal_for"] * 100).round(1)
fig4 = px.bar(
    share.sort_values("goal_share_pct", ascending=False).head(15),
    x="name", y="goal_share_pct", color="team_abbrev", hover_data=["points", "goal_for", "team_points"],
    labels={"name": "Pelaaja", "goal_share_pct": "Osuus joukkueen maaleista (%)"},
    title="Pelaajan pisteet suhteessa joukkueen tekemiin maaleihin (top 15)",
)
st.plotly_chart(fig4, use_container_width=True)

with st.expander("Näytä data taulukkona"):
    st.dataframe(summary)
