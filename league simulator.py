from __future__ import annotations

import dataclasses
import os
import time
from html import escape

import numpy as np
import requests
import streamlit as st

MATCHDAY_ACCENT = "#00E5FF"
MATCHDAY_BG = "#050505"


# ==============================================================================
# ECCEZIONI E CONFIGURAZIONE — tutto locale, nessuna dipendenza esterna
# ==============================================================================
class FootballDataError(Exception):
    """Errore controllato per qualunque problema di rete/configurazione/
    risposta verso Football-Data.org."""


FOOTBALL_DATA_API_BASE = "https://api.football-data.org/v4"

FOOTBALL_DATA_COMPETITIONS: dict[str, str] = {
    "England · Premier League": "PL",
    "Italy · Serie A": "SA",
    "Germany · Bundesliga": "BL1",
    "Spain · La Liga": "PD",
    "France · Ligue 1": "FL1",
}


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _get_api_token() -> str | None:
    """Legge la API key da st.secrets o da variabile d'ambiente. Ritorna
    None (invece di sollevare un'eccezione) se non configurata: verrà usata
    solo per tentare la chiamata live; il fallback demo non ne ha bisogno."""
    token = None
    try:
        token = st.secrets.get("FOOTBALL_DATA_API_KEY")  # type: ignore[union-attr]
    except Exception:
        token = None
    if not token:
        token = os.environ.get("FOOTBALL_DATA_API_KEY")
    return token or None


@st.cache_data(ttl=300, show_spinner=False)
def _live_api_get(path: str, params: dict | None = None) -> dict:
    token = _get_api_token()
    if not token:
        raise FootballDataError("Nessuna API key configurata per Football-Data.org.")
    try:
        response = requests.get(
            f"{FOOTBALL_DATA_API_BASE}{path}",
            headers={"X-Auth-Token": token},
            params=params or {},
            timeout=10,
        )
    except requests.RequestException as exc:
        raise FootballDataError(f"Errore di rete verso Football-Data.org: {exc}") from exc

    if response.status_code == 429:
        raise FootballDataError("Rate limit Football-Data.org superato.")
    if response.status_code != 200:
        raise FootballDataError(f"Football-Data.org ha risposto con status {response.status_code}.")

    return response.json()


# ==============================================================================
# DATASET DIMOSTRATIVO INTERNO — nessuna rete richiesta
# ==============================================================================
# Usato in automatico quando la chiamata live fallisce (chiave assente, rete
# irraggiungibile, rate limit...). Garantisce che il modulo sia sempre
# eseguibile in totale autonomia, senza alcuna dipendenza esterna.
_DEMO_TEAM_NAMES: list[str] = [
    "Obsidian United", "Cyan Rovers", "Broadcast City", "Reel Athletic",
    "Vertical Wanderers", "Shorts Town", "HUD Rangers", "Matchday FC",
    "Neon Albion", "Pixel Harbour",
]


