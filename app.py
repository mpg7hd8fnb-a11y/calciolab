from __future__ import annotations

import math
import os
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

# --- Time-Decay per i dati storici -------------------------------------------
PREVIOUS_SEASON_MAX_WEIGHT = 0.35
"""Peso massimo (35%) assegnato alle partite della STAGIONE PRECEDENTE nel
calcolo delle medie (tiri, xG, forma). Le partite della stagione corrente
valgono sempre il 100% (peso 1.0)."""

# --- Modalità Inizio Stagione --------------------------------------------------
EARLY_SEASON_MATCHDAY_THRESHOLD = 5
"""Sotto questa soglia di partite REALI giocate nella stagione corrente, la
squadra è considerata in 'Modalità Inizio Stagione': i dati osservati vengono
mescolati con il Power Index teorico di base (vedi blend_with_theoretical)."""

LEAGUE_AVERAGE_GOALS_PER_TEAM = 1.35
"""Gol attesi 'di libro' per una squadra media in una singola partita di
massima serie: ancoraggio del Power Index teorico di base a inizio stagione."""

# --- Slider manuali "Impatto Mercato" e "Impatto Infortuni" -------------------
MARKET_FACTOR_BOUNDS = (-0.20, 0.20)
"""Range consentito per lo slider 'Fattore Mercato' (-20% / +20%)."""

INJURY_FACTOR_BOUNDS = (-0.30, 0.30)
"""Range consentito per lo slider 'Impatto Infortuni / Titolari Assenti'
(-30% / +30%)."""

# --- Correzione Dixon-Coles -----------------------------------------------------
DIXON_COLES_RHO = -0.13
"""Parametro ρ di Dixon-Coles (Dixon & Coles, 1997): corregge la Poisson
bivariata indipendente sui 4 risultati a basso punteggio (0-0, 1-0, 0-1, 1-1),
dove nella realtà i pareggi/risultati bassi sono leggermente più frequenti di
quanto preveda il semplice prodotto di due Poisson indipendenti."""


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


def theoretical_expected_goals(team: str, league: str) -> float:
    """Gol attesi 'di libro' derivati solo dal rating strutturale (senza dati
    stagionali osservati): il Power Index teorico di base usato dalla
    Modalità Inizio Stagione quando i dati reali disponibili sono pochi."""
    rating_gap = base_power_rating(team, league) - BASE_RATING
    return LEAGUE_AVERAGE_GOALS_PER_TEAM * math.exp(RATING_LAMBDA_SENSITIVITY * rating_gap)


def blend_with_theoretical(observed_value: float, theoretical_value: float, matches_played: float) -> float:
    """Modalità Inizio Stagione: con meno di EARLY_SEASON_MATCHDAY_THRESHOLD
    partite REALI nella stagione corrente, mescola il valore osservato con
    quello teorico (Power Index di base), dando sempre più peso ai dati reali
    man mano che le giornate si accumulano (confidenza lineare 0→1)."""
    confidence = clamp(matches_played / EARLY_SEASON_MATCHDAY_THRESHOLD, 0.0, 1.0)
    return confidence * observed_value + (1 - confidence) * theoretical_value


def is_early_season_match(home_stats: "LiveTeamStats", away_stats: "LiveTeamStats") -> bool:
    """True se almeno una delle due squadre ha giocato meno di
    EARLY_SEASON_MATCHDAY_THRESHOLD partite REALI nella stagione corrente."""
    return (
        home_stats.current_season_matches < EARLY_SEASON_MATCHDAY_THRESHOLD
        or away_stats.current_season_matches < EARLY_SEASON_MATCHDAY_THRESHOLD
    )


def dixon_coles_tau(
    home_goals: int, away_goals: int, home_lambda: float, away_lambda: float, rho: float = DIXON_COLES_RHO
) -> float:
    """Fattore correttivo di Dixon-Coles (Dixon & Coles, 1997) per i quattro
    risultati a basso punteggio dove la Poisson bivariata indipendente è
    sistematicamente imprecisa: 0-0, 1-0, 0-1, 1-1. Per tutti gli altri
    risultati il fattore è 1.0 (nessuna correzione)."""
    if home_goals == 0 and away_goals == 0:
        return 1 - (home_lambda * away_lambda * rho)
    if home_goals == 0 and away_goals == 1:
        return 1 + (home_lambda * rho)
    if home_goals == 1 and away_goals == 0:
        return 1 + (away_lambda * rho)
    if home_goals == 1 and away_goals == 1:
        return 1 - rho
    return 1.0


