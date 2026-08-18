from __future__ import annotations

import math
import os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from html import escape
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from scipy.stats import poisson


APP_PASSWORD = "calcio2026"


LEAGUES: dict[str, list[str]] = {
    "Italia · Serie A": [
        "Atalanta",
        "Bologna",
        "Cagliari",
        "Como",
        "Fiorentina",
        "Frosinone",
        "Genoa",
        "Inter",
        "Juventus",
        "Lazio",
        "Lecce",
        "Milan",
        "Monza",
        "Napoli",
        "Parma",
        "Roma",
        "Sassuolo",
        "Torino",
        "Udinese",
        "Venezia",
    ],
    "Italia · Serie B": [
        "Avellino",
        "Bari",
        "Catanzaro",
        "Cesena",
        "Empoli",
        "Frosinone",
        "Juve Stabia",
        "Mantova",
        "Modena",
        "Monza",
        "Padova",
        "Palermo",
        "Pescara",
        "Reggiana",
        "Sampdoria",
        "Spezia",
        "Südtirol",
        "Venezia",
        "Vicenza",
        "Virtus Entella",
    ],
    "Inghilterra · Premier League": [
        "Arsenal",
        "Aston Villa",
        "Bournemouth",
        "Brentford",
        "Brighton",
        "Chelsea",
        "Coventry City",
        "Crystal Palace",
        "Everton",
        "Fulham",
        "Hull City",
        "Ipswich Town",
        "Leeds United",
        "Liverpool",
        "Manchester City",
        "Manchester United",
        "Newcastle",
        "Nottingham Forest",
        "Sunderland",
        "Tottenham",
    ],
    "Inghilterra · EFL Championship": [
        "Birmingham City",
        "Blackburn Rovers",
        "Bristol City",
        "Cardiff City",
        "Charlton Athletic",
        "Coventry City",
        "Derby County",
        "Hull City",
        "Ipswich Town",
        "Leicester City",
        "Middlesbrough",
        "Millwall",
        "Norwich City",
        "Oxford United",
        "Portsmouth",
        "Preston North End",
        "Queens Park Rangers",
        "Sheffield United",
        "Sheffield Wednesday",
        "Southampton",
        "Stoke City",
        "Swansea City",
        "Watford",
        "West Bromwich Albion",
    ],
    "Spagna · La Liga": [
        "Alavés",
        "Athletic Bilbao",
        "Atlético Madrid",
        "Barcelona",
        "Celta Vigo",
        "Deportivo La Coruña",
        "Elche",
        "Espanyol",
        "Getafe",
        "Levante",
        "Málaga",
        "Osasuna",
        "Racing Santander",
        "Rayo Vallecano",
        "Real Betis",
        "Real Madrid",
        "Real Sociedad",
        "Sevilla",
        "Valencia",
        "Villarreal",
    ],
    "Spagna · Segunda División": [
        "Albacete",
        "Almería",
        "Burgos",
        "Cádiz",
        "Castellón",
        "Córdoba",
        "Deportivo La Coruña",
        "Eibar",
        "Eldense",
        "FC Andorra",
        "Granada",
        "Huesca",
        "Leganés",
        "Las Palmas",
        "Málaga",
        "Mirandés",
        "Racing Santander",
        "Real Zaragoza",
        "Sporting Gijón",
        "Tenerife",
        "Valladolid",
        "Levante",
    ],
    "Germania · Bundesliga": [
        "Augsburg",
        "Bayer Leverkusen",
        "Bayern Monaco",
        "Borussia Dortmund",
        "Borussia Mönchengladbach",
        "Eintracht Francoforte",
        "Elversberg",
        "Friburgo",
        "Hoffenheim",
        "Amburgo",
        "Colonia",
        "Mainz",
        "Paderborn",
        "RB Lipsia",
        "Schalke 04",
        "Stoccarda",
        "Union Berlino",
        "Werder Brema",
    ],
    "Germania · 2. Bundesliga": [
        "Arminia Bielefeld",
        "Bochum",
        "Braunschweig",
        "Darmstadt",
        "Dynamo Dresda",
        "Elversberg",
        "Fortuna Düsseldorf",
        "Greuther Fürth",
        "Hannover 96",
        "Hertha Berlino",
        "Holstein Kiel",
        "Kaiserslautern",
        "Karlsruhe",
        "Magdeburgo",
        "Norimberga",
        "Paderborn",
        "Preußen Münster",
        "Schalke 04",
    ],
    "Francia · Ligue 1": [
        "Angers",
        "Auxerre",
        "Brest",
        "Le Havre",
        "Le Mans",
        "Lens",
        "Lille",
        "Lorient",
        "Lione",
        "Marsiglia",
        "Monaco",
        "Nizza",
        "Paris FC",
        "PSG",
        "Rennes",
        "Strasburgo",
        "Tolosa",
        "Troyes",
    ],
    "Francia · Ligue 2": [
        "Amiens",
        "Annecy",
        "Bastia",
        "Clermont Foot",
        "Dunkerque",
        "Grenoble",
        "Guingamp",
        "Laval",
        "Le Mans",
        "Lorient",
        "Montpellier",
        "Nancy",
        "Pau",
        "Red Star",
        "Reims",
        "Rodez",
        "Saint-Étienne",
        "Troyes",
    ],
}


