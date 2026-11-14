"""Shared fixtures and a network guard."""

from pathlib import Path

import matplotlib
import pytest
import requests

from tennis_career._parse import _read_array

matplotlib.use("Agg")


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def reject_request(*args, **kwargs):
        raise AssertionError("Live network access forbidden in tests")
    monkeypatch.setattr(requests.sessions.Session, "request", reject_request)


@pytest.fixture(params=["FemalePlayerCareer.js", "MalePlayerCareer.js"])
def career_source(request):
    return (Path(__file__).parent / "fixtures" / request.param).read_text()


@pytest.fixture
def career_rows(career_source):
    return _read_array(career_source, "morematchmx")
