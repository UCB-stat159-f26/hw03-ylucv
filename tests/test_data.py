"""Offline parsing, age calculations, and retrieval tests."""

import json

import pandas as pd
import pytest
import requests

from tennis_career import _source, get_career_matches
from tennis_career._parse import _clean_matches, _read_array


def test_clean_both_formats(career_rows):
    born = "19810926" if len(career_rows[0][16]) == 8 else "19860603"
    data = _clean_matches(career_rows, born)
    first_date = pd.Timestamp(career_rows[0][0])
    raw_age = career_rows[0][16]
    expected = ((first_date - pd.Timestamp(raw_age)).days / 365.2425
                if len(raw_age) == 8 else float(raw_age))
    first = data.loc[data["opponent"] == career_rows[0][11]].iloc[0]
    assert first["age_opponent"] == pytest.approx(expected)
    assert first["age_player"] == pytest.approx(
        (first_date - pd.Timestamp(born)).days / 365.2425)
    assert first["age_diff"] == pytest.approx(first["age_player"] - expected)
    assert len(data) == 3
    assert data["date_match"].is_monotonic_increasing
    assert first["win_lose"] == "lost"


@pytest.mark.parametrize("invalid", ["", "00000000", "garbage", "-5", "inf", "20990101"])
def test_skip_unusable_ages(career_rows, invalid):
    career_rows[0][16] = invalid
    data = _clean_matches(career_rows, "19810926")
    assert len(data) == 2
    assert data.attrs["skipped_rows"] == 1


def test_deduplication_and_walkovers(career_rows):
    career_rows[0][9] = "W/O"
    data = _clean_matches(career_rows + career_rows, "19810926")
    assert len(data) == 3
    assert data["is_walkover"].sum() == 1


def test_updated_profile_record_preferred(career_rows):
    updated = career_rows[0].copy()
    updated[9] = "6-0 6-0"
    data = _clean_matches(career_rows + [updated], "19810926")
    assert len(data) == 3
    assert data.loc[data["opponent"] == updated[11], "score"].item() == "6-0 6-0"


@pytest.mark.parametrize("field,value", [(0, "bad"), (0, "19000101"), (4, "X")])
def test_skip_unusable_dates_and_results(career_rows, field, value):
    career_rows[0][field] = value
    assert len(_clean_matches(career_rows, "19810926")) == 2


@pytest.mark.parametrize("records", [[], [[]], ["invalid"]])
def test_bad_records(records):
    with pytest.raises(ValueError, match="17 fields"):
        _clean_matches(records, "19810926")


def test_no_usable_matches(career_rows):
    for row in career_rows:
        row[16] = ""
    with pytest.raises(ValueError, match="No matches"):
        _clean_matches(career_rows, "19810926")


@pytest.mark.parametrize("source", ["<html>error</html>", "var morematchmx = [bad];",
                                   "var morematchmx = {};"])
def test_invalid_javascript(source):
    with pytest.raises(ValueError, match="morematchmx"):
        _read_array(source, "morematchmx")


def test_parser_ignores_surrounding_code(career_source):
    source = career_source + "; var unrelated = []; throw new Error('never executed');"
    assert len(_read_array(source, "morematchmx")) == 3


@pytest.mark.parametrize("name", ["serena williams", "Serena Williams", "SerenaWilliams",
                                 "SERENAWILLIAMS", "  Serena   Williams  "])
def test_name_variants(monkeypatch, name):
    monkeypatch.setattr(_source, "_download", lambda _: 'var playerlist=["(W) Serena Williams"];')
    assert _source._resolve_player(name) == ("W", "Serena Williams")


@pytest.mark.parametrize("name", ["GastonSanchez", "Gaston Sanchez", "", "  ", None, 42])
def test_invalid_names(monkeypatch, name):
    monkeypatch.setattr(_source, "_download", lambda _: 'var playerlist=["(M) Rafael Nadal"];')
    with pytest.raises(ValueError, match="name|player"):
        get_career_matches(name)


def test_public_retrieval(monkeypatch, career_rows):
    tour, name = ("W", "Serena Williams") if len(career_rows[0][16]) == 8 else ("M", "Rafael Nadal")
    slug = name.replace(" ", "")
    profile = 'var dob=19810926; var careerjs=1; var matchmx=' + json.dumps(career_rows[-1:])
    path = f"jsmatches/{slug}.js" if tour == "W" else f"cgi-bin/player-classic.cgi?p={slug}"
    responses = {"mwplayerlist.js": f'var playerlist=["({tour}) {name}"];',
                 path: profile, f"jsmatches/{slug}Career.js":
                 "var morematchmx=" + json.dumps(career_rows)}
    monkeypatch.setattr(_source, "_download", responses.__getitem__)
    data = get_career_matches(name)
    assert len(data) == 3
    assert data.attrs["player"] == name
    assert data.attrs["birth_date"] == "19810926"


def test_complete_profile_without_archive():
    assert _source._career_records("var careerjs=0; var matchmx=[];", "Test") == []


def test_missing_player_birth(monkeypatch):
    monkeypatch.setattr(_source, "_download", lambda _: "var matchmx=[];")
    with pytest.raises(ValueError, match="birth date"):
        _source._player_source("W", "Serena Williams")


def test_network_error(monkeypatch):
    def fail(*args, **kwargs):
        raise requests.Timeout("timeout")
    monkeypatch.setattr(requests, "get", fail)
    with pytest.raises(ConnectionError, match="Tennis Abstract"):
        _source._download("test.js")


def test_download_settings(monkeypatch):
    class Response:
        text = "var matchmx=[];"
        def raise_for_status(self):
            pass
    def respond(url, **kwargs):
        assert url == "https://www.tennisabstract.com/test.js"
        assert kwargs["timeout"] == 30
        assert kwargs["headers"]["User-Agent"]
        return Response()
    monkeypatch.setattr(requests, "get", respond)
    assert _source._download("test.js") == "var matchmx=[];"