def _build_demo_matches() -> list[dict]:
    """Genera uno storico sintetico (partite concluse, per stimare il
    modello) più una giornata di 10 fixture ancora da giocare (matchday=1),
    nello stesso formato JSON di Football-Data.org atteso dal resto del
    modulo."""
    rng = np.random.default_rng(seed=42)
    matches: list[dict] = []

    for round_index in range(3):
        shifted = _DEMO_TEAM_NAMES[round_index:] + _DEMO_TEAM_NAMES[:round_index]
        pairs = list(zip(shifted[: len(shifted) // 2], shifted[len(shifted) // 2 :]))
        for home, away in pairs:
            home_goals = int(rng.poisson(1.4))
            away_goals = int(rng.poisson(1.1))
            matches.append(
                {
                    "status": "FINISHED",
                    "matchday": round_index,
                    "homeTeam": {"name": home},
                    "awayTeam": {"name": away},
                    "score": {"fullTime": {"home": home_goals, "away": away_goals}},
                }
            )

    pairs = list(zip(_DEMO_TEAM_NAMES[:5], _DEMO_TEAM_NAMES[5:]))
    for home, away in pairs:
        matches.append(
            {
                "status": "SCHEDULED",
                "matchday": 1,
                "homeTeam": {"name": home},
                "awayTeam": {"name": away},
                "score": {"fullTime": {"home": None, "away": None}},
            }
        )

    return matches


_DEMO_LEAGUE_DATA: dict[str, list[dict]] = {league: _build_demo_matches() for league in FOOTBALL_DATA_COMPETITIONS}


# ==============================================================================
# ACCESSO DATI — Football-Data.org live, con fallback demo automatico
# ==============================================================================
def fetch_league_matches(league: str) -> list[dict]:
    """Prova prima la chiamata live a Football-Data.org; se fallisce per
    qualunque motivo (chiave assente, rete, rate limit...) ricade sul
    dataset dimostrativo interno, cosi la funzione non solleva mai
    un'eccezione bloccante verso il chiamante."""
    code = FOOTBALL_DATA_COMPETITIONS.get(league)
    if code:
        try:
            data = _live_api_get(f"/competitions/{code}/matches")
            matches = data.get("matches")
            if isinstance(matches, list) and matches:
                return matches
        except FootballDataError:
            pass
    return _DEMO_LEAGUE_DATA.get(league, _build_demo_matches())


def fetch_team_crests(league: str) -> dict[str, str]:
    """Prova la chiamata live per gli stemmi; in fallback ritorna un
    dizionario vuoto (le card mostrano un'icona placeholder al posto dello
    stemma, nessun impatto sulla simulazione)."""
    code = FOOTBALL_DATA_COMPETITIONS.get(league)
    if not code:
        return {}
    try:
        data = _live_api_get(f"/competitions/{code}/teams")
    except FootballDataError:
        return {}
    crests: dict[str, str] = {}
    for team in data.get("teams", []):
        name, crest = team.get("name"), team.get("crest")
        if isinstance(name, str) and isinstance(crest, str):
            crests[name] = crest
    return crests


# ==============================================================================
# MODELLO STATISTICO — Poisson attack/defense + Monte Carlo
# ==============================================================================
@dataclasses.dataclass(frozen=True)
class MatchModel:
    home_team: str
    away_team: str
    home_lambda: float
    away_lambda: float


MDS_MODEL_LAMBDA_FLOOR = 0.15
MDS_MODEL_DEFAULT_HOME_AVG = 1.45
MDS_MODEL_DEFAULT_AWAY_AVG = 1.15


def _finished_matches(matches: list[dict]) -> list[dict]:
    finished: list[dict] = []
    for match in matches:
        if match.get("status") != "FINISHED":
            continue
        full_time = (match.get("score") or {}).get("fullTime") or {}
        home_goals, away_goals = full_time.get("home"), full_time.get("away")
        if not isinstance(home_goals, int) or not isinstance(away_goals, int):
            continue
        home_name = (match.get("homeTeam") or {}).get("name")
        away_name = (match.get("awayTeam") or {}).get("name")
        if isinstance(home_name, str) and isinstance(away_name, str):
            finished.append({"home": home_name, "away": away_name, "home_goals": home_goals, "away_goals": away_goals})
    return finished


def _league_average_goals(finished: list[dict]) -> tuple[float, float]:
    if not finished:
        return MDS_MODEL_DEFAULT_HOME_AVG, MDS_MODEL_DEFAULT_AWAY_AVG
    home_avg = sum(m["home_goals"] for m in finished) / len(finished)
    away_avg = sum(m["away_goals"] for m in finished) / len(finished)
    return max(home_avg, 0.1), max(away_avg, 0.1)


def _team_home_attack(finished: list[dict], team: str, league_home_avg: float) -> float:
    matches = [m for m in finished if m["home"] == team]
    if not matches or league_home_avg <= 0:
        return 1.0
    return (sum(m["home_goals"] for m in matches) / len(matches)) / league_home_avg


def _team_away_attack(finished: list[dict], team: str, league_away_avg: float) -> float:
    matches = [m for m in finished if m["away"] == team]
    if not matches or league_away_avg <= 0:
        return 1.0
    return (sum(m["away_goals"] for m in matches) / len(matches)) / league_away_avg


def _team_home_defense(finished: list[dict], team: str, league_away_avg: float) -> float:
    matches = [m for m in finished if m["home"] == team]
    if not matches or league_away_avg <= 0:
        return 1.0
    return (sum(m["away_goals"] for m in matches) / len(matches)) / league_away_avg


def _team_away_defense(finished: list[dict], team: str, league_home_avg: float) -> float:
    matches = [m for m in finished if m["away"] == team]
    if not matches or league_home_avg <= 0:
        return 1.0
    return (sum(m["home_goals"] for m in matches) / len(matches)) / league_home_avg


def try_build_match_model(league: str, home: str, away: str) -> tuple[MatchModel | None, str | None]:
    """Stima un MatchModel con un classico schema Poisson 'attack/defense'
    sulle partite concluse restituite da fetch_league_matches (locale, con
    fallback demo automatico — vedi sopra)."""
    try:
        matches = fetch_league_matches(league)
    except FootballDataError as exc:
        return None, str(exc)

    finished = _finished_matches(matches)
    league_home_avg, league_away_avg = _league_average_goals(finished)

    home_attack = _team_home_attack(finished, home, league_home_avg)
    away_defense = _team_away_defense(finished, away, league_home_avg)
    away_attack = _team_away_attack(finished, away, league_away_avg)
    home_defense = _team_home_defense(finished, home, league_away_avg)

    home_lambda = max(league_home_avg * home_attack * away_defense, MDS_MODEL_LAMBDA_FLOOR)
    away_lambda = max(league_away_avg * away_attack * home_defense, MDS_MODEL_LAMBDA_FLOOR)

    return MatchModel(home_team=home, away_team=away, home_lambda=home_lambda, away_lambda=away_lambda), None


def run_simulation(model: MatchModel, n_simulations: int = 10_000) -> dict[str, dict[str, np.ndarray]]:
    """Monte Carlo Poisson locale: estrae n_simulations punteggi
    casa/trasferta dai due lambda del model."""
    rng = np.random.default_rng()
    home_goals = rng.poisson(max(model.home_lambda, 0.01), size=n_simulations)
    away_goals = rng.poisson(max(model.away_lambda, 0.01), size=n_simulations)
    return {"raw": {"home_goals": home_goals, "away_goals": away_goals}}


# ==============================================================================
# ENTERTAINMENT CALIBRATION — league-level xG multipliers & score shaping
# ==============================================================================
LEAGUE_GOAL_MULTIPLIERS: dict[str, float] = {
    "England · Premier League": 1.18,
    "Italy · Serie A": 1.15,
    "Germany · Bundesliga": 1.20,
    "Spain · La Liga": 1.00,
    "France · Ligue 1": 1.10,
}
LEAGUE_GOAL_MULTIPLIER_DEFAULT = 1.0

LEAGUE_ZERO_ZERO_SUPPRESSED: set[str] = {"Italy · Serie A"}

MDS_MAX_GOALS_PER_TEAM = 4
MDS_LAMBDA_CEILING = 3.0
MDS_ZERO_ZERO_RESAMPLE_ATTEMPTS = 25

MDS_ZERO_ZERO_MATCHDAY_CAP = 2
# HARD CAP GIORNATA: al massimo questo numero di 0-0 può comparire come
# punteggio rivelato nell'intera giornata simulata.

MDS_ZERO_ZERO_BOOST_STEP = 0.50
# Incremento di xG (additivo, cumulativo) applicato ad ogni giro del ciclo
# while anti-0-0 di giornata, SOLO ai match ancora 0-0.

MDS_ZERO_ZERO_MAX_BOOST_ROUNDS = 15

MDS_HOOK_SECONDS = 1.5
MDS_CARD_REVEAL_DELAY_SECONDS = 0.6


def _apply_league_calibration(league: str, home_lambda: float, away_lambda: float) -> tuple[float, float, float]:
    multiplier = LEAGUE_GOAL_MULTIPLIERS.get(league, LEAGUE_GOAL_MULTIPLIER_DEFAULT)
    adj_home = clamp(home_lambda * multiplier, 0.1, MDS_LAMBDA_CEILING)
    adj_away = clamp(away_lambda * multiplier, 0.1, MDS_LAMBDA_CEILING)
    return adj_home, adj_away, multiplier


def _cap_extreme_scores(home_goals: np.ndarray, away_goals: np.ndarray) -> None:
    np.clip(home_goals, 0, MDS_MAX_GOALS_PER_TEAM, out=home_goals)
    np.clip(away_goals, 0, MDS_MAX_GOALS_PER_TEAM, out=away_goals)


def _suppress_zero_zero(
    rng: np.random.Generator, home_goals: np.ndarray, away_goals: np.ndarray, home_lambda: float, away_lambda: float
) -> None:
    zero_zero_mask = (home_goals == 0) & (away_goals == 0)
    indices = np.flatnonzero(zero_zero_mask)
    if indices.size == 0:
        return
    for index in indices:
        for _attempt in range(MDS_ZERO_ZERO_RESAMPLE_ATTEMPTS):
            new_home = rng.poisson(home_lambda)
            new_away = rng.poisson(away_lambda)
            if new_home != 0 or new_away != 0:
                home_goals[index] = new_home
                away_goals[index] = new_away
                break
        else:
            home_goals[index] = 1
            away_goals[index] = 0


def _empirical_score_and_outcomes(home_goals: np.ndarray, away_goals: np.ndarray) -> dict[str, object]:
    n = len(home_goals)
    pairs, counts = np.unique(np.stack([home_goals, away_goals], axis=1), axis=0, return_counts=True)
    top_index = int(np.argmax(counts))
    top_home, top_away = pairs[top_index]
    home_wins = float((home_goals > away_goals).sum())
    draws = float((home_goals == away_goals).sum())
    away_wins = float((home_goals < away_goals).sum())
    return {
        "score": f"{int(top_home)}-{int(top_away)}",
        "home_goals_total": int(top_home),
        "away_goals_total": int(top_away),
        "home_prob": home_wins / n,
        "draw_prob": draws / n,
        "away_prob": away_wins / n,
    }


def _revealed_outcome_pill(outcome: dict[str, object]) -> tuple[str, float]:
    home_goals, away_goals = outcome["home_goals_total"], outcome["away_goals_total"]
    if home_goals > away_goals:
        return "1", outcome["home_prob"]
    if home_goals < away_goals:
        return "2", outcome["away_prob"]
    return "X", outcome["draw_prob"]


# ==============================================================================
# CSS — Obsidian / Electric Cyan Broadcast HUD (9:16)
# ==============================================================================
MATCHDAY_CSS = f"""
<style>
.mds-wrap {{
    background: {MATCHDAY_BG};
    border: 1px solid rgba(0,229,255,0.35);
    border-radius: 18px;
    padding: 18px 20px;
    margin-bottom: 16px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5), 0 0 22px rgba(0,229,255,0.10);
}}

.mds-hook-wrap {{
    background: {MATCHDAY_BG};
    border: 1px solid rgba(0,229,255,0.55);
    border-radius: 20px;
    padding: 34px 22px;
    margin-bottom: 16px;
    text-align: center;
    box-shadow: 0 12px 38px rgba(0,0,0,0.6), 0 0 36px rgba(0,229,255,0.18);
}}
.mds-hook-title {{
    font-family: "Courier New", monospace;
    font-size: 1.5rem;
    font-weight: 900;
    letter-spacing: 0.10em;
    color: {MATCHDAY_ACCENT};
    text-shadow: 0 0 16px rgba(0,229,255,0.85);
    margin-bottom: 8px;
    animation: mdsPulse 1s ease-in-out infinite;
}}
.mds-hook-subtitle {{
    font-family: "Courier New", monospace;
    font-size: 0.85rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #d8dadc;
    margin-bottom: 18px;
}}
.mds-hook-track {{
    width: 100%;
    height: 8px;
    border-radius: 999px;
    background: rgba(255,255,255,0.08);
    overflow: hidden;
}}
.mds-hook-fill {{
    height: 100%;
    width: 0%;
    border-radius: 999px;
    background: linear-gradient(90deg, {MATCHDAY_ACCENT}, #00ff87);
    box-shadow: 0 0 14px rgba(0,229,255,0.85);
    animation: mdsFill {MDS_HOOK_SECONDS}s cubic-bezier(0.22, 0.61, 0.36, 1) forwards;
}}
@keyframes mdsFill {{
    from {{ width: 0%; }}
    to {{ width: 100%; }}
}}
@keyframes mdsPulse {{
    0%, 100% {{ opacity: 0.6; }}
    50% {{ opacity: 1; }}
}}

.mds-card {{
    position: relative;
    background: {MATCHDAY_BG};
    border: 1px solid {MATCHDAY_ACCENT};
    border-radius: 18px;
    padding: 22px 16px 36px 16px;
    margin-bottom: 14px;
    box-shadow: 0 0 22px rgba(0,229,255,0.16), 0 8px 22px rgba(0,0,0,0.55);
    text-align: center;
    opacity: 0;
    animation: mdsCardIn 0.4s ease forwards;
}}
@keyframes mdsCardIn {{
    from {{ opacity: 0; transform: translateY(14px) scale(0.985); }}
    to {{ opacity: 1; transform: translateY(0) scale(1); }}
}}
.mds-calib-tag {{
    position: absolute;
    top: 10px;
    left: 14px;
    font-family: "Courier New", monospace;
    font-size: 0.58rem;
    letter-spacing: 0.03em;
    color: {MATCHDAY_ACCENT};
    opacity: 0.7;
}}
.mds-card-teams {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 18px;
}}
.mds-team {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    min-width: 0;
}}
.mds-crest {{
    width: 58px;
    height: 58px;
    object-fit: contain;
}}
.mds-crest-placeholder {{
    width: 58px;
    height: 58px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.9rem;
    opacity: 0.6;
}}
.mds-team-name {{
    font-weight: 800;
    font-size: 0.86rem;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    color: #f5f5f5;
    text-align: center;
    overflow-wrap: break-word;
    line-height: 1.2;
    min-height: 2.1em;
}}
.mds-score {{
    font-size: 3.1rem;
    font-weight: 900;
    letter-spacing: 0.05em;
    font-variant-numeric: tabular-nums;
    background: linear-gradient(135deg, {MATCHDAY_ACCENT}, #ffffff);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin: 0 4px;
    line-height: 1;
    white-space: nowrap;
}}
.mds-pill {{
    position: absolute;
    bottom: 12px;
    right: 14px;
    font-family: "Courier New", monospace;
    font-size: 0.74rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    padding: 4px 14px;
    border-radius: 999px;
    border: 1px solid rgba(0,229,255,0.55);
    background: rgba(0,229,255,0.10);
    color: {MATCHDAY_ACCENT};
    white-space: nowrap;
}}
.mds-header-title {{
    font-family: "Courier New", monospace;
    font-size: 1.05rem;
    font-weight: 900;
    letter-spacing: 0.1em;
    color: {MATCHDAY_ACCENT};
    text-transform: uppercase;
    text-shadow: 0 0 10px rgba(0,229,255,0.5);
    margin-bottom: 4px;
}}
.mds-disclaimer {{
    font-size: 0.72rem;
    color: #9aa0a6;
    line-height: 1.4;
    margin: 4px 0 14px 0;
    padding: 8px 12px;
    border-left: 3px solid {MATCHDAY_ACCENT};
    background: rgba(0,229,255,0.05);
    border-radius: 6px;
}}

.mds-summary-wrap {{
    background: {MATCHDAY_BG};
    border: 1px solid {MATCHDAY_ACCENT};
    border-radius: 18px;
    padding: 18px 16px;
    margin-top: 6px;
    box-shadow: 0 0 24px rgba(0,229,255,0.18), 0 8px 22px rgba(0,0,0,0.55);
    opacity: 0;
    animation: mdsCardIn 0.5s ease forwards;
}}
.mds-summary-title {{
    font-family: "Courier New", monospace;
    font-size: 0.8rem;
    font-weight: 900;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {MATCHDAY_ACCENT};
    text-align: center;
    margin-bottom: 12px;
    text-shadow: 0 0 8px rgba(0,229,255,0.5);
}}
.mds-summary-row {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: center;
}}
.mds-summary-badge {{
    flex: 1;
    min-width: 110px;
    background: #0a0a0a;
    border: 1px solid rgba(0,229,255,0.5);
    border-radius: 14px;
    padding: 10px 12px;
    text-align: center;
}}
.mds-summary-value {{
    font-family: "Courier New", monospace;
    font-size: 1.35rem;
    font-weight: 900;
    color: {MATCHDAY_ACCENT};
    text-shadow: 0 0 10px rgba(0,229,255,0.6);
    line-height: 1.1;
}}
.mds-summary-label {{
    font-size: 0.63rem;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #9aa0a6;
    margin-top: 2px;
}}
.mds-surprise-box {{
    margin-top: 10px;
    background: #0a0a0a;
    border: 1px solid rgba(0,229,255,0.5);
    border-radius: 14px;
    padding: 12px 14px;
    text-align: center;
}}
.mds-surprise-label {{
    font-size: 0.63rem;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #9aa0a6;
    margin-bottom: 4px;
}}
.mds-surprise-value {{
    font-family: "Courier New", monospace;
    font-size: 1.0rem;
    font-weight: 800;
    color: #f5f5f5;
    letter-spacing: 0.02em;
}}
.mds-surprise-value span {{
    color: {MATCHDAY_ACCENT};
}}
</style>
"""


# ==============================================================================
# DATA HELPERS
# ==============================================================================
def _available_matchdays(league: str) -> list[int]:
    try:
        matches = fetch_league_matches(league)
    except FootballDataError:
        return []
    return sorted({int(match["matchday"]) for match in matches if isinstance(match.get("matchday"), int)})


def _matchday_fixtures(league: str, matchday: int) -> list[tuple[str, str]]:
    try:
        matches = fetch_league_matches(league)
    except FootballDataError:
        return []
    fixtures: list[tuple[str, str]] = []
    for match in matches:
        if match.get("matchday") != matchday:
            continue
        home_team = match.get("homeTeam", {})
        away_team = match.get("awayTeam", {})
        if not isinstance(home_team, dict) or not isinstance(away_team, dict):
            continue
        home_name, away_name = home_team.get("name"), away_team.get("name")
        if isinstance(home_name, str) and isinstance(away_name, str):
            fixtures.append((home_name, away_name))
    return fixtures


# ==============================================================================
# SIMULATION — raw fixture pass + matchday-wide anti-zero-zero while-loop
# ==============================================================================
def _simulate_fixture_raw(league: str, home: str, away: str, calibration_enabled: bool):
    model, error = try_build_match_model(league, home, away)
    if model is None:
        return None, error, None, None, []

    if calibration_enabled:
        adj_home, adj_away, multiplier = _apply_league_calibration(league, model.home_lambda, model.away_lambda)
        model = dataclasses.replace(model, home_lambda=adj_home, away_lambda=adj_away)
    else:
        multiplier = 1.0

    simulation = run_simulation(model, n_simulations=10_000)
    home_goals = simulation["raw"]["home_goals"].copy()
    away_goals = simulation["raw"]["away_goals"].copy()

    calib_notes: list[str] = []
    if calibration_enabled:
        if multiplier != 1.0:
            calib_notes.append(f"×{multiplier:.2f} xG")
        if league in LEAGUE_ZERO_ZERO_SUPPRESSED:
            rng = np.random.default_rng()
            _suppress_zero_zero(rng, home_goals, away_goals, model.home_lambda, model.away_lambda)
            calib_notes.append("No 0-0")
        _cap_extreme_scores(home_goals, away_goals)
        calib_notes.append(f"Cap {MDS_MAX_GOALS_PER_TEAM}")

    return model, None, home_goals, away_goals, calib_notes


def _run_full_matchday(league: str, fixtures: list[tuple[str, str]], calibration_enabled: bool) -> list[dict[str, object]]:
    """1) Simula tutte le fixture in un array temporaneo (`results`).
    2) Se calibrazione abilitata e gli 0-0 rivelati sono > MDS_ZERO_ZERO_
       MATCHDAY_CAP (2), un ciclo while incrementa di MDS_ZERO_ZERO_BOOST_
       STEP (+0.50) l'xG (cumulativo) SOLO dei match ancora 0-0 e li
       ri-simula da zero, finché il conteggio non scende a <= 2 o si
       raggiunge il tetto di sicurezza MDS_ZERO_ZERO_MAX_BOOST_ROUNDS."""
    results: list[dict[str, object]] = []
    fixture_state: list[dict[str, object] | None] = []

    for home, away in fixtures:
        model, error, home_goals, away_goals, calib_notes = _simulate_fixture_raw(league, home, away, calibration_enabled)
        if model is None:
            results.append({"home": home, "away": away, "error": error})
            fixture_state.append(None)
            continue
        outcome = _empirical_score_and_outcomes(home_goals, away_goals)
        outcome["home"] = home
        outcome["away"] = away
        outcome["calib_tag"] = "⚙️ " + " · ".join(calib_notes) if calib_notes else ""
        results.append(outcome)
        fixture_state.append({"model": model, "calib_notes": calib_notes})

    if calibration_enabled:
        cumulative_boost = 0.0
        rounds = 0
        while rounds < MDS_ZERO_ZERO_MAX_BOOST_ROUNDS:
            zero_zero_indices = [i for i, r in enumerate(results) if "error" not in r and r.get("score") == "0-0"]
            if len(zero_zero_indices) <= MDS_ZERO_ZERO_MATCHDAY_CAP:
                break

            rounds += 1
            cumulative_boost += MDS_ZERO_ZERO_BOOST_STEP
            rng = np.random.default_rng()

            for i in zero_zero_indices:
                state = fixture_state[i]
                base_model = state["model"]
                boosted_home = clamp(base_model.home_lambda + cumulative_boost, 0.1, MDS_LAMBDA_CEILING)
                boosted_away = clamp(base_model.away_lambda + cumulative_boost, 0.1, MDS_LAMBDA_CEILING)
                boosted_model = dataclasses.replace(base_model, home_lambda=boosted_home, away_lambda=boosted_away)

                simulation = run_simulation(boosted_model, n_simulations=10_000)
                home_goals = simulation["raw"]["home_goals"].copy()
                away_goals = simulation["raw"]["away_goals"].copy()
                _cap_extreme_scores(home_goals, away_goals)
                _suppress_zero_zero(rng, home_goals, away_goals, boosted_home, boosted_away)
                _cap_extreme_scores(home_goals, away_goals)

                outcome = _empirical_score_and_outcomes(home_goals, away_goals)
                notes = list(state["calib_notes"]) + [f"0-0 cap +{cumulative_boost:.2f} xG"]
                outcome["home"] = fixtures[i][0]
                outcome["away"] = fixtures[i][1]
                outcome["calib_tag"] = "⚙️ " + " · ".join(notes)
                results[i] = outcome

    return results


# ==============================================================================
# RENDERING — HUD Broadcast engine (hook + one-by-one reveal + summary)
# ==============================================================================
def _render_hook_banner(placeholder) -> None:
    placeholder.markdown(
        f'<div class="mds-hook-wrap">'
        f'<div class="mds-hook-title">⚡ WAYNELAB AI ENGINE</div>'
        f'<div class="mds-hook-subtitle">10,000 MONTE CARLO RUNS...</div>'
        f'<div class="mds-hook-track"><div class="mds-hook-fill"></div></div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _crest_html(name: str, crests: dict[str, str]) -> str:
    url = crests.get(name)
    if url:
        return f'<img src="{escape(url)}" class="mds-crest" />'
    return '<div class="mds-crest-placeholder">🛡️</div>'


def _render_match_card(home: str, away: str, outcome: dict[str, object], crests: dict[str, str]) -> None:
    calib_tag = outcome.get("calib_tag", "")
    calib_html = f'<div class="mds-calib-tag">{escape(calib_tag)}</div>' if calib_tag else ""
    pill_code, pill_prob = _revealed_outcome_pill(outcome)
    st.markdown(
        f'<div class="mds-card">'
        f"{calib_html}"
        f'<div class="mds-card-teams">'
        f'<div class="mds-team">{_crest_html(home, crests)}'
        f'<div class="mds-team-name">{escape(home)}</div></div>'
        f'<div class="mds-score">{escape(outcome["score"])}</div>'
        f'<div class="mds-team">{_crest_html(away, crests)}'
        f'<div class="mds-team-name">{escape(away)}</div></div>'
        f"</div>"
        f'<div class="mds-pill">{pill_code} · {pill_prob:.0%}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _most_surprising_result(results: list[dict[str, object]]) -> str:
    """Individua il match il cui esito rivelato aveva, tra i tre 1X2
    calcolati sugli stessi array Monte Carlo, la probabilità più bassa —
    cioè il risultato statisticamente meno atteso della giornata."""
    valid = [r for r in results if "error" not in r and "home_goals_total" in r]
    if not valid:
        return "—"
    surprise_pick = min(valid, key=lambda r: _revealed_outcome_pill(r)[1])
    _, prob = _revealed_outcome_pill(surprise_pick)
    return (
        f'{escape(str(surprise_pick["home"]))} <span>{escape(str(surprise_pick["score"]))}</span> '
        f'{escape(str(surprise_pick["away"]))} — only {prob:.0%} predicted'
    )


def _render_matchday_summary(results: list[dict[str, object]]) -> None:
    valid = [r for r in results if "error" not in r and "home_goals_total" in r]
    if not valid:
        return
    total_goals = sum(r["home_goals_total"] + r["away_goals_total"] for r in valid)
    avg_goals = total_goals / len(valid)
    surprise_html = _most_surprising_result(results)

    st.markdown(
        '<div class="mds-summary-wrap">'
        '<div class="mds-summary-title">📊 Matchday Summary</div>'
        '<div class="mds-summary-row">'
        f'<div class="mds-summary-badge"><div class="mds-summary-value">{total_goals}</div>'
        f'<div class="mds-summary-label">Total Goals</div></div>'
        f'<div class="mds-summary-badge"><div class="mds-summary-value">{avg_goals:.2f}</div>'
        f'<div class="mds-summary-label">Avg Goals / Match</div></div>'
        "</div>"
        '<div class="mds-surprise-box">'
        '<div class="mds-surprise-label">🎲 Most Surprising Result</div>'
        f'<div class="mds-surprise-value">{surprise_html}</div>'
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


# ==============================================================================
# MAIN TAB ENTRY POINT — nessun parametro, nessuna dipendenza esterna
# ==============================================================================
def render_matchday_simulator_tab() -> None:
    """Entry point della tab. Nessun argomento richiesto: tutte le funzioni
    di supporto (dati, modello Poisson/Monte Carlo, CSS, dataset demo di
    fallback) sono definite più sopra in questo stesso file."""
    st.markdown(MATCHDAY_CSS, unsafe_allow_html=True)
    st.markdown('<div class="mds-header-title">🏆 MATCHDAY LIVE SIMULATOR</div>', unsafe_allow_html=True)
    st.caption(
        "Standalone HUD Broadcast engine, built for TikTok/Reels/Shorts recordings (9:16) — one "
        "match revealed at a time, powered by its own local Poisson attack/defense model."
    )
    st.markdown(
        '<div class="mds-disclaimer">🎬 <b>Entertainment Calibration</b>: this tab applies '
        "discretionary per-league xG multipliers and score-shaping rules (goal cap, 0-0 exclusion "
        "for select leagues, max 2×0-0 per matchday via an xG boost loop) tuned for social-video "
        "pacing. This module runs its own standalone Poisson model — turn the toggle off below to "
        "see the model without engagement calibration.</div>",
        unsafe_allow_html=True,
    )

    calibration_enabled = st.toggle(
        "🎯 Enable Engagement Calibration (league xG multipliers, 0-0 cap, score cap)",
        value=True,
        key="mds_calibration_enabled",
    )

    col_league, col_matchday = st.columns(2)
    with col_league:
        league = st.selectbox("Competition", options=list(FOOTBALL_DATA_COMPETITIONS), key="mds_league_select")

    matchdays = _available_matchdays(league)
    with col_matchday:
        if matchdays:
            matchday = st.selectbox(
                "Matchday", options=matchdays, format_func=lambda n: f"Giornata {n}", key="mds_matchday_select"
            )
        else:
            st.warning("No live matchday data available for this competition.")
            return

    fixtures = _matchday_fixtures(league, matchday)
    if not fixtures:
        st.info(f"No fixtures found for Giornata {matchday} in {league}.")
        return

    st.caption(f"📋 {len(fixtures)} fixtures loaded for Giornata {matchday}.")

    run_clicked = st.button("⚡ SIMULATE FULL MATCHDAY", type="primary", key="mds_run_button")

    try:
        crests = fetch_team_crests(league)
    except FootballDataError:
        crests = {}

    if run_clicked:
        # RESET RIGIDO DELLO STATO: cancella esplicitamente qualunque chiave
        # di session_state riconducibile a questo modulo PRIMA di generare
        # la nuova giornata, così la UI riparte sempre da zero. Il filtro è
        # basato su substring ampio ("matchday"/"mds"/"results") e cancella
        # anche le chiavi dei widget di questa tab — è voluto: garantisce un
        # refresh visivo completo ad ogni simulazione. I valori già letti in
        # questa run (calibration_enabled, league, matchday) restano validi.
        # IMPORTANTE: nessun risultato viene scritto in st.session_state
        # prima o durante il ciclo di reveal qui sotto — solo DOPO che tutte
        # le card sono state mostrate una alla volta (vedi punto 4). Questo
        # è tassativo: scrivere in session_state durante l'animazione
        # innesca un rerun di Streamlit che interrompe la sequenza.
        for key in list(st.session_state.keys()):
            if "matchday" in key or "mds" in key or "results" in key:
                del st.session_state[key]

        # 1) Hook da social: banner temporaneo dentro un st.empty(), visibile
        #    per 1.5s, poi svuotato esplicitamente.
        hook_placeholder = st.empty()
        _render_hook_banner(hook_placeholder)
        time.sleep(MDS_HOOK_SECONDS)
        hook_placeholder.empty()

        # 2) Simulazione completa della giornata, calcolata INTERAMENTE IN
        #    MEMORIA prima di disegnare qualunque card (hard cap anti-0-0 a
        #    ciclo while incluso — vedi _run_full_matchday). Questo passaggio
        #    non scrive nulla a schermo: la UI resta vuota (subito dopo
        #    l'hook) finché il calcolo non è completo.
        results = _run_full_matchday(league, fixtures, calibration_enabled)

        # 3) REVEAL SEQUENZIALE — CRITICO: un contenitore dinamico unico,
        #    poi un ciclo esplicito for i, outcome in enumerate(results) che
        #    per ogni iterazione (a) crea uno slot st.empty() dedicato dentro
        #    il contenitore, (b) ci disegna dentro la card corrente, (c) SOLO
        #    DOPO chiama time.sleep(0.6). Ogni slot è un elemento nuovo e
        #    distinto: Streamlit invia il relativo aggiornamento al browser
        #    non appena viene scritto, quindi il time.sleep successivo crea
        #    un ritardo visibile reale prima della card successiva. Se anche
        #    con questa struttura le card continuano a comparire tutte
        #    insieme, la causa non è in questo file (l'ordine
        #    disegna-poi-aspetta è quello corretto e standard di Streamlit)
        #    ma quasi certamente un livello di buffering a monte
        #    (reverse proxy / CDN che bufferizza la risposta HTTP/WebSocket
        #    prima di consegnarla al browser): in tal caso va disattivato il
        #    buffering lato hosting, non modificato lo script Python.
        cards_container = st.container()
        for index, outcome in enumerate(results):
            card_slot = cards_container.empty()
            with card_slot.container():
                if "error" in outcome:
                    st.warning(f"{outcome['home']} vs {outcome['away']}: {outcome['error']}")
                else:
                    _render_match_card(outcome["home"], outcome["away"], outcome, crests)
            time.sleep(MDS_CARD_REVEAL_DELAY_SECONDS)

        # 4) Banner di riepilogo finale — disegnato, e SOLO ORA i risultati
        #    vengono eventualmente esposti ad altre parti dello stato (qui
        #    non serve nemmeno: la tab non li ripersiste, cosi il reset del
        #    punto 1 al prossimo click riparte sempre pulito).
        _render_matchday_summary(results)
        st.success(f"✅ Giornata {matchday} fully simulated — {len(fixtures)} matches.")