def match_outcome_probabilities(
    home_lambda: float, away_lambda: float, max_goals: int = 10, rho: float = DIXON_COLES_RHO
) -> tuple[float, float, float]:
    """Probabilità 1X2 (vittoria casa, pareggio, vittoria trasferta) calcolate
    dalla matrice di Poisson bivariata su home_lambda/away_lambda, con la
    correzione di Dixon-Coles applicata ai 4 risultati a basso punteggio per
    una stima più accurata dei pareggi: la stessa distribuzione (Poisson +
    Dixon-Coles) usata anche dalla simulazione Monte Carlo, a garanzia di
    coerenza fra tutte le viste dell'app."""
    home_pmf = [poisson.pmf(i, home_lambda) for i in range(max_goals + 1)]
    away_pmf = [poisson.pmf(j, away_lambda) for j in range(max_goals + 1)]
    home_win = draw = away_win = 0.0
    for i, p_home in enumerate(home_pmf):
        for j, p_away in enumerate(away_pmf):
            joint = p_home * p_away * dixon_coles_tau(i, j, home_lambda, away_lambda, rho)
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


def exact_score_probabilities(
    home_lambda: float, away_lambda: float, max_goals: int = 6, rho: float = DIXON_COLES_RHO
) -> list[tuple[str, float]]:
    """Probabilità dei risultati esatti (Poisson bivariata + correzione
    Dixon-Coles), ordinate per probabilità decrescente: stima ultra-accurata
    dei punteggi a basso score (0-0, 1-0, 0-1, 1-1) e degli altri risultati."""
    cells: list[tuple[str, float]] = []
    total = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            probability = poisson.pmf(i, home_lambda) * poisson.pmf(j, away_lambda)
            probability *= dixon_coles_tau(i, j, home_lambda, away_lambda, rho)
            cells.append((f"{i}-{j}", probability))
            total += probability
    if total <= 0:
        return []
    return sorted(
        ((score, probability / total) for score, probability in cells),
        key=lambda item: item[1],
        reverse=True,
    )


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
    recente, slider manuali, Dixon-Coles) applicati dal motore per il match."""
    early_season_warning: bool = False
    """True se una delle due squadre ha meno di EARLY_SEASON_MATCHDAY_THRESHOLD
    partite reali nella stagione corrente (Modalità Inizio Stagione attiva)."""
    home_current_season_matches: int = 0
    away_current_season_matches: int = 0
    manual_factor_home: float = 0.0
    """Somma di Fattore Mercato + Impatto Infortuni applicata alla squadra di casa."""
    manual_factor_away: float = 0.0
    """Somma di Fattore Mercato + Impatto Infortuni applicata alla squadra ospite."""



class FootballDataError(RuntimeError):
    """Raised when Football-Data.org cannot provide the requested live data."""


@dataclass(frozen=True)
class LiveTeamStats:
    team_id: int
    team_name: str
    matches: float
    home_matches: float
    away_matches: float
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
    current_season_matches: int = 0
    """Partite REALI (non pesate) disputate nella stagione in corso: usato per
    la Modalità Inizio Stagione (vedi EARLY_SEASON_MATCHDAY_THRESHOLD)."""


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
    season_start, teams, matches, _crests = fetch_competition_snapshot(league)
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


def _parse_team_crests(payload: dict[str, object]) -> dict[str, str]:
    """Estrae il campo 'crest' (URL dello stemma ufficiale) di ogni squadra,
    usato per l'header della dashboard con i loghi dei club."""
    response = payload.get("teams", [])
    if not isinstance(response, list):
        return {}
    crest_map: dict[str, str] = {}
    for team in response:
        if not isinstance(team, dict):
            continue
        name = team.get("name") or team.get("shortName")
        crest = team.get("crest")
        if isinstance(name, str) and isinstance(crest, str) and crest:
            crest_map[name] = crest
    return crest_map


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
) -> tuple[int, tuple[tuple[int, str], ...], tuple[dict[str, object], ...], dict[str, str]]:
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
        crest_map = _parse_team_crests(teams_payload)
        return season_start, teams, _parse_finished_matches(matches_payload), crest_map
    except FootballDataError:
        fallback_teams = _fallback_team_snapshot(league)
        if len(fallback_teams) < 2:
            raise
        # L'API non è disponibile: continuiamo con la lista di riserva delle
        # squadre della nuova stagione, senza calendario/risultati live né loghi.
        return season_start, fallback_teams, (), {}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_league_teams(league: str) -> tuple[tuple[int, str], ...]:
    return fetch_competition_snapshot(league)[1]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_team_crests(league: str) -> dict[str, str]:
    """URL degli stemmi ufficiali per ogni squadra del campionato (se
    disponibili da Football-Data.org)."""
    return fetch_competition_snapshot(league)[3]


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


