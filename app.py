from __future__ import annotations

import json
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
    # massima serie a tutti gli effetti (il DIZIONARIO FASCE DI FORZA non
    # dipende comunque dalla lega selezionata, solo dal nome della squadra).
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
    # Campionati "secondari" (scraping FBref, vedi SECONDARY_LEAGUES più sotto):
    # baseline trasparenti stimate su medie storiche di categoria, sulla stessa
    # falsariga delle massime serie qui sopra.
    "SB": {"shots": 11.6, "shots_on_target": 3.8, "corners": 4.4, "cards": 2.5, "fouls": 13.2},
    "SD": {"shots": 11.4, "shots_on_target": 3.7, "corners": 4.3, "cards": 2.7, "fouls": 13.6},
}


# ==============================================================================
# CAMPIONATI SECONDARI (SCRAPING AUTOMATICO E GRATUITO) — Serie B & Segunda
# ==============================================================================
# Football-Data.org (piano gratuito) non copre la Serie B italiana né la
# Segunda División spagnola. Per questi due campionati i dati della stagione
# corrente (classifica, gol fatti/subiti, partite giocate) vengono estratti
# automaticamente da FBref tramite web scraping (pandas.read_html), SENZA
# alcuna chiave API. Questa fonte alimenta un ramo di calcolo dedicato in
# build_match_model che NON usa il DIZIONARIO FASCE DI FORZA fisso (vedi
# fetch_secondary_team_profile), ma calcola Attacco/Difesa dinamicamente
# dalla classifica reale, squadra per squadra.
SECONDARY_LEAGUES: dict[str, dict[str, str]] = {
    "Italia · Serie B": {
        "code": "SB",
        "fbref_url": "https://fbref.com/en/comps/18/Serie-B-Stats",
        "table_id_hint": "overall",
    },
    "Spagna · Segunda División": {
        "code": "SD",
        "fbref_url": "https://fbref.com/en/comps/17/Segunda-Division-Stats",
        "table_id_hint": "overall",
    },
}
"""Mappatura campionato -> {codice interno, URL FBref della pagina
'Stats' del campionato, frammento id della tabella classifica}. Aggiungere un
nuovo campionato scrapato richiede solo una nuova voce qui + un'eventuale
riga in MICRO_EVENT_BASELINES."""

