"""Public career data retrieval."""

from ._parse import _clean_matches
from ._source import _career_records, _player_source, _resolve_player


def get_career_matches(player_name):
    """Retrieve cleaned career matches as a pandas DataFrame.

    - player_name: full name; spaces and capitalization optional
    - Output: match dates, player/opponent ages, age difference, results
    - ValueError: invalid name or unusable source data
    - ConnectionError: failed download; 30-second timeout per request
    """
    tour, name = _resolve_player(player_name)
    source, birth_date, slug = _player_source(tour, name)
    matches = _clean_matches(_career_records(source, slug), birth_date)
    matches.attrs.update(player=name, birth_date=birth_date)
    return matches
