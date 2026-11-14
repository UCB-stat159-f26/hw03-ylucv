"""Private helpers for JavaScript arrays and match cleaning."""

import json
import re

import pandas as pd

_DAYS_PER_YEAR = 365.2425
_FIELDS = {0: "date_match", 1: "tournament", 2: "surface", 4: "win_lose",
           8: "round", 9: "score", 11: "opponent", 16: "opponent_age_raw"}


def _read_array(source, variable):
    match = re.search(rf"\b(?:var|let|const)\s+{variable}\s*=\s*", source)
    if not match:
        raise ValueError(f"Missing JavaScript array: {variable}")
    try:
        records, _ = json.JSONDecoder().raw_decode(source[match.end():])
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JavaScript array: {variable}") from error
    if not isinstance(records, list):
        raise ValueError(f"Expected a list in {variable}")
    return records


def _match_frame(records):
    if not records or any(not isinstance(row, list) or len(row) < 17 for row in records):
        raise ValueError("Expected match rows with at least 17 fields")
    frame = pd.DataFrame([{name: row[i] for i, name in _FIELDS.items()}
                          for row in records])
    frame["date_match"] = pd.to_datetime(frame["date_match"], format="%Y%m%d",
                                         errors="coerce")
    frame["win_lose"] = frame["win_lose"].map({"W": "won", "L": "lost"})
    return frame


def _opponent_ages(frame):
    raw = frame["opponent_age_raw"].astype("string")
    is_dob = raw.str.fullmatch(r"\d{8}").fillna(False)
    births = pd.to_datetime(raw.where(is_dob), format="%Y%m%d", errors="coerce")
    years = (frame["date_match"] - births).dt.days / _DAYS_PER_YEAR
    ages = pd.to_numeric(raw.where(~is_dob), errors="coerce").astype(float)
    return ages.where(~is_dob, years)


def _clean_matches(records, birth_date):
    frame = _match_frame(records)
    born = pd.to_datetime(str(birth_date), format="%Y%m%d", errors="raise")
    frame["age_player"] = (frame["date_match"] - born).dt.days / _DAYS_PER_YEAR
    frame["age_opponent"] = _opponent_ages(frame)
    valid = (frame["age_player"].between(0, 100) &
             frame["age_opponent"].between(0, 100) & frame["win_lose"].notna())
    cleaned = _finish_matches(frame.loc[valid].copy())
    cleaned.attrs["skipped_rows"] = int((~valid).sum())
    return cleaned


def _finish_matches(cleaned):
    cleaned["age_diff"] = cleaned["age_player"] - cleaned["age_opponent"]
    cleaned["is_walkover"] = cleaned["score"].str.contains("W/O", case=False, regex=False)
    keys = ["date_match", "tournament", "round", "opponent"]
    cleaned = cleaned.drop(columns="opponent_age_raw").drop_duplicates(keys, keep="last")
    cleaned = cleaned.sort_values(["date_match", "opponent", "round"], kind="stable")
    if cleaned.empty:
        raise ValueError("No matches with usable dates, ages, and results")
    return cleaned.reset_index(drop=True)