SECONDARY_LEAGUE_SCRAPE_HEADERS = {
    # Alcuni siti (incluso FBref) restituiscono una risposta ridotta o un
    # blocco anti-bot senza uno User-Agent "da browser".
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
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


# ==============================================================================
# MOTORE UNICO DI SIMULAZIONE — Team Tiers + Dynamic Decay (Power Rating v3)
# ==============================================================================
# Corregge il bug di inizializzazione: prima le squadre non catalogate (o con
# un nome restituito dall'API leggermente diverso da quello atteso) finivano
# tutte sullo stesso rating di default, risultando talvolta più forti di top
# club realmente più forti ma appesantiti da un calo di forma. Ora ogni
# squadra viene sempre risolta in una delle 5 Fasce di Forza tramite fuzzy
# matching sul nome, con un fallback esplicito a Tier 3 (mai un default
# piatto arbitrario).
BASE_RATING = 1500.0
"""Rating ELO di riferimento (centro scala), usato come ancoraggio per
elo_expected_score e per i moltiplicatori derivati dal rating diff."""

RATING_SCALE = 400.0
"""Base della formula ELO standard (400 punti = fattore 10x nelle quote attese)."""

HOME_ADVANTAGE_RATING = 60.0
"""Bonus di rating ELO per il fattore campo, usato per differenziare
tiri/corner/cartellini in base al gap di rating (vedi rating_scaling_factors)."""

HOME_ADVANTAGE_GOAL_MULTIPLIER = 1.12
"""Moltiplicatore diretto sui gol attesi della squadra di casa (~+12%),
applicato al lambda calcolato da Attacco_Finale × Difesa_Finale avversaria."""

RATING_LAMBDA_SENSITIVITY = 0.0022
"""Quanto un punto di differenza di rating ELO sposta, in scala esponenziale,
tiri/corner/cartellini rispetto alla media osservata. I gol attesi derivano
invece direttamente da Attacco_Finale/Difesa_Finale (vedi build_match_model)."""

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

EARLY_SEASON_MATCHDAY_THRESHOLD = 5
"""Dalla Giornata 5 (N partite REALI giocate nella stagione corrente) si usa
il 100% dei dati/statistiche reali. Sotto questa soglia si applica la
Transizione Dinamica (Dynamic Decay, vedi dynamic_decay_weights)."""

LEAGUE_AVERAGE_GOALS_PER_TEAM = 1.35
"""Gol attesi 'di libro' per una squadra media in una singola partita di
massima serie: fattore di scala del modello Attacco_Finale × Difesa_Finale."""

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


# --- 1. DIZIONARIO FASCE DI FORZA (TEAM TIERS) --------------------------------
TEAM_TIER_PROFILES: dict[int, dict[str, float]] = {
    1: {"rating": 1750.0, "attack": 1.35, "defense": 0.70},  # Top / Titolo
    2: {"rating": 1600.0, "attack": 1.15, "defense": 0.85},  # Europa
    3: {"rating": 1480.0, "attack": 1.00, "defense": 1.00},  # Metà classifica
    4: {"rating": 1380.0, "attack": 0.85, "defense": 1.15},  # Salvezza
    5: {"rating": 1280.0, "attack": 0.75, "defense": 1.30},  # Neopromosse
}

TEAM_TIER_DEFAULT = 3
"""Fallback esplicito per una squadra non trovata nel dizionario: Tier 3
(Base Rating 1480) — MAI il vecchio default piatto 1500."""

TEAM_TIER_LABELS: dict[int, str] = {
    1: "Tier 1 · Top/Titolo",
    2: "Tier 2 · Europa",
    3: "Tier 3 · Metà classifica",
    4: "Tier 4 · Salvezza",
    5: "Tier 5 · Neopromosse",
}

# Chiavi in minuscolo: lookup_team_tier fa un matching per sottostringa (in
# entrambe le direzioni), quindi bastano frammenti brevi e distintivi — così
# 'Internazionale Milano' o 'FC Internazionale' vengono comunque riconosciuti
# come 'inter' senza bisogno di elencare ogni possibile variante del nome.
TEAM_TIER_KEYWORDS: dict[int, tuple[str, ...]] = {
    1: (  # Top / Titolo
        "inter", "juventus", "juve", "milan", "napoli", "atalanta",
        "manchester city", "man city", "arsenal", "liverpool",
        "real madrid", "bayern", "barcelona", "barça", "barca",
        "psg", "paris saint", "atletico madrid", "atlético madrid",
        "bayer leverkusen", "borussia dortmund",
    ),
    2: (  # Europa / Champions League
        "roma", "lazio", "fiorentina", "bologna", "chelsea", "tottenham",
        "spurs", "newcastle", "aston villa", "manchester united",
        "man united", "man utd", "rb lipsia", "rb leipzig", "marsiglia",
        "marseille", "villarreal", "stoccarda", "stuttgart", "lione",
        "lyon", "monaco", "psv", "sporting cp", "sporting", "porto",
        "como", "como 1907", "fc como",
    ),
    3: (  # Metà classifica
        "torino", "genoa", "udinese", "sassuolo", "everton", "fulham",
        "crystal palace", "brighton", "bournemouth", "athletic bilbao",
        "real betis", "lens", "lille", "feyenoord", "club brugge",
        "galatasaray",
    ),
    4: (  # Salvezza
        "lecce", "cagliari", "monza", "verona", "parma",
        "brentford", "forest", "nottingham", "leeds", "sunderland",
        "elche", "levante", "shakhtar", "slavia praga", "slavia prague",
    ),
    5: (  # Neopromosse
        "frosinone", "venezia", "coventry", "hull", "ipswich",
        "racing santander", "deportivo", "coruña", "coruna", "málaga",
        "malaga", "schalke", "elversberg", "paderborn", "troyes",
        "le mans", "ado den haag", "cambuur", "académico de viseu",
        "academico de viseu", "marítimo", "maritimo",
    ),
}


def _normalize_team_name(name: str) -> str:
    """Normalizza un nome squadra per il matching flessibile: minuscolo e
    spazi ripuliti, così un nome restituito dall'API in una forma diversa
    (es. 'Internazionale Milano' invece di 'Inter') viene riconosciuto."""
    return " ".join(name.strip().lower().split())


def lookup_team_tier(team_name: str) -> int:
    """LOGICA DI MATCHING FLESSIBILE (Fuzzy Matching/Normalization): cerca il
    nome (o un suo frammento) fra le keyword di ciascuna Fascia di Forza,
    controllando entrambe le direzioni della sottostringa. Se nessuna keyword
    corrisponde, il fallback è TEAM_TIER_DEFAULT (Tier 3 · 1480), mai il
    vecchio default piatto 1500."""
    normalized = _normalize_team_name(team_name)
    if not normalized:
        return TEAM_TIER_DEFAULT
    for tier in (1, 2, 3, 4, 5):
        for keyword in TEAM_TIER_KEYWORDS.get(tier, ()):
            if keyword in normalized or normalized in keyword:
                return tier
    return TEAM_TIER_DEFAULT


def team_tier_profile(team_name: str) -> dict[str, float]:
    """Profilo di Fascia (rating/attacco/difesa) risolto per la squadra
    tramite fuzzy matching sul DIZIONARIO FASCE DI FORZA (TEAM_TIER_PROFILES)."""
    return TEAM_TIER_PROFILES[lookup_team_tier(team_name)]


def dynamic_decay_weights(matches_played: int) -> tuple[float, float]:
    """TRANSIZIONE DINAMICA PER LE PRIME 5 GIORNATE (Dynamic Decay):
    Peso_Fascia = (5 - N) / 5, Peso_Stats = N / 5, con N = partite REALI
    giocate nella stagione corrente (clampato a [0, 5]). Da N ≥ 5 in poi si
    usa il 100% dei dati/statistiche reali (Peso_Fascia = 0)."""
    n = clamp(matches_played, 0, EARLY_SEASON_MATCHDAY_THRESHOLD)
    tier_weight = (EARLY_SEASON_MATCHDAY_THRESHOLD - n) / EARLY_SEASON_MATCHDAY_THRESHOLD
    stats_weight = n / EARLY_SEASON_MATCHDAY_THRESHOLD
    return tier_weight, stats_weight


def is_top_tier(team: str) -> bool:
    """True se la squadra è risolta in Tier 1 (Top/Titolo)."""
    return lookup_team_tier(team) == 1


def elo_expected_score(rating_a: float, rating_b: float) -> float:
    """Probabilità attesa stile ELO che la squadra A prevalga su B (0-1),
    dato il differenziale di rating fra le due (formula ELO standard)."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / RATING_SCALE))


def rating_scaling_factors(rating_diff: float, damping: float = 1.0) -> tuple[float, float]:
    """Converte un differenziale di rating ELO (squadra A meno squadra B) in
    una coppia di moltiplicatori continui (boost per A, suppressione per B)
    da applicare a tiri/corner/cartellini. `damping` attenua l'effetto per le
    metriche meno legate al puro gap di qualità (es. corner)."""
    exponent = RATING_LAMBDA_SENSITIVITY * damping * rating_diff
    boost = clamp(math.exp(exponent), 0.4, 2.6)
    suppression = clamp(math.exp(-exponent), 0.38, 2.5)
    return boost, suppression


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
    fatigue_attack_malus_home: float = 0.0
    fatigue_defense_malus_home: float = 0.0
    fatigue_attack_malus_away: float = 0.0
    fatigue_defense_malus_away: float = 0.0
    """Malus di Affaticamento & Turnover (Fase 2) effettivamente applicati ad
    attacco/difesa di ciascuna squadra, usati per il badge di allerta in UI."""



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



# ==============================================================================
# SCRAPING SERIE B / SEGUNDA DIVISIÓN (FBref) — 100% AUTOMATICO E GRATUITO
# ==============================================================================
# Estensione puramente additiva: NON tocca in alcun modo il percorso dati
# Football-Data.org (fetch_team_live_stats/build_match_model per i campionati
# principali restano identici). Per Serie B e Segunda División la classifica
# reale della stagione corrente viene scaricata da FBref e usata per calcolare
# Alpha (Attacco) e Beta (Difesa) DINAMICI squadra per squadra — mai un Tier
# fisso uguale per tutte le squadre.
class SecondaryLeagueDataError(FootballDataError):
    """Errore nello scraping FBref per un campionato secondario (Serie B,
    Segunda División). Eredita da FootballDataError così i punti dell'app che
    già gestiscono 'except FootballDataError' continuano a funzionare senza
    modifiche."""


def is_secondary_league(league: str) -> bool:
    """True se il campionato è coperto tramite scraping FBref (Serie B,
    Segunda División) invece che da Football-Data.org."""
    return league in SECONDARY_LEAGUES


def _extract_all_tables_html(page_html: str) -> list[str]:
    """FBref nasconde alcune tabelle dentro commenti HTML (<!-- ... -->) per
    scoraggiare lo scraping ingenuo. Restituisce sia le tabelle visibili sia
    quelle commentate, come frammenti HTML pronti per pandas.read_html."""
    import re

    commented_blocks = re.findall(r"<!--(.*?)-->", page_html, flags=re.DOTALL)
    return [page_html] + [block for block in commented_blocks if "<table" in block]


def _read_standings_table(page_html: str) -> pd.DataFrame:
    """Cerca, fra tutte le tabelle della pagina FBref (comprese quelle nei
    commenti HTML), la tabella-classifica con le colonne minime necessarie
    (Squad, MP, GF, GA) e la normalizza."""
    import io

    required_columns = {"Squad", "MP", "GF", "GA"}
    for html_fragment in _extract_all_tables_html(page_html):
        try:
            tables = pd.read_html(io.StringIO(html_fragment))
        except ValueError:
            continue
        for table in tables:
            # FBref usa spesso intestazioni multi-livello: le appiattiamo
            # tenendo solo l'ultimo livello (il nome colonna "reale").
            if isinstance(table.columns, pd.MultiIndex):
                table = table.copy()
                table.columns = [str(col[-1]) for col in table.columns]
            columns = set(str(col) for col in table.columns)
            if required_columns.issubset(columns):
                return table
    raise SecondaryLeagueDataError(
        "Impossibile individuare la tabella classifica su FBref (struttura pagina cambiata?)."
    )


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_secondary_league_data(league: str) -> pd.DataFrame:
    """Scarica automaticamente e gratuitamente la classifica REALE della
    stagione corrente per un campionato secondario (Serie B, Segunda
    División) da FBref, con pandas.read_html. Ritorna un DataFrame con almeno
    le colonne Squad, MP, W, D, L, GF, GA, Pts, indicizzato per squadra.
    Cache 30 minuti (ttl=1800): il campionato non cambia classifica più volte
    in mezz'ora, e riduce il carico sul sito sorgente."""
    config = SECONDARY_LEAGUES.get(league)
    if config is None:
        raise SecondaryLeagueDataError(f"{league} non è un campionato secondario configurato.")

    try:
        response = requests.get(
            config["fbref_url"], headers=SECONDARY_LEAGUE_SCRAPE_HEADERS, timeout=25
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise SecondaryLeagueDataError(
            f"Connessione a FBref non riuscita per {league}: {error}"
        ) from error

    table = _read_standings_table(response.text)
    table = table.copy()
    table = table[table["Squad"].notna()]
    # Righe di intestazione ripetute a metà tabella (comuni su FBref) hanno
    # 'Squad' uguale al testo dell'intestazione: le scartiamo confrontando MP.
    for column in ("MP", "W", "D", "L", "GF", "GA", "Pts"):
        if column in table.columns:
            table[column] = pd.to_numeric(table[column], errors="coerce")
    table = table.dropna(subset=["MP", "GF", "GA"])
    table = table[table["MP"] > 0]
    table["Squad"] = table["Squad"].astype(str).str.strip()
    if table.empty:
        raise SecondaryLeagueDataError(f"Classifica FBref vuota o non interpretabile per {league}.")
    return table.reset_index(drop=True)


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_secondary_league_teams(league: str) -> tuple[str, ...]:
    """Elenco squadre (ordine alfabetico) del campionato secondario, letto
    dalla classifica scrapata. Fallback sulla lista statica in LEAGUES se lo
    scraping fallisce, così la UI resta comunque utilizzabile."""
    try:
        standings = fetch_secondary_league_data(league)
        teams = sorted(standings["Squad"].unique().tolist())
        if len(teams) >= 2:
            return tuple(teams)
    except SecondaryLeagueDataError:
        pass
    return tuple(LEAGUES.get(league, []))


def secondary_league_averages(standings: pd.DataFrame) -> tuple[float, float]:
    """Media gol fatti/subiti per squadra a partita nell'INTERO campionato
    scrapato (non la costante fissa LEAGUE_AVERAGE_GOALS_PER_TEAM, che è
    calibrata sulle massime serie): usata per normalizzare Alpha/Beta in modo
    specifico per Serie B/Segunda División, la cui media gol differisce da
    quella delle prime divisioni."""
    total_matches = float(standings["MP"].sum())
    if total_matches <= 0:
        return LEAGUE_AVERAGE_GOALS_PER_TEAM, LEAGUE_AVERAGE_GOALS_PER_TEAM
    avg_gf = float(standings["GF"].sum()) / total_matches
    avg_ga = float(standings["GA"].sum()) / total_matches
    # In una classifica chiusa GF totali == GA totali per costruzione: le
    # teniamo comunque distinte per chiarezza/robustezza a dati parziali.
    return clamp(avg_gf, 0.4, 3.5), clamp(avg_ga, 0.4, 3.5)


def fetch_secondary_team_stats(league: str, team: str) -> LiveTeamStats:
    """Statistiche 'live' di una squadra di Serie B/Segunda División,
    ricavate dalla classifica scrapata da FBref. Non essendoci uno split
    casa/trasferta nella tabella-classifica aggregata, i gol fatti/subiti
    vengono ripartiti in proporzione uguale fra le due componenti (home/away)
    — un'approssimazione dichiarata, che NON altera il totale usato per
    calcolare Alpha/Beta. Le partite REALI giocate (MP) alimentano comunque
    la Modalità Inizio Stagione (Dynamic Decay) come per Football-Data.org."""
    standings = fetch_secondary_league_data(league)
    row = standings[standings["Squad"].str.casefold() == team.casefold()]
    if row.empty:
        # Fuzzy fallback: alcuni nomi possono differire leggermente (accenti,
        # abbreviazioni) fra la lista squadre e la tabella classifica.
        normalized_target = _normalize_team_name(team)
        row = standings[
            standings["Squad"].apply(
                lambda name: normalized_target in _normalize_team_name(str(name))
                or _normalize_team_name(str(name)) in normalized_target
            )
        ]
    if row.empty:
        raise SecondaryLeagueDataError(f"{team} non trovata nella classifica FBref di {league}.")

    record = row.iloc[0]
    matches = float(record["MP"])
    goals_for = float(record["GF"])
    goals_against = float(record["GA"])
    code = SECONDARY_LEAGUES[league]["code"]
    baseline = MICRO_EVENT_BASELINES[code]
    scoring_factor = clamp(0.88 + (goals_for / matches) * 0.08, 0.88, 1.12) if matches else 1.0

    return LiveTeamStats(
        team_id=-1,
        team_name=str(record["Squad"]),
        matches=matches,
        home_matches=matches / 2,
        away_matches=matches / 2,
        goals_for=goals_for,
        goals_against=goals_against,
        home_goals_for=goals_for / 2,
        home_goals_against=goals_against / 2,
        away_goals_for=goals_for / 2,
        away_goals_against=goals_against / 2,
        total_shots=baseline["shots"] * scoring_factor * matches,
        shots_on_target=baseline["shots_on_target"] * scoring_factor * matches,
        corners=baseline["corners"] * matches,
        cards=baseline["cards"] * matches,
        fouls=baseline["fouls"] * matches,
        recent_form=(),  # Non disponibile dalla sola tabella classifica: Form Factor neutro.
        form_factor=1.0,
        current_season_matches=int(matches),
    )


SECONDARY_TIER_RATING_MIN = 1280.0
"""Rating minimo (ultima in classifica) per il profilo dinamico delle
squadre di Serie B/Segunda División — stesso estremo inferiore usato da
TEAM_TIER_PROFILES (Tier 5) per restare su una scala comparabile."""

SECONDARY_TIER_RATING_MAX = 1650.0
"""Rating massimo (capolista) per il profilo dinamico: leggermente sotto il
Tier 1 delle massime serie (1750), perché una capolista di Serie B/Segunda
resta comunque un gradino sotto ai top club europei."""


def secondary_team_dynamic_profile(league: str, team: str, standings: pd.DataFrame) -> dict[str, float]:
    """Profilo Attacco/Difesa/Rating calcolato IN MODO DINAMICO dalla
    classifica reale — nessun Tier fisso condiviso fra squadre diverse:

    * Alpha (Attacco) = (Gol Fatti / Partite Giocate) / (Media Gol del Campionato)
    * Beta  (Difesa)  = (Gol Subiti / Partite Giocate) / (Media Gol Subiti del Campionato)
    * Rating = interpolazione lineare fra SECONDARY_TIER_RATING_MIN e
      SECONDARY_TIER_RATING_MAX in base al percentile di Punti/Partita (ppg)
      della squadra rispetto a max/min della classifica corrente — così la
      capolista e la retrocessa hanno rating ben distinti, la Modalità Inizio
      Stagione ha comunque un punto di ancoraggio anche con pochissime
      partite giocate.

    Usato sia come 'stats profile' (Alpha/Beta) sia come 'prior' per il
    Dynamic Decay ad inizio stagione (al posto di TEAM_TIER_PROFILES)."""
    avg_gf, avg_ga = secondary_league_averages(standings)
    row = standings[standings["Squad"].str.casefold() == team.casefold()]
    if row.empty:
        normalized_target = _normalize_team_name(team)
        row = standings[
            standings["Squad"].apply(
                lambda name: normalized_target in _normalize_team_name(str(name))
                or _normalize_team_name(str(name)) in normalized_target
            )
        ]
    if row.empty:
        raise SecondaryLeagueDataError(f"{team} non trovata nella classifica FBref di {league}.")
    record = row.iloc[0]
    matches = float(record["MP"])

    alpha = clamp((float(record["GF"]) / matches) / avg_gf, 0.3, 3.0) if matches else 1.0
    beta = clamp((float(record["GA"]) / matches) / avg_ga, 0.3, 3.0) if matches else 1.0

    if "Pts" in standings.columns and standings["Pts"].notna().any():
        ppg_series = standings["Pts"].astype(float) / standings["MP"].astype(float).replace(0, np.nan)
    else:
        # Nessuna colonna Pts affidabile: ricostruiamo i punti da W/D (3-1-0).
        wins = standings.get("W", pd.Series(0, index=standings.index)).astype(float)
        draws = standings.get("D", pd.Series(0, index=standings.index)).astype(float)
        ppg_series = (wins * 3 + draws) / standings["MP"].astype(float).replace(0, np.nan)
    ppg_series = ppg_series.dropna()
    team_ppg = float(ppg_series.loc[row.index[0]]) if row.index[0] in ppg_series.index else float(ppg_series.mean())
    ppg_min, ppg_max = float(ppg_series.min()), float(ppg_series.max())
    if ppg_max - ppg_min > 1e-6:
        percentile = clamp((team_ppg - ppg_min) / (ppg_max - ppg_min), 0.0, 1.0)
    else:
        percentile = 0.5
    rating = SECONDARY_TIER_RATING_MIN + (SECONDARY_TIER_RATING_MAX - SECONDARY_TIER_RATING_MIN) * percentile

    return {"rating": rating, "attack": alpha, "defense": beta}


def secondary_competition_season_status(league: str) -> str:
    """Versione di competition_season_status() per i campionati scrapati da
    FBref: indica quante squadre sono state caricate e da quale fonte."""
    try:
        standings = fetch_secondary_league_data(league)
        return f"{len(standings)} squadre · dati live da FBref (scraping automatico)"
    except SecondaryLeagueDataError:
        return "lista di riserva (scraping FBref non disponibile al momento)"


def build_match_model(
    league: str,
    home: str,
    away: str,
    market_factor_home: float = 0.0,
    market_factor_away: float = 0.0,
    injury_factor_home: float = 0.0,
    injury_factor_away: float = 0.0,
    fatigue_home: dict[str, object] | None = None,
    fatigue_away: dict[str, object] | None = None,
) -> MatchModel:
    secondary = is_secondary_league(league)
    if secondary:
        standings = fetch_secondary_league_data(league)
        home_stats = fetch_secondary_team_stats(league, home)
        away_stats = fetch_secondary_team_stats(league, away)
    else:
        home_stats = fetch_team_live_stats(league, home)
        away_stats = fetch_team_live_stats(league, away)

    # --- 0. Slider manuali "Fattore Mercato" e "Impatto Infortuni/Titolari
    # Assenti", calcolati subito perché si applicano direttamente su
    # Attacco_Finale/Difesa_Finale (step 3) prima del calcolo di xG/tiri. ----
    manual_factor_home = clamp(market_factor_home, *MARKET_FACTOR_BOUNDS) + clamp(
        injury_factor_home, *INJURY_FACTOR_BOUNDS
    )
    manual_factor_away = clamp(market_factor_away, *MARKET_FACTOR_BOUNDS) + clamp(
        injury_factor_away, *INJURY_FACTOR_BOUNDS
    )

    # --- 0b. Indice di Affaticamento & Turnover (Fase 2): si SOMMA agli
    # slider manuali di Mercato/Infortuni, senza sovrascriverli — vedi step 3
    # dove attacco/difesa/malus vengono combinati additivamente.
    fatigue_home = fatigue_home or {"attack_malus": 0.0, "defense_malus": 0.0}
    fatigue_away = fatigue_away or {"attack_malus": 0.0, "defense_malus": 0.0}
    fatigue_attack_malus_home = float(fatigue_home.get("attack_malus", 0.0))
    fatigue_defense_malus_home = float(fatigue_home.get("defense_malus", 0.0))
    fatigue_attack_malus_away = float(fatigue_away.get("attack_malus", 0.0))
    fatigue_defense_malus_away = float(fatigue_away.get("defense_malus", 0.0))

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

    # --- 2. DIZIONARIO FASCE DI FORZA + TRANSIZIONE DINAMICA (Dynamic Decay) --
    # Ogni squadra viene risolta in una Fascia di Forza tramite fuzzy matching
    # (lookup_team_tier), con fallback esplicito a Tier 3 — mai un default
    # piatto. Le statistiche osservate vengono convertite in moltiplicatori
    # Attacco/Difesa relativi alla media di lega, poi mescolate con quelle di
    # Fascia secondo N = partite reali giocate nella stagione corrente:
    #   N < 5  → Peso_Fascia=(5-N)/5, Peso_Stats=N/5
    #   N >= 5 → 100% statistiche reali (Peso_Fascia=0)
    early_season = is_early_season_match(home_stats, away_stats)

    if secondary:
        # --- RATING DINAMICO (NO TIER FISSI) ---------------------------------
        # Per Serie B/Segunda División il 'prior' di inizio stagione non è un
        # Tier fisso condiviso da più squadre, ma un profilo Attacco/Difesa/
        # Rating calcolato dalla classifica reale scrapata (Alpha/Beta), vedi
        # secondary_team_dynamic_profile. La media gol di riferimento per
        # normalizzare le statistiche osservate è quella REALE del campionato
        # scrapato, non la costante fissa delle massime serie.
        home_tier = secondary_team_dynamic_profile(league, home, standings)
        away_tier = secondary_team_dynamic_profile(league, away, standings)
        league_avg_goals, _league_avg_goals_against = secondary_league_averages(standings)
    else:
        home_tier = team_tier_profile(home)
        away_tier = team_tier_profile(away)
        league_avg_goals = LEAGUE_AVERAGE_GOALS_PER_TEAM

    home_tier_weight, home_stats_weight = dynamic_decay_weights(home_stats.current_season_matches)
    away_tier_weight, away_stats_weight = dynamic_decay_weights(away_stats.current_season_matches)

    def _stats_multiplier(value_per_match: float) -> float:
        return clamp(value_per_match / league_avg_goals, 0.3, 3.0)

    def _stats_rating(attack_mult: float, defense_mult: float) -> float:
        return BASE_RATING + (RATING_SCALE / 2) * (attack_mult - 1.0) - (RATING_SCALE / 2) * (defense_mult - 1.0)

    home_stats_attack = _stats_multiplier(home_goal_for)
    home_stats_defense = _stats_multiplier(home_goal_against)
    away_stats_attack = _stats_multiplier(away_goal_for)
    away_stats_defense = _stats_multiplier(away_goal_against)
    home_stats_rating = _stats_rating(home_stats_attack, home_stats_defense)
    away_stats_rating = _stats_rating(away_stats_attack, away_stats_defense)

    rating_finale_home = home_tier["rating"] * home_tier_weight + home_stats_rating * home_stats_weight
    rating_finale_away = away_tier["rating"] * away_tier_weight + away_stats_rating * away_stats_weight
    attacco_finale_home = home_tier["attack"] * home_tier_weight + home_stats_attack * home_stats_weight
    difesa_finale_home = home_tier["defense"] * home_tier_weight + home_stats_defense * home_stats_weight
    attacco_finale_away = away_tier["attack"] * away_tier_weight + away_stats_attack * away_stats_weight
    difesa_finale_away = away_tier["defense"] * away_tier_weight + away_stats_defense * away_stats_weight

    # --- 3. Slider manuali (Mercato/Infortuni) + Indice di Affaticamento &
    # Turnover (Fase 2), SOMMATI fra loro (nessuno sovrascrive l'altro) e
    # applicati DIRETTAMENTE su Attacco_Finale/Difesa_Finale (e sul Rating_
    # Finale per coerenza con tiri/corner/cartellini), PRIMA del calcolo
    # della matrice Dixon-Coles/Monte Carlo. -----------------------------------
    attacco_finale_home = clamp(
        attacco_finale_home * (1 + manual_factor_home + fatigue_attack_malus_home), 0.25, 2.6
    )
    difesa_finale_home = clamp(
        difesa_finale_home * (1 - manual_factor_home + fatigue_defense_malus_home), 0.25, 2.6
    )
    attacco_finale_away = clamp(
        attacco_finale_away * (1 + manual_factor_away + fatigue_attack_malus_away), 0.25, 2.6
    )
    difesa_finale_away = clamp(
        difesa_finale_away * (1 - manual_factor_away + fatigue_defense_malus_away), 0.25, 2.6
    )
    rating_finale_home += (manual_factor_home + fatigue_attack_malus_home) * RATING_SCALE
    rating_finale_away += (manual_factor_away + fatigue_attack_malus_away) * RATING_SCALE

    # --- 4. Gol attesi (xG) dal modello Attacco × Difesa avversaria ------------
    # (parametrizzazione classica alla Dixon-Coles: λ_casa = lega × Attacco_
    # casa × Difesa_ospite × fattore campo; λ_trasferta speculare, senza
    # fattore campo).
    home_lambda = clamp(
        league_avg_goals * attacco_finale_home * difesa_finale_away * HOME_ADVANTAGE_GOAL_MULTIPLIER,
        0.05,
        5.5,
    )
    away_lambda = clamp(
        league_avg_goals * attacco_finale_away * difesa_finale_home,
        0.05,
        5.0,
    )

    rating_diff = (rating_finale_home + HOME_ADVANTAGE_RATING) - rating_finale_away

    # --- 5. Tiri totali/in porta: stessa Transizione Dinamica (baseline di
    # Fascia derivata dall'Attacco di Tier, mescolata alle statistiche reali),
    # poi slider manuali e infine il gap di rating (smorzato). -----------------
    competition_code = SECONDARY_LEAGUES[league]["code"] if secondary else FOOTBALL_DATA_COMPETITIONS[league]
    micro_baseline = MICRO_EVENT_BASELINES[competition_code]
    shots_per_goal = micro_baseline["shots"] / league_avg_goals
    sot_per_goal = micro_baseline["shots_on_target"] / league_avg_goals

    home_shots_tier_baseline = home_tier["attack"] * shots_per_goal
    away_shots_tier_baseline = away_tier["attack"] * shots_per_goal
    home_sot_tier_baseline = home_tier["attack"] * sot_per_goal
    away_sot_tier_baseline = away_tier["attack"] * sot_per_goal

    home_shots_blended = home_shots_tier_baseline * home_tier_weight + home_shots_raw * home_stats_weight
    away_shots_blended = away_shots_tier_baseline * away_tier_weight + away_shots_raw * away_stats_weight
    home_sot_blended = home_sot_tier_baseline * home_tier_weight + home_sot_raw * home_stats_weight
    away_sot_blended = away_sot_tier_baseline * away_tier_weight + away_sot_raw * away_stats_weight

    home_shots_blended *= 1 + manual_factor_home + fatigue_attack_malus_home
    home_sot_blended *= 1 + manual_factor_home + fatigue_attack_malus_home
    away_shots_blended *= 1 + manual_factor_away + fatigue_attack_malus_away
    away_sot_blended *= 1 + manual_factor_away + fatigue_attack_malus_away

    shot_boost, shot_suppress = rating_scaling_factors(rating_diff, damping=SHOT_RATING_DAMPING)
    home_shots = max(home_shots_blended * shot_boost, 1.0)
    away_shots = max(away_shots_blended * shot_suppress, 1.0)
    home_sot = max(home_sot_blended * shot_boost, 0.3)
    away_sot = max(away_sot_blended * shot_suppress, 0.3)
    shots_total = home_shots + away_shots

    # --- 6. Corner: legati anche al possesso, sensibilità ulteriormente smorzata
    corner_boost, corner_suppress = rating_scaling_factors(rating_diff, damping=CORNER_RATING_DAMPING)
    corners_total = home_corners_raw * corner_boost + away_corners_raw * corner_suppress

    # --- 7. Cartellini: la squadra in difficoltà commette più falli tattici ----
    normalized_gap = clamp(abs(rating_diff) / RATING_SCALE, 0.0, 1.0)
    if rating_diff >= 0:
        home_cards = home_cards_raw * (1 - 0.5 * CARD_UNDERDOG_BONUS * normalized_gap)
        away_cards = away_cards_raw * (1 + CARD_UNDERDOG_BONUS * normalized_gap)
    else:
        home_cards = home_cards_raw * (1 + CARD_UNDERDOG_BONUS * normalized_gap)
        away_cards = away_cards_raw * (1 - 0.5 * CARD_UNDERDOG_BONUS * normalized_gap)
    home_cards = clamp(home_cards, 0.1, 6.0)
    away_cards = clamp(away_cards, 0.1, 6.0)

    # --- 8. Probabilità 1X2: Poisson bivariata + correzione Dixon-Coles --------
    # Stessa distribuzione usata dalle tabelle micro-eventi e dalla simulazione
    # Monte Carlo, cosicché ogni vista dell'app racconti lo stesso match.
    home_win_prob, draw_prob, away_win_prob = match_outcome_probabilities(home_lambda, away_lambda)

    if secondary:
        home_label = f"Rating dinamico FBref (Alpha {home_tier['attack']:.2f}/Beta {home_tier['defense']:.2f})"
        away_label = f"Rating dinamico FBref (Alpha {away_tier['attack']:.2f}/Beta {away_tier['defense']:.2f})"
    else:
        home_label = TEAM_TIER_LABELS[lookup_team_tier(home)]
        away_label = TEAM_TIER_LABELS[lookup_team_tier(away)]
    engine_note = (
        f"{home_label} ({home}, rating {rating_finale_home:.0f}) "
        f"vs {away_label} ({away}, rating {rating_finale_away:.0f}) · "
        f"Peso Fascia/Stats: {home}={home_tier_weight:.0%}/{home_stats_weight:.0%}, "
        f"{away}={away_tier_weight:.0%}/{away_stats_weight:.0%} · "
        f"correzione Dixon-Coles ρ={DIXON_COLES_RHO:+.2f}"
    )
    if secondary:
        engine_note += " · fonte dati: FBref (scraping automatico, classifica stagione corrente)"
    if home_stats.recent_form:
        engine_note += f" · forma {home}: {''.join(home_stats.recent_form)}"
    if away_stats.recent_form:
        engine_note += f" · forma {away}: {''.join(away_stats.recent_form)}"
    if manual_factor_home:
        engine_note += f" · slider {home}: {manual_factor_home:+.0%}"
    if manual_factor_away:
        engine_note += f" · slider {away}: {manual_factor_away:+.0%}"
    if fatigue_attack_malus_home or fatigue_defense_malus_home:
        engine_note += (
            f" · affaticamento {home}: attacco {fatigue_attack_malus_home:+.0%}/"
            f"difesa {fatigue_defense_malus_home:+.0%}"
        )
    if fatigue_attack_malus_away or fatigue_defense_malus_away:
        engine_note += (
            f" · affaticamento {away}: attacco {fatigue_attack_malus_away:+.0%}/"
            f"difesa {fatigue_defense_malus_away:+.0%}"
        )
    if early_season:
        engine_note += (
            f" · ⚠️ Antepost Tiering attivo: {home} {home_stats.current_season_matches} "
            f"partite reali, {away} {away_stats.current_season_matches} partite reali "
            f"(soglia piena confidenza: {EARLY_SEASON_MATCHDAY_THRESHOLD})"
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
        home_rating=rating_finale_home,
        away_rating=rating_finale_away,
        home_win_prob=home_win_prob,
        draw_prob=draw_prob,
        away_win_prob=away_win_prob,
        engine_note=engine_note,
        early_season_warning=early_season,
        home_current_season_matches=home_stats.current_season_matches,
        away_current_season_matches=away_stats.current_season_matches,
        manual_factor_home=manual_factor_home,
        manual_factor_away=manual_factor_away,
        fatigue_attack_malus_home=fatigue_attack_malus_home,
        fatigue_defense_malus_home=fatigue_defense_malus_home,
        fatigue_attack_malus_away=fatigue_attack_malus_away,
        fatigue_defense_malus_away=fatigue_defense_malus_away,
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


def goal_market_probabilities(model: MatchModel, max_goals: int = 12) -> dict[str, object]:
    """Probabilità Under/Over gol (totali di partita e per singola squadra) e
    Goal/No Goal, calcolate dalla stessa matrice di Poisson bivariata con
    correzione Dixon-Coles già usata per il pronostico 1X2 e i risultati
    esatti (match_outcome_probabilities / exact_score_probabilities), per
    piena coerenza con il resto del motore di simulazione."""
    home_lambda = model.home_lambda
    away_lambda = model.away_lambda
    home_pmf = [poisson.pmf(i, home_lambda) for i in range(max_goals + 1)]
    away_pmf = [poisson.pmf(j, away_lambda) for j in range(max_goals + 1)]

    joint = [[0.0] * (max_goals + 1) for _ in range(max_goals + 1)]
    total = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            probability = home_pmf[i] * away_pmf[j] * dixon_coles_tau(i, j, home_lambda, away_lambda)
            joint[i][j] = probability
            total += probability
    if total <= 0:
        total = 1.0

    # --- 1. Under/Over gol totali di partita (Casa + Trasferta) ----------------
    total_over: dict[float, float] = {}
    for line in (1.5, 2.5, 3.5, 4.5):
        threshold = math.floor(line)
        over_p = sum(
            joint[i][j]
            for i in range(max_goals + 1)
            for j in range(max_goals + 1)
            if i + j > threshold
        )
        total_over[line] = clamp(over_p / total, 0.0, 1.0)

    # --- 2. Under/Over gol individuali (marginali della matrice congiunta) -----
    home_marginal = [sum(row) / total for row in joint]
    away_marginal = [
        sum(joint[i][j] for i in range(max_goals + 1)) / total for j in range(max_goals + 1)
    ]
    home_over: dict[float, float] = {}
    away_over: dict[float, float] = {}
    for line in (0.5, 1.5, 2.5):
        threshold = math.floor(line)
        home_over[line] = clamp(sum(p for i, p in enumerate(home_marginal) if i > threshold), 0.0, 1.0)
        away_over[line] = clamp(sum(p for j, p in enumerate(away_marginal) if j > threshold), 0.0, 1.0)

    # --- 3. Goal (entrambe segnano) / No Goal -----------------------------------
    goal_goal = clamp(
        sum(joint[i][j] for i in range(1, max_goals + 1) for j in range(1, max_goals + 1)) / total,
        0.0,
        1.0,
    )
    no_goal = clamp(1.0 - goal_goal, 0.0, 1.0)

    return {
        "total_over": total_over,
        "home_over": home_over,
        "away_over": away_over,
        "goal_goal": goal_goal,
        "no_goal": no_goal,
    }


# ==============================================================================
# FASE 1: VALUE BETTING & UX — Kelly Criterion + Heatmap dei Mercati
# ==============================================================================
# Estensione puramente additiva: non modifica Power Rating, TEAM_TIERS,
# Dixon-Coles, Dynamic Decay né alcun calcolo di xG esistente. Riusa solo le
# probabilità già calcolate da match_outcome_probabilities/
# goal_market_probabilities per garantire coerenza con le altre schede.
KELLY_FRACTION = 0.25
"""Quarter Kelly: frazione conservativa applicata al Kelly Criterion pieno
per contenere la varianza sul bankroll (Fractional Kelly Stake)."""

HEATMAP_HIGH_THRESHOLD = 0.70
"""Soglia Heatmap 'Verde Chiaro/Smeraldo': probabilità >= 70%."""

HEATMAP_MID_THRESHOLD = 0.50
"""Soglia Heatmap 'Giallo/Arancione': probabilità fra 50% e 69%. Sotto il
50% la cella è 'Rosso/Grigio'."""


def kelly_stake_percent(probability: float, decimal_odds: float | None, fraction: float = KELLY_FRACTION) -> float | None:
    """Fractional Kelly Stake (%):
    ((Probabilità_Algoritmo * Quota_Bookmaker) - 1) / (Quota_Bookmaker - 1) * 100
    moltiplicato per `fraction` (default Quarter Kelly, 25%). Restituisce
    None se non è stata inserita una quota valida (>1.0) — nessuno stake
    viene calcolato/mostrato in quel caso, solo la probabilità dell'algoritmo."""
    if decimal_odds is None or decimal_odds <= 1.0:
        return None
    full_kelly = ((probability * decimal_odds) - 1) / (decimal_odds - 1)
    return full_kelly * fraction * 100


def value_bet_badge(stake_percent: float | None) -> tuple[str, str, str]:
    """Badge Value Bet: (etichetta, colore_sfondo, colore_testo).
    - Stake > 0% → 'VALUE BET DETECTED' (verde).
    - Stake <= 0% → 'NO VALUE' (grigio neutro).
    - Nessuna quota inserita → badge non mostrato (None gestito dal chiamante)."""
    if stake_percent is None:
        return "QUOTA NON INSERITA", "#1e293b", "#94a3b8"
    if stake_percent > 0:
        return "VALUE BET DETECTED", "#16a34a", "#052e16"
    return "NO VALUE", "#475569", "#e2e8f0"


def expected_value_percent(probability: float, decimal_odds: float | None) -> float | None:
    """Expected Value %: EV% = (Probabilità_Algoritmo × Quota_Bookmaker - 1)
    × 100. Restituisce None se non è stata inserita una quota valida (>1.0)."""
    if decimal_odds is None or decimal_odds <= 1.0:
        return None
    return ((probability * decimal_odds) - 1) * 100


KELLY_MARKET_GROUPS: dict[str, str] = {
    "kelly_home": "Esito 1X2",
    "kelly_draw": "Esito 1X2",
    "kelly_away": "Esito 1X2",
    "kelly_over25": "Over/Under 2.5",
    "kelly_under25": "Over/Under 2.5",
    "kelly_gg": "Goal/No Goal",
    "kelly_ng": "Goal/No Goal",
}
"""Raggruppamento dei mercati Kelly per famiglia correlata: usato per
escludere Value Bet duplicate/correlate (es. Over 2.5 e Under 2.5, o due
esiti dello stesso 1X2) dall'ordinamento e dal box Best Value Bet — solo la
scommessa con lo Stake Kelly più alto del gruppo viene mantenuta."""


def rank_value_bets(
    kelly_rows: list[tuple[str, str, float, float | None, float | None]],
) -> list[dict[str, object]]:
    """Rileva, calcola l'Expected Value e ORDINA le Value Bet (Stake Kelly
    > 0) dalla più alta alla più bassa percentuale di Stake consigliata,
    escludendo scommesse duplicate/correlate: per ciascun gruppo di mercati
    collegati (KELLY_MARKET_GROUPS) mantiene solo quella con lo Stake più
    alto. kelly_rows: (key, label, probabilità, quota, stake) — vedi
    compute_kelly_rows_detailed."""
    best_per_group: dict[str, dict[str, object]] = {}
    for key, label, probability, odds, stake in kelly_rows:
        if stake is None or stake <= 0:
            continue
        group = KELLY_MARKET_GROUPS.get(key, key)
        candidate = {
            "key": key,
            "label": label,
            "probability": probability,
            "odds": odds,
            "stake": stake,
            "ev": expected_value_percent(probability, odds),
            "group": group,
        }
        current_best = best_per_group.get(group)
        if current_best is None or stake > current_best["stake"]:
            best_per_group[group] = candidate
    return sorted(best_per_group.values(), key=lambda row: row["stake"], reverse=True)


# ==============================================================================
# INTEGRAZIONE THE ODDS API — Recupero automatico quote reali (con fallback
# manuale). Estensione puramente additiva: legge solo probabilità già
# calcolate dal motore esistente e non modifica Dixon-Coles, TEAM_TIERS,
# Power Rating o alcun altro calcolo statistico.
# ==============================================================================
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"

ODDS_API_SPORT_KEYS: dict[str, str] = {
    "Italia · Serie A": "soccer_italy_serie_a",
    "Inghilterra · Premier League": "soccer_epl",
    "Inghilterra · EFL Championship": "soccer_efl_champ",
    "Spagna · La Liga": "soccer_spain_la_liga",
    "Germania · Bundesliga": "soccer_germany_bundesliga",
    "Francia · Ligue 1": "soccer_france_ligue_one",
    "Paesi Bassi · Eredivisie": "soccer_netherlands_eredivisie",
    "Portogallo · Primeira Liga": "soccer_portugal_primeira_liga",
    "Europa · UEFA Champions League": "soccer_uefa_champs_league",
}
"""Mappatura campionato interno -> sport key di The Odds API. Se la lega
selezionata non è mappata, get_live_odds ripiega automaticamente su None
(inserimento manuale)."""

ODDS_API_MARKET_MAP: dict[str, tuple[str, str]] = {
    "kelly_home": ("h2h", "home"),
    "kelly_draw": ("h2h", "draw"),
    "kelly_away": ("h2h", "away"),
    "kelly_over25": ("totals", "Over"),
    "kelly_under25": ("totals", "Under"),
    "kelly_gg": ("btts", "Yes"),
    "kelly_ng": ("btts", "No"),
}
"""Mappatura chiave mercato Kelly interna -> (mercato The Odds API, esito)."""


@st.cache_data(ttl=300, show_spinner=False)
def get_live_odds(
    home_team: str, away_team: str, market: str, league: str, api_key: str
) -> dict[str, float] | None:
    """Recupera le quote reali da The Odds API per il mercato richiesto
    (`market`: una delle chiavi Kelly interne, es. 'kelly_home') sulla
    partita home_team-away_team. Ritorna {bookmaker: quota} oppure None se
    l'API Key non è inserita, la lega non è mappata, la chiamata fallisce o
    l'evento/mercato non è disponibile — in tutti questi casi il chiamante
    deve ripiegare sull'inserimento manuale (st.number_input), senza mai
    bloccare l'app."""
    if not api_key:
        return None
    odds_market = ODDS_API_MARKET_MAP.get(market)
    sport_key = ODDS_API_SPORT_KEYS.get(league)
    if odds_market is None or sport_key is None:
        return None
    api_market, outcome_selector = odds_market

    try:
        response = requests.get(
            f"{ODDS_API_BASE_URL}/sports/{sport_key}/odds",
            params={
                "apiKey": api_key,
                "regions": "eu",
                "markets": api_market,
                "oddsFormat": "decimal",
            },
            timeout=8,
        )
        response.raise_for_status()
        events = response.json()
    except (requests.RequestException, ValueError):
        return None
    if not isinstance(events, list):
        return None

    target_home = _normalize_team_name(home_team)
    target_away = _normalize_team_name(away_team)
    event = next(
        (
            item
            for item in events
            if isinstance(item, dict)
            and target_home in _normalize_team_name(str(item.get("home_team", "")))
            and target_away in _normalize_team_name(str(item.get("away_team", "")))
        ),
        None,
    )
    if event is None:
        return None

    bookmaker_odds: dict[str, float] = {}
    for bookmaker in event.get("bookmakers", []) or []:
        if not isinstance(bookmaker, dict):
            continue
        title = str(bookmaker.get("title") or "Bookmaker")
        for bm_market in bookmaker.get("markets", []) or []:
            if not isinstance(bm_market, dict) or bm_market.get("key") != api_market:
                continue
            for outcome in bm_market.get("outcomes", []) or []:
                if not isinstance(outcome, dict):
                    continue
                outcome_name = str(outcome.get("name", "")).strip()
                price = outcome.get("price")
                if price is None:
                    continue
                matched = False
                if api_market == "h2h":
                    normalized_outcome = _normalize_team_name(outcome_name)
                    if outcome_selector == "home" and (
                        target_home in normalized_outcome or normalized_outcome in target_home
                    ):
                        matched = True
                    elif outcome_selector == "away" and (
                        target_away in normalized_outcome or normalized_outcome in target_away
                    ):
                        matched = True
                    elif outcome_selector == "draw" and outcome_name.lower() == "draw":
                        matched = True
                elif api_market == "totals":
                    if outcome.get("point") == 2.5 and outcome_name.lower() == outcome_selector.lower():
                        matched = True
                elif api_market == "btts":
                    if outcome_name.lower() == outcome_selector.lower():
                        matched = True
                if matched:
                    try:
                        bookmaker_odds[title] = float(price)
                    except (TypeError, ValueError):
                        pass
    return bookmaker_odds or None


def render_bookmaker_comparison_table(our_fair_odds: float, bookmaker_odds: dict[str, float]) -> None:
    """Tabella 'Confronto Bookmaker': la quota equa del nostro algoritmo
    (fair odds, inverso della probabilità stimata) affiancata alle quote
    reali recuperate da The Odds API, con il bookmaker che offre la quota
    più alta evidenziato in verde (il maggior valore per chi scommette)."""
    if not bookmaker_odds:
        return
    best_bookmaker = max(bookmaker_odds, key=bookmaker_odds.get)
    rows_html = [f"<tr><td>🤖 Il nostro algoritmo (fair odds)</td><td>{our_fair_odds:.2f}</td></tr>"]
    for bookmaker, price in sorted(bookmaker_odds.items(), key=lambda item: item[1], reverse=True):
        row_style = (
            ' style="background:#16a34a;color:#052e16;font-weight:700"'
            if bookmaker == best_bookmaker
            else ""
        )
        marker = " 🏆" if bookmaker == best_bookmaker else ""
        rows_html.append(f"<tr{row_style}><td>{escape(bookmaker)}{marker}</td><td>{price:.2f}</td></tr>")
    st.markdown(
        '<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse">'
        "<thead><tr><th>Fonte</th><th>Quota</th></tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def double_chance_probabilities(model: MatchModel) -> dict[str, float]:
    """Probabilità Doppia Chance (1X, X2, 12), derivate dalle stesse
    probabilità 1X2 (Poisson bivariata + Dixon-Coles) del motore — nessun
    nuovo calcolo statistico, solo somme delle probabilità già esistenti."""
    return {
        "1X": clamp(model.home_win_prob + model.draw_prob, 0.0, 1.0),
        "X2": clamp(model.draw_prob + model.away_win_prob, 0.0, 1.0),
        "12": clamp(model.home_win_prob + model.away_win_prob, 0.0, 1.0),
    }


def heatmap_market_probabilities(model: MatchModel, home: str, away: str) -> list[dict[str, object]]:
    """Elenco dei mercati (1X2, Doppia Chance, Over/Under 1.5-2.5-3.5,
    Goal/No Goal) con la relativa probabilità, per la Heatmap ad alta
    probabilità. Riusa goal_market_probabilities/double_chance_probabilities,
    già coerenti con Dixon-Coles."""
    markets = goal_market_probabilities(model)
    dc = double_chance_probabilities(model)
    return [
        {"Mercato": f"1 · {home}", "Probabilità": model.home_win_prob},
        {"Mercato": "X · Pareggio", "Probabilità": model.draw_prob},
        {"Mercato": f"2 · {away}", "Probabilità": model.away_win_prob},
        {"Mercato": "1X · Doppia Chance", "Probabilità": dc["1X"]},
        {"Mercato": "X2 · Doppia Chance", "Probabilità": dc["X2"]},
        {"Mercato": "12 · Doppia Chance", "Probabilità": dc["12"]},
        {"Mercato": "Over 1.5", "Probabilità": markets["total_over"][1.5]},
        {"Mercato": "Under 1.5", "Probabilità": 1 - markets["total_over"][1.5]},
        {"Mercato": "Over 2.5", "Probabilità": markets["total_over"][2.5]},
        {"Mercato": "Under 2.5", "Probabilità": 1 - markets["total_over"][2.5]},
        {"Mercato": "Over 3.5", "Probabilità": markets["total_over"][3.5]},
        {"Mercato": "Under 3.5", "Probabilità": 1 - markets["total_over"][3.5]},
        {"Mercato": "Goal (GG)", "Probabilità": markets["goal_goal"]},
        {"Mercato": "No Goal (NG)", "Probabilità": markets["no_goal"]},
        {"Mercato": f"Over 1.5 {home}", "Probabilità": markets["home_over"][1.5]},
        {"Mercato": f"Over 1.5 {away}", "Probabilità": markets["away_over"][1.5]},
    ]


def top_heatmap_markets(model: MatchModel, home: str, away: str, top_n: int = 5) -> list[dict[str, object]]:
    """Top N mercati per probabilità decrescente, per la griglia visiva
    compatta in cima alla scheda Value Betting & Heatmap."""
    rows = heatmap_market_probabilities(model, home, away)
    return sorted(rows, key=lambda row: row["Probabilità"], reverse=True)[:top_n]


def heatmap_color(probability: float) -> tuple[str, str]:
    """(colore_sfondo, colore_testo) per una cella della Heatmap, in base
    alle soglie HEATMAP_HIGH_THRESHOLD/HEATMAP_MID_THRESHOLD."""
    if probability >= HEATMAP_HIGH_THRESHOLD:
        return "#10b981", "#052e16"  # Verde chiaro / smeraldo
    if probability >= HEATMAP_MID_THRESHOLD:
        return "#f59e0b", "#3a2400"  # Giallo / arancione
    return "#7f1d1d", "#fee2e2"  # Rosso / grigio scuro


# ==============================================================================
# FASE 2: MODELLO DI AFFATICAMENTO, IMPEGNI INFRASETTIMANALI E TURNOVER
# ==============================================================================
# Estensione puramente additiva: non sovrascrive gli slider di Mercato/
# Infortuni già esistenti, ma si SOMMA a loro come ulteriore modificatore
# dinamico su Attacco_Finale/Difesa_Finale, applicato PRIMA della matrice di
# Dixon-Coles (vedi build_match_model, step 3).
FATIGUE_ATTACK_MALUS_SHORT_REST = -0.08
"""< 72 ore (≤3 giorni) dall'ultimo impegno ufficiale: malus attacco -8%."""
FATIGUE_DEFENSE_MALUS_SHORT_REST = 0.08
"""< 72 ore: malus difesa (vulnerabilità difensiva) +8% (concede di più)."""

FATIGUE_ATTACK_MALUS_MID_REST = -0.04
"""Tra 72 e 96 ore (4 giorni) dall'ultimo impegno: malus attacco -4%."""
FATIGUE_DEFENSE_MALUS_MID_REST = 0.04
"""Tra 72 e 96 ore: malus difesa +4%."""

FATIGUE_TRAVEL_ATTACK_MALUS = -0.03
"""Trasferta europea/viaggio lungo nei 4 giorni precedenti: malus
aggiuntivo attacco -3% (si somma al malus da giorni di riposo)."""
FATIGUE_TRAVEL_DEFENSE_MALUS = 0.03
"""Trasferta europea/viaggio lungo: malus aggiuntivo difesa +3%."""

TURNOVER_LEVELS: dict[str, float] = {
    "Nessun turnover": 0.0,
    "Turnover parziale (-3%)": -0.03,
    "Turnover massiccio (-7%)": -0.07,
}
"""Malus attacco per il Livello di Turnover Previsto in formazione."""

TURNOVER_DEFENSE_FACTOR = 0.5
"""Quota del malus di turnover che si riflette anche sulla vulnerabilità
difensiva: una formazione rimaneggiata concede di più, ma in misura minore
rispetto a quanto perde in fase offensiva."""

FATIGUE_ALERT_THRESHOLD = 0.05
"""Soglia (5%) di malus complessivo sull'attacco oltre la quale mostrare il
badge di allerta affaticamento nell'interfaccia."""


def fatigue_rest_component(rest_days: int) -> tuple[float, float]:
    """Componente 'giorni di riposo' del Malus Fisiologico: ritorna
    (malus_attacco, malus_difesa) in base ai giorni trascorsi dall'ultimo
    match ufficiale.
    - ≤3 giorni (< 72 ore, es. giovedì di Europa League + domenica): malus
      pieno.
    - 4 giorni (fra 72 e 96 ore): malus ridotto.
    - ≥5 giorni (> 96 ore): nessun malus."""
    if rest_days <= 3:
        return FATIGUE_ATTACK_MALUS_SHORT_REST, FATIGUE_DEFENSE_MALUS_SHORT_REST
    if rest_days == 4:
        return FATIGUE_ATTACK_MALUS_MID_REST, FATIGUE_DEFENSE_MALUS_MID_REST
    return 0.0, 0.0


def fatigue_turnover_index(rest_days: int, european_away_trip: bool, turnover_level: str) -> dict[str, object]:
    """Indice di Affaticamento & Turnover completo per una squadra: somma la
    componente 'giorni di riposo' (fatigue_rest_component), l'eventuale
    trasferta europea/viaggio lungo nei 4 giorni precedenti, e il Livello di
    Turnover Previsto. Ritorna i malus totali su attacco/difesa più il
    dettaglio delle singole componenti, usato per il badge di allerta."""
    rest_attack, rest_defense = fatigue_rest_component(rest_days)

    has_travel_malus = european_away_trip and rest_days <= 4
    travel_attack = FATIGUE_TRAVEL_ATTACK_MALUS if has_travel_malus else 0.0
    travel_defense = FATIGUE_TRAVEL_DEFENSE_MALUS if has_travel_malus else 0.0

    turnover_attack = TURNOVER_LEVELS.get(turnover_level, 0.0)
    turnover_defense = turnover_attack * TURNOVER_DEFENSE_FACTOR

    return {
        "attack_malus": rest_attack + travel_attack + turnover_attack,
        "defense_malus": rest_defense + travel_defense + turnover_defense,
        "rest_days": rest_days,
        "european_away_trip": european_away_trip,
        "turnover_level": turnover_level,
        "has_travel_malus": has_travel_malus,
    }


def fatigue_alert_message(team: str, fatigue: dict[str, object]) -> str | None:
    """Messaggio di allerta ('⚠️ Allerta Affaticamento: <squadra> ...') se il
    malus complessivo sull'attacco supera FATIGUE_ALERT_THRESHOLD (5% in
    valore assoluto), altrimenti None (nessun badge da mostrare)."""
    if abs(fatigue["attack_malus"]) < FATIGUE_ALERT_THRESHOLD:
        return None
    details = []
    if fatigue["rest_days"] <= 4:
        details.append(f"ha giocato {fatigue['rest_days']} giorni fa")
    if fatigue["has_travel_malus"]:
        details.append("in trasferta europea")
    if fatigue["turnover_level"] != "Nessun turnover":
        details.append(f"turnover previsto: {fatigue['turnover_level'].split(' (')[0].lower()}")
    detail_text = " · ".join(details) if details else "condizione fisica non ottimale"
    return f"⚠️ Allerta Affaticamento: {team} {detail_text} (malus attacco {fatigue['attack_malus']:+.0%})"


# ==============================================================================
# FASE 3a: TRACCIAMENTO FINANZIARIO BANKROLL (ROI / YIELD)
# ==============================================================================
# Estensione puramente additiva e indipendente dal motore di simulazione: non
# legge né modifica Power Rating, TEAM_TIERS, Dixon-Coles, slider manuali o
# Affaticamento/Turnover. Persistenza su file locali (CSV/JSON con pandas),
# così lo storico non si azzera al ricaricamento della pagina — in hosting
# con filesystem effimero (es. redeploy) i file vengono ricreati vuoti al
# riavvio del processo, ma sopravvivono a un normale refresh del browser.
BANKROLL_LOG_PATH = "bankroll_log.csv"
BANKROLL_CONFIG_PATH = "bankroll_config.json"
BANKROLL_LOG_COLUMNS = [
    "timestamp", "league", "match", "market", "odds", "stake", "stake_type", "outcome", "profit",
]
BET_OUTCOMES = ("In Corso", "Vinta", "Persa")
DEFAULT_INITIAL_BANKROLL = 1000.0


def load_bankroll_config() -> dict[str, float]:
    """Carica il Bankroll Iniziale da file JSON; fallback al default se il
    file non esiste ancora (prima esecuzione) o è corrotto."""
    try:
        with open(BANKROLL_CONFIG_PATH, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
        return {"initial_bankroll": float(config.get("initial_bankroll", DEFAULT_INITIAL_BANKROLL))}
    except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError):
        return {"initial_bankroll": DEFAULT_INITIAL_BANKROLL}


def save_bankroll_config(initial_bankroll: float) -> None:
    try:
        with open(BANKROLL_CONFIG_PATH, "w", encoding="utf-8") as config_file:
            json.dump({"initial_bankroll": float(initial_bankroll)}, config_file)
    except OSError:
        pass  # Filesystem in sola lettura o non disponibile: si prosegue senza persistenza.


def load_bankroll_log() -> pd.DataFrame:
    """Carica lo storico delle giocate da CSV, creando un DataFrame vuoto
    (con le colonne corrette) se il file non esiste ancora o è vuoto."""
    try:
        df = pd.read_csv(BANKROLL_LOG_PATH)
        for column in BANKROLL_LOG_COLUMNS:
            if column not in df.columns:
                df[column] = pd.Series(dtype="object")
        return df[BANKROLL_LOG_COLUMNS]
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=BANKROLL_LOG_COLUMNS)


def save_bankroll_log(df: pd.DataFrame) -> None:
    try:
        df.to_csv(BANKROLL_LOG_PATH, index=False)
    except OSError:
        pass  # Filesystem in sola lettura o non disponibile: si prosegue senza persistenza.


def compute_bet_profit(odds: float, stake: float, outcome: str) -> float:
    """Profitto/perdita di una singola giocata: stake*(quota-1) se vinta,
    -stake se persa, 0 se ancora 'In Corso' (non ancora conteggiata nel ROI)."""
    if outcome == "Vinta":
        return stake * (odds - 1)
    if outcome == "Persa":
        return -stake
    return 0.0


def append_bet(league: str, match: str, market: str, odds: float, stake: float, stake_type: str, outcome: str) -> pd.DataFrame:
    """Aggiunge una nuova giocata allo storico persistito e lo restituisce
    aggiornato (già salvato su file)."""
    df = load_bankroll_log()
    new_row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "league": league,
        "match": match,
        "market": market,
        "odds": odds,
        "stake": stake,
        "stake_type": stake_type,
        "outcome": outcome,
        "profit": compute_bet_profit(odds, stake, outcome),
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_bankroll_log(df)
    return df


def recompute_and_save_log(df: pd.DataFrame) -> pd.DataFrame:
    """Ricalcola la colonna 'profit' per ogni riga (es. dopo che l'utente ha
    aggiornato manualmente un esito da 'In Corso' a 'Vinta'/'Persa' nella
    tabella) e ripersiste lo storico aggiornato."""
    df = df.copy()
    df["profit"] = [
        compute_bet_profit(float(row["odds"]), float(row["stake"]), str(row["outcome"]))
        for _, row in df.iterrows()
    ]
    save_bankroll_log(df)
    return df


def bankroll_metrics(df: pd.DataFrame, initial_bankroll: float) -> dict[str, float]:
    """Metriche finanziarie in tempo reale: Profitto/Perdita Totale, ROI%,
    Win Rate% (solo su giocate concluse), Bankroll Attuale."""
    if df.empty:
        return {
            "total_staked": 0.0, "total_profit": 0.0, "roi": 0.0,
            "win_rate": 0.0, "current_bankroll": initial_bankroll, "settled_count": 0,
        }
    settled = df[df["outcome"].isin(["Vinta", "Persa"])]
    total_staked = float(settled["stake"].sum()) if not settled.empty else 0.0
    total_profit = float(settled["profit"].sum()) if not settled.empty else 0.0
    roi = (total_profit / total_staked * 100) if total_staked > 0 else 0.0
    win_rate = (float((settled["outcome"] == "Vinta").sum()) / len(settled) * 100) if len(settled) > 0 else 0.0
    return {
        "total_staked": total_staked,
        "total_profit": total_profit,
        "roi": roi,
        "win_rate": win_rate,
        "current_bankroll": initial_bankroll + total_profit,
        "settled_count": len(settled),
    }


def bankroll_timeline(df: pd.DataFrame, initial_bankroll: float) -> pd.DataFrame:
    """Serie storica del Bankroll (per il grafico st.line_chart): valore
    dopo ciascuna giocata conclusa, in ordine cronologico."""
    settled = df[df["outcome"].isin(["Vinta", "Persa"])].copy()
    if settled.empty:
        return pd.DataFrame({"Giocata": [0], "Bankroll (€)": [initial_bankroll]})
    settled = settled.sort_values("timestamp")
    settled["Bankroll (€)"] = initial_bankroll + settled["profit"].astype(float).cumsum()
    settled["Giocata"] = range(1, len(settled) + 1)
    timeline = settled[["Giocata", "Bankroll (€)"]].reset_index(drop=True)
    starting_point = pd.DataFrame({"Giocata": [0], "Bankroll (€)": [initial_bankroll]})
    return pd.concat([starting_point, timeline], ignore_index=True)


# ==============================================================================
# FASE 3b: SINTESI TESTUALE GENERATA DA AI (MATCH EXECUTIVE SUMMARY)
# ==============================================================================
def _get_llm_api_key() -> tuple[str, str] | None:
    """Cerca una chiave API LLM (Anthropic, OpenAI, Gemini) fra le variabili
    d'ambiente o gli st.secrets, in questo ordine di priorità. Ritorna
    (provider, chiave) oppure None se nessuna è configurata — in quel caso il
    chiamante ripiega automaticamente sul generatore di template Python."""
    candidates = (
        ("anthropic", "ANTHROPIC_API_KEY"),
        ("openai", "OPENAI_API_KEY"),
        ("gemini", "GOOGLE_API_KEY"),
        ("gemini", "GEMINI_API_KEY"),
    )
    for provider, env_name in candidates:
        api_key = os.environ.get(env_name)
        if not api_key:
            try:
                api_key = st.secrets.get(env_name)
            except Exception:
                api_key = None
        if api_key:
            return provider, api_key
    return None


def build_match_summary_prompt(
    model: MatchModel,
    home: str,
    away: str,
    fatigue_home: dict[str, object] | None,
    fatigue_away: dict[str, object] | None,
    kelly_rows: list[tuple[str, float, float | None]],
) -> str:
    """Costruisce il prompt testuale con tutti i dati già calcolati dal
    motore (Power Rating, xG, 1X2, affaticamento, value bet), da passare
    all'LLM per generare il Report Analitico Intelligence."""
    value_bets = [f"{label} (prob. {prob:.0%}, stake consigliato {stake:.1f}%)" for label, prob, stake in kelly_rows if stake is not None and stake > 0]
    lines = [
        f"Partita: {home} vs {away}.",
        f"Power Rating: {home} {model.home_rating:.0f}, {away} {model.away_rating:.0f}.",
        f"xG attesi: {home} {model.home_lambda:.2f}, {away} {model.away_lambda:.2f}.",
        f"Probabilità 1X2: 1={model.home_win_prob:.0%} X={model.draw_prob:.0%} 2={model.away_win_prob:.0%}.",
    ]
    if model.manual_factor_home or model.manual_factor_away:
        lines.append(
            f"Slider manuali (Mercato+Infortuni): {home} {model.manual_factor_home:+.0%}, "
            f"{away} {model.manual_factor_away:+.0%}."
        )
    if fatigue_home and abs(float(fatigue_home.get("attack_malus", 0.0))) >= FATIGUE_ALERT_THRESHOLD:
        lines.append(f"Affaticamento {home}: malus attacco {float(fatigue_home['attack_malus']):+.0%}.")
    if fatigue_away and abs(float(fatigue_away.get("attack_malus", 0.0))) >= FATIGUE_ALERT_THRESHOLD:
        lines.append(f"Affaticamento {away}: malus attacco {float(fatigue_away['attack_malus']):+.0%}.")
    lines.append("Value bet rilevate: " + ("; ".join(value_bets) if value_bets else "nessuna al momento."))
    lines.append(
        "Scrivi un Report Analitico Intelligence di 3-4 punti chiave in italiano, in linguaggio "
        "naturale e professionale, in formato elenco puntato Markdown, per un utente che deve "
        "decidere se scommettere su questa partita. Copri: 1) confronto Power Rating/favorita, "
        "2) impatto di slider manuali/affaticamento se presenti, 3) eventuali value bet rilevate, "
        "4) sintesi del pronostico 1X2/xG. Non inventare dati non forniti."
    )
    return "\n".join(lines)


def generate_match_summary_ai(prompt: str, provider: str, api_key: str) -> str | None:
    """Tenta la generazione del report via LLM (Anthropic/OpenAI/Gemini).
    Ritorna None per qualunque errore (libreria non installata, rete, quota,
    chiave non valida...), così il chiamante ripiega sul template Python
    senza mai far crashare l'app."""
    try:
        if provider == "anthropic":
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(getattr(block, "text", "") for block in response.content)
            return text.strip() or None
        if provider == "openai":
            import openai

            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
            )
            text = response.choices[0].message.content
            return text.strip() if text else None
        if provider == "gemini":
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            response = gemini_model.generate_content(prompt)
            return response.text.strip() if getattr(response, "text", None) else None
    except Exception:
        return None
    return None


def generate_match_summary_template(
    model: MatchModel,
    home: str,
    away: str,
    fatigue_home: dict[str, object] | None,
    fatigue_away: dict[str, object] | None,
    kelly_rows: list[tuple[str, float, float | None]],
) -> str:
    """Fallback senza LLM: genera 3-4 punti chiave in linguaggio naturale
    incrociando i dati già calcolati dal motore, con un generatore di
    template testuale condizionale in Python (nessuna chiamata esterna)."""
    bullets: list[str] = []

    favorite = home if model.home_rating >= model.away_rating else away
    underdog = away if favorite == home else home
    favorite_rating = model.home_rating if favorite == home else model.away_rating
    underdog_rating = model.away_rating if favorite == home else model.home_rating
    bullets.append(
        f"**Power Rating**: {favorite} parte favorita con un Power Rating di {favorite_rating:.0f} "
        f"contro il {underdog_rating:.0f} di {underdog}."
    )

    impact_notes = []
    if model.manual_factor_home:
        impact_notes.append(f"{home} (slider {model.manual_factor_home:+.0%})")
    if model.manual_factor_away:
        impact_notes.append(f"{away} (slider {model.manual_factor_away:+.0%})")
    if fatigue_home and abs(float(fatigue_home.get("attack_malus", 0.0))) >= FATIGUE_ALERT_THRESHOLD:
        impact_notes.append(f"{home} affaticata (malus attacco {float(fatigue_home['attack_malus']):+.0%})")
    if fatigue_away and abs(float(fatigue_away.get("attack_malus", 0.0))) >= FATIGUE_ALERT_THRESHOLD:
        impact_notes.append(f"{away} affaticata (malus attacco {float(fatigue_away['attack_malus']):+.0%})")
    if impact_notes:
        bullets.append("**Assenze / Mercato / Affaticamento**: attenzione a " + ", ".join(impact_notes) + ".")
    else:
        bullets.append("**Assenze / Mercato / Affaticamento**: nessun correttivo manuale rilevante applicato.")

    value_bets = [
        f"'{label}' quota inserita, probabilità stimata {prob:.0%}, stake consigliato {stake:.1f}%"
        for label, prob, stake in kelly_rows
        if stake is not None and stake > 0
    ]
    if value_bets:
        bullets.append("**Value Bet rilevate**: " + "; ".join(value_bets) + ".")
    else:
        bullets.append("**Value Bet**: nessuna quota inserita o nessun vantaggio rilevato al momento nel tab Value Betting.")

    total_goals = model.home_lambda + model.away_lambda
    bullets.append(
        f"**Pronostico**: 1={model.home_win_prob:.0%} · X={model.draw_prob:.0%} · 2={model.away_win_prob:.0%}, "
        f"con xG combinato atteso di {total_goals:.2f} gol."
    )

    return "\n\n".join(f"- {bullet}" for bullet in bullets)


def generate_match_executive_summary(
    model: MatchModel,
    home: str,
    away: str,
    fatigue_home: dict[str, object] | None,
    fatigue_away: dict[str, object] | None,
    kelly_rows: list[tuple[str, float, float | None]],
) -> tuple[str, str]:
    """Ritorna (testo_report, fonte) dove fonte è 'AI (<provider>)' o
    'Template Python'. Prova prima l'LLM se una chiave API è configurata;
    in assenza di chiave o in caso di qualunque errore, ripiega
    automaticamente sul generatore di template — l'app non si blocca mai."""
    api = _get_llm_api_key()
    if api is not None:
        provider, api_key = api
        prompt = build_match_summary_prompt(model, home, away, fatigue_home, fatigue_away, kelly_rows)
        ai_text = generate_match_summary_ai(prompt, provider, api_key)
        if ai_text:
            return ai_text, f"AI ({provider})"
    return generate_match_summary_template(model, home, away, fatigue_home, fatigue_away, kelly_rows), "Template Python"


def _kelly_market_definitions(model: MatchModel, home: str, away: str) -> list[tuple[str, str, float]]:
    """Elenco (key, label, probabilità) dei mercati coperti dal Calcolatore
    Kelly: unica fonte condivisa fra render_value_betting_tab,
    compute_kelly_rows_from_session e compute_kelly_rows_detailed."""
    goal_markets = goal_market_probabilities(model)
    return [
        ("kelly_home", f"1 · Vittoria {home}", model.home_win_prob),
        ("kelly_draw", "X · Pareggio", model.draw_prob),
        ("kelly_away", f"2 · Vittoria {away}", model.away_win_prob),
        ("kelly_over25", "Over 2.5 gol", goal_markets["total_over"][2.5]),
        ("kelly_under25", "Under 2.5 gol", 1 - goal_markets["total_over"][2.5]),
        ("kelly_gg", "Goal (GG)", goal_markets["goal_goal"]),
        ("kelly_ng", "No Goal (NG)", goal_markets["no_goal"]),
    ]


def compute_kelly_rows_detailed(
    model: MatchModel, home: str, away: str
) -> list[tuple[str, str, float, float | None, float | None]]:
    """Rilegge le quote eventualmente già inserite dall'utente nel tab Value
    Betting (session_state, stesse chiavi widget di render_value_betting_tab)
    e calcola lo stake Kelly per ciascun mercato. Ritorna (key, label,
    probabilità, quota, stake) — versione completa usata per l'ordinamento
    delle Value Bet e il box Best Value Bet of the Match."""
    rows: list[tuple[str, str, float, float | None, float | None]] = []
    for key, label, probability in _kelly_market_definitions(model, home, away):
        odds = st.session_state.get(f"{key}_odds", 0.0)
        valid_odds = odds if odds and odds > 1.0 else None
        stake = kelly_stake_percent(probability, valid_odds)
        rows.append((key, label, probability, valid_odds, stake))
    return rows


def compute_kelly_rows_from_session(model: MatchModel, home: str, away: str) -> list[tuple[str, float, float | None]]:
    """Versione compatta (label, probabilità, stake) di
    compute_kelly_rows_detailed: usata dal Report Analitico Intelligence per
    citare le value bet rilevate senza dover conoscere key/quota."""
    return [
        (label, probability, stake)
        for _key, label, probability, _odds, stake in compute_kelly_rows_detailed(model, home, away)
    ]


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
    fatigue_home: dict[str, object] | None = None,
    fatigue_away: dict[str, object] | None = None,
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
            fatigue_home=fatigue_home,
            fatigue_away=fatigue_away,
        )
    except FootballDataError as error:
        source = "FBref" if is_secondary_league(league) else "Football-Data.org"
        return None, f"Dati {source} non disponibili: {error}"
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


def render_sidebar_controls() -> dict[str, object]:
    """Slider manuali nella sidebar: Fattore Mercato (-20%/+20%) e Impatto
    Infortuni/Titolari Assenti (-30%/+30%), per casa e trasferta, più
    l'Indice di Affaticamento & Turnover (Fase 2). I valori incrementano/
    riducono Power Index e attacco/difesa attesa PRIMA del calcolo di xG,
    tiri e probabilità (vedi build_match_model)."""
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

    st.markdown("### 🩺 Affaticamento & Impegni Infrasettimanali")
    with st.expander("Affaticamento & Impegni Infrasettimanali", expanded=False):
        st.caption(
            "Giorni di riposo, trasferte europee e turnover previsto: si SOMMANO "
            "agli slider di Mercato/Assenze qui sopra, senza sovrascriverli."
        )
        col_rest_home, col_rest_away = st.columns(2)
        with col_rest_home:
            rest_days_home = st.slider(
                "Giorni di riposo Casa", 2, 7, 7, key="rest_days_home",
                help="7 = 7 o più giorni di riposo (nessun malus).",
            )
        with col_rest_away:
            rest_days_away = st.slider(
                "Giorni di riposo Trasferta", 2, 7, 7, key="rest_days_away",
                help="7 = 7 o più giorni di riposo (nessun malus).",
            )

        col_travel_home, col_travel_away = st.columns(2)
        with col_travel_home:
            travel_home = st.checkbox(
                "Trasferta europea faticosa Casa", key="travel_home",
            )
        with col_travel_away:
            travel_away = st.checkbox(
                "Trasferta europea faticosa Trasferta", key="travel_away",
            )

        col_turnover_home, col_turnover_away = st.columns(2)
        with col_turnover_home:
            turnover_home = st.selectbox(
                "Turnover previsto Casa", options=list(TURNOVER_LEVELS), key="turnover_home",
            )
        with col_turnover_away:
            turnover_away = st.selectbox(
                "Turnover previsto Trasferta", options=list(TURNOVER_LEVELS), key="turnover_away",
            )

    st.markdown("### 🎲 The Odds API (quote reali)")
    with st.expander("Recupero automatico quote bookmaker", expanded=False):
        st.caption(
            "Inserisci una API Key gratuita di [The Odds API](https://the-odds-api.com) "
            "per recuperare automaticamente le quote reali (Sisal, Snai, bet365...) nel "
            "Calcolatore Kelly. Senza chiave, o se la chiamata fallisce, restano attivi "
            "gli inserimenti manuali delle quote — l'app non si blocca mai."
        )
        odds_api_key = st.text_input(
            "API Key The Odds API",
            type="password",
            key="odds_api_key",
            placeholder="Lascia vuoto per inserire le quote manualmente",
        )

    fatigue_home = fatigue_turnover_index(rest_days_home, travel_home, turnover_home)
    fatigue_away = fatigue_turnover_index(rest_days_away, travel_away, turnover_away)

    return {
        "market_factor_home": market_factor_home,
        "market_factor_away": market_factor_away,
        "injury_factor_home": injury_factor_home,
        "injury_factor_away": injury_factor_away,
        "fatigue_home": fatigue_home,
        "fatigue_away": fatigue_away,
        "odds_api_key": odds_api_key,
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


def _render_heatmap_cell(label: str, probability: float, *, big: bool = False) -> None:
    """Singola cella colorata della Heatmap (verde/arancione/rosso)."""
    bg, text_color = heatmap_color(probability)
    value_size = "1.6rem" if big else "1.05rem"
    label_size = ".8rem" if big else ".72rem"
    st.markdown(
        f'<div style="background:{bg};color:{text_color};border-radius:12px;'
        f'padding:{"16px 10px" if big else "10px 6px"};margin-bottom:10px;'
        f'text-align:center;font-weight:700">'
        f'<div style="font-size:{label_size};opacity:.9">{escape(str(label))}</div>'
        f'<div style="font-size:{value_size};margin-top:4px">{probability:.0%}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_best_value_bet_box(ranked_bets: list[dict[str, object]]) -> None:
    """👑 BEST VALUE BET OF THE MATCH: box in evidenza con la Value Bet dallo
    Stake Kelly più alto (già deduplicata per mercati correlati da
    rank_value_bets), seguito dalla classifica delle altre Value Bet
    rilevate, ordinate per Stake Kelly decrescente."""
    if not ranked_bets:
        st.info(
            "Nessuna Value Bet rilevata al momento: inserisci le quote reali del "
            "bookmaker nel Calcolatore Kelly qui sotto per attivare l'ordinamento."
        )
        return

    best = ranked_bets[0]
    ev_text = f"{best['ev']:+.1f}%" if best["ev"] is not None else "n/d"
    st.markdown(
        '<div style="background:linear-gradient(135deg,#f59e0b,#facc15);color:#1c1300;'
        'border-radius:16px;padding:18px 22px;margin-bottom:18px;'
        'box-shadow:0 6px 20px rgba(245,158,11,.35)">'
        '<div style="font-size:1rem;font-weight:800;letter-spacing:.03em">'
        '👑 BEST VALUE BET OF THE MATCH</div>'
        f'<div style="font-size:1.5rem;font-weight:800;margin-top:6px">{escape(str(best["label"]))}</div>'
        '<div style="margin-top:8px;font-weight:600;font-size:.95rem">'
        f'Quota {best["odds"]:.2f} · Probabilità algoritmo {best["probability"]:.1%} · '
        f'Expected Value {ev_text} · <u>Stake consigliato {best["stake"]:.1f}%</u>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    if len(ranked_bets) > 1:
        st.markdown("##### 📋 Altre Value Bet rilevate (ordinate per Stake Kelly)")
        ranking_frame = pd.DataFrame(
            [
                {
                    "Mercato": row["label"],
                    "Quota": f"{row['odds']:.2f}",
                    "Probabilità": f"{row['probability']:.1%}",
                    "Expected Value": f"{row['ev']:+.1f}%" if row["ev"] is not None else "n/d",
                    "Stake Kelly": f"{row['stake']:.1f}%",
                }
                for row in ranked_bets[1:]
            ]
        )
        st.dataframe(ranking_frame, use_container_width=True, hide_index=True)
    st.markdown("---")


def render_value_betting_tab(model: MatchModel, home: str, away: str, league: str, odds_api_key: str) -> None:
    """FASE 1: VALUE BETTING & UX — Heatmap dei mercati ad alta probabilità
    + Calcolatore Kelly Criterion (Quarter Kelly), con recupero automatico
    delle quote reali da The Odds API (fallback manuale se assente/fallisce).
    Estensione puramente additiva: legge solo il MatchModel già calcolato dal
    motore esistente."""
    ranked_bets = rank_value_bets(compute_kelly_rows_detailed(model, home, away))
    render_best_value_bet_box(ranked_bets)

    st.markdown(
        "### 🟩 Heatmap dei Mercati ad Alta Probabilità\n"
        "I 5 mercati più probabili per questa partita, calcolati dalla stessa "
        "matrice Poisson + Dixon-Coles usata nelle altre schede. "
        "🟩 ≥70% · 🟧 50-69% · 🟥 <50%."
    )
    top_markets = top_heatmap_markets(model, home, away, top_n=5)
    heatmap_cols = st.columns(len(top_markets))
    for col, row in zip(heatmap_cols, top_markets):
        with col:
            _render_heatmap_cell(row["Mercato"], row["Probabilità"], big=True)

    with st.expander("Griglia completa dei mercati (1X2, Doppia Chance, Over/Under, Goal/No Goal)"):
        all_rows = heatmap_market_probabilities(model, home, away)
        grid_cols = st.columns(4)
        for index, row in enumerate(all_rows):
            with grid_cols[index % 4]:
                _render_heatmap_cell(row["Mercato"], row["Probabilità"])

    st.markdown("---")
    st.markdown(
        "### 💰 Calcolatore Kelly Criterion (Quarter Kelly)\n"
        "Con una API Key di The Odds API inserita in sidebar, la quota "
        "migliore disponibile viene recuperata e proposta automaticamente "
        "per ciascun mercato — resta comunque modificabile a mano. Senza "
        "chiave (o se il recupero fallisce) inserisci la quota reale "
        "manualmente: se la probabilità del nostro algoritmo supera quella "
        "implicita nella quota, lo stake consigliato (25% del Kelly pieno) "
        "sarà positivo — altrimenti nessun vantaggio (**NO VALUE**)."
    )
    if odds_api_key:
        st.caption("🎲 The Odds API collegata: recupero automatico attivo per i mercati disponibili.")

    header_cols = st.columns([2.4, 1, 1.1, 2.5])
    header_cols[0].caption("Mercato")
    header_cols[1].caption("Probabilità algoritmo")
    header_cols[2].caption("Quota bookmaker")
    header_cols[3].caption("Esito Kelly")

    for key, label, probability in _kelly_market_definitions(model, home, away):
        live_odds = get_live_odds(home, away, key, league, odds_api_key) if odds_api_key else None
        best_live_odds = max(live_odds.values()) if live_odds else None

        odds_input_key = f"{key}_odds"
        if best_live_odds is not None and odds_input_key not in st.session_state:
            # Pre-compila l'input manuale con la quota migliore recuperata
            # automaticamente, SENZA sovrascrivere un valore già inserito
            # dall'utente in una sessione precedente — resta sempre modificabile.
            st.session_state[odds_input_key] = round(best_live_odds, 2)

        col_label, col_prob, col_odds, col_badge = st.columns([2.4, 1, 1.1, 2.5])
        with col_label:
            st.markdown(f"**{label}**")
            if best_live_odds is not None:
                st.caption(f"🎲 Auto da The Odds API: {best_live_odds:.2f}")
        with col_prob:
            st.markdown(f"{probability:.1%}")
        with col_odds:
            odds = st.number_input(
                "Quota",
                min_value=0.0,
                max_value=50.0,
                value=0.0,
                step=0.05,
                key=odds_input_key,
                label_visibility="collapsed",
            )
        with col_badge:
            stake = kelly_stake_percent(probability, odds if odds > 1.0 else None)
            badge_label, bg, text_color = value_bet_badge(stake)
            if stake is None:
                st.caption("Inserisci una quota per calcolare lo stake")
            else:
                detail = f"Stake consigliato: {stake:.1f}%" if stake > 0 else "Quota sbilanciata a favore del bookmaker"
                st.markdown(
                    f'<div style="background:{bg};color:{text_color};border-radius:8px;'
                    f'padding:6px 10px;font-weight:700;text-align:center">{badge_label}'
                    f'<br><span style="font-size:.82rem;font-weight:500">{detail}</span></div>',
                    unsafe_allow_html=True,
                )

        if live_odds:
            with st.expander(f"📊 Confronto Bookmaker — {label}"):
                render_bookmaker_comparison_table(fair_odds(probability), live_odds)

    st.caption(
        f"Fractional Kelly Stake = ((Probabilità × Quota) - 1) / (Quota - 1) × 100, "
        f"scalato al {KELLY_FRACTION:.0%} (Quarter Kelly) per contenere la varianza sul bankroll."
    )


def render_match_executive_summary(
    model: MatchModel,
    home: str,
    away: str,
    fatigue_home: dict[str, object] | None,
    fatigue_away: dict[str, object] | None,
) -> None:
    """🤖 Report Analitico Intelligence: expander in cima alla pagina match
    con 3-4 punti chiave in linguaggio naturale, generati via LLM se una
    chiave API è configurata, altrimenti tramite template Python (fallback
    automatico trasparente — non richiede alcuna azione dell'utente)."""
    kelly_rows = compute_kelly_rows_from_session(model, home, away)
    with st.expander("🤖 Report Analitico Intelligence", expanded=True):
        summary_text, source = generate_match_executive_summary(model, home, away, fatigue_home, fatigue_away, kelly_rows)
        st.markdown(summary_text)
        st.caption(f"Generato da: {source} · aggiornato in base a Power Rating, slider manuali e quote inserite.")


def render_bankroll_tab() -> None:
    """📊 Gestione Bankroll & Storico: Bankroll Iniziale, form nuova giocata,
    storico persistito su file (CSV/JSON), metriche ROI/Yield/Win Rate e
    grafico dell'andamento del bankroll. Modulo indipendente dal motore di
    simulazione (non legge Power Rating/Dixon-Coles/slider manuali)."""
    st.markdown(
        "### 📊 Gestione Bankroll & Storico\n"
        "Traccia le giocate effettuate e monitora ROI, Win Rate e andamento "
        "del bankroll nel tempo. Lo storico è salvato su file e non si "
        "azzera ricaricando la pagina."
    )

    config = load_bankroll_config()
    initial_bankroll = st.number_input(
        "Bankroll Iniziale (€)",
        min_value=0.0,
        value=float(config["initial_bankroll"]),
        step=50.0,
        key="initial_bankroll_input",
    )
    if initial_bankroll != config["initial_bankroll"]:
        save_bankroll_config(initial_bankroll)

    st.markdown("---")
    st.markdown("##### ➕ Registra una nuova giocata")
    with st.form("new_bet_form", clear_on_submit=True):
        col_league, col_match = st.columns(2)
        with col_league:
            bet_league = st.selectbox("Campionato", options=list(FOOTBALL_DATA_COMPETITIONS), key="bet_league")
        with col_match:
            bet_match = st.text_input("Partita", placeholder="es. Inter - Cagliari", key="bet_match")

        col_market, col_odds, col_outcome = st.columns(3)
        with col_market:
            bet_market = st.text_input("Mercato / Pronostico", placeholder="es. 1, Over 2.5", key="bet_market")
        with col_odds:
            bet_odds = st.number_input("Quota", min_value=1.01, value=1.90, step=0.05, key="bet_odds")
        with col_outcome:
            bet_outcome = st.selectbox("Esito", options=BET_OUTCOMES, key="bet_outcome")

        col_stake_type, col_stake_value = st.columns(2)
        with col_stake_type:
            stake_type = st.radio("Stake in", options=["€", "% Bankroll (Kelly)"], horizontal=True, key="bet_stake_type")
        with col_stake_value:
            if stake_type == "€":
                stake_amount = st.number_input("Stake (€)", min_value=0.0, value=10.0, step=1.0, key="bet_stake_eur")
            else:
                stake_percent = st.number_input("Stake (% bankroll)", min_value=0.0, value=2.0, step=0.5, key="bet_stake_pct")
                current_bankroll_for_stake = bankroll_metrics(load_bankroll_log(), initial_bankroll)["current_bankroll"]
                stake_amount = current_bankroll_for_stake * stake_percent / 100

        submitted = st.form_submit_button("Registra giocata", type="primary")
        if submitted:
            if not bet_match or not bet_market:
                st.warning("Inserisci almeno Partita e Mercato prima di registrare la giocata.")
            else:
                append_bet(bet_league, bet_match, bet_market, bet_odds, stake_amount, stake_type, bet_outcome)
                st.success(f"Giocata registrata: {bet_match} · {bet_market} · stake {stake_amount:.2f}€")
                st.rerun()

    st.markdown("---")
    log_df = load_bankroll_log()

    if log_df.empty:
        st.info("Nessuna giocata registrata finora. Usa il form sopra per iniziare a tracciare il tuo storico.")
        return

    st.markdown("##### ✏️ Storico giocate (modifica l'esito per aggiornare ROI/Bankroll)")
    edited_df = st.data_editor(
        log_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "outcome": st.column_config.SelectboxColumn("outcome", options=list(BET_OUTCOMES)),
            "profit": st.column_config.NumberColumn("profit", disabled=True, format="%.2f €"),
        },
        key="bankroll_log_editor",
    )
    if not edited_df.equals(log_df):
        edited_df = recompute_and_save_log(edited_df)
        st.rerun()

    metrics = bankroll_metrics(edited_df, initial_bankroll)
    st.markdown("##### 📈 Metriche finanziarie")
    col_pnl, col_roi, col_winrate, col_bankroll = st.columns(4)
    with col_pnl:
        st.metric("Profitto/Perdita Totale", f"{metrics['total_profit']:+.2f} €")
    with col_roi:
        st.metric("ROI", f"{metrics['roi']:+.1f}%")
    with col_winrate:
        st.metric("Win Rate", f"{metrics['win_rate']:.1f}%", help=f"Su {metrics['settled_count']} giocate concluse")
    with col_bankroll:
        st.metric("Bankroll Attuale", f"{metrics['current_bankroll']:.2f} €", delta=f"{metrics['total_profit']:+.2f} €")

    st.markdown("##### 📉 Andamento del Bankroll")
    timeline = bankroll_timeline(edited_df, initial_bankroll)
    st.line_chart(timeline.set_index("Giocata"))


ALL_LEAGUE_OPTIONS: list[str] = list(FOOTBALL_DATA_COMPETITIONS) + list(SECONDARY_LEAGUES)
"""Elenco completo dei campionati selezionabili in UI: i campionati
principali (Football-Data.org) seguiti dai campionati secondari coperti via
scraping automatico FBref (Serie B, Segunda División)."""


def render_dashboard(sidebar_values: dict[str, float]) -> None:
    st.markdown(
        "### Impostazioni partita\n"
        "Squadre, calendario e risultati dei campionati principali vengono "
        "recuperati da Football-Data.org; Serie B e Segunda División sono "
        "caricate automaticamente e gratuitamente da FBref. Non sono "
        "quotazioni di un bookmaker."
    )

    col_league, col_home, col_away = st.columns(3)
    with col_league:
        league = st.selectbox(
            "Campionato",
            options=ALL_LEAGUE_OPTIONS,
            key="league_select",
        )

    secondary = is_secondary_league(league)
    data_source_label = "FBref (scraping automatico)" if secondary else "Football-Data.org"

    try:
        if secondary:
            teams = list(fetch_secondary_league_teams(league))
        else:
            teams = [name for _, name in fetch_league_teams(league)]
    except FootballDataError as error:
        st.error(f"{data_source_label} non disponibile: {error}")
        teams = []

    if len(teams) < 2:
        with col_home:
            st.selectbox("Squadra di casa", options=teams, disabled=True)
        with col_away:
            st.selectbox("Squadra ospite", options=teams, disabled=True)
        st.warning(f"{data_source_label} non ha restituito due squadre disponibili.")
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

    if secondary:
        st.info(
            f"{data_source_label}: {len(teams)} squadre caricate · "
            f"{secondary_competition_season_status(league)}. "
            "Attacco/Difesa calcolati dinamicamente dalla classifica reale "
            "(nessun Tier fisso). Micro-eventi stimati su baseline di categoria."
        )
    else:
        try:
            status_text = (
                f"Football-Data.org: {len(teams)} squadre caricate · "
                f"{competition_season_status(league)}. "
                "Micro-eventi stimati su baseline di campionato."
            )
            st.info(status_text)
        except FootballDataError as error:
            st.warning(f"Stato stagione non disponibile: {error}")

    if secondary:
        with st.expander("📅 Calendario stagione corrente", expanded=False):
            st.caption(
                "Il calendario partite non è incluso nello scraping automatico "
                "della classifica: sono disponibili solo le squadre e le "
                "statistiche aggregate (gol fatti/subiti, partite giocate)."
            )
    else:
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

    if secondary:
        # FBref non espone gli stemmi ufficiali via scraping semplice: la
        # dashboard resta pienamente funzionante, solo senza i loghi club.
        crests = {}
    else:
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
        fatigue_home=sidebar_values.get("fatigue_home"),
        fatigue_away=sidebar_values.get("fatigue_away"),
    )

    if model is None:
        st.error(error_message)
        return

    # --- 🤖 Report Analitico Intelligence (Fase 3b), in cima alla pagina match --
    render_match_executive_summary(
        model, home, away, sidebar_values.get("fatigue_home"), sidebar_values.get("fatigue_away")
    )

    # --- Avviso Modalità Inizio Stagione (badge/warning giallo) -----------------
    if model.early_season_warning:
        st.warning(
            "⚠️ Analisi a confidenza ridotta - Inizio Stagione in corso  \n"
            f"{home}: {model.home_current_season_matches} partite disputate · "
            f"{away}: {model.away_current_season_matches} partite disputate "
            f"(soglia piena confidenza: {EARLY_SEASON_MATCHDAY_THRESHOLD}). "
            "Il Power Index viene mescolato con dati reali ancora parziali."
        )

    # --- Avviso Affaticamento & Turnover (Fase 2, badge/warning giallo) --------
    fatigue_home_input = sidebar_values.get("fatigue_home")
    fatigue_away_input = sidebar_values.get("fatigue_away")
    if fatigue_home_input:
        home_fatigue_alert = fatigue_alert_message(home, fatigue_home_input)
        if home_fatigue_alert:
            st.warning(home_fatigue_alert)
    if fatigue_away_input:
        away_fatigue_alert = fatigue_alert_message(away, fatigue_away_input)
        if away_fatigue_alert:
            st.warning(away_fatigue_alert)

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

    tab_poisson, tab_goal_markets, tab_value_betting, tab_montecarlo = st.tabs(
        [
            "Analisi Quote & Probabilità (Poisson)",
            "📊 Statistiche Gol & Mercati",
            "💰 Value Betting & Heatmap",
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

    with tab_goal_markets:
        st.markdown(
            "Percentuali Under/Over e Goal/No Goal calcolate dalla stessa matrice "
            "di Poisson bivariata con correzione Dixon-Coles usata per il "
            "pronostico 1X2 e i risultati esatti, quindi pienamente coerenti "
            "con le altre schede."
        )
        markets = goal_market_probabilities(model)

        st.markdown("##### Under / Over gol totali (partita)")
        total_cols = st.columns(4)
        for index, line in enumerate((1.5, 2.5, 3.5, 4.5)):
            over_p = markets["total_over"][line]
            under_p = 1 - over_p
            with total_cols[index]:
                st.metric(f"Over {line:.1f}", f"{over_p:.1%}")
                st.progress(min(max(over_p, 0.0), 1.0))
                st.caption(f"Under {line:.1f}: {under_p:.1%}")

        st.markdown("##### Under / Over gol squadra Casa")
        home_cols = st.columns(3)
        for index, line in enumerate((0.5, 1.5, 2.5)):
            over_p = markets["home_over"][line]
            under_p = 1 - over_p
            with home_cols[index]:
                st.metric(f"{home} · Over {line:.1f}", f"{over_p:.1%}")
                st.progress(min(max(over_p, 0.0), 1.0))
                st.caption(f"Under {line:.1f}: {under_p:.1%}")

        st.markdown("##### Under / Over gol squadra Trasferta")
        away_cols = st.columns(3)
        for index, line in enumerate((0.5, 1.5, 2.5)):
            over_p = markets["away_over"][line]
            under_p = 1 - over_p
            with away_cols[index]:
                st.metric(f"{away} · Over {line:.1f}", f"{over_p:.1%}")
                st.progress(min(max(over_p, 0.0), 1.0))
                st.caption(f"Under {line:.1f}: {under_p:.1%}")

        st.markdown("##### Goal / No Goal (entrambe le squadre segnano)")
        gg_col, ng_col = st.columns(2)
        with gg_col:
            st.metric("Goal (GG)", f"{markets['goal_goal']:.1%}")
            st.progress(min(max(markets["goal_goal"], 0.0), 1.0))
        with ng_col:
            st.metric("No Goal (NG)", f"{markets['no_goal']:.1%}")
            st.progress(min(max(markets["no_goal"], 0.0), 1.0))

    with tab_value_betting:
        render_value_betting_tab(model, home, away, league, sidebar_values.get("odds_api_key", ""))

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

        main_tab_analysis, main_tab_bankroll = st.tabs(
            ["⚽ Analisi Match", "📊 Gestione Bankroll & Storico"]
        )
        with main_tab_analysis:
            render_dashboard(sidebar_values)
        with main_tab_bankroll:
            render_bankroll_tab()
    else:
        render_login()


if __name__ == "__main__":
    main()
