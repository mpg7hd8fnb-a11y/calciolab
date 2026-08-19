from __future__ import annotations

import math
import os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from html import escape
from typing import Iterable, Sequence

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
    "Paesi Bassi · Eredivisie": [
        "ADO Den Haag",
        "Ajax",
        "AZ Alkmaar",
        "Excelsior",
        "Feyenoord",
        "Fortuna Sittard",
        "Go Ahead Eagles",
        "Groningen",
        "Heerenveen",
        "NEC Nijmegen",
        "PEC Zwolle",
        "PSV Eindhoven",
        "SC Cambuur",
        "Sparta Rotterdam",
        "Telstar",
        "Twente",
        "Utrecht",
        "Willem II",
    ],
    "Portogallo · Primeira Liga": [
        "Académico de Viseu",
        "Alverca",
        "Arouca",
        "Benfica",
        "Braga",
        "Casa Pia",
        "Estoril",
        "Estrela da Amadora",
        "Famalicão",
        "Gil Vicente",
        "Marítimo",
        "Moreirense",
        "Nacional",
        "Porto",
        "Rio Ave",
        "Santa Clara",
        "Sporting CP",
        "Vitória de Guimarães",
    ],
    "Europa · UEFA Champions League": [
        "Arsenal",
        "Aston Villa",
        "Atlético Madrid",
        "Barcelona",
        "Bayern Monaco",
        "Borussia Dortmund",
        "Chelsea",
        "Club Brugge",
        "Como",
        "Feyenoord",
        "Galatasaray",
        "Inter",
        "Juventus",
        "Lens",
        "Lille",
        "Liverpool",
        "Manchester City",
        "Manchester United",
        "Napoli",
        "Porto",
        "PSG",
        "PSV Eindhoven",
        "RB Lipsia",
        "Real Betis",
        "Real Madrid",
        "Roma",
        "Shakhtar Donetsk",
        "Slavia Praga",
        "Sporting CP",
        "Stoccarda",
        "Villarreal",
    ],
}


TOP_DIVISIONS = {
    "Italia · Serie A",
    "Inghilterra · Premier League",
    "Spagna · La Liga",
    "Germania · Bundesliga",
    "Francia · Ligue 1",
    "Paesi Bassi · Eredivisie",
    "Portogallo · Primeira Liga",
    # La Champions League riunisce club di nazioni diverse: va trattata come
    # massima serie a tutti gli effetti, senza applicare il gap di rating
    # riservato ai campionati di seconda fascia (vedi base_power_rating).
    "Europa · UEFA Champions League",
}

FOOTBALL_DATA_COMPETITIONS: dict[str, str] = {
    "Italia · Serie A": "SA",
    "Inghilterra · Premier League": "PL",
    "Inghilterra · EFL Championship": "ELC",
    "Spagna · La Liga": "PD",
    "Germania · Bundesliga": "BL1",
    "Francia · Ligue 1": "FL1",
    "Paesi Bassi · Eredivisie": "DED",
    "Portogallo · Primeira Liga": "PPL",
    "Europa · UEFA Champions League": "CL",
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
    "DED": {"shots": 13.2, "shots_on_target": 4.6, "corners": 5.2, "cards": 1.9, "fouls": 11.0},
    "PPL": {"shots": 11.5, "shots_on_target": 3.8, "corners": 4.5, "cards": 2.6, "fouls": 13.5},
    "CL": {"shots": 12.6, "shots_on_target": 4.4, "corners": 4.9, "cards": 1.7, "fouls": 10.5},
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
    # Paesi Bassi · Eredivisie
    "ADO Den Haag",
    "SC Cambuur",
    # Portogallo · Primeira Liga
    "Académico de Viseu",
    "Marítimo",
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
    "Aston Villa": 1.06,
    "Real Madrid": 1.18,
    "Barcelona": 1.15,
    "Atlético Madrid": 1.08,
    "Villarreal": 1.03,
    "Athletic Bilbao": 1.02,
    "Real Betis": 1.00,
    "Bayern Monaco": 1.18,
    "Bayer Leverkusen": 1.13,
    "Borussia Dortmund": 1.08,
    "RB Lipsia": 1.06,
    "Stoccarda": 1.03,
    "PSG": 1.18,
    "Monaco": 1.08,
    "Marsiglia": 1.04,
    "Lione": 1.03,
    "Lens": 1.00,
    "Lille": 1.02,
    # --- Club di Champions League fuori dalle 5 leghe principali -------------
    # Lo stesso rating vale sia in campionato sia in Champions League, così il
    # Global Power Rating resta coerente indipendentemente dalla nazione delle
    # due squadre in campo (vedi base_power_rating).
    "PSV Eindhoven": 1.05,
    "Feyenoord": 1.02,
    "Sporting CP": 1.06,
    "Porto": 1.05,
    "Club Brugge": 1.00,
    "Galatasaray": 1.02,
    "Shakhtar Donetsk": 0.98,
    "Slavia Praga": 0.97,
    "Como": 0.95,
}