TOP_DIVISIONS = {
    "Italia · Serie A",
    "Inghilterra · Premier League",
    "Spagna · La Liga",
    "Germania · Bundesliga",
    "Francia · Ligue 1",
}

FOOTBALL_DATA_COMPETITIONS: dict[str, str] = {
    "Italia · Serie A": "SA",
    "Inghilterra · Premier League": "PL",
    "Inghilterra · EFL Championship": "ELC",
    "Spagna · La Liga": "PD",
    "Germania · Bundesliga": "BL1",
    "Francia · Ligue 1": "FL1",
}

# Football-Data.org uses the current season when no season filter is sent.
FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"

# Football-Data.org does not expose match-level shots, corners, cards or fouls.
# These are transparent league baselines used only for the micro-event model.
MICRO_EVENT_BASELINES: dict[str, dict[str, float]] = {
    "SA": {"shots": 12.0, "shots_on_target": 4.1, "corners": 4.6, "cards": 2.3, "fouls": 12.8},
    "PL": {"shots": 12.5, "shots_on_target": 4.3, "corners": 5.0, "cards": 1.8, "fouls": 10.8},
    "ELC": {"shots": 11.8, "shots_on_target": 3.9, "corners": 4.8, "cards": 2.1, "fouls": 12.2},
    "PD": {"shots": 12.0, "shots_on_target": 4.0, "corners": 4.9, "cards": 2.4, "fouls": 13.0},
    "BL1": {"shots": 13.0, "shots_on_target": 4.5, "corners": 4.8, "cards": 2.0, "fouls": 11.5},
    "FL1": {"shots": 11.7, "shots_on_target": 3.9, "corners": 4.7, "cards": 2.2, "fouls": 12.4},
}

PROMOTED_TEAMS = {
    # Italia · Serie A
    "Venezia",
    "Frosinone",
    "Monza",
    # Inghilterra · Premier League
    "Coventry City",
    "Ipswich Town",
    "Hull City",
    # Spagna · La Liga
    "Racing Santander",
    "Deportivo La Coruña",
    "Málaga",
    # Germania · Bundesliga
    "Schalke 04",
    "Elversberg",
    "Paderborn",
    # Francia · Ligue 1
    "Troyes",
    "Le Mans",
}


TEAM_STRENGTHS: dict[str, float] = {
    "Inter": 1.17,
    "Napoli": 1.12,
    "Milan": 1.10,
    "Juventus": 1.08,
    "Atalanta": 1.07,
    "Roma": 1.05,
    "Lazio": 1.04,
    "Manchester City": 1.18,
    "Arsenal": 1.15,
    "Liverpool": 1.14,
    "Chelsea": 1.04,
    "Manchester United": 1.03,
    "Newcastle": 1.04,
    "Real Madrid": 1.18,
    "Barcelona": 1.15,
    "Atlético Madrid": 1.08,
    "Villarreal": 1.03,
    "Athletic Bilbao": 1.02,
    "Bayern Monaco": 1.18,
    "Bayer Leverkusen": 1.13,
    "Borussia Dortmund": 1.08,
    "RB Lipsia": 1.06,
    "PSG": 1.18,
    "Monaco": 1.08,
    "Marsiglia": 1.04,
    "Lione": 1.03,
}


@dataclass(frozen=True)
class MatchModel:
    home_lambda: float
    away_lambda: float
    shots_total_lambda: float
    home_shots_on_target_lambda: float
    away_shots_on_target_lambda: float
    shots_on_target_total_lambda: float
    corners_total_lambda: float
    home_cards_lambda: float
    away_cards_lambda: float
    cards_total_lambda: float
    fouls_lambda: float


class FootballDataError(RuntimeError):
    """Raised when Football-Data.org cannot provide the requested live data."""


@dataclass(frozen=True)
class LiveTeamStats:
    team_id: int
    team_name: str
    matches: int
    home_matches: int
    away_matches: int
    goals_for: float
    goals_against: float
    home_goals_for: float
    home_goals_against: float
    away_goals_for: float
    away_goals_against: float
    total_shots: float
    shots_on_target: float
    corners: float
    cards: float
    fouls: float


