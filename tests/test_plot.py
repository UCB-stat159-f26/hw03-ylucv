"""Offline checks for plotted coordinates, styling, and validation."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.axes import Axes
from matplotlib.colors import to_hex

from tennis_career import plot_career_matches
from tennis_career._parse import _clean_matches


@pytest.fixture
def matches(career_rows):
    data = _clean_matches(career_rows, "19810926")
    data.attrs["player"] = "Test Player"
    return data


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def test_scatter_coordinates_and_colors(matches):
    before = matches.copy(deep=True)
    ax = plot_career_matches(matches)
    assert isinstance(ax, Axes)
    assert "Test Player" in ax.get_title(loc="left")
    for artist, result, color in zip(ax.collections, ["won", "lost"], ["#4acbed", "#953a8c"]):
        expected = matches.loc[matches["win_lose"] == result, ["age_player", "age_diff"]]
        np.testing.assert_allclose(artist.get_offsets(), expected.to_numpy(dtype=float))
        assert to_hex(artist.get_facecolors()[0]) == color
    np.testing.assert_array_equal(ax.lines[0].get_ydata(), [0, 0])
    assert [text.get_text() for text in ax.get_legend().get_texts()] == ["Lost", "Won"]
    assert len(ax.texts) == 0
    pd.testing.assert_frame_equal(matches, before)


def test_all_ages_visible_and_figure_saved(matches, tmp_path):
    matches.loc[matches.index[-1], "age_player"] = 45
    ax = plot_career_matches(matches)
    assert ax.get_xlim()[1] > 45
    output = tmp_path / "career.png"
    ax.figure.savefig(output)
    assert output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.parametrize("bad", [None, pd.DataFrame(), pd.DataFrame({"opponent": ["A"]})])
def test_missing_columns(bad):
    with pytest.raises(ValueError, match="columns"):
        plot_career_matches(bad)


def test_empty_data(matches):
    with pytest.raises(ValueError, match="nonempty"):
        plot_career_matches(matches.iloc[:0])


@pytest.mark.parametrize("field,value", [("win_lose", "draw"), ("age_player", np.inf),
                                       ("age_diff", np.nan), ("age_player", -1)])
def test_invalid_plot_values(matches, field, value):
    matches.loc[0, field] = value
    with pytest.raises(ValueError):
        plot_career_matches(matches)


def test_numeric_strings(matches):
    matches["age_player"] = matches["age_player"].astype(str)
    ax = plot_career_matches(matches)
    assert ax.collections
