"""Career scatter plot: player age versus opponent age difference."""

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_COLORS = {"won": "#4acbed", "lost": "#953a8c"}
_REQUIRED = {"age_player", "age_diff", "win_lose"}


def _validate_plot_data(matches):
    if not isinstance(matches, pd.DataFrame) or not _REQUIRED.issubset(matches.columns):
        raise ValueError(f"Expected a DataFrame with columns: {sorted(_REQUIRED)}")
    if matches.empty or not matches["win_lose"].isin(_COLORS).all():
        raise ValueError("Expected nonempty match data with 'won' or 'lost' results")
    numeric = matches[["age_player", "age_diff"]].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(numeric.to_numpy(dtype=float, na_value=np.nan)).all():
        raise ValueError("Player ages and age differences must be finite numbers")
    if (numeric["age_player"] < 0).any():
        raise ValueError("Player ages must be nonnegative")
    return matches.assign(**numeric)


def _style_axes(ax, matches):
    ax.axhline(0, color="#b3b3b3", linewidth=1.2, zorder=1)
    ax.set(xlabel="Player age (years)", ylabel="Player age − opponent age (years)")
    ax.set_title(f"{matches.attrs.get('player', 'Player')}: career matches", loc="left")
    ax.grid(color="#e6e6e6", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(math.floor(matches["age_player"].min()) - 0.5,
                math.ceil(matches["age_player"].max()) + 0.5)


def plot_career_matches(matches):
    """Plot cleaned career matches; return a Matplotlib Axes.

    - matches: DataFrame from get_career_matches
    - x: player age; y: player age minus opponent age
    - Blue: wins; purple: losses; gray line: equal ages
    - Save: ax.figure.savefig("career.png", dpi=200)
    - ValueError: missing columns, invalid results, or nonfinite ages
    """
    data = _validate_plot_data(matches)
    _, ax = plt.subplots(figsize=(12, 7), layout="constrained")
    for result, color in _COLORS.items():
        group = data.loc[data["win_lose"] == result]
        ax.scatter(group["age_player"], group["age_diff"], color=color,
                   s=30, alpha=0.7, edgecolors="none", label=result.capitalize())
    _style_axes(ax, data)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], frameon=False, ncol=2, loc="upper left")
    return ax