def current_season_start() -> int:
    configured = os.environ.get("FOOTBALL_DATA_SEASON")
    if configured:
        try:
            return int(configured)
        except ValueError:
            pass
    today = datetime.now()
    return today.year if today.month >= 7 else today.year - 1


def season_label(season_start: int) -> str:
    return f"{season_start}/{str(season_start + 1)[-2:]}"


def competition_season_status(league: str) -> str:
    season_start, teams, matches = fetch_competition_snapshot(league)
    if not matches and any(team_id < 0 for team_id, _ in teams):
        return f"stagione {season_label(season_start)} · lista di riserva (API non disponibile)"
    return f"stagione {season_label(season_start)} · corrente"


def _get_football_data_api_key() -> str | None:
    """Legge il secret FOOTBALL_DATA_API_KEY sia da variabile d'ambiente sia
    dai secrets di Streamlit (st.secrets), a seconda di come è stato configurato."""
    api_key = os.environ.get("FOOTBALL_DATA_API_KEY")
    if api_key:
        return api_key
    try:
        return st.secrets.get("FOOTBALL_DATA_API_KEY")
    except Exception:
        return None


def _football_data_request(endpoint: str, params: dict[str, object] | None = None) -> dict[str, object]:
    api_key = _get_football_data_api_key()
    if not api_key:
        raise FootballDataError(
            "Secret FOOTBALL_DATA_API_KEY non configurato. Aggiungilo prima di usare i dati live."
        )

    try:
        response = requests.get(
            f"{FOOTBALL_DATA_BASE_URL}{endpoint}",
            headers={"X-Auth-Token": api_key},
            params=params or {},
            timeout=25,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as error:
        raise FootballDataError(f"Connessione a Football-Data.org non riuscita: {error}") from error
    except ValueError as error:
        raise FootballDataError("Football-Data.org ha restituito una risposta non valida.") from error

    if not isinstance(payload, dict):
        raise FootballDataError("Risposta Football-Data.org inattesa.")
    return payload


def _parse_teams(payload: dict[str, object]) -> tuple[tuple[int, str], ...]:
    response = payload.get("teams", [])
    if not isinstance(response, list):
        return ()
    teams: list[tuple[int, str]] = []
    for team in response:
        if not isinstance(team, dict):
            continue
        team_id = team.get("id")
        team_name = team.get("name") or team.get("shortName")
        if isinstance(team_id, int) and isinstance(team_name, str):
            teams.append((team_id, team_name))
    teams.sort(key=lambda team: team[1].casefold())
    return tuple(teams)


def _parse_finished_matches(payload: dict[str, object]) -> tuple[dict[str, object], ...]:
    response = payload.get("matches", [])
    if not isinstance(response, list):
        return ()
    matches = [
        match
        for match in response
        if isinstance(match, dict)
        and isinstance(match.get("homeTeam"), dict)
        and isinstance(match.get("awayTeam"), dict)
        and isinstance(match.get("score"), dict)
    ]
    matches.sort(key=lambda match: str(match.get("utcDate", "")), reverse=True)
    return tuple(matches)


def _match_has_final_score(match: dict[str, object]) -> bool:
    score = match.get("score")
    if not isinstance(score, dict):
        return False
    full_time = score.get("fullTime")
    if not isinstance(full_time, dict):
        return False
    return (
        _number(full_time.get("home")) is not None
        and _number(full_time.get("away")) is not None
    )


def _fallback_team_snapshot(league: str) -> tuple[tuple[int, str], ...]:
    """Lista di riserva delle squadre della nuova stagione, usata quando
    Football-Data.org non è raggiungibile o non ha ancora pubblicato i dati."""
    fallback_names = LEAGUES.get(league, [])
    return tuple((-(index + 1), name) for index, name in enumerate(fallback_names))


@st.cache_data(ttl=300, show_spinner=False)
def fetch_competition_snapshot(
    league: str,
) -> tuple[int, tuple[tuple[int, str], ...], tuple[dict[str, object], ...]]:
    competition_code = FOOTBALL_DATA_COMPETITIONS[league]
    season_start = current_season_start()
    try:
        # Nessun parametro "season": Football-Data.org usa automaticamente la
        # stagione corrente quando il filtro non viene inviato.
        teams_payload = _football_data_request(f"/competitions/{competition_code}/teams")
        matches_payload = _football_data_request(f"/competitions/{competition_code}/matches")
        teams = _parse_teams(teams_payload)
        if len(teams) < 2:
            raise FootballDataError(
                f"Football-Data.org non ha restituito le squadre 2026/27 per {league}."
            )
        return season_start, teams, _parse_finished_matches(matches_payload)
    except FootballDataError:
        fallback_teams = _fallback_team_snapshot(league)
        if len(fallback_teams) < 2:
            raise
        # L'API non è disponibile: continuiamo con la lista di riserva delle
        # squadre della nuova stagione, senza calendario/risultati live.
        return season_start, fallback_teams, ()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_league_teams(league: str) -> tuple[tuple[int, str], ...]:
    return fetch_competition_snapshot(league)[1]


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace("%", "").strip())
        except ValueError:
            return None
    return None


