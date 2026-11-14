"""Private helpers for Tennis Abstract downloads and player lookup."""

import re
import unicodedata
from urllib.parse import quote

import requests

from ._parse import _read_array

_BASE_URL = "https://www.tennisabstract.com"


def _download(path):
    try:
        response = requests.get(f"{_BASE_URL}/{path}", timeout=30,
                                headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except requests.RequestException as error:
        raise ConnectionError(f"Could not retrieve Tennis Abstract data: {path}") from error
    response.encoding = "utf-8"
    return response.text


def _normalize_name(name):
    folded = unicodedata.normalize("NFKD", name.casefold())
    return "".join(char for char in folded if char.isalpha())


def _resolve_player(player_name):
    if not isinstance(player_name, str) or not _normalize_name(player_name):
        raise ValueError("Player name must be a nonempty string")
    entries = _read_array(_download("mwplayerlist.js"), "playerlist")
    matches = {(entry[1], entry[4:]) for entry in entries
               if _normalize_name(entry[4:]) == _normalize_name(player_name)}
    if len(matches) != 1:
        raise ValueError(f"Unknown or ambiguous player: {player_name!r}; use a full name")
    return matches.pop()


def _player_source(tour, name):
    slug = quote(name.replace(" ", ""), safe="")
    path = (f"jsmatches/{slug}.js" if tour == "W" else
            f"cgi-bin/player-classic.cgi?p={slug}")
    source = _download(path)
    birth = re.search(r"\bvar\s+dob\s*=\s*['\"]?(\d{8})", source)
    if not birth:
        raise ValueError(f"Missing player birth date: {name}")
    return source, birth.group(1), slug


def _career_records(source, slug):
    recent = _read_array(source, "matchmx")
    if re.search(r"\bvar\s+careerjs\s*=\s*1\s*;", source):
        archive = _download(f"jsmatches/{slug}Career.js")
        return _read_array(archive, "morematchmx") + recent
    return recent