# ==============================================================================
# MOTORE UNICO DI SIMULAZIONE — Global Power Rating (stile ELO / Opta)
# ==============================================================================
# Tutte le stime dell'app (xG, probabilità 1X2, tiri fatti/subiti, corner,
# cartellini, tabelle micro-eventi, quote implicite e simulazione Monte Carlo)
# passano da un'unica fonte di verità: il rating di forza (Global Power
# Rating) calcolato qui sotto per ciascuna squadra. Questo evita che due parti
# dell'interfaccia raccontino storie diverse sullo stesso match.
#
# Il rating combina:
#  1. una componente STRUTTURALE di lungo periodo (TEAM_STRENGTHS per i club
#     più forti, un gap di categoria per neo-promosse/campionati minori);
#  2. una componente DINAMICA di breve periodo (il Form Factor sulle ultime
#     partite, già calcolato in fetch_team_live_stats);
#  3. un bonus di FATTORE CAMPO applicato solo in fase di calcolo del match.
#
# Il differenziale di rating fra le due squadre viene poi convertito in
# moltiplicatori continui (non un semplice interruttore on/off) che scalano
# gol attesi, tiri fatti/subiti, corner e cartellini in modo proporzionale
# all'ampiezza del gap, così una sfida come Arsenal-Coventry produce xG e
# probabilità 1X2 nettamente sbilanciati, mentre due squadre equivalenti
# restano vicine alla parità.

BASE_RATING = 1500.0
"""Rating ELO di riferimento per una squadra di media forza in massima serie."""

RATING_SCALE = 400.0
"""Punti di rating equivalenti a un'unità del moltiplicatore TEAM_STRENGTHS
(1.18 di forza ≈ +72 punti rating) e base della formula ELO standard."""

SECOND_TIER_RATING_GAP = 180.0
"""Gap di rating fra un campionato di seconda fascia (Championship, Serie B,
Segunda División, 2. Bundesliga, Ligue 2) e la media della massima serie."""

PROMOTED_TEAM_RATING_GAP = 220.0
"""Gap di rating di partenza per una neo-promossa nella massima serie, prima
che i risultati stagionali (Form Factor) lo aggiornino."""

HOME_ADVANTAGE_RATING = 60.0
"""Bonus di rating ELO per il fattore campo, applicato solo nel calcolo del
singolo match (non è memorizzato nel rating strutturale della squadra)."""

RATING_LAMBDA_SENSITIVITY = 0.0022
"""Quanto un punto di differenza di rating ELO sposta, in scala esponenziale,
il gol atteso/i tiri di ciascuna squadra rispetto alla media osservata."""

SHOT_RATING_DAMPING = 0.7
"""I tiri (fatti/in porta) seguono il gap di rating con un'intensità inferiore
ai gol (che dipendono anche da efficienza/episodi), da qui lo smorzamento."""

CORNER_RATING_DAMPING = 0.35
"""I corner sono più legati al possesso palla che al gap di qualità puro:
smorzamento più marcato rispetto ai tiri."""

CARD_UNDERDOG_BONUS = 0.25
"""Quota aggiuntiva di cartellini per la squadra più debole, che difende più
a lungo e commette più falli tattici contro un avversario superiore."""


def base_power_rating(team: str, league: str) -> float:
    """Componente strutturale del Global Power Rating, prima del Form Factor.

    - Se la squadra ha un rating esplicito in TEAM_STRENGTHS (big club delle
      5 leghe principali), il rating ELO viene derivato da quel moltiplicatore.
    - Se è una neo-promossa (PROMOTED_TEAMS), parte con un gap di rating che
      riflette la provenienza da un campionato minore.
    - Se il campionato selezionato non è di massima serie (Championship,
      Serie B, ecc.), l'intera squadra parte con il gap di seconda fascia.
    - Altrimenti riceve il rating medio di massima serie (BASE_RATING).
    """
    if team in TEAM_STRENGTHS:
        return BASE_RATING + (TEAM_STRENGTHS[team] - 1.0) * RATING_SCALE
    if team in PROMOTED_TEAMS:
        return BASE_RATING - PROMOTED_TEAM_RATING_GAP
    if league not in TOP_DIVISIONS:
        return BASE_RATING - SECOND_TIER_RATING_GAP
    return BASE_RATING