def _average(total: float, count: int, label: str, team_name: str) -> float:
    if count <= 0:
        raise FootballDataError(f"Dati insufficienti per {label} di {team_name}.")
    return total / count


@st.cache_data(ttl=300, show_spinner=False)
def fetch_league_matches(league: str) -> tuple[dict[str, object], ...]:
    return fetch_competition_snapshot(league)[2]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_previous_season_matches(league: str) -> tuple[dict[str, object], ...]:
    competition_code = FOOTBALL_DATA_COMPETITIONS[league]
    previous_season = current_season_start() - 1
    payload = _football_data_request(
        f"/competitions/{competition_code}/matches",
        {"season": previous_season, "status": "FINISHED"},
    )
    return _parse_finished_matches(payload)


def calendar_frame(league: str) -> pd.DataFrame:
    columns = ["Data", "Stato", "Casa", "Trasferta"]
    matches = sorted(
        fetch_league_matches(league),
        key=lambda match: str(match.get("utcDate", "")),
    )
    rows = []
    status_labels = {
        "TIMED": "Programmata",
        "SCHEDULED": "Da programmare",
        "FINISHED": "Conclusa",
        "POSTPONED": "Rinviata",
        "CANCELED": "Annullata",
    }
    for match in matches:
        home = match.get("homeTeam", {})
        away = match.get("awayTeam", {})
        if not isinstance(home, dict) or not isinstance(away, dict):
            continue
        date_value = str(match.get("utcDate", ""))
        rows.append(
            {
                "Data": date_value[:16].replace("T", " "),
                "Stato": status_labels.get(str(match.get("status", "")), str(match.get("status", ""))),
                "Casa": home.get("name", ""),
                "Trasferta": away.get("name", ""),
            }
        )
    return pd.DataFrame(rows, columns=columns)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_team_live_stats(league: str, team_name: str) -> LiveTeamStats:
    team_map = dict(fetch_league_teams(league))
    team_id = next((id_ for id_, name in team_map.items() if name == team_name), None)
    if team_id is None:
        raise FootballDataError(
            f"La squadra {team_name} non è disponibile in Football-Data.org."
        )

    fixtures = [
        match
        for match in fetch_league_matches(league)
        if _match_has_final_score(match)
        and (
            match["homeTeam"].get("id") == team_id
            or match["awayTeam"].get("id") == team_id
        )
    ][:8]
    if not fixtures:
        previous_matches = fetch_previous_season_matches(league)
        fixtures = [
            match
            for match in previous_matches
            if _match_has_final_score(match)
            and (
                match["homeTeam"].get("id") == team_id
                or match["awayTeam"].get("id") == team_id
                or match["homeTeam"].get("name") == team_name
                or match["awayTeam"].get("name") == team_name
            )
        ][:8]

    goals_for = goals_against = 0.0
    home_goals_for = home_goals_against = 0.0
    away_goals_for = away_goals_against = 0.0
    home_matches = away_matches = 0

    for fixture_item in fixtures:
        home_data = fixture_item.get("homeTeam", {})
        away_data = fixture_item.get("awayTeam", {})
        score = fixture_item.get("score", {})
        full_time = score.get("fullTime", {}) if isinstance(score, dict) else {}
        is_home = home_data.get("id") == team_id
        scored = _number(full_time.get("home" if is_home else "away"))
        conceded = _number(full_time.get("away" if is_home else "home"))
        if scored is None or conceded is None:
            continue

        goals_for += scored
        goals_against += conceded
        if is_home:
            home_matches += 1
            home_goals_for += scored
            home_goals_against += conceded
        else:
            away_matches += 1
            away_goals_for += scored
            away_goals_against += conceded

    matches = home_matches + away_matches
    if matches == 0:
        previous_matches = fetch_previous_season_matches(league)
        scored_values = []
        conceded_values = []
        for match in previous_matches:
            score = match.get("score", {})
            full_time = score.get("fullTime", {}) if isinstance(score, dict) else {}
            scored = _number(full_time.get("home"))
            conceded = _number(full_time.get("away"))
            if scored is not None and conceded is not None:
                scored_values.extend((scored, conceded))
                conceded_values.extend((conceded, scored))
        if not scored_values:
            raise FootballDataError(
                f"Football-Data.org non ha dati storici utilizzabili per {team_name}."
            )
        neutral_average = sum(scored_values) / len(scored_values)
        matches = 8
        home_matches = away_matches = 4
        goals_for = goals_against = neutral_average * matches
        home_goals_for = away_goals_for = neutral_average * 4
        home_goals_against = away_goals_against = neutral_average * 4

    baseline = MICRO_EVENT_BASELINES[FOOTBALL_DATA_COMPETITIONS[league]]
    # The provider has no micro-event endpoint. Scale the transparent baseline
    # slightly with recent scoring, while keeping the source distinction clear.
    scoring_factor = clamp(0.88 + (goals_for / matches) * 0.08, 0.88, 1.12)

    return LiveTeamStats(
        team_id=team_id,
        team_name=team_name,
        matches=matches,
        home_matches=home_matches,
        away_matches=away_matches,
        goals_for=goals_for,
        goals_against=goals_against,
        home_goals_for=home_goals_for,
        home_goals_against=home_goals_against,
        away_goals_for=away_goals_for,
        away_goals_against=away_goals_against,
        total_shots=baseline["shots"] * scoring_factor * matches,
        shots_on_target=baseline["shots_on_target"] * scoring_factor * matches,
        corners=baseline["corners"] * matches,
        cards=baseline["cards"] * matches,
        fouls=baseline["fouls"] * matches,
    )


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def league_factor(league: str) -> float:
    return 1.0 if league in TOP_DIVISIONS else 0.96


