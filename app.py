"""Streamlit + Plotly -visualisointisovellus: suomalaiset NHL-pelaajat (data SQLitestä)."""

import plotly.express as px
import streamlit as st

from src.database import load_game_logs

st.set_page_config(page_title="Suomalaiset NHL-pelaajat", layout="wide")

# Pelipaikkojen lyhenteet suomeksi
PELIPAIKAT = {
    "C": "Keskushyökkääjä",
    "L": "Vasen laitahyökkääjä",
    "R": "Oikea laitahyökkääjä",
    "D": "Puolustaja",
}

# Sarakkeiden suomenkieliset nimet kaavioihin ja taulukkoon
NIMET = {
    "name": "Pelaaja",
    "team_name": "Joukkue",
    "position": "Pelipaikka",
    "games": "Ottelut",
    "toi": "Keskim. peliaika (min)",
    "points": "Pisteet",
    "shots": "Laukaukset",
    "p60": "Pisteet / 60 min",
    "age": "Ikä",
    "bmi": "Painoindeksi",
    "draft_pick": "Varausvalinta (kokonaisvalinta)",
    "goal_for": "Joukkueen tekemät maalit",
    "team_points": "Joukkueen pisteet",
    "goal_share_pct": "Osuus joukkueen maaleista (%)",
    "game_date": "Päivämäärä",
    "value": "Pisteet",
    "variable": "Mittari",
}


@st.cache_data
def hae_data():
    df = load_game_logs()
    df["position_fi"] = df["position"].replace(PELIPAIKAT)
    return df


df = hae_data()

st.title("Suomalaiset NHL-pelaajat")

# Sivupalkin suodattimet
pelipaikka = st.sidebar.radio("Pelipaikka", ["Kaikki", "Hyökkääjät", "Puolustajat"])
max_ottelut = int(df.groupby("player_id").size().to_numpy().max())
min_ottelut = st.sidebar.slider("Vähimmäismäärä otteluita", 1, max_ottelut, 5)
pelaaja = st.sidebar.selectbox("Pelaaja (kuntopuntari)", sorted(df["name"].unique()))

# Pelipaikkasuodatus
data = df
if pelipaikka == "Hyökkääjät":
    data = data[data["position"].isin(["C", "L", "R"])]
elif pelipaikka == "Puolustajat":
    data = data[data["position"] == "D"]

# Kaavio 1: peliaika vs. pisteet
yhteenveto = data.groupby(["name", "team_name"], as_index=False).agg(
    games=("game_id", "count"),
    toi=("toi_min", "mean"),
    points=("points", "sum"),
    shots=("shots", "sum"),
    p60=("points_per_60", "mean"),
)
yhteenveto = yhteenveto.loc[yhteenveto["games"] >= min_ottelut]

kaavio1 = px.scatter(
    yhteenveto, x="toi", y="points", size="shots", color="team_name", hover_name="name",
    hover_data=["games", "p60"], labels=NIMET,
    title="Peliaika vs. pisteet (pallon koko = laukaukset)",
)
st.plotly_chart(kaavio1, width="stretch")

# Kaavio 2: valitun pelaajan kuntopuntari
pelaajan_data = df.loc[df["name"] == pelaaja]
kaavio2 = px.line(
    pelaajan_data, x="game_date", y=["cumulative_points", "rolling_points_5"], hover_name="opponent",
    labels=NIMET,
    title=f"{pelaaja}: pistekertymä ja 5 ottelun liukuva keskiarvo",
)
# Päivämäärät suomalaiseen muotoon (päivä.kuukausi.vuosi, ei englanninkielisiä kuukausia)
kaavio2.update_xaxes(tickformat="%d.%m.%Y", hoverformat="%d.%m.%Y")
kaavio2.for_each_trace(
    lambda t: t.update(
        name={
            "cumulative_points": "Pistekertymä",
            "rolling_points_5": "5 ottelun liukuva keskiarvo",
        }[t.name],
        hovertemplate=(
            "<b>Vastustaja: %{hovertext}</b><br>"
            "Päivämäärä: %{x|%d.%m.%Y}<br>"
            + (
                "Pistekertymä: %{y}<extra></extra>"
                if t.name == "cumulative_points"
                else "5 ottelun liukuva keskiarvo: %{y:.2f}<extra></extra>"
            )
        ),
    )
)
st.plotly_chart(kaavio2, width="stretch")

# Kaavio 3: rikastettu data (profiili) – ikä vs. pisteet per 60 min
profiili = data.groupby(["name", "position_fi"], as_index=False).agg(
    age=("age", "first"), bmi=("bmi", "first"), p60=("points_per_60", "mean"),
    draft_pick=("draft_overall_pick", "first"), games=("game_id", "count"),
)
profiili = profiili.loc[profiili["games"] >= min_ottelut]
kaavio3 = px.scatter(
    profiili, x="age", y="p60", color="position_fi", size="bmi", hover_name="name",
    hover_data=["draft_pick"], labels={**NIMET, "position_fi": "Pelipaikka"},
    title="Ikä vs. pisteet / 60 min (pallon koko = painoindeksi)",
)
st.plotly_chart(kaavio3, width="stretch")

# Kaavio 4: joukkuekonteksti (sarjataulukko) – pelaajan osuus joukkueen maaleista
osuus = data.groupby(["name", "team_name"], as_index=False).agg(
    points=("points", "sum"), goal_for=("goal_for", "first"),
    team_points=("team_points", "first"), games=("game_id", "count"),
)
osuus = osuus.loc[osuus["games"] >= min_ottelut]
osuus["goal_share_pct"] = (osuus["points"] / osuus["goal_for"] * 100).round(1)
kaavio4 = px.bar(
    osuus.sort_values("goal_share_pct", ascending=False).head(15),
    x="name", y="goal_share_pct", color="team_name", hover_data=["points", "goal_for", "team_points"],
    labels=NIMET,
    title="Pelaajan pisteet suhteessa joukkueen tekemiin maaleihin (15 parasta)",
)
st.plotly_chart(kaavio4, width="stretch")

with st.expander("Näytä data taulukkona"):
    taulukko = yhteenveto.copy()
    taulukko["toi"] = taulukko["toi"].round(1)
    taulukko["p60"] = taulukko["p60"].round(2)
    st.dataframe(taulukko.rename(columns=NIMET))