def global_power_rating(team: str, league: str, form_factor: float) -> float:
    """Global Power Rating dinamico usato per il match: rating strutturale
    più la correzione data dal Form Factor (fino a ±RATING_SCALE·0.15 punti,
    coerente con FORM_FACTOR_MIN/MAX)."""
    return base_power_rating(team, league) + (form_factor - 1.0) * RATING_SCALE


def is_top_tier(team: str) -> bool:
    """True se la squadra è un club di fascia alta secondo TEAM_STRENGTHS."""
    return team in TEAM_STRENGTHS and TEAM_STRENGTHS[team] >= 1.08


def elo_expected_score(rating_a: float, rating_b: float) -> float:
    """Probabilità attesa stile ELO che la squadra A prevalga su B (0-1),
    dato il differenziale di rating fra le due (formula ELO standard)."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / RATING_SCALE))


def rating_scaling_factors(rating_diff: float, damping: float = 1.0) -> tuple[float, float]:
    """Converte un differenziale di rating ELO (squadra A meno squadra B) in
    una coppia di moltiplicatori continui (boost per A, suppressione per B)
    da applicare a gol attesi/tiri/corner. `damping` attenua l'effetto per le
    metriche meno legate al puro gap di qualità (es. corner)."""
    exponent = RATING_LAMBDA_SENSITIVITY * damping * rating_diff
    boost = clamp(math.exp(exponent), 0.4, 2.6)
    suppression = clamp(math.exp(-exponent), 0.38, 2.5)
    return boost, suppression


def match_outcome_probabilities(
    home_lambda: float, away_lambda: float, max_goals: int = 10
) -> tuple[float, float, float]:
    """Probabilità 1X2 (vittoria casa, pareggio, vittoria trasferta) calcolate
    analiticamente dalla matrice di Poisson bivariata su home_lambda/away_lambda:
    la stessa distribuzione usata per le tabelle micro-eventi e per la
    simulazione Monte Carlo, a garanzia di coerenza fra tutte le viste."""
    home_pmf = [poisson.pmf(i, home_lambda) for i in range(max_goals + 1)]
    away_pmf = [poisson.pmf(j, away_lambda) for j in range(max_goals + 1)]
    home_win = draw = away_win = 0.0
    for i, p_home in enumerate(home_pmf):
        for j, p_away in enumerate(away_pmf):
            joint = p_home * p_away
            if i > j:
                home_win += joint
            elif i == j:
                draw += joint
            else:
                away_win += joint
    # La massa residua oltre max_goals è trascurabile ma la ridistribuiamo
    # proporzionalmente per garantire che le tre probabilità sommino a 1.
    total = home_win + draw + away_win
    if total <= 0:
        return 1 / 3, 1 / 3, 1 / 3
    return home_win / total, draw / total, away_win / total


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
    home_rating: float = BASE_RATING
    """Global Power Rating dinamico della squadra di casa (senza fattore campo)."""
    away_rating: float = BASE_RATING
    """Global Power Rating dinamico della squadra ospite."""
    home_win_prob: float = 1 / 3
    draw_prob: float = 1 / 3
    away_win_prob: float = 1 / 3
    engine_note: str = ""
    """Riepilogo testuale dei correttivi (gap di rating, fattore campo, forma
    recente) applicati dal motore per questo match."""



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
    recent_form: tuple[str, ...] = ()
    """Ultimi risultati (più recente per primo): 'V' vittoria, 'N' pareggio, 'P' sconfitta."""
    form_factor: float = 1.0
    """Moltiplicatore dinamico ricavato dal Form Factor (vedi compute_form_factor)."""


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
    recent_results: list[str] = []
    recent_points: list[int] = []

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

        # Form Factor: tiene traccia solo delle ultime FORM_MATCHES_WINDOW
        # partite (le fixtures sono già ordinate dalla più recente).
        if len(recent_points) < FORM_MATCHES_WINDOW:
            if scored > conceded:
                recent_results.append("V")
                recent_points.append(3)
            elif scored == conceded:
                recent_results.append("N")
                recent_points.append(1)
            else:
                recent_results.append("P")
                recent_points.append(0)

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
        # Nessuna partita nella competizione corrente: niente serie di
        # risultati recenti da pesare, il Form Factor resta neutro (1.0).
        recent_results = []
        recent_points = []

    baseline = MICRO_EVENT_BASELINES[FOOTBALL_DATA_COMPETITIONS[league]]
    # The provider has no micro-event endpoint. Scale the transparent baseline
    # slightly with recent scoring, while keeping the source distinction clear.
    scoring_factor = clamp(0.88 + (goals_for / matches) * 0.08, 0.88, 1.12)
    form_factor = compute_form_factor(recent_points)

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
        recent_form=tuple(recent_results),
        form_factor=form_factor,
    )


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


# --- Form Factor (componente dinamica del Global Power Rating) --------------
# Le medie usate finora (fino a 8 partite, non pesate) non distinguono una
# squadra che sta attraversando un buon momento da una in crisi di risultati.
# Il Form Factor pesa i risultati più recenti più di quelli lontani e produce
# il moltiplicatore dinamico usato da global_power_rating() sopra.
FORM_MATCHES_WINDOW = 5
"""Numero di partite recenti considerate nel calcolo del Form Factor."""

FORM_RECENCY_WEIGHTS: tuple[float, ...] = (1.0, 0.85, 0.7, 0.55, 0.4)
"""Peso decrescente per ciascuna delle ultime FORM_MATCHES_WINDOW partite,
dalla più recente alla meno recente."""

FORM_FACTOR_MIN = 0.85
FORM_FACTOR_MAX = 1.15


def compute_form_factor(recent_points: Sequence[int]) -> float:
    """Form Factor dinamico: calcola un moltiplicatore intorno a 1.0 pesando
    i punti (Vittoria=3, Pareggio=1, Sconfitta=0) delle ultime partite con
    FORM_RECENCY_WEIGHTS. Una squadra in ottima forma recente arriva fino a
    FORM_FACTOR_MAX, una in crisi di risultati scende fino a FORM_FACTOR_MIN.
    Senza dati recenti restituisce 1.0 (nessuna correzione)."""
    if not recent_points:
        return 1.0
    weights = FORM_RECENCY_WEIGHTS[: len(recent_points)]
    weighted_points = sum(points * weight for points, weight in zip(recent_points, weights))
    weighted_max = sum(3 * weight for weight in weights)
    if weighted_max <= 0:
        return 1.0
    ratio = clamp(weighted_points / weighted_max, 0.0, 1.0)
    return FORM_FACTOR_MIN + (FORM_FACTOR_MAX - FORM_FACTOR_MIN) * ratio


def build_match_model(league: str, home: str, away: str) -> MatchModel:
    home_stats = fetch_team_live_stats(league, home)
    away_stats = fetch_team_live_stats(league, away)

    # --- 1. Statistiche osservate (baseline "grezza") --------------------------
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

    home_lambda_raw = (home_goal_for + away_goal_against) / 2
    away_lambda_raw = (away_goal_for + home_goal_against) / 2
    home_sot_raw = _average(home_stats.shots_on_target, home_stats.matches, "tiri in porta", home)
    away_sot_raw = _average(away_stats.shots_on_target, away_stats.matches, "tiri in porta", away)
    home_shots_raw = _average(home_stats.total_shots, home_stats.matches, "tiri totali", home)
    away_shots_raw = _average(away_stats.total_shots, away_stats.matches, "tiri totali", away)
    home_corners_raw = _average(home_stats.corners, home_stats.matches, "corner", home)
    away_corners_raw = _average(away_stats.corners, away_stats.matches, "corner", away)
    home_cards_raw = _average(home_stats.cards, home_stats.matches, "cartellini", home)
    away_cards_raw = _average(away_stats.cards, away_stats.matches, "cartellini", away)
    fouls = _average(home_stats.fouls, home_stats.matches, "falli", home)
    fouls += _average(away_stats.fouls, away_stats.matches, "falli", away)

    # --- 2. Global Power Rating (strutturale + Form Factor) --------------------
    home_rating = global_power_rating(home, league, home_stats.form_factor)
    away_rating = global_power_rating(away, league, away_stats.form_factor)

    # Il fattore campo entra come bonus di rating solo per il calcolo di questo
    # match: pesa quindi su OGNI metrica derivata dal differenziale, non solo
    # sui gol attesi, garantendo coerenza fra tutte le tabelle dell'app.
    rating_diff = (home_rating + HOME_ADVANTAGE_RATING) - away_rating

    # --- 3. Gol attesi (xG): piena sensibilità al gap di rating -----------------
    goal_boost, goal_suppress = rating_scaling_factors(rating_diff, damping=1.0)
    home_lambda = clamp(home_lambda_raw * goal_boost, 0.05, 5.5)
    away_lambda = clamp(away_lambda_raw * goal_suppress, 0.05, 5.0)

    # --- 4. Tiri totali/in porta: dipendono dal rating offensivo/difensivo -----
    # relativo, con sensibilità smorzata rispetto ai gol (i tiri riflettono la
    # pressione di gioco più che l'efficienza sotto porta).
    shot_boost, shot_suppress = rating_scaling_factors(rating_diff, damping=SHOT_RATING_DAMPING)
    home_shots = home_shots_raw * shot_boost
    away_shots = away_shots_raw * shot_suppress
    home_sot = home_sot_raw * shot_boost
    away_sot = away_sot_raw * shot_suppress
    shots_total = home_shots + away_shots

    # --- 5. Corner: legati anche al possesso, sensibilità ulteriormente smorzata
    corner_boost, corner_suppress = rating_scaling_factors(rating_diff, damping=CORNER_RATING_DAMPING)
    corners_total = home_corners_raw * corner_boost + away_corners_raw * corner_suppress

    # --- 6. Cartellini: la squadra in difficoltà commette più falli tattici ----
    normalized_gap = clamp(abs(rating_diff) / RATING_SCALE, 0.0, 1.0)
    if rating_diff >= 0:
        home_cards = home_cards_raw * (1 - 0.5 * CARD_UNDERDOG_BONUS * normalized_gap)
        away_cards = away_cards_raw * (1 + CARD_UNDERDOG_BONUS * normalized_gap)
    else:
        home_cards = home_cards_raw * (1 + CARD_UNDERDOG_BONUS * normalized_gap)
        away_cards = away_cards_raw * (1 - 0.5 * CARD_UNDERDOG_BONUS * normalized_gap)
    home_cards = clamp(home_cards, 0.1, 6.0)
    away_cards = clamp(away_cards, 0.1, 6.0)

    # --- 7. Probabilità 1X2: matrice di Poisson bivariata su home/away lambda --
    # Stessa distribuzione usata dalle tabelle micro-eventi e dalla simulazione
    # Monte Carlo, cosicché ogni vista dell'app racconti lo stesso match.
    home_win_prob, draw_prob, away_win_prob = match_outcome_probabilities(home_lambda, away_lambda)

    engine_note = (
        f"Global Power Rating: {home} {home_rating:.0f} (+{HOME_ADVANTAGE_RATING:.0f} campo) "
        f"vs {away} {away_rating:.0f} · gap effettivo {rating_diff:+.0f} punti · "
        f"xG ×{goal_boost:.2f}/×{goal_suppress:.2f} · tiri ×{shot_boost:.2f}/×{shot_suppress:.2f}"
    )
    if home_stats.recent_form:
        engine_note += f" · forma {home}: {''.join(home_stats.recent_form)}"
    if away_stats.recent_form:
        engine_note += f" · forma {away}: {''.join(away_stats.recent_form)}"

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
        home_rating=home_rating,
        away_rating=away_rating,
        home_win_prob=home_win_prob,
        draw_prob=draw_prob,
        away_win_prob=away_win_prob,
        engine_note=engine_note,
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

    # Frequenze 1X2 osservate nelle 10.000 simulazioni: servono a validare
    # che la probabilità analitica (Poisson bivariata) e quella simulata dal
    # motore Monte Carlo raccontino lo stesso match.
    home_wins = int((home_goals > away_goals).sum())
    draws = int((home_goals == away_goals).sum())
    away_wins = int((home_goals < away_goals).sum())
    outcome_rows = [
        {"Esito": "1 (vittoria casa)", "Simulazioni": home_wins, "Probabilità": home_wins / n_simulations},
        {"Esito": "X (pareggio)", "Simulazioni": draws, "Probabilità": draws / n_simulations},
        {"Esito": "2 (vittoria trasferta)", "Simulazioni": away_wins, "Probabilità": away_wins / n_simulations},
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
        "outcomes": pd.DataFrame(outcome_rows),
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


def render_outcome_table(model: MatchModel, home: str, away: str) -> str:
    """Tabella Pronostici 1X2 con quote implicite, calcolata dalla stessa
    matrice di Poisson bivariata (home_lambda/away_lambda) usata per le
    tabelle micro-eventi e per la simulazione Monte Carlo."""
    rows = [
        (f"1 · Vittoria {home}", model.home_win_prob),
        ("X · Pareggio", model.draw_prob),
        (f"2 · Vittoria {away}", model.away_win_prob),
    ]
    table_rows = []
    for label, probability in rows:
        row_style = (
            ' style="background:#39ff14;color:#061a0e;font-weight:700"'
            if probability > 0.8
            else ""
        )
        cells = [escape(label), f"{probability:.1%}", f"{fair_odds(probability):.2f}"]
        table_rows.append(
            f"<tr{row_style}>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>"
        )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in ["Esito", "Probabilità", "Fair odds"])
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
        (f"Global Power Rating {home}", model.home_rating),
        (f"Global Power Rating {away}", model.away_rating),
        ("xG casa", model.home_lambda),
        ("xG ospite", model.away_lambda),
        (f"Prob. vittoria {home}", model.home_win_prob * 100),
        ("Prob. pareggio", model.draw_prob * 100),
        (f"Prob. vittoria {away}", model.away_win_prob * 100),
    ]
    metric_html = "".join(
        f'<div style="flex:1;min-width:150px;padding:14px;border:1px solid #dbe3ef;'
        f'border-radius:10px"><div style="font-size:.85rem;color:#64748b">'
        f"{escape(label)}</div><strong style=\"font-size:1.5rem\">{value:.1f}</strong></div>"
        for label, value in metrics
    )
    note = escape(model.engine_note) if model.engine_note else "Global Power Rating calcolato."
    return (
        f"<h2>{escape(league)} · {escape(home)} — {escape(away)}</h2>"
        '<div style="display:flex;gap:10px;flex-wrap:wrap;margin:14px 0">'
        f"{metric_html}</div>"
        f'<p style="color:#475569">{note}</p>'
    )



def update_analysis(league: str, home: str, away: str) -> tuple[str, str, str]:
    if not home or not away or home == away:
        return render_match_summary(league, home, away), "", ""
    try:
        model = build_match_model(league, home, away)
    except FootballDataError as error:
        error_html = (
            '<p style="color:#b91c1c;font-weight:600">'
            f"Dati Football-Data.org non disponibili: {escape(str(error))}</p>"
        )
        return (
            error_html,
            '<p style="color:#b91c1c">Impossibile calcolare le probabilità 1X2 senza '
            f"risultati live: {escape(str(error))}</p>",
            '<p style="color:#b91c1c">Impossibile calcolare le probabilità senza '
            f"risultati live: {escape(str(error))}</p>",
        )
    return (
        render_match_summary(league, home, away),
        render_outcome_table(model, home, away),
        render_probability_table(pd.DataFrame(micro_event_rows(model))),
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

    match_summary_html, outcome_html, poisson_html = update_analysis(league, home, away)
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
        else:
            st.markdown("##### Pronostico 1X2")
            if outcome_html:
                st.markdown(outcome_html, unsafe_allow_html=True)
            st.markdown("##### Micro-eventi (tiri, corner, cartellini, falli)")
            if poisson_html:
                st.markdown(poisson_html, unsafe_allow_html=True)
            else:
                st.info("Probabilità non disponibili per questa selezione.")
        st.markdown(
            "##### Lettura del modello\n"
            "Tutte le probabilità (1X2 e micro-eventi) derivano dallo stesso "
            "Global Power Rating: gol attesi, tiri fatti/subiti e corner sono "
            "scalati in base al differenziale di rating fra le due squadre "
            "(fattore campo incluso), non da semplici medie grezze."
        )

    with tab_montecarlo:
        st.markdown(
            "Ogni esecuzione genera 10.000 partite indipendenti con distribuzioni "
            "di Poisson calcolate sugli stessi lambda del Global Power Rating: "
            "le frequenze qui sotto devono essere coerenti con il pronostico 1X2 "
            "mostrato nella scheda Poisson."
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
                    outcome_frame: pd.DataFrame = simulation["outcomes"]
                    event_frame: pd.DataFrame = simulation["events"]

                    st.markdown("**Pronostico 1X2 simulato (confronto con il calcolo analitico)**")
                    st.dataframe(outcome_frame, use_container_width=True, hide_index=True)

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