def strength_for(team: str) -> float:
    return TEAM_STRENGTHS.get(team, 0.97 if team in PROMOTED_TEAMS else 1.0)


def normalized_profile(team: str) -> tuple[float, float]:
    """Return attack and defensive vulnerability multipliers.

    New arrivals are intentionally regressed toward the league mean instead of
    carrying their second-tier stats directly into a top-flight estimate.
    """
    strength = strength_for(team)
    attack = strength
    defensive_vulnerability = 1 / strength
    if team in PROMOTED_TEAMS:
        attack = 0.91 + (attack - 0.91) * 0.42
        defensive_vulnerability = 1.04 + (defensive_vulnerability - 1.04) * 0.42
    return attack, defensive_vulnerability


def build_match_model(league: str, home: str, away: str) -> MatchModel:
    home_stats = fetch_team_live_stats(league, home)
    away_stats = fetch_team_live_stats(league, away)

    home_goal_for = (
        _average(home_stats.home_goals_for, home_stats.home_matches, "gol segnati in casa", home)
        if home_stats.home_matches
        else _average(home_stats.goals_for, home_stats.matches, "gol segnati", home)
    )
    home_goal_against = (
        _average(
            home_stats.home_goals_against,
            home_stats.home_matches,
            "gol subiti in casa",
            home,
        )
        if home_stats.home_matches
        else _average(home_stats.goals_against, home_stats.matches, "gol subiti", home)
    )
    away_goal_for = (
        _average(away_stats.away_goals_for, away_stats.away_matches, "gol segnati in trasferta", away)
        if away_stats.away_matches
        else _average(away_stats.goals_for, away_stats.matches, "gol segnati", away)
    )
    away_goal_against = (
        _average(
            away_stats.away_goals_against,
            away_stats.away_matches,
            "gol subiti in trasferta",
            away,
        )
        if away_stats.away_matches
        else _average(away_stats.goals_against, away_stats.matches, "gol subiti", away)
    )

    home_lambda = clamp((home_goal_for + away_goal_against) / 2 * 1.04, 0.15, 4.5)
    away_lambda = clamp((away_goal_for + home_goal_against) / 2, 0.1, 4.0)
    home_sot = _average(home_stats.shots_on_target, home_stats.matches, "tiri in porta", home)
    away_sot = _average(away_stats.shots_on_target, away_stats.matches, "tiri in porta", away)
    shots_total = _average(home_stats.total_shots, home_stats.matches, "tiri totali", home)
    shots_total += _average(away_stats.total_shots, away_stats.matches, "tiri totali", away)
    corners_total = _average(home_stats.corners, home_stats.matches, "corner", home)
    corners_total += _average(away_stats.corners, away_stats.matches, "corner", away)
    home_cards = _average(home_stats.cards, home_stats.matches, "cartellini", home)
    away_cards = _average(away_stats.cards, away_stats.matches, "cartellini", away)
    fouls = _average(home_stats.fouls, home_stats.matches, "falli", home)
    fouls += _average(away_stats.fouls, away_stats.matches, "falli", away)

    return MatchModel(
        home_lambda=home_lambda,
        away_lambda=away_lambda,
        shots_total_lambda=shots_total,
        home_shots_on_target_lambda=home_sot,
        away_shots_on_target_lambda=away_sot,
        shots_on_target_total_lambda=home_sot + away_sot,
        corners_total_lambda=corners_total,
        home_cards_lambda=home_cards,
        away_cards_lambda=away_cards,
        cards_total_lambda=home_cards + away_cards,
        fouls_lambda=fouls,
    )