def _average(total: float, count: float, label: str, team_name: str) -> float:
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

    def _team_fixtures(matches: tuple[dict[str, object], ...]) -> list[dict[str, object]]:
        return [
            match
            for match in matches
            if _match_has_final_score(match)
            and (
                match["homeTeam"].get("id") == team_id
                or match["awayTeam"].get("id") == team_id
                or match["homeTeam"].get("name") == team_name
                or match["awayTeam"].get("name") == team_name
            )
        ]

    current_fixtures = _team_fixtures(fetch_league_matches(league))[:8]
    try:
        previous_fixtures = _team_fixtures(fetch_previous_season_matches(league))[:8]
    except FootballDataError:
        previous_fixtures = []

    # Partite REALI (non pesate) disputate nella stagione in corso: base per
    # la Modalità Inizio Stagione (vedi EARLY_SEASON_MATCHDAY_THRESHOLD).
    current_season_matches = len(current_fixtures)

    # --- Time-Decay: stagione corrente peso 1.0, precedente al massimo
    # PREVIOUS_SEASON_MAX_WEIGHT (35%). La stagione corrente viene prima nel
    # pool, così ha sempre la priorità anche nel calcolo del Form Factor.
    weighted_pool: list[tuple[dict[str, object], float]] = [
        (fixture, 1.0) for fixture in current_fixtures
    ] + [(fixture, PREVIOUS_SEASON_MAX_WEIGHT) for fixture in previous_fixtures]

    goals_for = goals_against = 0.0
    home_goals_for = home_goals_against = 0.0
    away_goals_for = away_goals_against = 0.0
    home_matches = away_matches = 0.0
    recent_results: list[str] = []
    recent_points: list[int] = []
    recent_weights: list[float] = []

    for fixture_item, weight in weighted_pool:
        home_data = fixture_item.get("homeTeam", {})
        score = fixture_item.get("score", {})
        full_time = score.get("fullTime", {}) if isinstance(score, dict) else {}
        is_home = home_data.get("id") == team_id
        scored = _number(full_time.get("home" if is_home else "away"))
        conceded = _number(full_time.get("away" if is_home else "home"))
        if scored is None or conceded is None:
            continue

        goals_for += scored * weight
        goals_against += conceded * weight
        if is_home:
            home_matches += weight
            home_goals_for += scored * weight
            home_goals_against += conceded * weight
        else:
            away_matches += weight
            away_goals_for += scored * weight
            away_goals_against += conceded * weight

        # Form Factor: le prime FORM_MATCHES_WINDOW partite del pool (la
        # stagione corrente è in testa, quindi ha sempre la priorità; la
        # stagione precedente riempie la finestra solo a inizio stagione, con
        # peso ridotto tramite recent_weights).
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
            recent_weights.append(weight)

    matches = home_matches + away_matches
    if matches == 0:
        # Nessuna partita utilizzabile né in stagione corrente né in quella
        # precedente per questa squadra: fallback estremo sulla media di
        # tutte le partite della stagione precedente nel campionato.
        previous_matches = fetch_previous_season_matches(league)
        scored_values: list[float] = []
        for match in previous_matches:
            score = match.get("score", {})
            full_time = score.get("fullTime", {}) if isinstance(score, dict) else {}
            scored = _number(full_time.get("home"))
            conceded = _number(full_time.get("away"))
            if scored is not None and conceded is not None:
                scored_values.extend((scored, conceded))
        if not scored_values:
            raise FootballDataError(
                f"Football-Data.org non ha dati storici utilizzabili per {team_name}."
            )
        neutral_average = sum(scored_values) / len(scored_values)
        matches = 8.0
        home_matches = away_matches = 4.0
        goals_for = goals_against = neutral_average * matches
        home_goals_for = away_goals_for = neutral_average * 4
        home_goals_against = away_goals_against = neutral_average * 4
        recent_results = []
        recent_points = []
        recent_weights = []

    baseline = MICRO_EVENT_BASELINES[FOOTBALL_DATA_COMPETITIONS[league]]
    # The provider has no micro-event endpoint. Scale the transparent baseline
    # slightly with recent scoring, while keeping the source distinction clear.
    scoring_factor = clamp(0.88 + (goals_for / matches) * 0.08, 0.88, 1.12)
    form_factor = compute_form_factor(recent_points, recent_weights)

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
        current_season_matches=current_season_matches,
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


def compute_form_factor(
    recent_points: Sequence[int], season_weights: Sequence[float] | None = None
) -> float:
    """Form Factor dinamico: calcola un moltiplicatore intorno a 1.0 pesando
    i punti (Vittoria=3, Pareggio=1, Sconfitta=0) delle ultime partite con
    FORM_RECENCY_WEIGHTS, ulteriormente moltiplicati per `season_weights`
    (Time-Decay: 1.0 per la stagione corrente, PREVIOUS_SEASON_MAX_WEIGHT per
    la precedente), così un risultato della scorsa stagione pesa meno di uno
    di questa. Una squadra in ottima forma recente arriva fino a
    FORM_FACTOR_MAX, una in crisi di risultati scende fino a FORM_FACTOR_MIN.
    Senza dati recenti restituisce 1.0 (nessuna correzione)."""
    if not recent_points:
        return 1.0
    recency_weights = FORM_RECENCY_WEIGHTS[: len(recent_points)]
    season_weights = season_weights if season_weights is not None else [1.0] * len(recent_points)
    effective_weights = [rw * sw for rw, sw in zip(recency_weights, season_weights)]
    weighted_points = sum(points * weight for points, weight in zip(recent_points, effective_weights))
    weighted_max = sum(3 * weight for weight in effective_weights)
    if weighted_max <= 0:
        return 1.0
    ratio = clamp(weighted_points / weighted_max, 0.0, 1.0)
    return FORM_FACTOR_MIN + (FORM_FACTOR_MAX - FORM_FACTOR_MIN) * ratio



