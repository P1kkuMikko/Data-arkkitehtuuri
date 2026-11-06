"""Testit hakumoduulille (requests.get korvataan feikillä, ei oikeita API-kutsuja)."""

import pytest

from src import extract


class FeikkiVastaus:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data or {}

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


@pytest.fixture(autouse=True)
def ei_odotuksia(monkeypatch):
    """Ohitetaan time.sleep, jotta testit pysyvät nopeina."""
    monkeypatch.setattr(extract.time, "sleep", lambda s: None)


def test_get_json_palauttaa_jsonin(monkeypatch):
    monkeypatch.setattr(extract.requests, "get", lambda url, timeout: FeikkiVastaus(200, {"a": 1}))
    assert extract.get_json("testi") == {"a": 1}


def test_get_json_yrittaa_uudelleen_429_virheella(monkeypatch):
    vastaukset = [FeikkiVastaus(429), FeikkiVastaus(429), FeikkiVastaus(200, {"ok": True})]
    kutsut = []

    def feikki_get(url, timeout):
        kutsut.append(url)
        return vastaukset[len(kutsut) - 1]

    monkeypatch.setattr(extract.requests, "get", feikki_get)
    assert extract.get_json("testi") == {"ok": True}
    assert len(kutsut) == 3


def test_get_json_nostaa_virheen_muista_virhekoodeista(monkeypatch):
    monkeypatch.setattr(extract.requests, "get", lambda url, timeout: FeikkiVastaus(500))
    with pytest.raises(RuntimeError):
        extract.get_json("testi")


def test_fetch_finnish_players_suodattaa_suomalaiset_kenttapelaajat(monkeypatch):
    kokoonpano = {
        "forwards": [
            {"id": 1, "birthCountry": "FIN"},
            {"id": 2, "birthCountry": "CAN"},
        ],
        "defensemen": [{"id": 3, "birthCountry": "FIN"}],
        "goalies": [{"id": 4, "birthCountry": "FIN"}],  # maalivahdit jätetään pois
    }
    monkeypatch.setattr(extract, "get_json", lambda path: kokoonpano)
    pelaajat = extract.fetch_finnish_players(["FLA"])
    assert sorted(p["id"] for p in pelaajat) == [1, 3]
    assert all(p["teamAbbrev"] == "FLA" for p in pelaajat)