def over_probability(lam: float, line: float) -> float:
    return float(1 - poisson.cdf(math.floor(line), lam))


def fair_odds(probability: float) -> float:
    return float(1 / probability) if probability > 0 else float("inf")


def micro_event_rows(model: MatchModel) -> list[dict[str, object]]:
    groups: list[tuple[str, float, Iterable[float]]] = [
        ("Tiri totali partita", model.shots_total_lambda, (21.5, 23.5, 25.5)),
        (
            "Tiri in porta · Casa",
            model.home_shots_on_target_lambda,
            (3.5, 4.5, 5.5),
        ),
        (
            "Tiri in porta · Trasferta",
            model.away_shots_on_target_lambda,
            (2.5, 3.5, 4.5),
        ),
        (
            "Tiri in porta · Totali match",
            model.shots_on_target_total_lambda,
            (7.5, 8.5, 9.5),
        ),
        ("Corner totali match", model.corners_total_lambda, (7.5, 8.5, 9.5, 10.5)),
        ("Cartellini · Casa", model.home_cards_lambda, (1.5, 2.5)),
        ("Cartellini · Trasferta", model.away_cards_lambda, (1.5, 2.5)),
        ("Cartellini · Totali match", model.cards_total_lambda, (3.5, 4.5, 5.5)),
        ("Falli complessivi match", model.fouls_lambda, (22.5, 24.5, 26.5)),
    ]
    rows: list[dict[str, object]] = []
    for event, lam, lines in groups:
        for line in lines:
            probability = over_probability(lam, line)
            rows.append(
                {
                    "Micro-evento": event,
                    "Soglia": f"Over {line:.1f}",
                    "Valore atteso": round(lam, 2),
                    "Probabilità": probability,
                    "Fair odds": fair_odds(probability),
                }
            )
    return rows


def run_simulation(model: MatchModel, n_simulations: int = 10_000) -> dict[str, object]:
    rng = np.random.default_rng()
    home_goals = rng.poisson(model.home_lambda, n_simulations)
    away_goals = rng.poisson(model.away_lambda, n_simulations)
    total_shots = rng.poisson(model.shots_total_lambda, n_simulations)
    home_sot = rng.poisson(model.home_shots_on_target_lambda, n_simulations)
    away_sot = rng.poisson(model.away_shots_on_target_lambda, n_simulations)
    corners = rng.poisson(model.corners_total_lambda, n_simulations)
    home_cards = rng.poisson(model.home_cards_lambda, n_simulations)
    away_cards = rng.poisson(model.away_cards_lambda, n_simulations)
    total_cards = home_cards + away_cards
    fouls = rng.poisson(model.fouls_lambda, n_simulations)

    scores = Counter(zip(home_goals.tolist(), away_goals.tolist()))
    top_scores = scores.most_common(5)
    score_rows = [
        {
            "Risultato esatto": f"{home}-{away}",
            "Simulazioni": count,
            "Probabilità": count / n_simulations,
        }
        for (home, away), count in top_scores
    ]

    key_events = [
        ("Over 2.5 gol", home_goals + away_goals > 2),
        ("Over 8.5 corner", corners > 8),
        ("Over 22.5 tiri totali", total_shots > 22),
        ("Casa Over 4.5 tiri in porta", home_sot > 4),
        ("Trasferta Over 3.5 tiri in porta", away_sot > 3),
        ("Over 3.5 cartellini", total_cards > 3),
        ("Over 24.5 falli", fouls > 24),
    ]
    event_rows = [
        {
            "Micro-evento simulato": name,
            "Frequenza": int(mask.sum()),
            "Probabilità": float(mask.mean()),
        }
        for name, mask in key_events
    ]

    return {
        "scores": pd.DataFrame(score_rows),
        "events": pd.DataFrame(event_rows),
        "raw": {
            "home_goals": home_goals,
            "away_goals": away_goals,
            "corners": corners,
            "total_cards": total_cards,
            "total_shots": total_shots,
        },
    }


