- **tennis-career** — HW3 Python package; author: ylucv
- Career matches from Tennis Abstract; opponent age scatter plots inspired by [HW2's NYT reference](https://www.nytimes.com/interactive/2022/08/28/sports/tennis/serena-age-opponents.html)
- Installation from GitHub:

  ```bash
  python -m pip install git+https://github.com/UCB-stat159-f26/hw03-ylucv.git
  ```

- Usage — `get_career_matches(player_name)` → pandas DataFrame; `plot_career_matches(matches)` → Matplotlib Axes:

  ```python
  import matplotlib.pyplot as plt
  from tennis_career import get_career_matches, plot_career_matches

  serena = get_career_matches("serena williams")
  ax = plot_career_matches(serena)
  ax.figure.savefig("serena.png", dpi=200, bbox_inches="tight")

  rafa = get_career_matches("Rafael Nadal")
  plot_career_matches(rafa)
  plt.show()

  # Invalid name: ValueError with the supplied name
  get_career_matches("GastonSanchez")
  ```

- Name matching: case-insensitive; optional spaces; `"SerenaWilliams"` also accepted
- Downloads: site player index for name resolution; player profile for birth date and recent matches; career archive when indicated by the profile
- Sources: [player index](https://www.tennisabstract.com/mwplayerlist.js), [Serena archive](https://www.tennisabstract.com/jsmatches/SerenaWilliamsCareer.js), [Nadal archive](https://www.tennisabstract.com/jsmatches/RafaelNadalCareer.js)
- Cleaning:
  - JavaScript array extraction through JSON parsing; no JavaScript execution
  - Female archive opponents: birth dates → fractional ages
  - Male archive opponents: numeric ages; birth dates also supported in newer records
  - Player age: `(match date − player birth date).days / 365.2425`
  - Age difference: player age minus opponent age; positive values → older player
  - Invalid dates, missing ages, or unrecognized results: omitted; count in `matches.attrs["skipped_rows"]`
  - Overlapping archive/profile matches: deduplicated by date, tournament, round, and opponent; recent record preferred
  - Walkovers: retained; marked by `is_walkover`
  - Chronological sorting; all available ages included in plots; tournament dates as approximate match dates
- Output columns:

  | Column | Meaning |
  | --- | --- |
  | `date_match` | Match/tournament date; pandas datetime |
  | `age_player`, `age_opponent` | Fractional ages in years |
  | `age_diff` | Player age minus opponent age |
  | `win_lose` | `won` or `lost` |
  | `opponent`, `tournament`, `surface`, `round`, `score` | Match details |
  | `is_walkover` | Boolean walkover indicator |

- Plot: blue wins; purple losses; equal-age reference at zero; no match annotations
- Errors: `ValueError` for unknown players, unusable source data, or invalid plot input; `ConnectionError` for download failures; 30-second timeout per request
- Development and checks — Python 3.10+:

  ```bash
  python -m venv .venv
  source .venv/bin/activate
  python -m pip install -e '.[dev]'
  python -m pytest --cov=tennis_career --cov-report=term-missing
  python -m ruff check src tests
  python -m build
  ```

- Tests: supplied female/male fixtures; mocked downloads; live requests blocked throughout the automated suite
- CI: Python 3.10 and 3.12; offline tests, lint, package build
- Layout: `src/tennis_career/` package; `tests/fixtures/` source samples; `tests/` offline checks