def build_match_model(
    league: str,
    home: str,
    away: str,
    market_factor_home: float = 0.0,
    market_factor_away: float = 0.0,
    injury_factor_home: float = 0.0,
    injury_factor_away: float = 0.0,
) -> MatchModel:
    home_stats = fetch_team_live_stats(league, home)
    away_stats = fetch_team_live_stats(league, away)

    # --- 1. Statistiche osservate, già pesate con Time-Decay in
    # fetch_team_live_stats: stagione corrente 100%, precedente al massimo
    # PREVIOUS_SEASON_MAX_WEIGHT. -------------------------------------------
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

    # --- 2. Modalità Inizio Stagione: con meno di EARLY_SEASON_MATCHDAY_
    # THRESHOLD partite REALI in questa stagione, mescola il dato osservato
    # con il Power Index teorico di base (nessun dato stagionale). -----------
    early_season = is_early_season_match(home_stats, away_stats)
    home_lambda_raw = blend_with_theoretical(
        home_lambda_raw, theoretical_expected_goals(home, league), home_stats.current_season_matches
    )
    away_lambda_raw = blend_with_theoretical(
        away_lambda_raw, theoretical_expected_goals(away, league), away_stats.current_season_matches
    )

    # --- 3. Slider manuali "Fattore Mercato" e "Impatto Infortuni/Titolari
    # Assenti": la percentuale scelta nella sidebar incrementa/riduce sia il
    # Power Index sia la stima di attacco/difesa attesa PRIMA di calcolare
    # xG, tiri e probabilità. La squadra rinforzata segna di più (attacco) e
    # concede meno (difesa migliorata riduce l'attacco avversario), e
    # viceversa per un fattore negativo. -------------------------------------
    manual_factor_home = clamp(market_factor_home, *MARKET_FACTOR_BOUNDS) + clamp(
        injury_factor_home, *INJURY_FACTOR_BOUNDS
    )
    manual_factor_away = clamp(market_factor_away, *MARKET_FACTOR_BOUNDS) + clamp(
        injury_factor_away, *INJURY_FACTOR_BOUNDS
    )

    home_lambda_raw *= (1 + manual_factor_home) * (1 - manual_factor_away)
    away_lambda_raw *= (1 + manual_factor_away) * (1 - manual_factor_home)
    home_shots_raw *= (1 + manual_factor_home) * (1 - manual_factor_away)
    away_shots_raw *= (1 + manual_factor_away) * (1 - manual_factor_home)
    home_sot_raw *= (1 + manual_factor_home) * (1 - manual_factor_away)
    away_sot_raw *= (1 + manual_factor_away) * (1 - manual_factor_home)

    home_lambda_raw = max(home_lambda_raw, 0.02)
    away_lambda_raw = max(away_lambda_raw, 0.02)
    home_shots_raw = max(home_shots_raw, 1.0)
    away_shots_raw = max(away_shots_raw, 1.0)
    home_sot_raw = max(home_sot_raw, 0.3)
    away_sot_raw = max(away_sot_raw, 0.3)

    # --- 4. Global Power Rating (strutturale + Form Factor + slider manuali) -
    home_rating = global_power_rating(home, league, home_stats.form_factor) + manual_factor_home * RATING_SCALE
    away_rating = global_power_rating(away, league, away_stats.form_factor) + manual_factor_away * RATING_SCALE

    # Il fattore campo entra come bonus di rating solo per il calcolo di questo
    # match: pesa quindi su OGNI metrica derivata dal differenziale, non solo
    # sui gol attesi, garantendo coerenza fra tutte le tabelle dell'app.
    rating_diff = (home_rating + HOME_ADVANTAGE_RATING) - away_rating

    # --- 5. Gol attesi (xG): piena sensibilità al gap di rating -----------------
    goal_boost, goal_suppress = rating_scaling_factors(rating_diff, damping=1.0)
    home_lambda = clamp(home_lambda_raw * goal_boost, 0.05, 5.5)
    away_lambda = clamp(away_lambda_raw * goal_suppress, 0.05, 5.0)

    # --- 6. Tiri totali/in porta: dipendono dal rating offensivo/difensivo -----
    # relativo, con sensibilità smorzata rispetto ai gol (i tiri riflettono la
    # pressione di gioco più che l'efficienza sotto porta).
    shot_boost, shot_suppress = rating_scaling_factors(rating_diff, damping=SHOT_RATING_DAMPING)
    home_shots = home_shots_raw * shot_boost
    away_shots = away_shots_raw * shot_suppress
    home_sot = home_sot_raw * shot_boost
    away_sot = away_sot_raw * shot_suppress
    shots_total = home_shots + away_shots

    # --- 7. Corner: legati anche al possesso, sensibilità ulteriormente smorzata
    corner_boost, corner_suppress = rating_scaling_factors(rating_diff, damping=CORNER_RATING_DAMPING)
    corners_total = home_corners_raw * corner_boost + away_corners_raw * corner_suppress

    # --- 8. Cartellini: la squadra in difficoltà commette più falli tattici ----
    normalized_gap = clamp(abs(rating_diff) / RATING_SCALE, 0.0, 1.0)
    if rating_diff >= 0:
        home_cards = home_cards_raw * (1 - 0.5 * CARD_UNDERDOG_BONUS * normalized_gap)
        away_cards = away_cards_raw * (1 + CARD_UNDERDOG_BONUS * normalized_gap)
    else:
        home_cards = home_cards_raw * (1 + CARD_UNDERDOG_BONUS * normalized_gap)
        away_cards = away_cards_raw * (1 - 0.5 * CARD_UNDERDOG_BONUS * normalized_gap)
    home_cards = clamp(home_cards, 0.1, 6.0)
    away_cards = clamp(away_cards, 0.1, 6.0)

    # --- 9. Probabilità 1X2: Poisson bivariata + correzione Dixon-Coles --------
    # Stessa distribuzione usata dalle tabelle micro-eventi e dalla simulazione
    # Monte Carlo, cosicché ogni vista dell'app racconti lo stesso match.
    home_win_prob, draw_prob, away_win_prob = match_outcome_probabilities(home_lambda, away_lambda)

    engine_note = (
        f"Global Power Rating: {home} {home_rating:.0f} (+{HOME_ADVANTAGE_RATING:.0f} campo) "
        f"vs {away} {away_rating:.0f} · gap effettivo {rating_diff:+.0f} punti · "
        f"xG ×{goal_boost:.2f}/×{goal_suppress:.2f} · tiri ×{shot_boost:.2f}/×{shot_suppress:.2f} · "
        f"correzione Dixon-Coles ρ={DIXON_COLES_RHO:+.2f}"
    )
    if home_stats.recent_form:
        engine_note += f" · forma {home}: {''.join(home_stats.recent_form)}"
    if away_stats.recent_form:
        engine_note += f" · forma {away}: {''.join(away_stats.recent_form)}"
    if manual_factor_home:
        engine_note += f" · slider {home}: {manual_factor_home:+.0%}"
    if manual_factor_away:
        engine_note += f" · slider {away}: {manual_factor_away:+.0%}"
    if early_season:
        engine_note += (
            f" · ⚠️ Inizio Stagione: {home} {home_stats.current_season_matches} "
            f"partite, {away} {away_stats.current_season_matches} partite disputate finora"
        )

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
        early_season_warning=early_season,
        home_current_season_matches=home_stats.current_season_matches,
        away_current_season_matches=away_stats.current_season_matches,
        manual_factor_home=manual_factor_home,
        manual_factor_away=manual_factor_away,
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

    # --- Correzione Dixon-Coles sulla simulazione Monte Carlo -------------------
    # Ogni partita simulata riceve un peso: 1.0 di default, oppure il fattore
    # tau di Dixon-Coles per i 4 risultati a basso punteggio (0-0, 1-0, 0-1,
    # 1-1), così le frequenze pesate restano coerenti con la stessa
    # correzione applicata in match_outcome_probabilities.
    weights = np.ones(n_simulations)
    for h_goals, a_goals in ((0, 0), (0, 1), (1, 0), (1, 1)):
        cell_mask = (home_goals == h_goals) & (away_goals == a_goals)
        weights[cell_mask] = dixon_coles_tau(h_goals, a_goals, model.home_lambda, model.away_lambda)
    total_weight = float(weights.sum())

    weighted_scores: dict[tuple[int, int], float] = {}
    for h_goal, a_goal, weight in zip(home_goals.tolist(), away_goals.tolist(), weights.tolist()):
        key = (h_goal, a_goal)
        weighted_scores[key] = weighted_scores.get(key, 0.0) + weight
    top_scores = sorted(weighted_scores.items(), key=lambda item: item[1], reverse=True)[:5]
    score_rows = [
        {
            "Risultato esatto": f"{h_goal}-{a_goal}",
            "Simulazioni": int(round(weight)),
            "Probabilità": weight / total_weight,
        }
        for (h_goal, a_goal), weight in top_scores
    ]

    # Frequenze 1X2 (pesate Dixon-Coles) osservate nelle 10.000 simulazioni:
    # servono a validare che la probabilità analitica (Poisson bivariata +
    # Dixon-Coles) e quella simulata dal motore Monte Carlo raccontino lo
    # stesso match.
    home_win_mask = home_goals > away_goals
    draw_mask = home_goals == away_goals
    away_win_mask = home_goals < away_goals
    home_wins = float(weights[home_win_mask].sum())
    draws = float(weights[draw_mask].sum())
    away_wins = float(weights[away_win_mask].sum())
    outcome_rows = [
        {"Esito": "1 (vittoria casa)", "Simulazioni": int(round(home_wins)), "Probabilità": home_wins / total_weight},
        {"Esito": "X (pareggio)", "Simulazioni": int(round(draws)), "Probabilità": draws / total_weight},
        {"Esito": "2 (vittoria trasferta)", "Simulazioni": int(round(away_wins)), "Probabilità": away_wins / total_weight},
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
    """Tabella Pronostici 1X2 con quote implicite (Poisson bivariata +
    Dixon-Coles), a complemento delle metriche in evidenza mostrate con
    st.metric nella dashboard."""
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


def try_build_match_model(
    league: str,
    home: str,
    away: str,
    market_factor_home: float = 0.0,
    market_factor_away: float = 0.0,
    injury_factor_home: float = 0.0,
    injury_factor_away: float = 0.0,
) -> tuple[MatchModel | None, str]:
    """Costruisce il MatchModel (unico motore di simulazione) gestendo in modo
    uniforme i casi di squadre mancanti/uguali o dati Football-Data.org non
    disponibili. Restituisce (None, messaggio_errore) in caso di problemi."""
    if not home or not away:
        return None, "Carica le squadre da Football-Data.org per iniziare."
    if home == away:
        return None, "Seleziona due squadre diverse."
    try:
        model = build_match_model(
            league,
            home,
            away,
            market_factor_home=market_factor_home,
            market_factor_away=market_factor_away,
            injury_factor_home=injury_factor_home,
            injury_factor_away=injury_factor_away,
        )
    except FootballDataError as error:
        return None, f"Dati Football-Data.org non disponibili: {error}"
    return model, ""


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


def render_sidebar_controls() -> dict[str, float]:
    """Slider manuali nella sidebar: Fattore Mercato (-20%/+20%) e Impatto
    Infortuni/Titolari Assenti (-30%/+30%), per casa e trasferta. I valori
    incrementano/riducono Power Index e attacco/difesa attesa PRIMA del
    calcolo di xG, tiri e probabilità (vedi build_match_model)."""
    st.markdown("### 💼 Impatto Mercato / Aspettative")
    st.caption("Rinforzi o cessioni importanti rispetto alla media stagionale.")
    market_factor_home = (
        st.slider("Fattore Mercato Casa", -20, 20, 0, format="%d%%", key="market_factor_home") / 100
    )
    market_factor_away = (
        st.slider("Fattore Mercato Trasferta", -20, 20, 0, format="%d%%", key="market_factor_away") / 100
    )

    st.markdown("### 🩹 Impatto Infortuni / Titolari Assenti")
    st.caption("Assenze pesanti rispetto alla formazione tipo.")
    injury_factor_home = (
        st.slider("Impatto Infortuni Casa", -30, 30, 0, format="%d%%", key="injury_factor_home") / 100
    )
    injury_factor_away = (
        st.slider("Impatto Infortuni Trasferta", -30, 30, 0, format="%d%%", key="injury_factor_away") / 100
    )

    return {
        "market_factor_home": market_factor_home,
        "market_factor_away": market_factor_away,
        "injury_factor_home": injury_factor_home,
        "injury_factor_away": injury_factor_away,
    }


def render_team_header(league: str, home: str, away: str, crests: dict[str, str]) -> None:
    """Header con stemmi ufficiali (campo 'crest' di Football-Data.org)
    affiancati ai nomi delle squadre in grande."""
    st.markdown(f'<div class="league-tag">{escape(league)}</div>', unsafe_allow_html=True)
    col_home, col_vs, col_away = st.columns([2, 0.6, 2])
    with col_home:
        if crests.get(home):
            st.image(crests[home], width=84)
        st.markdown(f'<div class="team-name">{escape(home)}</div>', unsafe_allow_html=True)
        st.caption("Casa")
    with col_vs:
        st.markdown('<div class="vs-badge">VS</div>', unsafe_allow_html=True)
    with col_away:
        if crests.get(away):
            st.image(crests[away], width=84)
        st.markdown(f'<div class="team-name">{escape(away)}</div>', unsafe_allow_html=True)
        st.caption("Trasferta")


def render_metric_cards(cards: list[tuple[str, str]], columns: int = 4) -> None:
    """Card visive pulite (CSS custom) organizzate su più colonne per le
    stime dei micro-eventi (xG, tiri, corner, Under/Over...)."""
    cols = st.columns(columns)
    for index, (label, value) in enumerate(cards):
        with cols[index % columns]:
            st.markdown(
                f'<div class="metric-card"><div class="metric-card-label">{escape(label)}</div>'
                f'<div class="metric-card-value">{escape(value)}</div></div>',
                unsafe_allow_html=True,
            )


def render_dashboard(sidebar_values: dict[str, float]) -> None:
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

    with st.expander("📅 Calendario stagione 2026/27", expanded=False):
        st.dataframe(calendar, use_container_width=True, hide_index=True)

    if home == away:
        st.info("Seleziona due squadre diverse per avviare l'analisi.")
        return

    try:
        crests = fetch_team_crests(league)
    except FootballDataError:
        crests = {}

    st.markdown("---")
    render_team_header(league, home, away, crests)

    model, error_message = try_build_match_model(
        league,
        home,
        away,
        market_factor_home=sidebar_values["market_factor_home"],
        market_factor_away=sidebar_values["market_factor_away"],
        injury_factor_home=sidebar_values["injury_factor_home"],
        injury_factor_away=sidebar_values["injury_factor_away"],
    )

    if model is None:
        st.error(error_message)
        return

    # --- Avviso Modalità Inizio Stagione (badge/warning giallo) -----------------
    if model.early_season_warning:
        st.warning(
            "⚠️ Analisi a confidenza ridotta - Inizio Stagione in corso  \n"
            f"{home}: {model.home_current_season_matches} partite disputate · "
            f"{away}: {model.away_current_season_matches} partite disputate "
            f"(soglia piena confidenza: {EARLY_SEASON_MATCHDAY_THRESHOLD}). "
            "Il Power Index viene mescolato con dati reali ancora parziali."
        )

    # --- Visualizzazione 1X2 in evidenza (st.metric su 3 colonne) --------------
    col_1x2_home, col_1x2_draw, col_1x2_away = st.columns(3)
    with col_1x2_home:
        st.metric(f"🏠 Vittoria {home}", f"{model.home_win_prob:.1%}")
    with col_1x2_draw:
        st.metric("🤝 Pareggio", f"{model.draw_prob:.1%}")
    with col_1x2_away:
        st.metric(f"✈️ Vittoria {away}", f"{model.away_win_prob:.1%}")

    # --- Card visive pulite per le stime dei micro-eventi -----------------------
    total_goals_lambda = model.home_lambda + model.away_lambda
    over_25 = over_probability(total_goals_lambda, 2.5)
    metric_cards = [
        (f"Global Power Rating {home}", f"{model.home_rating:.0f}"),
        (f"Global Power Rating {away}", f"{model.away_rating:.0f}"),
        ("xG Casa", f"{model.home_lambda:.2f}"),
        ("xG Trasferta", f"{model.away_lambda:.2f}"),
        ("Tiri Totali", f"{model.shots_total_lambda:.1f}"),
        ("Tiri in Porta (match)", f"{model.shots_on_target_total_lambda:.1f}"),
        ("Corner Totali", f"{model.corners_total_lambda:.1f}"),
        ("Cartellini Totali", f"{model.cards_total_lambda:.1f}"),
        ("Over 2.5 Gol", f"{over_25:.1%}"),
        ("Under 2.5 Gol", f"{1 - over_25:.1%}"),
    ]
    render_metric_cards(metric_cards, columns=5)

    note = escape(model.engine_note) if model.engine_note else "Global Power Rating calcolato."
    st.caption(note)

    tab_poisson, tab_montecarlo = st.tabs(
        [
            "Analisi Quote & Probabilità (Poisson)",
            "Simulatore Monte Carlo (10.000 Partite)",
        ]
    )

    with tab_poisson:
        st.markdown(
            "Le righe in verde brillante indicano probabilità superiori all'80%. "
            "La fair odds è l'inverso della probabilità modellata. Pareggi e "
            "risultati a basso punteggio sono corretti con Dixon-Coles."
        )
        st.markdown("##### Dettaglio quote implicite 1X2")
        st.markdown(render_outcome_table(model, home, away), unsafe_allow_html=True)

        st.markdown("##### Risultati esatti più probabili (Poisson + Dixon-Coles)")
        exact_scores = exact_score_probabilities(model.home_lambda, model.away_lambda)[:6]
        exact_score_frame = pd.DataFrame(
            [{"Risultato": score, "Probabilità": f"{prob:.1%}"} for score, prob in exact_scores]
        )
        st.dataframe(exact_score_frame, use_container_width=True, hide_index=True)

        st.markdown("##### Micro-eventi (tiri, corner, cartellini, falli)")
        poisson_html = render_probability_table(pd.DataFrame(micro_event_rows(model)))
        st.markdown(poisson_html, unsafe_allow_html=True)

        st.markdown(
            "##### Lettura del modello\n"
            "Tutte le probabilità (1X2 e micro-eventi) derivano dallo stesso "
            "Global Power Rating: gol attesi, tiri fatti/subiti e corner sono "
            "scalati in base al differenziale di rating fra le due squadre "
            "(fattore campo incluso), con Time-Decay sui dati storici, "
            "Modalità Inizio Stagione e slider manuali applicati a monte, e "
            "correzione Dixon-Coles sui pareggi/risultati bassi."
        )

    with tab_montecarlo:
        st.markdown(
            "Ogni esecuzione genera 10.000 partite indipendenti con distribuzioni "
            "di Poisson calcolate sugli stessi lambda del Global Power Rating, "
            "pesate con la correzione Dixon-Coles sui risultati a basso punteggio: "
            "le frequenze qui sotto devono essere coerenti con il pronostico 1X2 "
            "mostrato nella scheda Poisson."
        )
        run_clicked = st.button(
            "Esegui 10.000 Simulazioni Monte Carlo",
            type="primary",
            key="simulate_button",
        )
        if run_clicked:
            simulation = run_simulation(model)
            score_frame: pd.DataFrame = simulation["scores"]
            outcome_frame: pd.DataFrame = simulation["outcomes"]
            event_frame: pd.DataFrame = simulation["events"]

            st.markdown("**Pronostico 1X2 simulato (confronto con il calcolo analitico)**")
            st.dataframe(outcome_frame, use_container_width=True, hide_index=True)

            col_scores, col_chart = st.columns(2)
            with col_scores:
                st.markdown("**I 5 risultati esatti più frequenti (pesati Dixon-Coles)**")
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
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e2e8f0",
                )
                st.plotly_chart(chart, use_container_width=True)

            st.markdown("**Frequenza dei micro-eventi chiave**")
            st.dataframe(event_frame, use_container_width=True, hide_index=True)
            st.success("Simulazione completata: 10.000 partite generate.")