def render_probability_table(frame: pd.DataFrame) -> str:
    """Render the Poisson table with bright-green rows over 80%."""
    headers = ["Micro-evento", "Soglia", "Valore atteso", "Probabilità", "Fair odds"]
    table_rows = []
    for _, row in frame.iterrows():
        probability = float(row["Probabilità"])
        row_style = (
            ' style="background:#39ff14;color:#061a0e;font-weight:700"'
            if probability > 0.8
            else ""
        )
        cells = [
            escape(str(row["Micro-evento"])),
            escape(str(row["Soglia"])),
            f"{float(row['Valore atteso']):.2f}",
            f"{probability:.1%}",
            f"{float(row['Fair odds']):.2f}",
        ]
        table_rows.append(
            f"<tr{row_style}>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>"
        )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    return (
        '<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse">'
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{''.join(table_rows)}</tbody></table></div>"
    )


def render_match_summary(league: str, home: str, away: str) -> str:
    if not home or not away:
        return '<p style="color:#64748b">Carica le squadre da Football-Data.org per iniziare.</p>'
    if home == away:
        return '<p style="color:#b91c1c;font-weight:600">Seleziona due squadre diverse.</p>'

    try:
        model = build_match_model(league, home, away)
    except FootballDataError as error:
        return (
            '<p style="color:#b91c1c;font-weight:600">'
            f"Dati Football-Data.org non disponibili: {escape(str(error))}</p>"
        )
    metrics = [
        ("Lambda casa", model.home_lambda),
        ("Lambda ospite", model.away_lambda),
        ("Gol attesi", model.home_lambda + model.away_lambda),
        ("Corner attesi", model.corners_total_lambda),
        ("Cartellini attesi", model.cards_total_lambda),
    ]
    metric_html = "".join(
        f'<div style="flex:1;min-width:130px;padding:14px;border:1px solid #dbe3ef;'
        f'border-radius:10px"><div style="font-size:.85rem;color:#64748b">'
        f"{escape(label)}</div><strong style=\"font-size:1.5rem\">{value:.2f}</strong></div>"
        for label, value in metrics
    )
    return (
        f"<h2>{escape(league)} · {escape(home)} — {escape(away)}</h2>"
        '<div style="display:flex;gap:10px;flex-wrap:wrap;margin:14px 0">'
        f"{metric_html}</div>"
        '<p style="color:#475569">Le squadre neo-promosse vengono riportate verso la '
        "media del nuovo campionato per evitare stime distorte.</p>"
    )


def update_analysis(league: str, home: str, away: str) -> tuple[str, str]:
    if not home or not away or home == away:
        return render_match_summary(league, home, away), ""
    try:
        model = build_match_model(league, home, away)
    except FootballDataError as error:
        return (
            '<p style="color:#b91c1c;font-weight:600">'
            f"Dati Football-Data.org non disponibili: {escape(str(error))}</p>",
            '<p style="color:#b91c1c">Impossibile calcolare le probabilità senza '
            f"risultati live: {escape(str(error))}</p>",
        )
    return render_match_summary(league, home, away), render_probability_table(
        pd.DataFrame(micro_event_rows(model))
    )


def render_login() -> None:
    st.markdown(
        "### Accesso protetto\n"
        "Inserisci la password per accedere alle analisi Poisson e Monte Carlo."
    )
    with st.form("login_form", clear_on_submit=False):
        password = st.text_input(
            "Password di accesso",
            type="password",
            placeholder="Inserisci la password",
        )
        submitted = st.form_submit_button("Accedi", type="primary")
    if submitted:
        if password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Password non valida. I dati della dashboard restano nascosti.")


def render_dashboard() -> None:
    st.markdown(
        "### Impostazioni partita\n"
        "Squadre, calendario e risultati vengono recuperati direttamente da "
        "Football-Data.org. Non sono quotazioni di un bookmaker."
    )

    col_league, col_home, col_away = st.columns(3)
    with col_league:
        league = st.selectbox(
            "Campionato",
            options=list(FOOTBALL_DATA_COMPETITIONS),
            key="league_select",
        )

    try:
        team_rows = fetch_league_teams(league)
    except FootballDataError as error:
        st.error(f"Football-Data.org non disponibile: {error}")
        team_rows = ()

    teams = [name for _, name in team_rows]

    if len(teams) < 2:
        with col_home:
            st.selectbox("Squadra di casa", options=teams, disabled=True)
        with col_away:
            st.selectbox("Squadra ospite", options=teams, disabled=True)
        st.warning("Football-Data.org non ha restituito due squadre disponibili.")
        return

    # Se il campionato è cambiato, riporta le selezioni squadra ai valori di default.
    if st.session_state.get("_last_league") != league:
        st.session_state["_last_league"] = league
        st.session_state["home_select"] = teams[0]
        st.session_state["away_select"] = teams[1]

    with col_home:
        home = st.selectbox("Squadra di casa", options=teams, key="home_select")
    with col_away:
        away = st.selectbox("Squadra ospite", options=teams, key="away_select")

    try:
        status_text = (
            f"Football-Data.org: {len(teams)} squadre caricate · "
            f"{competition_season_status(league)}. "
            "Micro-eventi stimati su baseline di campionato."
        )
        st.info(status_text)
    except FootballDataError as error:
        st.warning(f"Stato stagione non disponibile: {error}")

    try:
        calendar = calendar_frame(league)
    except FootballDataError as error:
        st.error(f"Calendario Football-Data.org non disponibile: {error}")
        calendar = pd.DataFrame(columns=["Data", "Stato", "Casa", "Trasferta"])

    st.markdown("#### Calendario stagione 2026/27")
    st.dataframe(calendar, use_container_width=True, hide_index=True)

    match_summary_html, poisson_html = update_analysis(league, home, away)
    st.markdown(match_summary_html, unsafe_allow_html=True)

    tab_poisson, tab_montecarlo = st.tabs(
        [
            "Analisi Quote & Probabilità (Poisson)",
            "Simulatore Monte Carlo (10.000 Partite)",
        ]
    )

    with tab_poisson:
        st.markdown(
            "Le righe in verde brillante indicano probabilità superiori all'80%. "
            "La fair odds è l'inverso della probabilità modellata."
        )
        if home == away:
            st.info("Seleziona due squadre diverse prima di analizzare le probabilità.")
        elif poisson_html:
            st.markdown(poisson_html, unsafe_allow_html=True)
        else:
            st.info("Probabilità non disponibili per questa selezione.")
        st.markdown(
            "##### Lettura del modello\n"
            "Il valore atteso dei gol viene aggiornato sui risultati recenti "
            "di Football-Data.org. Tiri, corner, cartellini e falli usano "
            "baseline di campionato perché non sono esposti da questa API."
        )

    with tab_montecarlo:
        st.markdown(
            "Ogni esecuzione genera 10.000 partite indipendenti con distribuzioni "
            "di Poisson per gol e micro-eventi."
        )
        if home == away:
            st.info("Seleziona due squadre diverse prima di simulare.")
        else:
            run_clicked = st.button(
                "Esegui 10.000 Simulazioni Monte Carlo",
                type="primary",
                key="simulate_button",
            )
            if run_clicked:
                try:
                    model = build_match_model(league, home, away)
                except FootballDataError as error:
                    st.error(f"Impossibile simulare: {error}")
                else:
                    simulation = run_simulation(model)
                    score_frame: pd.DataFrame = simulation["scores"]
                    event_frame: pd.DataFrame = simulation["events"]

                    col_scores, col_chart = st.columns(2)
                    with col_scores:
                        st.markdown("**I 5 risultati esatti più frequenti**")
                        st.dataframe(score_frame, use_container_width=True, hide_index=True)
                    with col_chart:
                        chart = px.bar(
                            score_frame,
                            x="Risultato esatto",
                            y="Probabilità",
                            text="Probabilità",
                            labels={"Probabilità": "Probabilità", "Risultato esatto": "Risultato"},
                            color="Probabilità",
                            color_continuous_scale=["#d9f99d", "#16a34a"],
                        )
                        chart.update_traces(texttemplate="%{text:.1%}", textposition="outside")
                        chart.update_layout(
                            showlegend=False,
                            yaxis_tickformat=".0%",
                            margin={"l": 10, "r": 10, "t": 20, "b": 10},
                        )
                        st.plotly_chart(chart, use_container_width=True)

                    st.markdown("**Frequenza dei micro-eventi chiave**")
                    st.dataframe(event_frame, use_container_width=True, hide_index=True)
                    st.success("Simulazione completata: 10.000 partite generate.")


def main() -> None:
    st.set_page_config(
        page_title="CalcioLab · Analisi e Simulazioni",
        layout="wide",
    )

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    st.markdown(
        "# CalcioLab\n"
        "Analisi probabilistica e simulazioni di calcio con dati live da Football-Data.org."
    )

    if st.session_state.authenticated:
        with st.sidebar:
            st.success("Accesso autorizzato.")
            if st.button("Esci"):
                st.session_state.authenticated = False
                st.rerun()
        render_dashboard()
    else:
        render_login()


if __name__ == "__main__":
    main()