DARK_THEME_CSS = """
<style>
:root {
    --clab-bg: #0f1420;
    --clab-card: #171e2e;
    --clab-border: #2a3348;
    --clab-accent: #22d3ee;
    --clab-text: #e2e8f0;
    --clab-muted: #94a3b8;
}

html, body, [class*="css"] {
    font-family: "Inter", "Segoe UI", -apple-system, sans-serif;
}

.stApp {
    background: radial-gradient(circle at top left, #131a2b 0%, var(--clab-bg) 55%);
    color: var(--clab-text);
}

section[data-testid="stSidebar"] {
    background: #0b0f19;
    border-right: 1px solid var(--clab-border);
}

.league-tag {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 999px;
    background: rgba(34, 211, 238, 0.12);
    color: var(--clab-accent);
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    margin-bottom: 10px;
}

.team-name {
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--clab-text);
    margin-top: 6px;
}

.vs-badge {
    text-align: center;
    font-weight: 800;
    font-size: 1.1rem;
    color: var(--clab-muted);
    margin-top: 34px;
    border: 1px solid var(--clab-border);
    border-radius: 999px;
    padding: 6px 0;
    background: var(--clab-card);
}

.metric-card {
    background: linear-gradient(160deg, var(--clab-card) 0%, #131a2b 100%);
    border: 1px solid var(--clab-border);
    border-radius: 16px;
    padding: 16px 14px;
    margin-bottom: 14px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
}

.metric-card-label {
    font-size: 0.78rem;
    color: var(--clab-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 6px;
}

.metric-card-value {
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--clab-accent);
}

div[data-testid="stMetric"] {
    background: var(--clab-card);
    border: 1px solid var(--clab-border);
    border-radius: 16px;
    padding: 14px 10px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
}

table {
    border-radius: 12px;
    overflow: hidden;
}

thead tr {
    background: #1c2438;
    color: var(--clab-text);
}

tbody tr {
    border-bottom: 1px solid var(--clab-border);
}

td, th {
    padding: 8px 10px !important;
}
</style>
"""


def main() -> None:
    st.set_page_config(
        page_title="CalcioLab · Analisi e Simulazioni",
        layout="wide",
    )
    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    st.markdown(
        "# ⚽ CalcioLab\n"
        "Analisi probabilistica e simulazioni di calcio con dati live da Football-Data.org."
    )

    if st.session_state.authenticated:
        with st.sidebar:
            st.success("Accesso autorizzato.")
            if st.button("Esci"):
                st.session_state.authenticated = False
                st.rerun()
            st.markdown("---")
            sidebar_values = render_sidebar_controls()
        render_dashboard(sidebar_values)
    else:
        render_login()


if __name__ == "__main__":
    main()
