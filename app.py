from __future__ import annotations

import json
import math
import os
import random
import time
from dataclasses import dataclass
from datetime import datetime
from html import escape
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import streamlit.components.v1 as components
from scipy.stats import poisson


APP_PASSWORD = "wayne2026"


LEAGUES: dict[str, list[str]] = {
    "Italy · Serie A": [
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
    "Italy · Serie B": [
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
    "England · Premier League": [
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
    "England · EFL Championship": [
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
    "Spain · La Liga": [
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
    "Spain · Segunda División": [
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
    "Germany · Bundesliga": [
        "Augsburg",
        "Bayer Leverkusen",
        "Bayern Munich",
        "Borussia Dortmund",
        "Borussia Mönchengladbach",
        "Eintracht Francoforte",
        "Elversberg",
        "Friburgo",
        "Hoffenheim",
        "Hamburg",
        "Cologne",
        "Mainz",
        "Paderborn",
        "RB Lipsia",
        "Schalke 04",
        "Stuttgart",
        "Union Berlino",
        "Werder Brema",
    ],
    "Germany · 2. Bundesliga": [
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
        "Nuremberg",
        "Paderborn",
        "Preußen Münster",
        "Schalke 04",
    ],
    "France · Ligue 1": [
        "Angers",
        "Auxerre",
        "Brest",
        "Le Havre",
        "Le Mans",
        "Lens",
        "Lille",
        "Lorient",
        "Lyon",
        "Marseille",
        "Monaco",
        "Nice",
        "Paris FC",
        "PSG",
        "Rennes",
        "Strasbourg",
        "Toulouse",
        "Troyes",
    ],
    "France · Ligue 2": [
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
    "Netherlands · Eredivisie": [
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
    "Portugal · Primeira Liga": [
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
    "Europe · UEFA Champions League": [
        "Arsenal",
        "Aston Villa",
        "Atlético Madrid",
        "Barcelona",
        "Bayern Munich",
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
        "Stuttgart",
        "Villarreal",
    ],
    "International · FIFA World Cup": [
        "Argentina", "Australia", "Belgium", "Brazil", "Cameroon", "Canada",
        "Colombia", "Costa Rica", "Croatia", "Denmark", "Ecuador", "England",
        "France", "Germany", "Ghana", "Iran", "Italy", "Japan", "Mexico",
        "Morocco", "Netherlands", "Poland", "Portugal", "Qatar", "Saudi Arabia",
        "Senegal", "Serbia", "South Korea", "Spain", "Switzerland", "Tunisia",
        "USA", "Uruguay", "Wales",
    ],
    "International · UEFA European Championship": [
        "Albania", "Austria", "Belgium", "Croatia", "Czech Republic", "Denmark",
        "England", "France", "Georgia", "Germany", "Hungary", "Italy",
        "Netherlands", "Poland", "Portugal", "Romania", "Scotland", "Serbia",
        "Slovakia", "Slovenia", "Spain", "Switzerland", "Turkey", "Ukraine",
    ],
    "International · UEFA Nations League": [
        "Albania", "Andorra", "Armenia", "Austria", "Belgium", "Bosnia and Herzegovina",
        "Bulgaria", "Croatia", "Cyprus", "Czech Republic", "Denmark", "England",
        "Estonia", "Faroe Islands", "Finland", "France", "Georgia", "Germany",
        "Gibraltar", "Greece", "Hungary", "Iceland", "Israel", "Italy",
        "Kazakhstan", "Kosovo", "Latvia", "Liechtenstein", "Lithuania",
        "Luxembourg", "Malta", "Moldova", "Montenegro", "Netherlands",
        "North Macedonia", "Northern Ireland", "Norway", "Poland", "Portugal",
        "Republic of Ireland", "Romania", "San Marino", "Scotland", "Serbia",
        "Slovakia", "Slovenia", "Spain", "Sweden", "Switzerland", "Turkey",
        "Ukraine", "Wales",
    ],
    "International · Friendlies": [
        "Argentina", "Brazil", "Belgium", "Croatia", "Colombia", "Denmark",
        "Egypt", "England", "France", "Germany", "Ghana", "Italy", "Ivory Coast",
        "Japan", "Mexico", "Morocco", "Netherlands", "Nigeria", "Norway",
        "Portugal", "Senegal", "South Korea", "Spain", "Sweden", "Switzerland",
        "Tunisia", "Turkey", "USA", "Uruguay", "Wales",
    ],
}

NATIONAL_TEAM_COMPETITIONS: set[str] = {
    "International · FIFA World Cup",
    "International · UEFA European Championship",
    "International · UEFA Nations League",
    "International · Friendlies",
}
"""League display names treated as national-team competitions: matches team
xG estimation to a broader, cross-competition lookback (see
fetch_team_recent_matches_extended) instead of the single-competition
current/previous-season split used for club leagues, since national sides
play far fewer fixtures per year and a strict season boundary does not
apply to them."""

NATIONAL_TEAM_MATCH_WINDOW = 10
"""How many of a national team's most recent FINISHED matches (across ALL
competitions — qualifiers, finals, Nations League, friendlies) to pull for
Attack/Defense (alpha/beta) estimation, wider than the club-league lookback
(8) to compensate for national teams' sparser annual fixture list."""


def is_national_team_competition(league: str) -> bool:
    """True if `league` is one of the international/national-team
    competitions (see NATIONAL_TEAM_COMPETITIONS)."""
    return league in NATIONAL_TEAM_COMPETITIONS


TOP_DIVISIONS = {
    "Italy · Serie A",
    "England · Premier League",
    "Spain · La Liga",
    "Germany · Bundesliga",
    "France · Ligue 1",
    "Netherlands · Eredivisie",
    "Portugal · Primeira Liga",
    # La Champions League riunisce club di nazioni diverse: va trattata come
    # massima serie a tutti gli effetti (il DIZIONARIO FASCE DI FORZA non
    # dipende comunque dalla lega selezionata, solo dal nome della squadra).
    "Europe · UEFA Champions League",
}

FOOTBALL_DATA_COMPETITIONS: dict[str, str] = {
    "Italy · Serie A": "SA",
    "England · Premier League": "PL",
    "England · EFL Championship": "ELC",
    "Spain · La Liga": "PD",
    "Germany · Bundesliga": "BL1",
    "France · Ligue 1": "FL1",
    "Netherlands · Eredivisie": "DED",
    "Portugal · Primeira Liga": "PPL",
    "Europe · UEFA Champions League": "CL",
    # International / national-team competitions. WC and EC are confirmed
    # Football-Data.org codes; UNL and FRIENDLY are best-effort — if the API
    # tier does not expose them, the app degrades gracefully to the fallback
    # roster above (same safety net already used for every club league).
    "International · FIFA World Cup": "WC",
    "International · UEFA European Championship": "EC",
    "International · UEFA Nations League": "UNL",
    "International · Friendlies": "FRIENDLY",
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
    # International matches: generally slightly fewer shots/corners than
    # club football (less cohesive attacking patterns, more cautious
    # setups), cards vary with the stakes of the fixture.
    "WC": {"shots": 11.0, "shots_on_target": 3.8, "corners": 4.3, "cards": 2.2, "fouls": 12.0},
    "EC": {"shots": 11.2, "shots_on_target": 3.9, "corners": 4.4, "cards": 2.3, "fouls": 12.2},
    "UNL": {"shots": 10.8, "shots_on_target": 3.6, "corners": 4.1, "cards": 2.0, "fouls": 12.0},
    "FRIENDLY": {"shots": 10.3, "shots_on_target": 3.4, "corners": 3.9, "cards": 1.5, "fouls": 10.8},
}

PROMOTED_TEAMS = {
    # Italy · Serie A
    "Venezia",
    "Frosinone",
    "Monza",
    # England · Premier League
    "Coventry City",
    "Ipswich Town",
    "Hull City",
    # Spain · La Liga
    "Racing Santander",
    "Deportivo La Coruña",
    "Málaga",
    # Germany · Bundesliga
    "Schalke 04",
    "Elversberg",
    "Paderborn",
    # France · Ligue 1
    "Troyes",
    "Le Mans",
    # Netherlands · Eredivisie
    "ADO Den Haag",
    "SC Cambuur",
    # Portugal · Primeira Liga
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
tiri/corner/cartellini in base al gap di rating (vedi rating_scaling_factors).
NOTE: this is added only to the *local* rating_diff used for shots/corners/
cards scaling — it is never added to rating_finale_home/away themselves, so
it cannot inflate the Power Rating shown in the UI."""

HOME_ADVANTAGE_GOAL_MULTIPLIER = 1.15
"""Direct multiplier on the home team's expected goals (xG), calibrated to
a MODERATE, verified home-advantage bump of +0.20/+0.25 expected goals for
a league-average matchup (never a disproportionate multiplier of team
strength): at LEAGUE_AVERAGE_GOALS_PER_TEAM (1.35) with average attack/
defense multipliers of 1.0 each, home_lambda_base = 1.35 × 1.15 = 1.5525,
i.e. a +0.2025 xG bump — squarely inside the requested +0.20/+0.25 window.
The bump scales proportionally with the match's baseline lambda (stronger
attacks get a slightly larger absolute bump, weaker ones a smaller one),
which is standard Dixon-Coles practice, but always stays a fixed +15% of
that baseline — it never multiplies the *rating gap* between the teams."""

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

EARLY_SEASON_MATCHDAY_THRESHOLD = 10
"""Dalla Giornata 10 (N partite REALI giocate nella stagione corrente, un
campione minimo di 10-15 partite come richiesto) si usa il 100% dei dati/
statistiche reali. Sotto questa soglia si applica la Transizione Dinamica
(Dynamic Decay, vedi dynamic_decay_weights), che pesa progressivamente di
più il rating di Fascia man mano che il campione reale è piccolo — questo,
insieme allo shrinkage di REGRESSION_TO_MEAN_SAMPLE_SIZE applicato PRIMA
del blend (vedi _shrink_to_mean), è la doppia barriera che impedisce a
2-3 risultati estremi di un club di fascia media di sbilanciare il rating
sopra quello di una big con un campione più ampio e affidabile."""

REGRESSION_TO_MEAN_SAMPLE_SIZE = 12.0
"""Numero di partite (pesate) oltre il quale un moltiplicatore Attacco/
Difesa calcolato dalle statistiche osservate viene usato al 100% del suo
valore grezzo. Con un campione più piccolo, il moltiplicatore viene
'ristretto' (shrinkage Bayesiano) verso 1.0 (la media di lega) in proporzione
al campione disponibile — vedi _shrink_to_mean. Questo è un livello di
protezione SEPARATO e complementare al Dynamic Decay Tier/Stats: quello
sfuma fra il rating di Fascia e quello reale; questo attenua il rating
reale stesso quando è ancora statisticamente inaffidabile (es. 2-3 partite
di un neopromosso con un filotto di vittorie non devono produrre un
moltiplicatore Attacco vicino al tetto di 3.0)."""

CLUB_MATCH_LOOKBACK = 15
"""Massimo numero di partite recenti (per stagione corrente e per stagione
precedente separatamente) recuperate per ogni squadra di club — alzato da 8
a 15 per garantire un campione minimo di 10-15 partite come richiesto,
riducendo ulteriormente la sensibilità del rating a 2-3 risultati anomali
isolati (si veda anche REGRESSION_TO_MEAN_SAMPLE_SIZE, che agisce sullo
stesso problema da un angolo complementare)."""

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
    1: "Tier 1 · Title Contender",
    2: "Tier 2 · European Spot",
    3: "Tier 3 · Mid-Table",
    4: "Tier 4 · Relegation Battle",
    5: "Tier 5 · Newly Promoted",
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
        # National teams · Tier 1 (major football powers / World Cup favorites)
        "brazil", "france", "argentina", "england", "spain", "germany",
        "portugal", "italy", "belgium", "netherlands",
    ),
    2: (  # Europa / Champions League
        "roma", "lazio", "fiorentina", "bologna", "chelsea", "tottenham",
        "spurs", "newcastle", "aston villa", "manchester united",
        "man united", "man utd", "rb lipsia", "rb leipzig", "marsiglia",
        "marseille", "villarreal", "stoccarda", "stuttgart", "lione",
        "lyon", "monaco", "psv", "sporting cp", "sporting", "porto",
        "como", "como 1907", "fc como",
        # National teams · Tier 2 (consistently competitive)
        "croatia", "uruguay", "denmark", "switzerland", "morocco",
        "colombia", "japan", "senegal", "mexico", "usa", "united states",
        "poland", "serbia", "wales", "ukraine",
    ),
    3: (  # Metà classifica
        "torino", "genoa", "udinese", "sassuolo", "everton", "fulham",
        "crystal palace", "brighton", "bournemouth", "athletic bilbao",
        "real betis", "lens", "lille", "feyenoord", "club brugge",
        "galatasaray",
        # National teams · Tier 3 (mid-table internationals)
        "scotland", "austria", "turkey", "hungary", "romania", "slovakia",
        "czech republic", "greece", "norway", "sweden", "canada",
        "south korea", "australia", "tunisia", "ecuador", "costa rica",
    ),
    4: (  # Salvezza
        "lecce", "cagliari", "monza", "verona", "parma",
        "brentford", "forest", "nottingham", "leeds", "sunderland",
        "elche", "levante", "shakhtar", "slavia praga", "slavia prague",
        # National teams · Tier 4 (qualification-battle nations)
        "iceland", "finland", "slovenia", "bosnia and herzegovina",
        "northern ireland", "republic of ireland", "israel", "georgia",
        "albania", "north macedonia", "montenegro", "bulgaria",
    ),
    5: (  # Neopromosse
        "frosinone", "venezia", "coventry", "hull", "ipswich",
        "racing santander", "deportivo", "coruña", "coruna", "málaga",
        "malaga", "schalke", "elversberg", "paderborn", "troyes",
        "le mans", "ado den haag", "cambuur", "académico de viseu",
        "academico de viseu", "marítimo", "maritimo",
        # National teams · Tier 5 (minor UEFA/friendly-circuit nations)
        "andorra", "san marino", "liechtenstein", "malta", "gibraltar",
        "faroe islands", "luxembourg", "moldova", "kosovo", "cyprus",
        "estonia", "latvia", "lithuania", "armenia", "kazakhstan",
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
    """TRANSIZIONE DINAMICA PER LE PRIME EARLY_SEASON_MATCHDAY_THRESHOLD
    GIORNATE (Dynamic Decay): Peso_Fascia = (T - N) / T, Peso_Stats = N / T,
    con N = partite REALI giocate nella stagione corrente e T =
    EARLY_SEASON_MATCHDAY_THRESHOLD (clampato a [0, T]). Da N ≥ T in poi si
    usa il 100% dei dati/statistiche reali (Peso_Fascia = 0)."""
    n = clamp(matches_played, 0, EARLY_SEASON_MATCHDAY_THRESHOLD)
    tier_weight = (EARLY_SEASON_MATCHDAY_THRESHOLD - n) / EARLY_SEASON_MATCHDAY_THRESHOLD
    stats_weight = n / EARLY_SEASON_MATCHDAY_THRESHOLD
    return tier_weight, stats_weight


def _shrink_to_mean(
    multiplier: float, sample_size: float, full_confidence_n: float = REGRESSION_TO_MEAN_SAMPLE_SIZE
) -> float:
    """Bayesian-style shrinkage (Regression to the Mean): pulls a per-match
    Attack/Defense multiplier toward the league-average of 1.0 when the
    sample of matches behind it is small, in direct proportion to how
    small that sample is. With `sample_size >= full_confidence_n`, the raw
    multiplier is returned unchanged (full confidence); with a small
    sample (e.g. 2-3 matches for a mid/low-tier side on a hot streak), the
    multiplier is pulled most of the way back to 1.0, preventing it from
    outweighing a Big club's larger, more reliable sample. This runs
    BEFORE the Dynamic Decay Tier/Stats blend (dynamic_decay_weights) and
    is a separate, complementary safeguard: that function blends Tier
    rating with real stats; this function tempers the real stats
    themselves while they are still statistically unreliable."""
    confidence = clamp(sample_size / max(full_confidence_n, 1e-9), 0.0, 1.0)
    return 1.0 + (multiplier - 1.0) * confidence


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
    """Most recent results first: 'W' win, 'D' draw, 'L' loss."""
    recent_matches: tuple[dict[str, object], ...] = ()
    """Detail of the same matches behind `recent_form` (most recent first,
    up to FORM_MATCHES_WINDOW): each entry is
    {'date', 'opponent', 'scored', 'conceded', 'result'} — used to render
    the Recent Form badges and the Team Form & H2H tables without any new
    calculation (pure display data captured alongside the existing Form
    Factor loop)."""
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
        return f"season {season_label(season_start)} · fallback list (API unavailable)"
    return f"season {season_label(season_start)} · current"


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
            "FOOTBALL_DATA_API_KEY secret not configured. Add it before using live data."
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
        raise FootballDataError(f"Connection to Football-Data.org failed: {error}") from error
    except ValueError as error:
        raise FootballDataError("Football-Data.org returned an invalid response.") from error

    if not isinstance(payload, dict):
        raise FootballDataError("Unexpected Football-Data.org response.")
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
                f"Football-Data.org did not return the 2026/27 teams for {league}."
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
        raise FootballDataError(f"Insufficient data for {label} of {team_name}.")
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
    columns = ["Date", "Status", "Home", "Away"]
    matches = sorted(
        fetch_league_matches(league),
        key=lambda match: str(match.get("utcDate", "")),
    )
    rows = []
    status_labels = {
        "TIMED": "Scheduled",
        "SCHEDULED": "To Be Scheduled",
        "FINISHED": "Finished",
        "POSTPONED": "Postponed",
        "CANCELED": "Cancelled",
    }
    for match in matches:
        home = match.get("homeTeam", {})
        away = match.get("awayTeam", {})
        if not isinstance(home, dict) or not isinstance(away, dict):
            continue
        date_value = str(match.get("utcDate", ""))
        rows.append(
            {
                "Date": date_value[:16].replace("T", " "),
                "Status": status_labels.get(str(match.get("status", "")), str(match.get("status", ""))),
                "Home": home.get("name", ""),
                "Away": away.get("name", ""),
            }
        )
    return pd.DataFrame(rows, columns=columns)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_team_recent_matches_extended(
    league: str, team_name: str, limit: int = NATIONAL_TEAM_MATCH_WINDOW
) -> tuple[dict[str, object], ...]:
    """For sparse-schedule competitions (national teams): fetches a team's
    most recent FINISHED matches ACROSS ALL COMPETITIONS (qualifiers,
    tournament finals, Nations League, friendlies) via Football-Data.org's
    per-team endpoint, instead of the single-competition/current-season
    endpoint used for club leagues. This avoids starving the Attack/Defense
    (alpha/beta) estimate when a national side has played very few — or
    zero — matches within the one specific tournament being analyzed."""
    team_map = dict(fetch_league_teams(league))
    team_id = next((id_ for id_, name in team_map.items() if name == team_name), None)
    if team_id is None or team_id < 0:
        # Negative synthetic IDs come from the offline fallback roster
        # (_fallback_team_snapshot): there is no live team ID to query.
        raise FootballDataError(f"No live Football-Data.org team ID available for {team_name}.")
    payload = _football_data_request(
        f"/teams/{team_id}/matches",
        {"status": "FINISHED", "limit": limit},
    )
    return _parse_finished_matches(payload)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_team_live_stats(league: str, team_name: str) -> LiveTeamStats:
    team_map = dict(fetch_league_teams(league))
    team_id = next((id_ for id_, name in team_map.items() if name == team_name), None)
    if team_id is None:
        raise FootballDataError(
            f"The team {team_name} is not available in Football-Data.org."
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

    if is_national_team_competition(league):
        # National teams play far fewer matches per year than clubs, and a
        # single tournament's own fixture list can be near-empty between
        # windows. Pull the team's recent matches across ALL competitions
        # instead, all weighted equally — there is no clean "current vs
        # previous season" boundary for a national side, so the club-league
        # Time-Decay previous-season discount does not apply here.
        try:
            extended_matches = fetch_team_recent_matches_extended(league, team_name)
            current_fixtures = _team_fixtures(extended_matches)[:NATIONAL_TEAM_MATCH_WINDOW]
        except FootballDataError:
            current_fixtures = _team_fixtures(fetch_league_matches(league))[:NATIONAL_TEAM_MATCH_WINDOW]
        previous_fixtures: list[dict[str, object]] = []
    else:
        current_fixtures = _team_fixtures(fetch_league_matches(league))[:CLUB_MATCH_LOOKBACK]
        try:
            previous_fixtures = _team_fixtures(fetch_previous_season_matches(league))[:CLUB_MATCH_LOOKBACK]
        except FootballDataError:
            previous_fixtures = []

    # Partite REALI (non pesate) disputate nella stagione in corso: base per
    # la Modalità Inizio Stagione (vedi EARLY_SEASON_MATCHDAY_THRESHOLD).
    # dynamic_decay_weights() clamps this internally to
    # [0, EARLY_SEASON_MATCHDAY_THRESHOLD], so the same formula is correct
    # whether current_fixtures came from a club season or the national-team
    # extended lookback above.
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
    recent_match_details: list[dict[str, object]] = []

    for fixture_item, weight in weighted_pool:
        home_data = fixture_item.get("homeTeam", {})
        away_data = fixture_item.get("awayTeam", {})
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
                recent_results.append("W")
                recent_points.append(3)
            elif scored == conceded:
                recent_results.append("D")
                recent_points.append(1)
            else:
                recent_results.append("L")
                recent_points.append(0)
            recent_weights.append(weight)
            opponent_name = str((away_data if is_home else home_data).get("name", "Unknown"))
            recent_match_details.append(
                {
                    "date": str(fixture_item.get("utcDate", ""))[:10],
                    "opponent": opponent_name,
                    "scored": scored,
                    "conceded": conceded,
                    "result": recent_results[-1],
                }
            )

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
                f"Football-Data.org has no usable historical data for {team_name}."
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
        recent_match_details = []

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
        recent_matches=tuple(recent_match_details),
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
    fatigue_home: dict[str, object] | None = None,
    fatigue_away: dict[str, object] | None = None,
) -> MatchModel:
    home_stats = fetch_team_live_stats(league, home)
    away_stats = fetch_team_live_stats(league, away)

    # --- Defensive Home/Away data-integrity check ------------------------
    # fetch_team_live_stats resolves each team's stats by team_id/team_name
    # independently, so a swap here is not structurally possible in the
    # current code — but this check makes that guarantee explicit and fails
    # loudly (instead of silently mis-crossing alpha_home with beta_home)
    # if a future change ever breaks that invariant.
    if home_stats.team_name != home or away_stats.team_name != away:
        raise FootballDataError(
            f"Home/Away data integrity check failed: expected stats for "
            f"{home} (home) vs {away} (away), but got {home_stats.team_name} "
            f"vs {away_stats.team_name}. Aborting to avoid a mis-crossed "
            f"Attack/Defense calculation."
        )

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
        _average(home_stats.home_goals_for, home_stats.home_matches, "goals scored at home", home)
        if home_stats.home_matches
        else _average(home_stats.goals_for, home_stats.matches, "goals scored", home)
    )
    home_goal_against = (
        _average(
            home_stats.home_goals_against,
            home_stats.home_matches,
            "goals conceded at home",
            home,
        )
        if home_stats.home_matches
        else _average(home_stats.goals_against, home_stats.matches, "goals conceded", home)
    )
    away_goal_for = (
        _average(away_stats.away_goals_for, away_stats.away_matches, "goals scored away", away)
        if away_stats.away_matches
        else _average(away_stats.goals_for, away_stats.matches, "goals scored", away)
    )
    away_goal_against = (
        _average(
            away_stats.away_goals_against,
            away_stats.away_matches,
            "goals conceded away",
            away,
        )
        if away_stats.away_matches
        else _average(away_stats.goals_against, away_stats.matches, "goals conceded", away)
    )
    home_sot_raw = _average(home_stats.shots_on_target, home_stats.matches, "shots on target", home)
    away_sot_raw = _average(away_stats.shots_on_target, away_stats.matches, "shots on target", away)
    home_shots_raw = _average(home_stats.total_shots, home_stats.matches, "total shots", home)
    away_shots_raw = _average(away_stats.total_shots, away_stats.matches, "total shots", away)
    home_corners_raw = _average(home_stats.corners, home_stats.matches, "corners", home)
    away_corners_raw = _average(away_stats.corners, away_stats.matches, "corners", away)
    home_cards_raw = _average(home_stats.cards, home_stats.matches, "cards", home)
    away_cards_raw = _average(away_stats.cards, away_stats.matches, "cards", away)
    fouls = _average(home_stats.fouls, home_stats.matches, "fouls", home)
    fouls += _average(away_stats.fouls, away_stats.matches, "fouls", away)

    # --- 2. DIZIONARIO FASCE DI FORZA + TRANSIZIONE DINAMICA (Dynamic Decay) --
    # Ogni squadra viene risolta in una Fascia di Forza tramite fuzzy matching
    # (lookup_team_tier), con fallback esplicito a Tier 3 — mai un default
    # piatto. Le statistiche osservate vengono convertite in moltiplicatori
    # Attacco/Difesa relativi alla media di lega, poi mescolate con quelle di
    # Fascia secondo N = partite reali giocate nella stagione corrente:
    #   N < 5  → Peso_Fascia=(5-N)/5, Peso_Stats=N/5
    #   N >= 5 → 100% statistiche reali (Peso_Fascia=0)
    early_season = is_early_season_match(home_stats, away_stats)

    home_tier = team_tier_profile(home)
    away_tier = team_tier_profile(away)
    home_tier_weight, home_stats_weight = dynamic_decay_weights(home_stats.current_season_matches)
    away_tier_weight, away_stats_weight = dynamic_decay_weights(away_stats.current_season_matches)

    def _stats_multiplier(value_per_match: float) -> float:
        return clamp(value_per_match / LEAGUE_AVERAGE_GOALS_PER_TEAM, 0.3, 3.0)

    def _stats_rating(attack_mult: float, defense_mult: float) -> float:
        return BASE_RATING + (RATING_SCALE / 2) * (attack_mult - 1.0) - (RATING_SCALE / 2) * (defense_mult - 1.0)

    # --- Regression to the Mean (shrinkage) --------------------------------
    # home_goal_for/home_goal_against (and their away counterparts) are each
    # backed by a specific number of matches — home_matches/away_matches
    # when the home-/away-specific split was used, or the full `matches`
    # count in the small-sample fallback. Shrinking with THAT exact sample
    # size (not a coarser proxy) ensures a side with only 2-3 home matches
    # this season — even a hot streak — gets pulled hard back toward the
    # league-average multiplier of 1.0, so it cannot outweigh a Big club's
    # larger, more reliable sample. See REGRESSION_TO_MEAN_SAMPLE_SIZE.
    home_sample_size = home_stats.home_matches if home_stats.home_matches else home_stats.matches
    away_sample_size = away_stats.away_matches if away_stats.away_matches else away_stats.matches

    home_stats_attack = _shrink_to_mean(_stats_multiplier(home_goal_for), home_sample_size)
    home_stats_defense = _shrink_to_mean(_stats_multiplier(home_goal_against), home_sample_size)
    away_stats_attack = _shrink_to_mean(_stats_multiplier(away_goal_for), away_sample_size)
    away_stats_defense = _shrink_to_mean(_stats_multiplier(away_goal_against), away_sample_size)
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
        LEAGUE_AVERAGE_GOALS_PER_TEAM * attacco_finale_home * difesa_finale_away * HOME_ADVANTAGE_GOAL_MULTIPLIER,
        0.05,
        5.5,
    )
    away_lambda = clamp(
        LEAGUE_AVERAGE_GOALS_PER_TEAM * attacco_finale_away * difesa_finale_home,
        0.05,
        5.0,
    )

    rating_diff = (rating_finale_home + HOME_ADVANTAGE_RATING) - rating_finale_away

    # --- 5. Tiri totali/in porta: stessa Transizione Dinamica (baseline di
    # Fascia derivata dall'Attacco di Tier, mescolata alle statistiche reali),
    # poi slider manuali e infine il gap di rating (smorzato). -----------------
    competition_code = FOOTBALL_DATA_COMPETITIONS[league]
    micro_baseline = MICRO_EVENT_BASELINES[competition_code]
    shots_per_goal = micro_baseline["shots"] / LEAGUE_AVERAGE_GOALS_PER_TEAM
    sot_per_goal = micro_baseline["shots_on_target"] / LEAGUE_AVERAGE_GOALS_PER_TEAM

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

    home_tier_number = lookup_team_tier(home)
    away_tier_number = lookup_team_tier(away)
    engine_note = (
        f"{TEAM_TIER_LABELS[home_tier_number]} ({home}, rating {rating_finale_home:.0f}) "
        f"vs {TEAM_TIER_LABELS[away_tier_number]} ({away}, rating {rating_finale_away:.0f}) · "
        f"Tier/Stats Weight: {home}={home_tier_weight:.0%}/{home_stats_weight:.0%}, "
        f"{away}={away_tier_weight:.0%}/{away_stats_weight:.0%} · "
        f"Dixon-Coles correction ρ={DIXON_COLES_RHO:+.2f}"
    )
    if home_stats.recent_form:
        engine_note += f" · {home} form: {''.join(home_stats.recent_form)}"
    if away_stats.recent_form:
        engine_note += f" · {away} form: {''.join(away_stats.recent_form)}"
    if manual_factor_home:
        engine_note += f" · {home} slider: {manual_factor_home:+.0%}"
    if manual_factor_away:
        engine_note += f" · {away} slider: {manual_factor_away:+.0%}"
    if fatigue_attack_malus_home or fatigue_defense_malus_home:
        engine_note += (
            f" · {home} fatigue: attack {fatigue_attack_malus_home:+.0%}/"
            f"defense {fatigue_defense_malus_home:+.0%}"
        )
    if fatigue_attack_malus_away or fatigue_defense_malus_away:
        engine_note += (
            f" · {away} fatigue: attack {fatigue_attack_malus_away:+.0%}/"
            f"defense {fatigue_defense_malus_away:+.0%}"
        )
    if early_season:
        engine_note += (
            f" · ⚠️ Antepost Tiering active: {home} {home_stats.current_season_matches} "
            f"real matches, {away} {away_stats.current_season_matches} real matches "
            f"(full-confidence threshold: {EARLY_SEASON_MATCHDAY_THRESHOLD})"
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
        ("Total Match Shots", model.shots_total_lambda, (21.5, 23.5, 25.5)),
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
        ("Total Match Corners", model.corners_total_lambda, (7.5, 8.5, 9.5, 10.5)),
        ("Cartellini · Casa", model.home_cards_lambda, (1.5, 2.5)),
        ("Cartellini · Trasferta", model.away_cards_lambda, (1.5, 2.5)),
        ("Cartellini · Totali match", model.cards_total_lambda, (3.5, 4.5, 5.5)),
        ("Total Match Fouls", model.fouls_lambda, (22.5, 24.5, 26.5)),
    ]
    rows: list[dict[str, object]] = []
    for event, lam, lines in groups:
        for line in lines:
            probability = over_probability(lam, line)
            rows.append(
                {
                    "Micro-Event": event,
                    "Threshold": f"Over {line:.1f}",
                    "Expected Value": round(lam, 2),
                    "Probability": probability,
                    "Fair Odds": fair_odds(probability),
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
# FASE 4: DASHBOARD GRAFICI & MICRO-EVENTI (Plotly)
# ==============================================================================
# Estensione puramente additiva e solo di VISUALIZZAZIONE: non introduce
# nessun nuovo calcolo statistico. Riusa esattamente la stessa matrice di
# Poisson bivariata + correzione Dixon-Coles già impiegata da
# match_outcome_probabilities / goal_market_probabilities / exact_score_
# probabilities, così i grafici raccontano sempre lo stesso match delle altre
# schede (Pronostici, Statistiche Gol & Mercati, Monte Carlo).
def goal_distribution_probabilities(model: MatchModel, max_goals: int = 10) -> dict[str, object]:
    """Distribuzione di probabilità dei gol TOTALI di partita (0, 1, 2, 3, 4,
    5+) e matrice congiunta Casa/Trasferta (Poisson bivariata + correzione
    Dixon-Coles), usata sia dal grafico a barre 'Distribuzione Gol Totali'
    sia dalla Heatmap dei risultati esatti e dai Multigol."""
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

    total_goals_probability: dict[int, float] = {n: 0.0 for n in range(5)}
    five_plus_probability = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            total_goals = i + j
            probability = joint[i][j] / total
            if total_goals <= 4:
                total_goals_probability[total_goals] += probability
            else:
                five_plus_probability += probability

    return {
        "joint": joint,
        "total": total,
        "totals": total_goals_probability,
        "five_plus": clamp(five_plus_probability, 0.0, 1.0),
    }


def multigol_probabilities(goal_distribution: dict[str, object]) -> dict[str, float]:
    """Probabilità dei mercati Multigol (range di gol TOTALI di partita:
    1-2, 2-3, 3-4, 2-4), derivate dalla stessa matrice congiunta Poisson +
    Dixon-Coles già calcolata da goal_distribution_probabilities — nessun
    nuovo calcolo statistico introdotto."""
    joint = goal_distribution["joint"]
    total = goal_distribution["total"]
    max_goals = len(joint) - 1

    def _range_probability(low: int, high: int) -> float:
        probability = 0.0
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                total_goals = i + j
                if low <= total_goals <= high:
                    probability += joint[i][j]
        return clamp(probability / total, 0.0, 1.0)

    return {
        "Multigol 1-2": _range_probability(1, 2),
        "Multigol 2-3": _range_probability(2, 3),
        "Multigol 3-4": _range_probability(3, 4),
        "Multigol 2-4": _range_probability(2, 4),
    }


def exact_score_matrix(goal_distribution: dict[str, object], grid_size: int = 5) -> pd.DataFrame:
    """Matrice grid_size x grid_size (default: 0-4 gol per squadra) delle
    probabilità dei risultati esatti (Poisson bivariata + Dixon-Coles), pronta
    per la Heatmap: righe = gol Trasferta, colonne = gol Casa (si legge come
    un tradizionale tabellone risultati)."""
    joint = goal_distribution["joint"]
    total = goal_distribution["total"]
    rows = []
    for away_goals in range(grid_size):
        row = [joint[home_goals][away_goals] / total for home_goals in range(grid_size)]
        rows.append(row)
    return pd.DataFrame(
        rows,
        index=[f"{g} Trasferta" for g in range(grid_size)],
        columns=[f"{g} Casa" for g in range(grid_size)],
    )


def render_charts_dashboard_tab(model: MatchModel, home: str, away: str) -> None:
    """📊 Charts Dashboard & Micro-Events: an immediate visual snapshot of
    the goal distribution, the Goal/No Goal market, the exact-score map and
    the Multi-Goal ranges — all fed by the same bivariate Poisson matrix +
    Dixon-Coles correction already used by the Forecast, Goal Stats &
    Markets, and Monte Carlo Simulator tabs."""
    st.markdown(
        "### 📊 Charts Dashboard & Micro-Events\n"
        "An immediate visual snapshot of goal probabilities, calculated by "
        "the same engine (bivariate Poisson + Dixon-Coles correction) used "
        "in the other tabs: no new calculations, just additional charts."
    )

    goal_distribution = goal_distribution_probabilities(model)
    goal_markets = goal_market_probabilities(model)

    chart_col_1, chart_col_2 = st.columns(2)

    with chart_col_1:
        st.markdown("##### ⚽ Total Goals Distribution (match)")
        totals = goal_distribution["totals"]
        labels = ["0 goals", "1 goal", "2 goals", "3 goals", "4 goals", "5+ goals"]
        values = [
            totals[0], totals[1], totals[2], totals[3], totals[4], goal_distribution["five_plus"],
        ]
        totals_frame = pd.DataFrame({"Total Goals": labels, "Probability": values})
        totals_chart = px.bar(
            totals_frame,
            x="Total Goals",
            y="Probability",
            text="Probability",
            color="Probability",
            color_continuous_scale=["#1e3a5f", "#22d3ee"],
        )
        totals_chart.update_traces(texttemplate="%{text:.1%}", textposition="outside")
        totals_chart.update_layout(
            showlegend=False,
            yaxis_tickformat=".0%",
            margin={"l": 10, "r": 10, "t": 20, "b": 10},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
        )
        st.plotly_chart(totals_chart, use_container_width=True)
        st.caption("The bars cover Under/Over 0.5-4.5 goals: a base for evaluating any Under/Over line.")

    with chart_col_2:
        st.markdown("##### 🥅 Goal / No Goal Market")
        gg_frame = pd.DataFrame(
            {
                "Outcome": ["Goal (GG)", "No Goal (NG)"],
                "Probability": [goal_markets["goal_goal"], goal_markets["no_goal"]],
            }
        )
        gg_chart = px.pie(
            gg_frame,
            names="Outcome",
            values="Probability",
            hole=0.55,
            color="Outcome",
            color_discrete_map={"Goal (GG)": "#16a34a", "No Goal (NG)": "#7f1d1d"},
        )
        gg_chart.update_traces(texttemplate="%{percent}", textinfo="label+percent")
        gg_chart.update_layout(
            margin={"l": 10, "r": 10, "t": 20, "b": 10},
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
            showlegend=False,
        )
        st.plotly_chart(gg_chart, use_container_width=True)
        st.caption("Goal (GG) = both teams score · No Goal (NG) = at least one fails to score.")

    st.markdown("##### 🗺️ Exact Score Map (0-4 goals per team)")
    st.caption(
        "Probability matrix (bivariate Poisson + Dixon-Coles correction): "
        "the more intense the color, the more likely the exact score."
    )
    score_matrix = exact_score_matrix(goal_distribution, grid_size=5)
    heatmap_chart = px.imshow(
        score_matrix,
        text_auto=".1%",
        color_continuous_scale="Viridis",
        aspect="auto",
        labels={"color": "Probability"},
    )
    heatmap_chart.update_layout(
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0",
        coloraxis_showscale=True,
    )
    heatmap_chart.update_xaxes(side="bottom")
    st.plotly_chart(heatmap_chart, use_container_width=True)

    st.markdown("##### 🎯 Multi-Goal Distribution")
    multigol = multigol_probabilities(goal_distribution)
    multigol_frame = pd.DataFrame(
        {"Market": list(multigol.keys()), "Probability": list(multigol.values())}
    )
    multigol_chart = px.bar(
        multigol_frame,
        x="Market",
        y="Probability",
        text="Probability",
        color="Probability",
        color_continuous_scale=["#3f1d5e", "#a855f7"],
    )
    multigol_chart.update_traces(texttemplate="%{text:.1%}", textposition="outside")
    multigol_chart.update_layout(
        showlegend=False,
        yaxis_tickformat=".0%",
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0",
    )
    st.plotly_chart(multigol_chart, use_container_width=True)
    st.caption(
        "Multi-Goal X-Y = probability that the match's total goals fall "
        "within the indicated range (endpoints included)."
    )

    st.caption(
        f"{home} vs {away} · combined expected xG {model.home_lambda + model.away_lambda:.2f} goals. "
        "Plotly charts generated from the same Poisson/Dixon-Coles matrix as the other tabs, "
        "consistent with the Monte Carlo simulation."
    )


# ==============================================================================
# FASE 5: ANALIZZATORE MULTI ESITO & VALUE BET (gruppi di risultati esatti)
# ==============================================================================
# Estensione puramente additiva: riusa la stessa matrice di risultati esatti
# (Poisson bivariata + correzione Dixon-Coles) già calcolata da
# exact_score_probabilities, oltre alle funzioni già esistenti fair_odds,
# expected_value_percent e kelly_stake_percent (Fase 1) — nessun nuovo
# calcolo statistico introdotto, solo un nuovo modo di aggregare/consultare
# le probabilità già prodotte dal motore.
MULTI_ESITO_GROUPS: dict[str, list[str]] = {
    "Group A · Clean Sheet Home Win (1-0, 2-0, 3-0)": ["1-0", "2-0", "3-0"],
    "Group B · Home Win Conceding (2-1, 3-1, 4-1)": ["2-1", "3-1", "4-1"],
    "Group C · Clean Sheet Away Win (0-1, 0-2, 0-3)": ["0-1", "0-2", "0-3"],
    "Group D · Main Draws (0-0, 1-1, 2-2)": ["0-0", "1-1", "2-2"],
    "Group E · Over/Goal Combo (2-1, 1-2, 2-2, 3-1, 1-3)": ["2-1", "1-2", "2-2", "3-1", "1-3"],
}
"""Preset Multi-Outcome groups: popular combinations of exact scores on
which bookmakers often offer a single odds ('combined multi-goal/outcome').
Each entry lists the 'Home-Away' scores included in the group."""

MULTI_ESITO_CUSTOM_LABEL = "🎯 Custom Multi-Outcome"
"""Special entry in the selector that activates the multiselect for manually
picking exact scores (see render_multi_esito_tab)."""


def exact_score_probability_map(model: MatchModel, max_goals: int = 6) -> dict[str, float]:
    """Converte l'elenco (già ordinato) restituito da
    exact_score_probabilities in un dizionario {'H-A': probabilità}, per un
    lookup diretto dei punteggi che compongono un gruppo Multi Esito. Stessa
    matrice di Poisson bivariata + correzione Dixon-Coles usata in tutte le
    altre schede (Pronostici, Dashboard Grafici, Monte Carlo)."""
    return {
        score: probability
        for score, probability in exact_score_probabilities(model.home_lambda, model.away_lambda, max_goals=max_goals)
    }


def cumulative_group_probability(score_map: dict[str, float], scores: Sequence[str]) -> float:
    """Somma le probabilità dei risultati esatti indicati (P_totale del
    gruppo Multi Esito), ignorando eventuali punteggi non presenti nella
    mappa (fuori dal range max_goals) invece di sollevare un errore."""
    return clamp(sum(score_map.get(score, 0.0) for score in scores), 0.0, 1.0)


def multi_esito_score_grid_options(max_goals: int = 5) -> list[str]:
    """Elenco ordinato di punteggi 'H-A' (0 a max_goals per squadra) da
    proporre nel multiselect 'Multi Esito Personalizzato' — una griglia
    ragionevole per l'uso pratico, coerente con quella della Heatmap dei
    Risultati Esatti nella Dashboard Grafici."""
    return [f"{home_goals}-{away_goals}" for home_goals in range(max_goals + 1) for away_goals in range(max_goals + 1)]


# ==============================================================================
# TEAM FORM & HEAD-TO-HEAD TAB
# ==============================================================================
# Purely additive: reads the recent_matches/recent_form already captured by
# fetch_team_live_stats (Time-Decay/Form Factor pipeline, unchanged) and
# only aggregates/displays them — no new fetch endpoint, no change to the
# Dixon-Coles engine, Team Tiers or Dynamic Decay weighting.
def compute_form_summary_stats(matches: tuple[dict[str, object], ...]) -> dict[str, float]:
    """Average goals scored/conceded and clean-sheet count over the recent
    matches already captured in LiveTeamStats.recent_matches (up to the
    last FORM_MATCHES_WINDOW games) — a simple read-only aggregation, not a
    new statistical model."""
    if not matches:
        return {"avg_scored": 0.0, "avg_conceded": 0.0, "clean_sheets": 0.0, "count": 0.0}
    scored_values = [float(match["scored"]) for match in matches]
    conceded_values = [float(match["conceded"]) for match in matches]
    clean_sheets = sum(1 for conceded in conceded_values if conceded == 0)
    count = len(matches)
    return {
        "avg_scored": sum(scored_values) / count,
        "avg_conceded": sum(conceded_values) / count,
        "clean_sheets": float(clean_sheets),
        "count": float(count),
    }


def render_recent_matches_table(team_name: str, matches: tuple[dict[str, object], ...]) -> None:
    """Compact WayneLab-styled table (Obsidian background, Electric Cyan
    header) with the last matches for one team: Date, Opponent, Score,
    Result (colored W/D/L pill)."""
    if not matches:
        st.info(f"No recent match data available for {team_name}.")
        return
    rows_html = []
    for match in matches:
        score_text = f"{int(match['scored'])}-{int(match['conceded'])}"
        rows_html.append(
            "<tr>"
            f"<td>{escape(str(match['date']) or 'n/a')}</td>"
            f"<td>{escape(str(match['opponent']))}</td>"
            f"<td>{escape(score_text)}</td>"
            f"<td>{_form_badge_html(str(match['result']), pill=True)}</td>"
            "</tr>"
        )
    st.markdown(
        '<div class="h2h-table-wrap"><table class="h2h-table">'
        "<thead><tr><th>Date</th><th>Opponent</th><th>Score</th><th>Result</th></tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def render_form_stats_subbox(stats: dict[str, float]) -> None:
    """Compact sub-box with Avg Goals Scored / Avg Goals Conceded / Clean
    Sheets over the last N games, styled as small WayneLab metric cards."""
    st.markdown(
        '<div class="form-stats-box">'
        '<div class="form-stats-item"><div class="form-stats-label">Avg Scored</div>'
        f'<div class="form-stats-value">{stats["avg_scored"]:.2f}</div></div>'
        '<div class="form-stats-item"><div class="form-stats-label">Avg Conceded</div>'
        f'<div class="form-stats-value">{stats["avg_conceded"]:.2f}</div></div>'
        '<div class="form-stats-item"><div class="form-stats-label">Clean Sheets</div>'
        f'<div class="form-stats-value">{int(stats["clean_sheets"])}/{int(stats["count"])}</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_team_form_tab(league: str, home: str, away: str) -> None:
    """📊 Team Form & H2H tab: last-5-games tables and form summary stats
    for both Home and Away teams, built from the same Football-Data.org
    fixtures already fetched by fetch_team_live_stats (cached) — a
    read-only view, no impact on the simulation engine."""
    st.markdown(
        "### 📊 Team Form & Head-to-Head\n"
        "Last 5 played matches for each team, sourced live from "
        "Football-Data.org — the same data feeding the Time-Decay / Form "
        "Factor component of the Dixon-Coles engine."
    )

    col_home, col_away = st.columns(2)

    with col_home:
        st.markdown(f"##### 🏠 {home} · Last 5 Matches")
        try:
            home_stats = fetch_team_live_stats(league, home)
            render_recent_matches_table(home, home_stats.recent_matches)
            render_form_stats_subbox(compute_form_summary_stats(home_stats.recent_matches))
        except FootballDataError as error:
            st.warning(f"Recent form unavailable for {home}: {error}")

    with col_away:
        st.markdown(f"##### ✈️ {away} · Last 5 Matches")
        try:
            away_stats = fetch_team_live_stats(league, away)
            render_recent_matches_table(away, away_stats.recent_matches)
            render_form_stats_subbox(compute_form_summary_stats(away_stats.recent_matches))
        except FootballDataError as error:
            st.warning(f"Recent form unavailable for {away}: {error}")

    st.caption(
        "W = Win · D = Draw · L = Loss. Clean Sheets counts matches where the team conceded 0 goals."
    )


def render_multi_esito_tab(model: MatchModel, home: str, away: str) -> None:
    """🎯 Multi-Outcome & Value Bet Analyzer: cumulative probability for
    groups of exact scores (preset or custom), Fair Odds, comparison with
    the entered bookmaker odds and Expected Value, with a suggested Kelly
    stake in case of a Value Bet. Reuses exclusively the probabilities
    already computed by the Poisson + Dixon-Coles engine."""
    st.markdown(
        "### 🎯 Multi-Outcome & Value Bet Analyzer\n"
        "Sums the probability of multiple exact scores (bivariate Poisson + "
        "Dixon-Coles correction) into a single 'Multi-Outcome', to compare it "
        "with the real odds offered by the bookmaker on that same combined "
        "market."
    )

    score_map = exact_score_probability_map(model, max_goals=6)

    group_options = list(MULTI_ESITO_GROUPS) + [MULTI_ESITO_CUSTOM_LABEL]
    selected_group = st.selectbox(
        "Select a Multi-Outcome Group",
        options=group_options,
        key="multi_esito_group",
    )

    if selected_group == MULTI_ESITO_CUSTOM_LABEL:
        available_scores = multi_esito_score_grid_options(max_goals=5)
        selected_scores = st.multiselect(
            "Custom Multi-Outcome — choose the exact scores to combine",
            options=available_scores,
            default=["1-0", "2-0"],
            key="multi_esito_custom_scores",
        )
    else:
        selected_scores = MULTI_ESITO_GROUPS[selected_group]
        st.caption("Scores included in the group: " + ", ".join(selected_scores))

    if not selected_scores:
        st.info("Select at least one exact score to calculate the cumulative probability.")
        return

    p_totale = cumulative_group_probability(score_map, selected_scores)
    quota_reale = fair_odds(p_totale)

    bookmaker_odds = st.number_input(
        "Bookmaker Odds for this Multi-Outcome",
        min_value=1.01,
        max_value=200.0,
        value=2.20,
        step=0.01,
        key="multi_esito_bookmaker_odds",
        help="Enter the real odds offered by the bookmaker on the selected combination of scores.",
    )

    ev_percent = expected_value_percent(p_totale, bookmaker_odds)
    stake_percent = kelly_stake_percent(p_totale, bookmaker_odds)

    metric_col_1, metric_col_2, metric_col_3, metric_col_4 = st.columns(4)
    with metric_col_1:
        st.metric("Cumulative Probability", f"{p_totale:.1%}")
    with metric_col_2:
        st.metric("Fair Odds", f"{quota_reale:.2f}")
    with metric_col_3:
        st.metric("Bookmaker Odds", f"{bookmaker_odds:.2f}")
    with metric_col_4:
        st.metric("Expected Value (EV)", f"{ev_percent:+.1f}%" if ev_percent is not None else "n/a")

    if ev_percent is not None and ev_percent > 0 and stake_percent is not None:
        st.markdown(
            '<div style="background:linear-gradient(135deg,#16a34a,#4ade80);color:#052e16;'
            'border-radius:16px;padding:18px 22px;margin-top:10px;'
            'box-shadow:0 6px 20px rgba(22,163,74,.35)">'
            '<div style="font-size:1.05rem;font-weight:800;letter-spacing:.02em">'
            '✅ VALUE BET FOUND!</div>'
            f'<div style="margin-top:8px;font-weight:600;font-size:.95rem">'
            f'Algorithm probability {p_totale:.1%} vs bookmaker odds {bookmaker_odds:.2f} '
            f'(fair odds {quota_reale:.2f}) · EV {ev_percent:+.1f}% · '
            f'<u>Suggested stake (Quarter Kelly): {stake_percent:.1f}%</u> of bankroll'
            '</div></div>',
            unsafe_allow_html=True,
        )
    else:
        ev_text = f"{ev_percent:+.1f}%" if ev_percent is not None else "n/a"
        st.markdown(
            '<div style="background:#3f1113;color:#fecaca;border-radius:16px;'
            'padding:18px 22px;margin-top:10px;border:1px solid #7f1d1d">'
            '<div style="font-size:1.05rem;font-weight:800;letter-spacing:.02em">'
            '⛔ NO VALUE (Underpriced)</div>'
            f'<div style="margin-top:8px;font-weight:600;font-size:.95rem">'
            f'The entered bookmaker odds ({bookmaker_odds:.2f}) do not cover the probability '
            f'estimated by the model ({p_totale:.1%}, fair odds {quota_reale:.2f}) · EV {ev_text}'
            '</div></div>',
            unsafe_allow_html=True,
        )

    with st.expander("📋 Probability detail for each score in the group"):
        detail_frame = pd.DataFrame(
            [
                {
                    "Result": score,
                    "Probability": f"{score_map.get(score, 0.0):.1%}",
                    "Fair Odds": f"{fair_odds(score_map.get(score, 0.0)):.2f}",
                }
                for score in selected_scores
            ]
        )
        st.dataframe(detail_frame, use_container_width=True, hide_index=True)

    st.caption(
        f"{home} vs {away} · Fractional Kelly Stake = ((Probability × Odds) - 1) / (Odds - 1) × 100, "
        f"scaled to {KELLY_FRACTION:.0%} (Quarter Kelly), consistent with the Kelly Calculator in "
        "the Value Betting & Heatmap tab."
    )


# ==============================================================================
# FASE 6: SIMULATORE LIVE MATCH MINUTO PER MINUTO (Stile FC/FIFA)
# ==============================================================================
# Modulo puramente di intrattenimento/visualizzazione, indipendente dal
# motore analitico: NON sostituisce né modifica in alcun modo le probabilità
# Poisson + Dixon-Coles usate dalle altre schede (Pronostici, Dashboard
# Grafici, Multi Esito, Value Betting, Monte Carlo), che restano l'unica
# fonte di riferimento per pronostici e value bet. Qui si genera solo UNA
# singola partita 'giocata' minuto per minuto, con esito diverso ad ogni
# simulazione, calibrata sugli stessi gol attesi (alpha) e cartellini attesi
# (beta) già calcolati dal motore per quel match.
LIVE_SHOTS_PER_GOAL_RATIO = 8.0
"""Tiri totali stimati per ogni gol atteso (alpha), usato come fallback se
non viene passata una lambda tiri esplicita al motore live."""

LIVE_SOT_PER_GOAL_RATIO = 3.0
"""Tiri in porta stimati per ogni gol atteso (alpha), fallback analogo a
LIVE_SHOTS_PER_GOAL_RATIO per i tiri in porta."""

LIVE_CORNER_BASE_LAMBDA = 5.0
"""Corner attesi di fallback per singola squadra (se non derivati dal
MatchModel), usati per calibrare la probabilità di corner per minuto."""

LIVE_CARD_YELLOW_TO_RED_RATIO = 0.06
"""Quota di ammonizioni che, nel motore live, degenera in un'espulsione
diretta (evento raro ma realistico)."""

LIVE_MATCH_ANIMATION_DELAY_SECONDS = 0.11
"""Pausa (in secondi) fra un minuto simulato e il successivo durante
l'animazione 'Cronaca Diretta': 90 minuti × 0.11s ≈ 10 secondi reali totali,
calibrati per una clip breve e ad alto impatto da registrare per i social
(TikTok/Reels/Shorts) senza tempi morti."""


def simulate_single_match(
    home_team: str,
    away_team: str,
    alpha_home: float,
    beta_home: float,
    alpha_away: float,
    beta_away: float,
    home_shots_lambda: float | None = None,
    away_shots_lambda: float | None = None,
    home_sot_lambda: float | None = None,
    away_sot_lambda: float | None = None,
    corners_lambda: float | None = None,
) -> dict[str, object]:
    """Simulates ONE single match minute by minute (1'-90'), arcade
    'match engine' style: `alpha_home`/`alpha_away` are each team's expected
    goals (xG) for the whole match (offensive intensity), while
    `beta_home`/`beta_away` are expected cards (disciplinary
    intensity/aggressiveness). Every minute, shots, shots on target/goals,
    corners and cards are rolled at random, with Bernoulli probabilities
    calibrated on these parameters (an approximation via thinning of a
    Poisson process). Returns the full event chronicle and the final
    statistical box score. Every call produces a different outcome (no fixed
    seed) — this is an illustrative module, not a source of probabilities:
    those remain the Poisson/Dixon-Coles engine used by the other tabs."""
    home_shots_lambda = home_shots_lambda if home_shots_lambda and home_shots_lambda > 0 else alpha_home * LIVE_SHOTS_PER_GOAL_RATIO
    away_shots_lambda = away_shots_lambda if away_shots_lambda and away_shots_lambda > 0 else alpha_away * LIVE_SHOTS_PER_GOAL_RATIO
    home_sot_lambda = home_sot_lambda if home_sot_lambda and home_sot_lambda > 0 else alpha_home * LIVE_SOT_PER_GOAL_RATIO
    away_sot_lambda = away_sot_lambda if away_sot_lambda and away_sot_lambda > 0 else alpha_away * LIVE_SOT_PER_GOAL_RATIO
    corners_lambda = corners_lambda if corners_lambda and corners_lambda > 0 else LIVE_CORNER_BASE_LAMBDA * 2

    # I tiri in porta non possono superare i tiri totali della stessa squadra.
    home_sot_lambda = min(home_sot_lambda, home_shots_lambda) if home_shots_lambda > 0 else 0.0
    away_sot_lambda = min(away_sot_lambda, away_shots_lambda) if away_shots_lambda > 0 else 0.0

    # Tasso di conversione per tiro in porta (probabilità che un tiro in
    # porta diventi gol), derivato in modo che il numero atteso di gol sulla
    # simulazione converga verso alpha_home/alpha_away.
    home_conversion = clamp(alpha_home / home_sot_lambda, 0.03, 0.6) if home_sot_lambda > 0 else 0.0
    away_conversion = clamp(alpha_away / away_sot_lambda, 0.03, 0.6) if away_sot_lambda > 0 else 0.0

    per_minute_home_shot = clamp(home_shots_lambda / 90, 0.0, 0.9)
    per_minute_away_shot = clamp(away_shots_lambda / 90, 0.0, 0.9)
    per_minute_corner = clamp(corners_lambda / 90, 0.0, 0.9)
    per_minute_card_home = clamp(beta_home / 90, 0.0, 0.5)
    per_minute_card_away = clamp(beta_away / 90, 0.0, 0.5)

    dominance_home = clamp(alpha_home / max(alpha_home + alpha_away, 0.01), 0.15, 0.85)

    events: list[dict[str, object]] = []
    stats = {
        "home_goals": 0, "away_goals": 0,
        "home_shots": 0, "away_shots": 0,
        "home_sot": 0, "away_sot": 0,
        "home_corners": 0, "away_corners": 0,
        "home_yellow": 0, "away_yellow": 0,
        "home_red": 0, "away_red": 0,
    }

    for minute in range(1, 91):
        if random.random() < per_minute_home_shot:
            stats["home_shots"] += 1
            if random.random() < clamp(home_sot_lambda / home_shots_lambda, 0.0, 1.0):
                stats["home_sot"] += 1
                if random.random() < home_conversion:
                    stats["home_goals"] += 1
                    events.append({
                        "minute": minute, "team": "home", "type": "goal",
                        "text": f"{minute}' ⚽ GOAL! {home_team} score! ({stats['home_goals']}-{stats['away_goals']})",
                    })
                else:
                    events.append({
                        "minute": minute, "team": "home", "type": "shot_on_target",
                        "text": f"{minute}' 🎯 Shot on target by {home_team}, saved by the keeper!",
                    })
            else:
                events.append({
                    "minute": minute, "team": "home", "type": "shot_off_target",
                    "text": f"{minute}' 📤 Shot off target by {home_team}.",
                })

        if random.random() < per_minute_away_shot:
            stats["away_shots"] += 1
            if random.random() < clamp(away_sot_lambda / away_shots_lambda, 0.0, 1.0):
                stats["away_sot"] += 1
                if random.random() < away_conversion:
                    stats["away_goals"] += 1
                    events.append({
                        "minute": minute, "team": "away", "type": "goal",
                        "text": f"{minute}' ⚽ GOAL! {away_team} score! ({stats['home_goals']}-{stats['away_goals']})",
                    })
                else:
                    events.append({
                        "minute": minute, "team": "away", "type": "shot_on_target",
                        "text": f"{minute}' 🎯 Shot on target by {away_team}, parried away!",
                    })
            else:
                events.append({
                    "minute": minute, "team": "away", "type": "shot_off_target",
                    "text": f"{minute}' 📤 Shot off target by {away_team}.",
                })

        if random.random() < per_minute_corner:
            if random.random() < dominance_home:
                stats["home_corners"] += 1
                events.append({
                    "minute": minute, "team": "home", "type": "corners",
                    "text": f"{minute}' 🚩 Corner kick for {home_team}.",
                })
            else:
                stats["away_corners"] += 1
                events.append({
                    "minute": minute, "team": "away", "type": "corners",
                    "text": f"{minute}' 🚩 Corner kick for {away_team}.",
                })

        if random.random() < per_minute_card_home:
            if random.random() < LIVE_CARD_YELLOW_TO_RED_RATIO:
                stats["home_red"] += 1
                events.append({
                    "minute": minute, "team": "home", "type": "red",
                    "text": f"{minute}' 🟥 SENT OFF! Straight red card for {home_team}!",
                })
            else:
                stats["home_yellow"] += 1
                events.append({
                    "minute": minute, "team": "home", "type": "yellow",
                    "text": f"{minute}' 🟨 Yellow card for {home_team}.",
                })

        if random.random() < per_minute_card_away:
            if random.random() < LIVE_CARD_YELLOW_TO_RED_RATIO:
                stats["away_red"] += 1
                events.append({
                    "minute": minute, "team": "away", "type": "red",
                    "text": f"{minute}' 🟥 SENT OFF! Straight red card for {away_team}!",
                })
            else:
                stats["away_yellow"] += 1
                events.append({
                    "minute": minute, "team": "away", "type": "yellow",
                    "text": f"{minute}' 🟨 Yellow card for {away_team}.",
                })

    possesso_home = round(clamp(50 + (dominance_home - 0.5) * 60, 25, 75))
    possesso_away = 100 - possesso_home

    return {
        "events": events,
        "stats": stats,
        "possesso_home": possesso_home,
        "possesso_away": possesso_away,
        "final_score": f"{stats['home_goals']} - {stats['away_goals']}",
    }


def run_live_match_from_model(model: MatchModel, home: str, away: str) -> dict[str, object]:
    """Prepara i parametri (alpha/beta + lambda di tiri/corner) dal
    MatchModel già calcolato dal motore Dixon-Coles e lancia
    simulate_single_match. I tiri totali per squadra vengono ripartiti dal
    totale di coppia (`shots_total_lambda`) nella stessa proporzione dei tiri
    in porta per squadra (già disponibili separatamente sul MatchModel),
    così la simulazione resta coerente con le medie del match analizzato."""
    sot_sum = model.home_shots_on_target_lambda + model.away_shots_on_target_lambda
    home_share = model.home_shots_on_target_lambda / sot_sum if sot_sum > 0 else 0.5
    home_shots_lambda = model.shots_total_lambda * home_share
    away_shots_lambda = model.shots_total_lambda * (1 - home_share)

    return simulate_single_match(
        home_team=home,
        away_team=away,
        alpha_home=model.home_lambda,
        beta_home=model.home_cards_lambda,
        alpha_away=model.away_lambda,
        beta_away=model.away_cards_lambda,
        home_shots_lambda=home_shots_lambda,
        away_shots_lambda=away_shots_lambda,
        home_sot_lambda=model.home_shots_on_target_lambda,
        away_sot_lambda=model.away_shots_on_target_lambda,
        corners_lambda=model.corners_total_lambda,
    )


# ==============================================================================
# COMPONENTI UI "DARK GAMING / BROADCAST" (restyling estetico riutilizzabile)
# ==============================================================================
# Funzioni di sola presentazione (HTML/CSS via st.markdown): non calcolano
# nulla di nuovo, si limitano a visualizzare in modo più coinvolgente dati
# già prodotti dal motore (MatchModel, simulate_single_match). Pensate per
# essere riutilizzate sia nel Simulatore Live sia nella Dashboard di analisi.
def _stat_bar_percentages(home_value: float, away_value: float) -> tuple[float, float]:
    """Converte due valori grezzi in una coppia di percentuali (somma 100)
    per la larghezza delle due metà della barra di confronto, con un minimo
    visibile del 6% anche quando un lato è a zero."""
    total = home_value + away_value
    if total <= 0:
        return 50.0, 50.0
    home_pct = clamp(home_value / total * 100, 6.0, 94.0)
    return home_pct, 100.0 - home_pct


def render_stat_bar(
    label: str,
    home_value: float,
    away_value: float,
    home_display: str | None = None,
    away_display: str | None = None,
) -> None:
    """Barra di confronto visivo (Visual Stat Bar) fra Casa e Trasferta per
    una singola statistica (tiri, corner, possesso...): la metà più lunga e
    più colorata (verde/azzurro per la Casa, arancione/rosso per la
    Trasferta) è quella della squadra dominante su quella metrica."""
    home_display = home_display if home_display is not None else f"{home_value:g}"
    away_display = away_display if away_display is not None else f"{away_value:g}"
    home_pct, away_pct = _stat_bar_percentages(float(home_value), float(away_value))
    st.markdown(
        '<div class="stat-bar-row">'
        f'<div class="stat-bar-values"><span>{escape(str(home_display))}</span>'
        f'<span>{escape(str(away_display))}</span></div>'
        '<div class="stat-bar-track">'
        f'<div class="stat-bar-home" style="width:{home_pct:.1f}%"></div>'
        f'<div class="stat-bar-away" style="width:{away_pct:.1f}%"></div>'
        '</div>'
        f'<div class="stat-bar-label">{escape(label)}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def broadcast_scoreboard_html(home: str, away: str, home_goals: int, away_goals: int, minute_label: str) -> str:
    """Markup HTML del tabellone stile Match TV/Broadcast: nomi squadra in
    grande, punteggio centrale ad alto impatto e badge minuto animato
    ('LED'). Restituisce la stringa HTML così da poter essere riutilizzata
    sia per un rendering statico (st.markdown) sia per l'aggiornamento
    live di un placeholder durante l'animazione minuto-per-minuto."""
    return (
        '<div class="scoreboard-wrap">'
        f'<div class="scoreboard-team"><div class="scoreboard-team-name">{escape(home)}</div>'
        '<div class="scoreboard-team-tag">🏠 CASA</div></div>'
        '<div class="scoreboard-center">'
        f'<div class="scoreboard-score">{home_goals} - {away_goals}</div>'
        f'<div class="scoreboard-minute-badge">⏱ {escape(minute_label)}</div>'
        '</div>'
        f'<div class="scoreboard-team"><div class="scoreboard-team-name">{escape(away)}</div>'
        '<div class="scoreboard-team-tag">✈️ TRASFERTA</div></div>'
        '</div>'
    )


def render_broadcast_scoreboard(home: str, away: str, home_goals: int, away_goals: int, minute_label: str) -> None:
    """Renderizza il tabellone Match TV/Broadcast (vedi broadcast_scoreboard_html)."""
    st.markdown(broadcast_scoreboard_html(home, away, home_goals, away_goals, minute_label), unsafe_allow_html=True)


def chronicle_feed_html(lines: Sequence[str], reverse: bool = False) -> str:
    """Markup HTML del feed di Cronaca stile Social/Ticker: box con
    scorrimento verticale pulito (scrollbar personalizzata) ed evidenziazione
    cromatica automatica di gol/cartellini in base alle emoji già presenti
    nel testo dell'evento (⚽ GOL, 🟨 GIALLO, 🟥 ROSSO)."""
    ordered = list(reversed(lines)) if reverse else list(lines)
    if not ordered:
        items_html = '<div class="chronicle-item">In attesa del primo episodio da segnalare...</div>'
    else:
        rendered_items = []
        for line in ordered:
            css_class = "chronicle-item"
            if "⚽" in line:
                css_class += " goal"
            elif "🟥" in line:
                css_class += " red"
            elif "🟨" in line:
                css_class += " yellow"
            rendered_items.append(f'<div class="{css_class}">{escape(line)}</div>')
        items_html = "".join(rendered_items)
    return f'<div class="chronicle-feed">{items_html}</div>'


def render_social_share_card(
    title: str,
    headline: str,
    subtitle: str,
    rows: Sequence[tuple[str, str]],
    accent: str = "#00E5FF",
) -> None:
    """📱 'Social Share Card' box: a compact, high-visual-impact card meant
    to be photographed/captured in a screenshot to share on social media —
    summarizes the result/forecast, key stats, and a footer with the app
    name. Content purely derived from data already computed elsewhere
    (MatchModel or simulate_single_match)."""
    rows_html = "".join(
        f'<div class="social-share-row"><span class="social-share-row-label">{escape(label)}</span>'
        f'<span class="social-share-row-value">{escape(value)}</span></div>'
        for label, value in rows
    )
    st.markdown(
        f'<div class="social-share-card" style="--social-accent:{escape(accent)}">'
        f'<div class="social-share-title">📱 Social Share Card</div>'
        f'<div class="social-share-title" style="opacity:.7;margin-top:2px">{escape(title)}</div>'
        f'<div class="social-share-headline">{escape(headline)}</div>'
        f'<div class="social-share-subtitle">{escape(subtitle)}</div>'
        f'<div class="social-share-rows">{rows_html}</div>'
        '<div class="social-share-footer">Powered by WayneLab 🦇📊</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_top_result_highlight_card(score_label: str, probability: float, simulations_count: int) -> None:
    """🏆 HUD reveal card for the 'Top Result' emerging from the 10,000
    Monte Carlo paths: giant gold/neon score front and center, with the
    confidence percentage in evidence — built to be the first thing a
    viewer's eye lands on when the simulation finishes."""
    st.markdown(
        '<div class="mc-highlight-card">'
        '<div class="mc-highlight-label">🏆 TOP RESULT · 10,000 SIMULATIONS</div>'
        f'<div class="mc-highlight-score">{escape(score_label)}</div>'
        f'<div class="mc-highlight-sub">Confidence: {probability:.1%} · {simulations_count:,} / 10,000 paths</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_three_way_probability_bar(
    home_prob: float,
    draw_prob: float,
    away_prob: float,
    home_label: str,
    away_label: str,
) -> None:
    """3-color 1X2 bar (Home green/blue neon · Draw gold · Away
    orange/red), with the percentages engraved directly in the segment
    when there is enough room, otherwise only in the legend."""
    total = max(home_prob + draw_prob + away_prob, 1e-9)
    home_pct = clamp(home_prob / total * 100, 0.0, 100.0)
    draw_pct = clamp(draw_prob / total * 100, 0.0, 100.0)
    away_pct = clamp(100.0 - home_pct - draw_pct, 0.0, 100.0)

    def _segment_text(pct: float) -> str:
        return f"{pct:.0f}%" if pct >= 8.0 else ""

    st.markdown(
        '<div class="three-way-bar-track">'
        f'<div class="three-way-seg three-way-home" style="width:{home_pct:.1f}%">{_segment_text(home_pct)}</div>'
        f'<div class="three-way-seg three-way-draw" style="width:{draw_pct:.1f}%">{_segment_text(draw_pct)}</div>'
        f'<div class="three-way-seg three-way-away" style="width:{away_pct:.1f}%">{_segment_text(away_pct)}</div>'
        '</div>'
        '<div class="three-way-legend">'
        f'<span>🏠 {escape(home_label)} {home_pct:.0f}%</span>'
        f'<span>🤝 Draw {draw_pct:.0f}%</span>'
        f'<span>✈️ {escape(away_label)} {away_pct:.0f}%</span>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_score_frequency_ranking(
    score_frame: pd.DataFrame, reference_probability: float, start_rank: int = 1
) -> None:
    """🏁 Neon ranking bars for the Monte Carlo exact-score frequencies:
    each row is sized relative to `reference_probability` (the single
    highest-probability row overall, i.e. the hero Top Result card's
    score) rather than the max of the rows being rendered here, so that —
    when called on the alternatives below the hero card — the viewer can
    immediately gauge, at a glance, how far behind the top pick they trail."""
    if score_frame.empty:
        return
    reference_probability = max(reference_probability, 1e-9)
    rows_html = []
    for offset, (_, row) in enumerate(score_frame.iterrows()):
        rank = start_rank + offset
        probability = float(row["Probability"])
        bar_pct = clamp(probability / reference_probability * 100, 3.0, 100.0)
        rows_html.append(
            '<div class="score-rank-item">'
            f'<div class="score-rank-badge">#{rank}</div>'
            '<div class="score-rank-body">'
            f'<div class="score-rank-top"><span>{escape(str(row["Exact Score"]))}</span>'
            f'<span>{probability:.1%}</span></div>'
            '<div class="score-rank-track">'
            f'<div class="score-rank-fill" style="width:{bar_pct:.1f}%"></div>'
            '</div></div></div>'
        )
    st.markdown("".join(rows_html), unsafe_allow_html=True)


def compute_micro_events_intel(raw: dict[str, object], outcome_probabilities: dict[str, float]) -> dict[str, float]:
    """Derives the Micro-Events Intel percentages straight from the raw
    per-simulation NumPy arrays already produced by run_simulation (goals,
    corners, cards) plus the already-computed 1X2 frequencies — a pure,
    read-only aggregation layer that does not touch the Monte Carlo engine
    itself. Asian Handicap lines are derived from the simulated goal
    difference (no push scenario at the .5 line, so the two sides are
    exact complements)."""
    home_goals = raw["home_goals"]
    away_goals = raw["away_goals"]
    total_goals = home_goals + away_goals
    goal_diff = home_goals - away_goals
    n = len(total_goals)

    return {
        "over_25_goals": float((total_goals > 2).mean()),
        "btts": float(((home_goals > 0) & (away_goals > 0)).mean()),
        "over_85_corners": float((raw["corners"] > 8).mean()),
        "over_95_corners": float((raw["corners"] > 9).mean()),
        "over_35_cards": float((raw["total_cards"] > 3).mean()),
        "over_45_cards": float((raw["total_cards"] > 4).mean()),
        "ah_home_minus_15": float((goal_diff >= 2).mean()),
        "ah_away_plus_15": float((goal_diff <= 1).mean()),
        "double_chance_1x": outcome_probabilities.get("1 (home win)", 0.0) + outcome_probabilities.get("X (draw)", 0.0),
        "double_chance_12": outcome_probabilities.get("1 (home win)", 0.0) + outcome_probabilities.get("2 (away win)", 0.0),
        "n_simulations": float(n),
    }


def _intel_bar_color(probability: float) -> str:
    """Neon gradient for an Intel bar: brighter/greener the higher the
    probability, shifting toward electric blue for lower readings —
    purely a color mapping, no new statistic involved."""
    if probability >= 0.6:
        return "linear-gradient(90deg, #00e5ff, #00ff87)"
    if probability >= 0.35:
        return "linear-gradient(90deg, #00e5ff, #ffd60a)"
    return "linear-gradient(90deg, #3b4252, #00e5ff)"


def render_intel_card(title: str, metrics: Sequence[tuple[str, float]]) -> None:
    """One 'Micro-Events Intel' card: a title plus one or more neon
    probability bars, each metric rendered large and high-contrast so it
    stays readable even when the dashboard is viewed on a phone screen
    inside a recorded video."""
    rows_html = []
    for label, probability in metrics:
        pct = clamp(probability * 100, 0.0, 100.0)
        rows_html.append(
            '<div class="intel-metric-row">'
            f'<div class="intel-metric-top"><span>{escape(label)}</span>'
            f'<span class="intel-metric-value">{probability:.1%}</span></div>'
            '<div class="intel-bar-track">'
            f'<div class="intel-bar-fill" style="width:{pct:.1f}%;background:{_intel_bar_color(probability)}"></div>'
            '</div></div>'
        )
    st.markdown(
        f'<div class="intel-card"><div class="intel-card-title">{escape(title)}</div>'
        f'{"".join(rows_html)}</div>',
        unsafe_allow_html=True,
    )


def render_micro_events_intel_column(intel: dict[str, float]) -> None:
    """📡 Compact vertical stack of the 4 core Micro-Events Intel cards
    (Over/Under 2.5 Goals, Both Teams to Score, Over Corners, Over Cards),
    built for Column 3 of the single-screen Monte Carlo HUD: no nested
    st.columns, just a lightweight vertical stack that fits one narrow
    column without pushing the page into vertical scroll."""
    render_intel_card("⚽ Over/Under 2.5 Goals", [("Over 2.5 Goals", intel["over_25_goals"])])
    render_intel_card("🥅 Both Teams to Score", [("BTTS / GOAL", intel["btts"])])
    render_intel_card(
        "🚩 Over Corners",
        [
            ("Over 8.5 Corners", intel["over_85_corners"]),
            ("Over 9.5 Corners", intel["over_95_corners"]),
        ],
    )
    render_intel_card(
        "🟨 Over Cards",
        [
            ("Over 3.5 Cards", intel["over_35_cards"]),
            ("Over 4.5 Cards", intel["over_45_cards"]),
        ],
    )


def render_micro_events_intel_grid(intel: dict[str, float], home: str, away: str) -> None:
    """📡 Micro-Events Intel dashboard: a grid of neon cards covering
    Over/Under 2.5 Goals, Both Teams to Score, Corners, Cards, and Asian
    Handicap / Double Chance — all derived from the same 10,000-path Monte
    Carlo output already computed above, laid out for instant at-a-glance
    reading on a recorded video."""
    st.markdown("##### 📡 Micro-Events Intel")
    grid_col_1, grid_col_2, grid_col_3 = st.columns(3)
    with grid_col_1:
        render_intel_card(
            "⚽ Over/Under 2.5 Goals",
            [("Over 2.5 Goals", intel["over_25_goals"])],
        )
    with grid_col_2:
        render_intel_card(
            "🥅 Both Teams to Score",
            [("BTTS / GOAL", intel["btts"])],
        )
    with grid_col_3:
        render_intel_card(
            "🚩 Corners",
            [
                ("Over 8.5 Corners", intel["over_85_corners"]),
                ("Over 9.5 Corners", intel["over_95_corners"]),
            ],
        )
    grid_col_4, grid_col_5 = st.columns(2)
    with grid_col_4:
        render_intel_card(
            "🟨 Cards",
            [
                ("Over 3.5 Cards", intel["over_35_cards"]),
                ("Over 4.5 Cards", intel["over_45_cards"]),
            ],
        )
    with grid_col_5:
        render_intel_card(
            "🎯 Asian Handicap & Double Chance",
            [
                (f"{home} -1.5 AH", intel["ah_home_minus_15"]),
                (f"{away} +1.5 AH", intel["ah_away_plus_15"]),
                ("Double Chance 1X", intel["double_chance_1x"]),
                ("Double Chance 12", intel["double_chance_12"]),
            ],
        )


def render_live_match_tab(model: MatchModel, home: str, away: str) -> None:
    """🎮 Live Match Simulator (FC/FIFA Style): 'Start Match Simulation'
    button that generates and animates ONE single match minute by minute
    (live chronicle + final scoreboard), with the option to replay it
    endlessly via 'Simulate Again'. Entertainment module independent from
    the analytical engine: the reference probabilities remain the
    Poisson/Dixon-Coles ones from the other tabs."""
    st.markdown(
        "### 🎮 Live Match Simulator (FC/FIFA Style)\n"
        "Watch a single match 'play out' minute by minute, with a live "
        "chronicle and a different outcome every time. Expected goals and "
        "cards are calibrated on the same match Global Power Rating — but "
        "this is an illustrative simulation of ONE match, it does not "
        "replace the Poisson/Dixon-Coles/Monte Carlo forecasts from the "
        "other tabs."
    )

    if st.session_state.get("live_match_teams") != (home, away):
        # Selected teams changed: the previous simulation is no longer
        # relevant and must be cleared to avoid showing a scoreboard for a
        # different match than the one currently being analyzed.
        st.session_state.pop("live_match_result", None)
        st.session_state.pop("live_match_chronicle", None)
        st.session_state["live_match_teams"] = (home, away)

    has_previous_result = "live_match_result" in st.session_state
    button_label = "🔄 Simulate Again" if has_previous_result else "▶️ Start Match Simulation"
    run_clicked = st.button(button_label, type="primary", key="live_match_run_button")

    if run_clicked:
        result = run_live_match_from_model(model, home, away)
        events_by_minute: dict[int, list[dict[str, object]]] = {}
        for event in result["events"]:
            events_by_minute.setdefault(int(event["minute"]), []).append(event)

        scoreboard_placeholder = st.empty()
        scoreboard_placeholder.markdown(
            broadcast_scoreboard_html(home, away, 0, 0, "0' LIVE"), unsafe_allow_html=True
        )
        progress_bar = st.progress(0, text="Kick-off! 0'")
        st.markdown("#### 📻 Live Feed")
        ticker = st.empty()
        ticker.markdown(chronicle_feed_html([]), unsafe_allow_html=True)

        chronicle: list[str] = []
        live_home_goals = 0
        live_away_goals = 0
        for minute in range(1, 91):
            for event in events_by_minute.get(minute, []):
                chronicle.append(str(event["text"]))
                if event["type"] == "goal":
                    if event["team"] == "home":
                        live_home_goals += 1
                    else:
                        live_away_goals += 1
            scoreboard_placeholder.markdown(
                broadcast_scoreboard_html(home, away, live_home_goals, live_away_goals, f"{minute}' LIVE"),
                unsafe_allow_html=True,
            )
            progress_bar.progress(minute / 90, text=f"⏱️ Minute {minute}'")
            ticker.markdown(chronicle_feed_html(chronicle[-8:]), unsafe_allow_html=True)
            time.sleep(LIVE_MATCH_ANIMATION_DELAY_SECONDS)
        progress_bar.progress(1.0, text="🏁 Full time! 90'+")
        scoreboard_placeholder.markdown(
            broadcast_scoreboard_html(home, away, live_home_goals, live_away_goals, "FT 90'+"),
            unsafe_allow_html=True,
        )

        st.session_state["live_match_result"] = result
        st.session_state["live_match_chronicle"] = chronicle

    if "live_match_result" not in st.session_state:
        st.info("Press '▶️ Start Match Simulation' to send the two teams onto the pitch.")
        return

    result = st.session_state["live_match_result"]
    stats = result["stats"]

    st.markdown("---")
    st.markdown("## 🏆 Final Scoreboard")
    render_broadcast_scoreboard(home, away, stats["home_goals"], stats["away_goals"], "FT 90'+")

    st.markdown("#### 📊 Stat Comparison")
    render_stat_bar("Total Shots", stats["home_shots"], stats["away_shots"])
    render_stat_bar("Shots on Target", stats["home_sot"], stats["away_sot"])
    render_stat_bar("Corner Kicks", stats["home_corners"], stats["away_corners"])
    render_stat_bar("Yellow Cards", stats["home_yellow"], stats["away_yellow"])
    render_stat_bar("Red Cards", stats["home_red"], stats["away_red"])
    render_stat_bar(
        "Ball Possession",
        result["possesso_home"],
        result["possesso_away"],
        f"{result['possesso_home']}%",
        f"{result['possesso_away']}%",
    )

    with st.expander("📜 Full Chronicle (90 minutes)", expanded=False):
        full_chronicle = st.session_state.get("live_match_chronicle", [])
        st.markdown(chronicle_feed_html(full_chronicle, reverse=True), unsafe_allow_html=True)

    st.markdown("### 📱 Social Share Card")
    social_rows = [
        ("⚽ Scorers", f"{stats['home_goals']} - {stats['away_goals']}"),
        ("🎯 Shots on target", f"{stats['home_sot']} - {stats['away_sot']}"),
        ("🚩 Corners", f"{stats['home_corners']} - {stats['away_corners']}"),
        (
            "🟨🟥 Cards",
            f"{stats['home_yellow'] + stats['home_red']} - {stats['away_yellow'] + stats['away_red']}",
        ),
        ("👟 Ball possession", f"{result['possesso_home']}% - {result['possesso_away']}%"),
    ]
    render_social_share_card(
        title=f"{home} vs {away}",
        headline=result["final_score"],
        subtitle="Live Match Simulation · WayneLab",
        rows=social_rows,
        accent="#00e5ff",
    )

    st.caption(
        "Illustrative minute-by-minute simulation: every run generates a different outcome, "
        "calibrated on the match's expected goals and cards, but it is NOT the source of the "
        "probabilities used in the other tabs (Poisson/Dixon-Coles remain the analytical reference)."
    )


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
    """Value Bet Badge: (label, background_color, text_color).
    - Stake > 0% → 'VALUE BET DETECTED' (green).
    - Stake <= 0% → 'NO VALUE' (neutral gray).
    - No odds entered → badge not shown (None handled by the caller)."""
    if stake_percent is None:
        return "ODDS NOT ENTERED", "#1e293b", "#94a3b8"
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
    "Italy · Serie A": "soccer_italy_serie_a",
    "England · Premier League": "soccer_epl",
    "England · EFL Championship": "soccer_efl_champ",
    "Spain · La Liga": "soccer_spain_la_liga",
    "Germany · Bundesliga": "soccer_germany_bundesliga",
    "France · Ligue 1": "soccer_france_ligue_one",
    "Netherlands · Eredivisie": "soccer_netherlands_eredivisie",
    "Portugal · Primeira Liga": "soccer_portugal_primeira_liga",
    "Europe · UEFA Champions League": "soccer_uefa_champs_league",
    # Best-effort: UEFA Nations League and Friendlies have no stable/common
    # Odds API sport key, so they are deliberately left unmapped — get_live_odds
    # already falls back to manual odds entry for any unmapped league.
    "International · FIFA World Cup": "soccer_fifa_world_cup",
    "International · UEFA European Championship": "soccer_uefa_european_championship",
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
    """'Bookmaker Comparison' table: our algorithm's fair odds (inverse of
    the estimated probability) side by side with the real odds retrieved
    from The Odds API, with the bookmaker offering the highest odds
    highlighted in green (the best value for the bettor)."""
    if not bookmaker_odds:
        return
    best_bookmaker = max(bookmaker_odds, key=bookmaker_odds.get)
    rows_html = [f"<tr><td>🤖 Our algorithm (fair odds)</td><td>{our_fair_odds:.2f}</td></tr>"]
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
        "<thead><tr><th>Source</th><th>Odds</th></tr></thead>"
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
    """List of markets (1X2, Double Chance, Over/Under 1.5-2.5-3.5, Goal/No
    Goal) with their probability, for the high-probability Heatmap. Reuses
    goal_market_probabilities/double_chance_probabilities, already
    consistent with Dixon-Coles."""
    markets = goal_market_probabilities(model)
    dc = double_chance_probabilities(model)
    return [
        {"Market": f"1 · {home}", "Probability": model.home_win_prob},
        {"Market": "X · Draw", "Probability": model.draw_prob},
        {"Market": f"2 · {away}", "Probability": model.away_win_prob},
        {"Market": "1X · Double Chance", "Probability": dc["1X"]},
        {"Market": "X2 · Double Chance", "Probability": dc["X2"]},
        {"Market": "12 · Double Chance", "Probability": dc["12"]},
        {"Market": "Over 1.5", "Probability": markets["total_over"][1.5]},
        {"Market": "Under 1.5", "Probability": 1 - markets["total_over"][1.5]},
        {"Market": "Over 2.5", "Probability": markets["total_over"][2.5]},
        {"Market": "Under 2.5", "Probability": 1 - markets["total_over"][2.5]},
        {"Market": "Over 3.5", "Probability": markets["total_over"][3.5]},
        {"Market": "Under 3.5", "Probability": 1 - markets["total_over"][3.5]},
        {"Market": "Goal (GG)", "Probability": markets["goal_goal"]},
        {"Market": "No Goal (NG)", "Probability": markets["no_goal"]},
        {"Market": f"Over 1.5 {home}", "Probability": markets["home_over"][1.5]},
        {"Market": f"Over 1.5 {away}", "Probability": markets["away_over"][1.5]},
    ]


def top_heatmap_markets(model: MatchModel, home: str, away: str, top_n: int = 5) -> list[dict[str, object]]:
    """Top N markets by descending probability, for the compact visual grid
    at the top of the Value Betting & Heatmap tab."""
    rows = heatmap_market_probabilities(model, home, away)
    return sorted(rows, key=lambda row: row["Probability"], reverse=True)[:top_n]


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
    "No rotation": 0.0,
    "Partial rotation (-3%)": -0.03,
    "Heavy rotation (-7%)": -0.07,
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
    """Alert message ('⚠️ Fatigue Alert: <team> ...') shown when the overall
    attack malus exceeds FATIGUE_ALERT_THRESHOLD (5% in absolute value),
    otherwise None (no badge to display)."""
    if abs(fatigue["attack_malus"]) < FATIGUE_ALERT_THRESHOLD:
        return None
    details = []
    if fatigue["rest_days"] <= 4:
        details.append(f"played {fatigue['rest_days']} days ago")
    if fatigue["has_travel_malus"]:
        details.append("on a European away trip")
    if fatigue["turnover_level"] != "No rotation":
        details.append(f"rotation expected: {fatigue['turnover_level'].split(' (')[0].lower()}")
    detail_text = " · ".join(details) if details else "not at full physical condition"
    return f"⚠️ Fatigue Alert: {team} {detail_text} (attack malus {fatigue['attack_malus']:+.0%})"


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
BET_OUTCOMES = ("Pending", "Won", "Lost")
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
    if outcome == "Won":
        return stake * (odds - 1)
    if outcome == "Lost":
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
    """Recomputes the 'profit' column for every row (e.g. after the user
    manually updated an outcome from 'Pending' to 'Won'/'Lost' in the
    table) and re-persists the updated history."""
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
    settled = df[df["outcome"].isin(["Won", "Lost"])]
    total_staked = float(settled["stake"].sum()) if not settled.empty else 0.0
    total_profit = float(settled["profit"].sum()) if not settled.empty else 0.0
    roi = (total_profit / total_staked * 100) if total_staked > 0 else 0.0
    win_rate = (float((settled["outcome"] == "Won").sum()) / len(settled) * 100) if len(settled) > 0 else 0.0
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
    settled = df[df["outcome"].isin(["Won", "Lost"])].copy()
    if settled.empty:
        return pd.DataFrame({"Bet": [0], "Bankroll (€)": [initial_bankroll]})
    settled = settled.sort_values("timestamp")
    settled["Bankroll (€)"] = initial_bankroll + settled["profit"].astype(float).cumsum()
    settled["Bet"] = range(1, len(settled) + 1)
    timeline = settled[["Bet", "Bankroll (€)"]].reset_index(drop=True)
    starting_point = pd.DataFrame({"Bet": [0], "Bankroll (€)": [initial_bankroll]})
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
    """Builds the text prompt with all the data already computed by the
    engine (Power Rating, xG, 1X2, fatigue, value bets), to pass to the LLM
    to generate the Intelligence Analysis Report."""
    value_bets = [f"{label} (prob. {prob:.0%}, suggested stake {stake:.1f}%)" for label, prob, stake in kelly_rows if stake is not None and stake > 0]
    lines = [
        f"Match: {home} vs {away}.",
        f"Power Rating: {home} {model.home_rating:.0f}, {away} {model.away_rating:.0f}.",
        f"Expected xG: {home} {model.home_lambda:.2f}, {away} {model.away_lambda:.2f}.",
        f"1X2 Probability: 1={model.home_win_prob:.0%} X={model.draw_prob:.0%} 2={model.away_win_prob:.0%}.",
    ]
    if model.manual_factor_home or model.manual_factor_away:
        lines.append(
            f"Manual sliders (Market+Injuries): {home} {model.manual_factor_home:+.0%}, "
            f"{away} {model.manual_factor_away:+.0%}."
        )
    if fatigue_home and abs(float(fatigue_home.get("attack_malus", 0.0))) >= FATIGUE_ALERT_THRESHOLD:
        lines.append(f"Fatigue {home}: attack malus {float(fatigue_home['attack_malus']):+.0%}.")
    if fatigue_away and abs(float(fatigue_away.get("attack_malus", 0.0))) >= FATIGUE_ALERT_THRESHOLD:
        lines.append(f"Fatigue {away}: attack malus {float(fatigue_away['attack_malus']):+.0%}.")
    lines.append("Value bets detected: " + ("; ".join(value_bets) if value_bets else "none at the moment."))
    lines.append(
        "Write a 3-4 key-point Intelligence Analysis Report in English, in natural "
        "and professional language, as a Markdown bullet list, for a user who has "
        "to decide whether to bet on this match. Cover: 1) Power Rating/favorite "
        "comparison, 2) impact of manual sliders/fatigue if present, 3) any value "
        "bets detected, 4) summary of the 1X2/xG forecast. Do not invent data that "
        "was not provided."
    )
    return "\n".join(lines)


def generate_match_summary_ai(prompt: str, provider: str, api_key: str) -> str | None:
    """Attempts to generate the report via LLM (Anthropic/OpenAI/Gemini).
    Returns None for any error (library not installed, network, quota,
    invalid key...), so the caller falls back to the Python template
    without ever crashing the app."""
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
    """Fallback without LLM: generates 3-4 key points in natural language by
    cross-referencing data already computed by the engine, with a
    conditional Python text-template generator (no external calls)."""
    bullets: list[str] = []

    favorite = home if model.home_rating >= model.away_rating else away
    underdog = away if favorite == home else home
    favorite_rating = model.home_rating if favorite == home else model.away_rating
    underdog_rating = model.away_rating if favorite == home else model.home_rating
    bullets.append(
        f"**Power Rating**: {favorite} is favored with a Power Rating of {favorite_rating:.0f} "
        f"against {underdog_rating:.0f} for {underdog}."
    )

    impact_notes = []
    if model.manual_factor_home:
        impact_notes.append(f"{home} (slider {model.manual_factor_home:+.0%})")
    if model.manual_factor_away:
        impact_notes.append(f"{away} (slider {model.manual_factor_away:+.0%})")
    if fatigue_home and abs(float(fatigue_home.get("attack_malus", 0.0))) >= FATIGUE_ALERT_THRESHOLD:
        impact_notes.append(f"{home} fatigued (attack malus {float(fatigue_home['attack_malus']):+.0%})")
    if fatigue_away and abs(float(fatigue_away.get("attack_malus", 0.0))) >= FATIGUE_ALERT_THRESHOLD:
        impact_notes.append(f"{away} fatigued (attack malus {float(fatigue_away['attack_malus']):+.0%})")
    if impact_notes:
        bullets.append("**Absences / Market / Fatigue**: keep an eye on " + ", ".join(impact_notes) + ".")
    else:
        bullets.append("**Absences / Market / Fatigue**: no significant manual adjustment applied.")

    value_bets = [
        f"'{label}' odds entered, estimated probability {prob:.0%}, suggested stake {stake:.1f}%"
        for label, prob, stake in kelly_rows
        if stake is not None and stake > 0
    ]
    if value_bets:
        bullets.append("**Value Bets detected**: " + "; ".join(value_bets) + ".")
    else:
        bullets.append("**Value Bets**: no odds entered or no edge detected at the moment in the Value Betting tab.")

    total_goals = model.home_lambda + model.away_lambda
    bullets.append(
        f"**Forecast**: 1={model.home_win_prob:.0%} · X={model.draw_prob:.0%} · 2={model.away_win_prob:.0%}, "
        f"with a combined expected xG of {total_goals:.2f} goals."
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
    """Returns (report_text, source) where source is 'AI (<provider>)' or
    'Python Template'. Tries the LLM first if an API key is configured;
    without a key, or on any error, it automatically falls back to the
    template generator — the app never gets stuck."""
    api = _get_llm_api_key()
    if api is not None:
        provider, api_key = api
        prompt = build_match_summary_prompt(model, home, away, fatigue_home, fatigue_away, kelly_rows)
        ai_text = generate_match_summary_ai(prompt, provider, api_key)
        if ai_text:
            return ai_text, f"AI ({provider})"
    return generate_match_summary_template(model, home, away, fatigue_home, fatigue_away, kelly_rows), "Python Template"


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


def render_match_banner_compact(league: str, home: str, away: str, crests: dict[str, str]) -> None:
    """🦇 Compact Gotham-style Match Banner: a self-contained obsidian card
    with the league name and the Home vs Away team names/crests. Meant to
    be dropped at the top of a tab (e.g. Monte Carlo Simulator) so the
    match context stays visible even if a screen recording starts mid-page
    or is cropped to a single tab, without depending on the shared page
    header higher up. For national-team competitions, adds a small
    'INTERNATIONAL' badge next to the competition name and swaps the
    missing-crest placeholder from a club shield to a globe (flags come
    from the same `crests` map — Football-Data.org returns flag images for
    national teams through the identical /teams endpoint used for clubs)."""
    is_national = is_national_team_competition(league)
    placeholder_icon = "🌍" if is_national else "🛡️"
    home_crest = crests.get(home)
    away_crest = crests.get(away)
    home_crest_html = (
        f'<img src="{escape(home_crest)}" class="mc-match-banner-crest" />'
        if home_crest
        else f'<div class="mc-match-banner-crest-placeholder">{placeholder_icon}</div>'
    )
    away_crest_html = (
        f'<img src="{escape(away_crest)}" class="mc-match-banner-crest" />'
        if away_crest
        else f'<div class="mc-match-banner-crest-placeholder">{placeholder_icon}</div>'
    )
    international_badge_html = (
        '<span class="mc-prematch-badge" style="margin-left:6px">🌍 INTERNATIONAL</span>'
        if is_national
        else ""
    )
    st.markdown(
        '<div class="mc-match-banner">'
        f'<div class="mc-match-banner-league">{escape(league)}{international_badge_html}</div>'
        '<div class="mc-match-banner-row">'
        f'<div class="mc-match-banner-team">{home_crest_html}'
        f'<div class="mc-match-banner-name">{escape(home)}</div></div>'
        '<div class="mc-match-banner-vs">VS</div>'
        f'<div class="mc-match-banner-team">{away_crest_html}'
        f'<div class="mc-match-banner-name">{escape(away)}</div></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )


def _form_badge_html(result_letter: str, *, pill: bool = False) -> str:
    """Renders a single colored W/D/L badge: green 'W' (win), grey 'D'
    (draw), red 'L' (loss). `pill=True` produces the wider rounded-pill
    variant used in the Team Form & H2H tables; the default compact square
    variant is used in the Monte Carlo Pre-Match HUD strip."""
    css_class = {"W": "form-badge-w", "D": "form-badge-d", "L": "form-badge-l"}.get(result_letter, "form-badge-d")
    shape_class = "h2h-result-pill" if pill else "form-badge"
    return f'<span class="{shape_class} {css_class}">{escape(result_letter)}</span>'


def render_pre_match_stats_hud(
    model: MatchModel,
    home: str,
    away: str,
    home_form: tuple[str, ...] = (),
    away_form: tuple[str, ...] = (),
) -> None:
    """🛰️ Pre-Match Stats & Parameters HUD: a compact WayneLab panel shown
    right above the Run button with each team's expected goals (xG), a row
    of status badges for the engine parameters actually in play for this
    MatchModel, and a Recent Form (Last 5 Games) strip with colored W/D/L
    badges for both teams. Every value is read directly off the
    already-computed MatchModel / LiveTeamStats — no new calculation,
    purely a compact display layer so the pre-simulation screen carries
    real analytical content instead of empty space."""
    badges = ["Model: Dixon-Coles", "Iterations: 10,000", "Home Factor: Active"]
    if model.manual_factor_home or model.manual_factor_away:
        badges.append("Manual Sliders: Active")
    if model.fatigue_attack_malus_home or model.fatigue_attack_malus_away:
        badges.append("Fatigue Adj: Active")
    if model.early_season_warning:
        badges.append("Early Season Mode: Active")
    badges_html = "".join(f'<span class="mc-prematch-badge">{escape(badge)}</span>' for badge in badges)

    home_form_html = "".join(_form_badge_html(letter) for letter in home_form) or '<span class="form-strip-label">n/a</span>'
    away_form_html = "".join(_form_badge_html(letter) for letter in away_form) or '<span class="form-strip-label">n/a</span>'

    st.markdown(
        '<div class="mc-prematch-hud">'
        '<div class="mc-prematch-xg-row">'
        f'<div class="mc-prematch-xg-item"><div class="mc-prematch-xg-label">{escape(home)} xG</div>'
        f'<div class="mc-prematch-xg-value">{model.home_lambda:.2f}</div></div>'
        '<div class="mc-prematch-xg-divider">VS</div>'
        f'<div class="mc-prematch-xg-item"><div class="mc-prematch-xg-label">{escape(away)} xG</div>'
        f'<div class="mc-prematch-xg-value">{model.away_lambda:.2f}</div></div>'
        '</div>'
        f'<div class="mc-prematch-badges">{badges_html}</div>'
        '<div class="form-strip-row">'
        '<div class="form-strip-team">'
        f'<div class="form-strip-label">{escape(home)} · Last 5</div>'
        f'<div class="form-strip-badges">{home_form_html}</div>'
        '</div>'
        '<div class="form-strip-team">'
        f'<div class="form-strip-label">{escape(away)} · Last 5</div>'
        f'<div class="form-strip-badges">{away_form_html}</div>'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_monte_carlo_computing_hud(total_paths: int = 10_000, duration_seconds: float = 2.6) -> None:
    """⚙️ 'Computing' HUD shown while the 10,000 Monte Carlo paths run: a
    canvas-based digital-rain backdrop (Electric Blue glyphs) with an
    overlaid live counter racing from 0 to `total_paths` ('1,000... 5,000...
    10,000 paths calculated') and a neon green→blue progress bar underneath,
    built to hook a viewer's attention in the first seconds of a screen
    recording. Rendered through streamlit.components.v1.html — plain
    st.markdown strips <script> tags, so components.html is required for
    the animation to actually execute. The whole count-up is timed inside
    the embedded JavaScript so it runs smoothly without per-frame Streamlit
    reruns; Python only sleeps for the matching duration before clearing the
    placeholder. Purely a visual flourish: it never affects, delays, or
    replaces any part of the actual simulation logic, which runs instantly
    via NumPy right after this animation completes."""
    placeholder = st.empty()
    duration_ms = int(duration_seconds * 1000)
    with placeholder:
        components.html(
            f"""
            <div class="mc-hud-wrap" style="height:190px;">
              <canvas id="matrixCanvas" style="display:block;width:100%;height:190px;"></canvas>
              <div class="mc-hud-overlay">
                <div class="mc-hud-label">⚙️ RUNNING MONTE CARLO ENGINE</div>
                <div class="mc-hud-counter" id="mcCounter">0</div>
                <div class="mc-hud-sub" id="mcSub">paths calculated</div>
                <div class="mc-hud-track"><div class="mc-hud-fill" id="mcFill"></div></div>
              </div>
            </div>
            <script>
            const canvas = document.getElementById('matrixCanvas');
            const ctx = canvas.getContext('2d');
            function resizeCanvas() {{
                canvas.width = canvas.clientWidth;
                canvas.height = canvas.clientHeight;
            }}
            resizeCanvas();
            window.addEventListener('resize', resizeCanvas);
            const glyphs = '01λβαΣΔ⚽01λβαΣΔ01';
            const fontSize = 14;
            let columns = Math.floor(canvas.width / fontSize) || 20;
            let drops = new Array(columns).fill(1);
            function drawRain() {{
                ctx.fillStyle = 'rgba(5,5,5,0.18)';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = '#00E5FF';
                ctx.font = fontSize + 'px monospace';
                for (let i = 0; i < drops.length; i++) {{
                    const glyph = glyphs[Math.floor(Math.random() * glyphs.length)];
                    ctx.fillText(glyph, i * fontSize, drops[i] * fontSize);
                    if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {{
                        drops[i] = 0;
                    }}
                    drops[i]++;
                }}
            }}
            setInterval(drawRain, 45);

            const totalPaths = {total_paths};
            const durationMs = {duration_ms};
            const counterEl = document.getElementById('mcCounter');
            const fillEl = document.getElementById('mcFill');
            const startTime = performance.now();
            function tickCounter(now) {{
                const elapsed = now - startTime;
                const progress = Math.min(elapsed / durationMs, 1);
                const eased = 1 - Math.pow(1 - progress, 2);
                const current = Math.floor(eased * totalPaths);
                counterEl.textContent = current.toLocaleString('en-US');
                fillEl.style.width = (eased * 100).toFixed(0) + '%';
                if (progress < 1) {{
                    requestAnimationFrame(tickCounter);
                }} else {{
                    counterEl.textContent = totalPaths.toLocaleString('en-US');
                    fillEl.style.width = '100%';
                }}
            }}
            requestAnimationFrame(tickCounter);
            </script>
            """,
            height=190,
        )
    time.sleep(duration_seconds)
    placeholder.empty()


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
            "Exact Score": f"{h_goal}-{a_goal}",
            "Simulations": int(round(weight)),
            "Probability": weight / total_weight,
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
        {"Outcome": "1 (home win)", "Simulations": int(round(home_wins)), "Probability": home_wins / total_weight},
        {"Outcome": "X (draw)", "Simulations": int(round(draws)), "Probability": draws / total_weight},
        {"Outcome": "2 (away win)", "Simulations": int(round(away_wins)), "Probability": away_wins / total_weight},
    ]

    key_events = [
        ("Over 2.5 Goals", home_goals + away_goals > 2),
        ("Over 8.5 Corners", corners > 8),
        ("Over 22.5 Total Shots", total_shots > 22),
        ("Home Over 4.5 Shots on Target", home_sot > 4),
        ("Away Over 3.5 Shots on Target", away_sot > 3),
        ("Over 3.5 Cards", total_cards > 3),
        ("Over 24.5 Fouls", fouls > 24),
    ]
    event_rows = [
        {
            "Simulated Micro-Event": name,
            "Frequency": int(mask.sum()),
            "Probability": float(mask.mean()),
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
    headers = ["Micro-Event", "Threshold", "Expected Value", "Probability", "Fair Odds"]
    table_rows = []
    for _, row in frame.iterrows():
        probability = float(row["Probability"])
        row_style = (
            ' style="background:#39ff14;color:#061a0e;font-weight:700"'
            if probability > 0.8
            else ""
        )
        cells = [
            escape(str(row["Micro-Event"])),
            escape(str(row["Threshold"])),
            f"{float(row['Expected Value']):.2f}",
            f"{probability:.1%}",
            f"{float(row['Fair Odds']):.2f}",
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
    header_html = "".join(f"<th>{escape(header)}</th>" for header in ["Outcome", "Probability", "Fair Odds"])
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
    """Builds the MatchModel (the single simulation engine) handling
    missing/identical teams or unavailable Football-Data.org data
    uniformly. Returns (None, error_message) if there are problems."""
    if not home or not away:
        return None, "Load the teams from Football-Data.org to get started."
    if home == away:
        return None, "Select two different teams."
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
        return None, f"Football-Data.org data unavailable: {error}"
    return model, ""


def render_login() -> None:
    st.markdown(
        "### 🦇 Restricted Access\n"
        "Enter the password to access the Poisson and Monte Carlo analysis engine."
    )
    with st.form("login_form", clear_on_submit=False):
        password = st.text_input(
            "Access Password",
            type="password",
            placeholder="Enter the password",
        )
        submitted = st.form_submit_button("Log In", type="primary")
    if submitted:
        if password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid password. The dashboard data remains hidden.")


def render_sidebar_controls() -> dict[str, object]:
    """Manual sidebar sliders: Market Factor (-20%/+20%) and Injury/Missing
    Starters Impact (-30%/+30%), for home and away, plus the Fatigue &
    Rotation Index (Phase 2). Values increase/decrease the Power Index and
    expected attack/defense BEFORE the xG, shots and probability calculation
    (see build_match_model)."""
    st.markdown("### 💼 Market Impact / Expectations")
    st.caption("Major signings or departures relative to the season average.")
    market_factor_home = (
        st.slider("Home Market Factor", -20, 20, 0, format="%d%%", key="market_factor_home") / 100
    )
    market_factor_away = (
        st.slider("Away Market Factor", -20, 20, 0, format="%d%%", key="market_factor_away") / 100
    )

    st.markdown("### 🩹 Injuries / Missing Starters Impact")
    st.caption("Heavy absences relative to the usual starting lineup.")
    injury_factor_home = (
        st.slider("Home Injury Impact", -30, 30, 0, format="%d%%", key="injury_factor_home") / 100
    )
    injury_factor_away = (
        st.slider("Away Injury Impact", -30, 30, 0, format="%d%%", key="injury_factor_away") / 100
    )

    st.markdown("### 🩺 Fatigue & Midweek Fixtures")
    with st.expander("Fatigue & Midweek Fixtures", expanded=False):
        st.caption(
            "Rest days, European away trips and expected rotation: these ADD "
            "to the Market/Absences sliders above, without overriding them."
        )
        col_rest_home, col_rest_away = st.columns(2)
        with col_rest_home:
            rest_days_home = st.slider(
                "Home Rest Days", 2, 7, 7, key="rest_days_home",
                help="7 = 7 or more rest days (no malus).",
            )
        with col_rest_away:
            rest_days_away = st.slider(
                "Away Rest Days", 2, 7, 7, key="rest_days_away",
                help="7 = 7 or more rest days (no malus).",
            )

        col_travel_home, col_travel_away = st.columns(2)
        with col_travel_home:
            travel_home = st.checkbox(
                "Tiring European Away Trip · Home", key="travel_home",
            )
        with col_travel_away:
            travel_away = st.checkbox(
                "Tiring European Away Trip · Away", key="travel_away",
            )

        col_turnover_home, col_turnover_away = st.columns(2)
        with col_turnover_home:
            turnover_home = st.selectbox(
                "Expected Rotation · Home", options=list(TURNOVER_LEVELS), key="turnover_home",
            )
        with col_turnover_away:
            turnover_away = st.selectbox(
                "Expected Rotation · Away", options=list(TURNOVER_LEVELS), key="turnover_away",
            )

    st.markdown("### 🎲 The Odds API (real odds)")
    with st.expander("Automatic bookmaker odds retrieval", expanded=False):
        st.caption(
            "Enter a free API Key from [The Odds API](https://the-odds-api.com) "
            "to automatically pull real bookmaker odds into the Kelly "
            "Calculator. Without a key, or if the call fails, manual odds "
            "entry stays available — the app never breaks."
        )
        odds_api_key = st.text_input(
            "The Odds API Key",
            type="password",
            key="odds_api_key",
            placeholder="Leave empty to enter odds manually",
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
    league_tag_text = f"🌍 {league}" if is_national_team_competition(league) else league
    st.markdown(f'<div class="league-tag">{escape(league_tag_text)}</div>', unsafe_allow_html=True)
    col_home, col_vs, col_away = st.columns([2, 0.6, 2])
    with col_home:
        if crests.get(home):
            st.image(crests[home], width=84)
        st.markdown(f'<div class="team-name">{escape(home)}</div>', unsafe_allow_html=True)
        st.caption("Home")
    with col_vs:
        st.markdown('<div class="vs-badge">VS</div>', unsafe_allow_html=True)
    with col_away:
        if crests.get(away):
            st.image(crests[away], width=84)
        st.markdown(f'<div class="team-name">{escape(away)}</div>', unsafe_allow_html=True)
        st.caption("Away")


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
            "No Value Bet detected at the moment: enter the real bookmaker "
            "odds in the Kelly Calculator below to activate the ranking."
        )
        return

    best = ranked_bets[0]
    ev_text = f"{best['ev']:+.1f}%" if best["ev"] is not None else "n/a"
    st.markdown(
        '<div style="background:linear-gradient(135deg,#f59e0b,#facc15);color:#1c1300;'
        'border-radius:16px;padding:18px 22px;margin-bottom:18px;'
        'box-shadow:0 6px 20px rgba(245,158,11,.35)">'
        '<div style="font-size:1rem;font-weight:800;letter-spacing:.03em">'
        '👑 BEST VALUE BET OF THE MATCH</div>'
        f'<div style="font-size:1.5rem;font-weight:800;margin-top:6px">{escape(str(best["label"]))}</div>'
        '<div style="margin-top:8px;font-weight:600;font-size:.95rem">'
        f'Odds {best["odds"]:.2f} · Algorithm probability {best["probability"]:.1%} · '
        f'Expected Value {ev_text} · <u>Suggested stake {best["stake"]:.1f}%</u>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    if len(ranked_bets) > 1:
        st.markdown("##### 📋 Other Value Bets detected (ranked by Kelly Stake)")
        ranking_frame = pd.DataFrame(
            [
                {
                    "Market": row["label"],
                    "Odds": f"{row['odds']:.2f}",
                    "Probability": f"{row['probability']:.1%}",
                    "Expected Value": f"{row['ev']:+.1f}%" if row["ev"] is not None else "n/a",
                    "Kelly Stake": f"{row['stake']:.1f}%",
                }
                for row in ranked_bets[1:]
            ]
        )
        st.dataframe(ranking_frame, use_container_width=True, hide_index=True)
    st.markdown("---")


def render_value_betting_tab(model: MatchModel, home: str, away: str, league: str, odds_api_key: str) -> None:
    """PHASE 1: VALUE BETTING & UX — High-probability markets Heatmap
    + Kelly Criterion Calculator (Quarter Kelly), with automatic retrieval
    of real odds from The Odds API (manual fallback if absent/failing).
    Purely additive extension: only reads the MatchModel already computed
    by the existing engine."""
    ranked_bets = rank_value_bets(compute_kelly_rows_detailed(model, home, away))
    render_best_value_bet_box(ranked_bets)

    st.markdown(
        "### 🟩 High-Probability Markets Heatmap\n"
        "The 5 most likely markets for this match, calculated from the same "
        "Poisson + Dixon-Coles matrix used in the other tabs. "
        "🟩 ≥70% · 🟧 50-69% · 🟥 <50%."
    )
    top_markets = top_heatmap_markets(model, home, away, top_n=5)
    heatmap_cols = st.columns(len(top_markets))
    for col, row in zip(heatmap_cols, top_markets):
        with col:
            _render_heatmap_cell(row["Market"], row["Probability"], big=True)

    with st.expander("Full markets grid (1X2, Double Chance, Over/Under, Goal/No Goal)"):
        all_rows = heatmap_market_probabilities(model, home, away)
        grid_cols = st.columns(4)
        for index, row in enumerate(all_rows):
            with grid_cols[index % 4]:
                _render_heatmap_cell(row["Market"], row["Probability"])

    st.markdown("---")
    st.markdown(
        "### 💰 Kelly Criterion Calculator (Quarter Kelly)\n"
        "With a The Odds API key entered in the sidebar, the best available "
        "odds are automatically retrieved and proposed for each market — "
        "still fully editable by hand. Without a key (or if retrieval "
        "fails) enter the real odds manually: if our algorithm's "
        "probability exceeds the one implied by the odds, the suggested "
        "stake (25% of full Kelly) will be positive — otherwise there is no "
        "edge (**NO VALUE**)."
    )
    if odds_api_key:
        st.caption("🎲 The Odds API connected: automatic retrieval active for available markets.")

    header_cols = st.columns([2.4, 1, 1.1, 2.5])
    header_cols[0].caption("Market")
    header_cols[1].caption("Algorithm Probability")
    header_cols[2].caption("Bookmaker Odds")
    header_cols[3].caption("Kelly Outcome")

    for key, label, probability in _kelly_market_definitions(model, home, away):
        live_odds = get_live_odds(home, away, key, league, odds_api_key) if odds_api_key else None
        best_live_odds = max(live_odds.values()) if live_odds else None

        odds_input_key = f"{key}_odds"
        if best_live_odds is not None and odds_input_key not in st.session_state:
            # Pre-fills the manual input with the best odds retrieved
            # automatically, WITHOUT overwriting a value already entered by
            # the user in a previous session — it stays fully editable.
            st.session_state[odds_input_key] = round(best_live_odds, 2)

        col_label, col_prob, col_odds, col_badge = st.columns([2.4, 1, 1.1, 2.5])
        with col_label:
            st.markdown(f"**{label}**")
            if best_live_odds is not None:
                st.caption(f"🎲 Auto from The Odds API: {best_live_odds:.2f}")
        with col_prob:
            st.markdown(f"{probability:.1%}")
        with col_odds:
            odds = st.number_input(
                "Odds",
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
                st.caption("Enter odds to calculate the stake")
            else:
                detail = f"Suggested stake: {stake:.1f}%" if stake > 0 else "Odds skewed in favor of the bookmaker"
                st.markdown(
                    f'<div style="background:{bg};color:{text_color};border-radius:8px;'
                    f'padding:6px 10px;font-weight:700;text-align:center">{badge_label}'
                    f'<br><span style="font-size:.82rem;font-weight:500">{detail}</span></div>',
                    unsafe_allow_html=True,
                )

        if live_odds:
            with st.expander(f"📊 Bookmaker Comparison — {label}"):
                render_bookmaker_comparison_table(fair_odds(probability), live_odds)

    st.caption(
        f"Fractional Kelly Stake = ((Probability × Odds) - 1) / (Odds - 1) × 100, "
        f"scaled to {KELLY_FRACTION:.0%} (Quarter Kelly) to contain bankroll variance."
    )


def render_match_executive_summary(
    model: MatchModel,
    home: str,
    away: str,
    fatigue_home: dict[str, object] | None,
    fatigue_away: dict[str, object] | None,
) -> None:
    """🤖 Intelligence Analysis Report: expander at the top of the match
    page with 3-4 key points in natural language, generated via LLM if an
    API key is configured, otherwise via a Python template (transparent
    automatic fallback — requires no action from the user)."""
    kelly_rows = compute_kelly_rows_from_session(model, home, away)
    with st.expander("🤖 Intelligence Analysis Report", expanded=True):
        summary_text, source = generate_match_executive_summary(model, home, away, fatigue_home, fatigue_away, kelly_rows)
        st.markdown(summary_text)
        st.caption(f"Generated by: {source} · updated based on Power Rating, manual sliders and entered odds.")


def render_bankroll_tab() -> None:
    """📊 Bankroll & History Management: Initial Bankroll, new-bet form,
    history persisted to file (CSV/JSON), ROI/Yield/Win Rate metrics and a
    bankroll trend chart. Module independent from the simulation engine
    (does not read Power Rating/Dixon-Coles/manual sliders)."""
    st.markdown(
        "### 📊 Bankroll & History Management\n"
        "Track your placed bets and monitor ROI, Win Rate and bankroll "
        "trend over time. The history is saved to file and does not reset "
        "when you reload the page."
    )

    config = load_bankroll_config()
    initial_bankroll = st.number_input(
        "Initial Bankroll (€)",
        min_value=0.0,
        value=float(config["initial_bankroll"]),
        step=50.0,
        key="initial_bankroll_input",
    )
    if initial_bankroll != config["initial_bankroll"]:
        save_bankroll_config(initial_bankroll)

    st.markdown("---")
    st.markdown("##### ➕ Log a new bet")
    with st.form("new_bet_form", clear_on_submit=True):
        col_league, col_match = st.columns(2)
        with col_league:
            bet_league = st.selectbox("League", options=list(FOOTBALL_DATA_COMPETITIONS), key="bet_league")
        with col_match:
            bet_match = st.text_input("Match", placeholder="e.g. Inter - Cagliari", key="bet_match")

        col_market, col_odds, col_outcome = st.columns(3)
        with col_market:
            bet_market = st.text_input("Market / Pick", placeholder="e.g. 1, Over 2.5", key="bet_market")
        with col_odds:
            bet_odds = st.number_input("Odds", min_value=1.01, value=1.90, step=0.05, key="bet_odds")
        with col_outcome:
            bet_outcome = st.selectbox("Outcome", options=BET_OUTCOMES, key="bet_outcome")

        col_stake_type, col_stake_value = st.columns(2)
        with col_stake_type:
            stake_type = st.radio("Stake In", options=["€", "% Bankroll (Kelly)"], horizontal=True, key="bet_stake_type")
        with col_stake_value:
            if stake_type == "€":
                stake_amount = st.number_input("Stake (€)", min_value=0.0, value=10.0, step=1.0, key="bet_stake_eur")
            else:
                stake_percent = st.number_input("Stake (% bankroll)", min_value=0.0, value=2.0, step=0.5, key="bet_stake_pct")
                current_bankroll_for_stake = bankroll_metrics(load_bankroll_log(), initial_bankroll)["current_bankroll"]
                stake_amount = current_bankroll_for_stake * stake_percent / 100

        submitted = st.form_submit_button("Log Bet", type="primary")
        if submitted:
            if not bet_match or not bet_market:
                st.warning("Enter at least Match and Market before logging the bet.")
            else:
                append_bet(bet_league, bet_match, bet_market, bet_odds, stake_amount, stake_type, bet_outcome)
                st.success(f"Bet logged: {bet_match} · {bet_market} · stake {stake_amount:.2f}€")
                st.rerun()

    st.markdown("---")
    log_df = load_bankroll_log()

    if log_df.empty:
        st.info("No bets logged yet. Use the form above to start tracking your history.")
        return

    st.markdown("##### ✏️ Bet history (edit the outcome to update ROI/Bankroll)")
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
    st.markdown("##### 📈 Financial Metrics")
    col_pnl, col_roi, col_winrate, col_bankroll = st.columns(4)
    with col_pnl:
        st.metric("Total Profit/Loss", f"{metrics['total_profit']:+.2f} €")
    with col_roi:
        st.metric("ROI", f"{metrics['roi']:+.1f}%")
    with col_winrate:
        st.metric("Win Rate", f"{metrics['win_rate']:.1f}%", help=f"Out of {metrics['settled_count']} settled bets")
    with col_bankroll:
        st.metric("Current Bankroll", f"{metrics['current_bankroll']:.2f} €", delta=f"{metrics['total_profit']:+.2f} €")

    st.markdown("##### 📉 Bankroll Trend")
    timeline = bankroll_timeline(edited_df, initial_bankroll)
    st.line_chart(timeline.set_index("Bet"))


def render_dashboard(sidebar_values: dict[str, float]) -> None:
    st.markdown(
        "### Match Settings\n"
        "Teams, fixtures and results are fetched directly from "
        "Football-Data.org. These are not bookmaker odds."
    )

    col_league, col_home, col_away = st.columns(3)
    with col_league:
        league = st.selectbox(
            "League",
            options=list(FOOTBALL_DATA_COMPETITIONS),
            key="league_select",
        )

    try:
        team_rows = fetch_league_teams(league)
    except FootballDataError as error:
        st.error(f"Football-Data.org unavailable: {error}")
        team_rows = ()

    teams = [name for _, name in team_rows]

    if len(teams) < 2:
        with col_home:
            st.selectbox("Home Team", options=teams, disabled=True)
        with col_away:
            st.selectbox("Away Team", options=teams, disabled=True)
        st.warning("Football-Data.org did not return two available teams.")
        return

    # If the league changed, reset the team selections to their default values.
    if st.session_state.get("_last_league") != league:
        st.session_state["_last_league"] = league
        st.session_state["home_select"] = teams[0]
        st.session_state["away_select"] = teams[1]

    with col_home:
        home = st.selectbox("Home Team", options=teams, key="home_select")
    with col_away:
        away = st.selectbox("Away Team", options=teams, key="away_select")

    try:
        status_text = (
            f"Football-Data.org: {len(teams)} teams loaded · "
            f"{competition_season_status(league)}. "
            "Micro-events estimated on league baseline."
        )
        st.info(status_text)
    except FootballDataError as error:
        st.warning(f"Season status unavailable: {error}")

    try:
        calendar = calendar_frame(league)
    except FootballDataError as error:
        st.error(f"Football-Data.org fixtures unavailable: {error}")
        calendar = pd.DataFrame(columns=["Date", "Status", "Home", "Away"])

    with st.expander("📅 2026/27 Season Fixtures", expanded=False):
        st.dataframe(calendar, use_container_width=True, hide_index=True)

    if home == away:
        st.info("Select two different teams to start the analysis.")
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
        fatigue_home=sidebar_values.get("fatigue_home"),
        fatigue_away=sidebar_values.get("fatigue_away"),
    )

    if model is None:
        st.error(error_message)
        return

    # --- 🤖 Intelligence Analysis Report (Phase 3b), at the top of the match page --
    render_match_executive_summary(
        model, home, away, sidebar_values.get("fatigue_home"), sidebar_values.get("fatigue_away")
    )

    # --- Early Season Mode warning (yellow badge/warning) -----------------
    if model.early_season_warning:
        st.warning(
            "⚠️ Reduced-confidence analysis - Early Season in progress  \n"
            f"{home}: {model.home_current_season_matches} matches played · "
            f"{away}: {model.away_current_season_matches} matches played "
            f"(full-confidence threshold: {EARLY_SEASON_MATCHDAY_THRESHOLD}). "
            "The Power Index is being blended with still-partial real data."
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

    # --- 1X2 highlight display (st.metric across 3 columns) --------------
    col_1x2_home, col_1x2_draw, col_1x2_away = st.columns(3)
    with col_1x2_home:
        st.metric(f"🏠 {home} Win", f"{model.home_win_prob:.1%}")
    with col_1x2_draw:
        st.metric("🤝 Draw", f"{model.draw_prob:.1%}")
    with col_1x2_away:
        st.metric(f"✈️ {away} Win", f"{model.away_win_prob:.1%}")

    # --- Clean visual cards for micro-event estimates -----------------------
    total_goals_lambda = model.home_lambda + model.away_lambda
    over_25 = over_probability(total_goals_lambda, 2.5)
    metric_cards = [
        (f"Global Power Rating {home}", f"{model.home_rating:.0f}"),
        (f"Global Power Rating {away}", f"{model.away_rating:.0f}"),
        ("Home xG", f"{model.home_lambda:.2f}"),
        ("Away xG", f"{model.away_lambda:.2f}"),
        ("Total Shots", f"{model.shots_total_lambda:.1f}"),
        ("Shots on Target (match)", f"{model.shots_on_target_total_lambda:.1f}"),
        ("Total Corners", f"{model.corners_total_lambda:.1f}"),
        ("Total Cards", f"{model.cards_total_lambda:.1f}"),
        ("Over 2.5 Goals", f"{over_25:.1%}"),
        ("Under 2.5 Goals", f"{1 - over_25:.1%}"),
    ]
    render_metric_cards(metric_cards, columns=5)

    note = escape(model.engine_note) if model.engine_note else "Global Power Rating calculated."
    st.caption(note)

    if model.home_win_prob >= model.away_win_prob and model.home_win_prob >= model.draw_prob:
        pronostico_headline = f"🏆 Favorite: {home} ({model.home_win_prob:.0%})"
        pronostico_accent = "#00e5ff"
    elif model.away_win_prob > model.home_win_prob and model.away_win_prob >= model.draw_prob:
        pronostico_headline = f"🏆 Favorite: {away} ({model.away_win_prob:.0%})"
        pronostico_accent = "#00e5ff"
    else:
        pronostico_headline = f"🤝 Even Match: Draw {model.draw_prob:.0%}"
        pronostico_accent = "#00e5ff"

    render_social_share_card(
        title=f"{home} vs {away}",
        headline=pronostico_headline,
        subtitle="WayneLab Forecast · Poisson + Dixon-Coles Correction",
        rows=[
            (f"🏠 {home} Win", f"{model.home_win_prob:.0%}"),
            ("🤝 Draw", f"{model.draw_prob:.0%}"),
            (f"✈️ {away} Win", f"{model.away_win_prob:.0%}"),
            ("⚽ Combined Expected xG", f"{model.home_lambda + model.away_lambda:.2f}"),
            ("📈 Global Power Rating", f"{model.home_rating:.0f} - {model.away_rating:.0f}"),
        ],
        accent=pronostico_accent,
    )

    (
        tab_poisson,
        tab_team_form,
        tab_goal_markets,
        tab_charts_dashboard,
        tab_multi_esito,
        tab_value_betting,
        tab_montecarlo,
        tab_live_match,
    ) = st.tabs(
        [
            "Odds & Probability Analysis (Poisson)",
            "📊 Team Form & H2H",
            "📊 Goal Stats & Markets",
            "📊 Charts Dashboard & Micro-Events",
            "🎯 Multi-Outcome & Value Bet Analyzer",
            "💰 Value Betting & Heatmap",
            "Monte Carlo Simulator (10,000 Matches)",
            "🎮 Live Match Simulator (FC/FIFA Style)",
        ]
    )

    with tab_poisson:
        st.markdown(
            "Rows in bright green indicate probabilities above 80%. "
            "Fair odds are the inverse of the modeled probability. Draws and "
            "low-scoring results are corrected with Dixon-Coles."
        )
        st.markdown("##### 1X2 Implied Odds Detail")
        st.markdown(render_outcome_table(model, home, away), unsafe_allow_html=True)

        st.markdown("##### Most Likely Exact Scores (Poisson + Dixon-Coles)")
        exact_scores = exact_score_probabilities(model.home_lambda, model.away_lambda)[:6]
        exact_score_frame = pd.DataFrame(
            [{"Result": score, "Probability": f"{prob:.1%}"} for score, prob in exact_scores]
        )
        st.dataframe(exact_score_frame, use_container_width=True, hide_index=True)

        st.markdown("##### Micro-Events (shots, corners, cards, fouls)")
        poisson_html = render_probability_table(pd.DataFrame(micro_event_rows(model)))
        st.markdown(poisson_html, unsafe_allow_html=True)

        st.markdown(
            "##### Reading the Model\n"
            "All probabilities (1X2 and micro-events) derive from the same "
            "Global Power Rating: expected goals, shots for/against and "
            "corners are scaled based on the rating differential between "
            "the two teams (home advantage included), with Time-Decay on "
            "historical data, Early Season Mode and manual sliders applied "
            "upstream, and Dixon-Coles correction on draws/low scores."
        )

    with tab_team_form:
        render_team_form_tab(league, home, away)

    with tab_goal_markets:
        st.markdown(
            "Under/Over and Goal/No Goal percentages calculated from the "
            "same bivariate Poisson matrix with Dixon-Coles correction used "
            "for the 1X2 forecast and exact scores, therefore fully "
            "consistent with the other tabs."
        )
        markets = goal_market_probabilities(model)

        st.markdown("##### Total Goals Under / Over (match)")
        total_cols = st.columns(4)
        for index, line in enumerate((1.5, 2.5, 3.5, 4.5)):
            over_p = markets["total_over"][line]
            under_p = 1 - over_p
            with total_cols[index]:
                st.metric(f"Over {line:.1f}", f"{over_p:.1%}")
                st.progress(min(max(over_p, 0.0), 1.0))
                st.caption(f"Under {line:.1f}: {under_p:.1%}")

        st.markdown("##### Home Team Goals Under / Over")
        home_cols = st.columns(3)
        for index, line in enumerate((0.5, 1.5, 2.5)):
            over_p = markets["home_over"][line]
            under_p = 1 - over_p
            with home_cols[index]:
                st.metric(f"{home} · Over {line:.1f}", f"{over_p:.1%}")
                st.progress(min(max(over_p, 0.0), 1.0))
                st.caption(f"Under {line:.1f}: {under_p:.1%}")

        st.markdown("##### Away Team Goals Under / Over")
        away_cols = st.columns(3)
        for index, line in enumerate((0.5, 1.5, 2.5)):
            over_p = markets["away_over"][line]
            under_p = 1 - over_p
            with away_cols[index]:
                st.metric(f"{away} · Over {line:.1f}", f"{over_p:.1%}")
                st.progress(min(max(over_p, 0.0), 1.0))
                st.caption(f"Under {line:.1f}: {under_p:.1%}")

        st.markdown("##### Goal / No Goal (both teams score)")
        gg_col, ng_col = st.columns(2)
        with gg_col:
            st.metric("Goal (GG)", f"{markets['goal_goal']:.1%}")
            st.progress(min(max(markets["goal_goal"], 0.0), 1.0))
        with ng_col:
            st.metric("No Goal (NG)", f"{markets['no_goal']:.1%}")
            st.progress(min(max(markets["no_goal"], 0.0), 1.0))

    with tab_charts_dashboard:
        render_charts_dashboard_tab(model, home, away)

    with tab_multi_esito:
        render_multi_esito_tab(model, home, away)

    with tab_value_betting:
        render_value_betting_tab(model, home, away, league, sidebar_values.get("odds_api_key", ""))

    with tab_montecarlo:
        st.markdown(
            '<div class="mc-intro-caption">10,000 independent Poisson-distributed matches, weighted with the '
            "Dixon-Coles correction on low-scoring results · consistent with the 1X2 forecast in the Poisson tab.</div>",
            unsafe_allow_html=True,
        )

        render_match_banner_compact(league, home, away, crests)
        try:
            home_form = fetch_team_live_stats(league, home).recent_form
        except FootballDataError:
            home_form = ()
        try:
            away_form = fetch_team_live_stats(league, away).recent_form
        except FootballDataError:
            away_form = ()
        render_pre_match_stats_hud(model, home, away, home_form=home_form, away_form=away_form)

        if st.session_state.get("montecarlo_teams") != (home, away):
            # Selected teams changed: the previous simulation is no longer
            # relevant to the match currently being analyzed.
            st.session_state.pop("montecarlo_result", None)
            st.session_state["montecarlo_teams"] = (home, away)

        montecarlo_button_label = (
            "🔁 Relaunch 10,000 Monte Carlo Simulations"
            if "montecarlo_result" in st.session_state
            else "▶️ Run 10,000 Monte Carlo Simulations"
        )
        run_clicked = st.button(montecarlo_button_label, type="primary", key="simulate_button")

        if run_clicked:
            render_monte_carlo_computing_hud(total_paths=10_000, duration_seconds=2.6)
            st.session_state["montecarlo_result"] = run_simulation(model)

        if "montecarlo_result" not in st.session_state:
            st.info("Press the button to launch 10,000 Monte Carlo simulations for this match.")
        else:
            simulation = st.session_state["montecarlo_result"]
            score_frame: pd.DataFrame = simulation["scores"]
            outcome_frame: pd.DataFrame = simulation["outcomes"]
            raw = simulation["raw"]

            outcome_probabilities = {
                str(row["Outcome"]): float(row["Probability"]) for _, row in outcome_frame.iterrows()
            }
            top_score_row = score_frame.iloc[0]
            intel = compute_micro_events_intel(raw, outcome_probabilities)

            # --- Single-Screen HUD: 3 columns, all post-simulation data ----
            # side by side in one row so the whole dashboard fits one
            # viewport with no vertical scroll (screen-recording friendly).
            col_top_outcome, col_alt_frequencies, col_micro_intel = st.columns([1.2, 1, 1.2])

            with col_top_outcome:
                st.markdown('<div class="mc-col-title">🏆 TOP OUTCOME</div>', unsafe_allow_html=True)
                render_top_result_highlight_card(
                    score_label=str(top_score_row["Exact Score"]),
                    probability=float(top_score_row["Probability"]),
                    simulations_count=int(top_score_row["Simulations"]),
                )

            with col_alt_frequencies:
                st.markdown('<div class="mc-col-title">📊 ALTERNATIVE FREQUENCIES</div>', unsafe_allow_html=True)
                render_score_frequency_ranking(
                    score_frame.iloc[1:],
                    reference_probability=float(top_score_row["Probability"]),
                    start_rank=2,
                )

            with col_micro_intel:
                st.markdown('<div class="mc-col-title">📡 MICRO-EVENTS INTEL</div>', unsafe_allow_html=True)
                render_micro_events_intel_column(intel)

            st.caption(
                f"⚙️ 10,000 / 10,000 paths computed for {home} vs {away} · "
                "synced with the Dixon-Coles matrix above."
            )

            # --- Extended analytics, tucked away collapsed so the primary --
            # HUD above stays a single, scroll-free screen by default.
            with st.expander("📈 Extended Analytics (Match Outcome %, full Intel grid, Goal Distribution)", expanded=False):
                st.markdown("##### 🎯 Match Outcome Probability")
                render_three_way_probability_bar(
                    home_prob=outcome_probabilities.get("1 (home win)", 0.0),
                    draw_prob=outcome_probabilities.get("X (draw)", 0.0),
                    away_prob=outcome_probabilities.get("2 (away win)", 0.0),
                    home_label=home,
                    away_label=away,
                )
                st.caption("Frequencies observed over 10,000 simulated matches, weighted with the Dixon-Coles correction.")

                st.markdown("---")
                st.markdown("##### 📡 Full Micro-Events Intel Grid")
                render_micro_events_intel_grid(intel, home, away)

                st.markdown("---")
                st.markdown("##### 📈 Total Goals Distribution (10,000 Paths)")
                total_goals_array = raw["home_goals"] + raw["away_goals"]
                max_bucket = 7
                bucket_labels = [str(n) for n in range(max_bucket)] + [f"{max_bucket}+"]
                bucket_counts = [int((total_goals_array == n).sum()) for n in range(max_bucket)]
                bucket_counts.append(int((total_goals_array >= max_bucket).sum()))
                goals_distribution_frame = pd.DataFrame(
                    {
                        "Total Goals": bucket_labels,
                        "Simulations": bucket_counts,
                        "Probability": [count / len(total_goals_array) for count in bucket_counts],
                    }
                )
                goals_chart = px.bar(
                    goals_distribution_frame,
                    x="Total Goals",
                    y="Probability",
                    text="Probability",
                    color="Probability",
                    color_continuous_scale=["#161b22", "#00e5ff", "#00ff87"],
                )
                goals_chart.update_traces(texttemplate="%{text:.1%}", textposition="outside")
                goals_chart.update_layout(
                    showlegend=False,
                    yaxis_tickformat=".0%",
                    margin={"l": 10, "r": 10, "t": 10, "b": 10},
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e0e0e0",
                )
                st.plotly_chart(goals_chart, use_container_width=True)

    with tab_live_match:
        render_live_match_tab(model, home, away)


DARK_THEME_CSS = """
<style>
/* ==========================================================================
   WayneLab · Gotham Dark Theme (Batman-inspired, EA Sports FC / TV Broadcast style)
   Restyling puramente estetico (CSS + wrapper HTML via st.markdown): non
   tocca alcuna logica di calcolo (Dixon-Coles, Monte Carlo, Kelly, Multi
   Esito, Simulatore Live) — solo la presentazione visiva dei componenti.
   ========================================================================== */
:root {
    --clab-bg: #050505;
    --clab-bg-2: #0d0d0d;
    --clab-card: rgba(18, 18, 18, 0.68);
    --clab-border: rgba(0, 229, 255, 0.25);
    --clab-accent: #00e5ff;
    --clab-accent-2: #e0e0e0;
    --clab-text: #e0e0e0;
    --clab-muted: #9aa0a6;
}

html, body, [class*="css"] {
    font-family: "Inter", "Segoe UI", -apple-system, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 8% 0%, rgba(0, 229, 255, 0.07) 0%, transparent 45%),
        radial-gradient(circle at 92% 12%, rgba(0, 229, 255, 0.05) 0%, transparent 45%),
        linear-gradient(180deg, var(--clab-bg-2) 0%, var(--clab-bg) 60%);
    color: var(--clab-text);
}

section[data-testid="stSidebar"] {
    background: #020202;
    border-right: 1px solid var(--clab-border);
}

h1, h2, h3, h4, h5 {
    font-family: "Inter", "Segoe UI", -apple-system, sans-serif;
    letter-spacing: 0.01em;
}

.league-tag {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 999px;
    background: rgba(0, 229, 255, 0.12);
    border: 1px solid rgba(0, 229, 255, 0.35);
    color: var(--clab-accent-2);
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
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
    font-weight: 900;
    font-size: 1.1rem;
    color: var(--clab-bg);
    margin-top: 34px;
    border-radius: 999px;
    padding: 6px 0;
    background: linear-gradient(135deg, var(--clab-accent), var(--clab-accent-2));
    box-shadow: 0 0 18px rgba(0, 255, 135, 0.35);
}

/* Glassmorphism "glass" card reused by the existing metric-card component */
.metric-card {
    background: linear-gradient(160deg, var(--clab-card) 0%, rgba(14, 17, 23, 0.85) 100%);
    border: 1px solid var(--clab-border);
    border-radius: 16px;
    padding: 16px 14px;
    margin-bottom: 14px;
    backdrop-filter: blur(10px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 26px rgba(0, 255, 135, 0.12);
}

.metric-card-label {
    font-size: 0.78rem;
    color: var(--clab-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}

.metric-card-value {
    font-size: 1.55rem;
    font-weight: 800;
    background: linear-gradient(135deg, var(--clab-accent), var(--clab-accent-2));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

div[data-testid="stMetric"] {
    background: var(--clab-card);
    border: 1px solid var(--clab-border);
    border-radius: 16px;
    padding: 14px 10px;
    backdrop-filter: blur(10px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
}

table {
    border-radius: 12px;
    overflow: hidden;
}

thead tr {
    background: #141414;
    color: var(--clab-text);
}

tbody tr {
    border-bottom: 1px solid var(--clab-border);
}

td, th {
    padding: 8px 10px !important;
}

/* --------------------------------------------------------------------
   Tabellone stile Match TV / Broadcast (Simulatore Live)
   -------------------------------------------------------------------- */
.scoreboard-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 18px;
    background: linear-gradient(135deg, rgba(0, 255, 135, 0.08), rgba(0, 229, 255, 0.08));
    border: 1px solid var(--clab-accent);
    border-radius: 20px;
    padding: 22px 18px;
    margin: 14px 0 22px 0;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 34px rgba(0, 0, 0, 0.5), 0 0 24px rgba(0, 255, 135, 0.08);
}

.scoreboard-team {
    flex: 1;
    text-align: center;
    min-width: 0;
}

.scoreboard-team-name {
    font-size: 1.25rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--clab-text);
    overflow-wrap: break-word;
}

.scoreboard-team-tag {
    font-size: 0.68rem;
    color: var(--clab-muted);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 2px;
}

.scoreboard-center {
    text-align: center;
    padding: 0 12px;
}

.scoreboard-score {
    font-size: 3.6rem;
    font-weight: 900;
    letter-spacing: 0.04em;
    font-variant-numeric: tabular-nums;
    background: linear-gradient(135deg, var(--clab-accent), var(--clab-accent-2));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    line-height: 1;
}

.scoreboard-minute-badge {
    display: inline-block;
    margin-top: 10px;
    padding: 4px 16px;
    border-radius: 999px;
    background: #000;
    border: 1px solid var(--clab-accent);
    color: var(--clab-accent);
    font-weight: 800;
    font-family: "Courier New", monospace;
    letter-spacing: 0.06em;
    font-size: 0.8rem;
    animation: clab-pulse 1.4s ease-in-out infinite;
}

@keyframes clab-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(0, 255, 135, 0.45); }
    50% { box-shadow: 0 0 0 7px rgba(0, 255, 135, 0); }
}

/* --------------------------------------------------------------------
   Barre di confronto visivo (Visual Stat Bars)
   -------------------------------------------------------------------- */
.stat-bar-row {
    margin-bottom: 16px;
}

.stat-bar-values {
    display: flex;
    justify-content: space-between;
    font-weight: 800;
    font-size: 0.92rem;
    margin-bottom: 5px;
    color: var(--clab-text);
    font-variant-numeric: tabular-nums;
}

.stat-bar-track {
    display: flex;
    width: 100%;
    height: 10px;
    border-radius: 999px;
    overflow: hidden;
    background: #141414;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.stat-bar-home {
    background: linear-gradient(90deg, var(--clab-accent-2), var(--clab-accent));
    height: 100%;
}

.stat-bar-away {
    background: linear-gradient(90deg, #ff8a00, #ff2e63);
    height: 100%;
}

.stat-bar-label {
    text-align: center;
    font-size: 0.72rem;
    color: var(--clab-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 4px;
}

/* --------------------------------------------------------------------
   Feed di Cronaca stile Social / Ticker
   -------------------------------------------------------------------- */
.chronicle-feed {
    max-height: 300px;
    overflow-y: auto;
    background: rgba(13, 17, 23, 0.75);
    border: 1px solid rgba(0, 229, 255, 0.28);
    border-radius: 14px;
    padding: 6px 16px;
    backdrop-filter: blur(8px);
}

.chronicle-feed::-webkit-scrollbar {
    width: 6px;
}

.chronicle-feed::-webkit-scrollbar-thumb {
    background: rgba(0, 229, 255, 0.35);
    border-radius: 6px;
}

.chronicle-item {
    padding: 7px 0;
    border-bottom: 1px dashed rgba(255, 255, 255, 0.07);
    font-size: 0.9rem;
    color: var(--clab-text);
}

.chronicle-item:last-child {
    border-bottom: none;
}

.chronicle-item.goal {
    color: var(--clab-accent);
    font-weight: 800;
}

.chronicle-item.red {
    color: #ff4d4f;
    font-weight: 800;
}

.chronicle-item.yellow {
    color: #ffd60a;
    font-weight: 700;
}

/* --------------------------------------------------------------------
   Box "Scheda Social Share"
   -------------------------------------------------------------------- */
.social-share-card {
    border-radius: 20px;
    padding: 22px 24px;
    background: linear-gradient(160deg, rgba(22, 27, 34, 0.92), rgba(14, 17, 23, 0.96));
    border: 1px solid var(--social-accent, var(--clab-accent));
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.03) inset;
    margin-top: 18px;
    backdrop-filter: blur(10px);
}

.social-share-title {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--social-accent, var(--clab-accent));
    font-weight: 800;
}

.social-share-headline {
    font-size: 2rem;
    font-weight: 900;
    color: #ffffff;
    margin: 8px 0 4px 0;
}

.social-share-subtitle {
    font-size: 0.85rem;
    color: var(--clab-muted);
    margin-bottom: 14px;
}

.social-share-rows {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.social-share-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    font-size: 0.88rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    padding-bottom: 6px;
}

.social-share-row-label {
    color: var(--clab-muted);
}

.social-share-row-value {
    color: var(--clab-text);
    font-weight: 800;
    font-variant-numeric: tabular-nums;
    text-align: right;
}

.social-share-footer {
    margin-top: 14px;
    font-size: 0.68rem;
    color: #484f58;
    text-align: right;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* --------------------------------------------------------------------
   Monte Carlo · Compact Match Banner (pre-simulation, screen-recording ready)
   -------------------------------------------------------------------- */
.mc-match-banner {
    background: #050505;
    border: 1px solid #00e5ff;
    border-radius: 14px;
    padding: 14px 18px;
    margin: 8px 0 10px 0;
    box-shadow: 0 0 24px rgba(0, 229, 255, 0.15);
    backdrop-filter: blur(8px);
}

.mc-match-banner-league {
    font-family: "Courier New", monospace;
    font-size: 0.68rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #00e5ff;
    text-align: center;
    margin-bottom: 10px;
    opacity: 0.85;
}

.mc-match-banner-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 18px;
}

.mc-match-banner-team {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    min-width: 0;
}

.mc-match-banner-crest {
    width: 40px;
    height: 40px;
    object-fit: contain;
}

.mc-match-banner-crest-placeholder {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    opacity: 0.6;
}

.mc-match-banner-name {
    font-weight: 800;
    font-size: 0.95rem;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    color: #e0e0e0;
    text-align: center;
    overflow-wrap: break-word;
}

.mc-match-banner-vs {
    font-weight: 900;
    font-size: 0.85rem;
    color: #00e5ff;
    text-shadow: 0 0 8px rgba(0, 229, 255, 0.6);
}

/* --------------------------------------------------------------------
   Monte Carlo · Pre-Match Stats & Parameters HUD (shown before Run button)
   -------------------------------------------------------------------- */
.mc-prematch-hud {
    background: #050505;
    border: 1px solid #00e5ff;
    border-radius: 14px;
    padding: 12px 16px;
    margin: 0 0 10px 0;
    box-shadow: 0 0 20px rgba(0, 229, 255, 0.12);
    backdrop-filter: blur(8px);
}

.mc-prematch-xg-row {
    display: flex;
    justify-content: space-around;
    align-items: center;
    margin-bottom: 10px;
    padding-bottom: 10px;
    border-bottom: 1px dashed rgba(0, 229, 255, 0.2);
}

.mc-prematch-xg-item {
    text-align: center;
}

.mc-prematch-xg-label {
    font-family: "Courier New", monospace;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #9aa0a6;
    margin-bottom: 2px;
}

.mc-prematch-xg-value {
    font-size: 1.5rem;
    font-weight: 900;
    font-variant-numeric: tabular-nums;
    background: linear-gradient(135deg, #00e5ff, #e0e0e0);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    line-height: 1;
}

.mc-prematch-xg-divider {
    font-size: 0.8rem;
    color: #9aa0a6;
    font-weight: 700;
}

.mc-prematch-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    justify-content: center;
}

.mc-prematch-badge {
    font-family: "Courier New", monospace;
    font-size: 0.6rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 999px;
    border: 1px solid rgba(0, 229, 255, 0.4);
    color: #00e5ff;
    background: rgba(0, 229, 255, 0.08);
    white-space: nowrap;
}

/* --------------------------------------------------------------------
   Recent Form badges (W/D/L) — compact strip for the Monte Carlo
   Pre-Match HUD, and reused (larger) in the Team Form & H2H tab tables.
   -------------------------------------------------------------------- */
.form-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border-radius: 6px;
    font-size: 0.62rem;
    font-weight: 900;
    font-family: "Courier New", monospace;
    flex: 0 0 auto;
}

.form-badge-w {
    background: rgba(0, 255, 135, 0.16);
    color: #00ff87;
    border: 1px solid rgba(0, 255, 135, 0.5);
}

.form-badge-d {
    background: rgba(154, 160, 166, 0.16);
    color: #9aa0a6;
    border: 1px solid rgba(154, 160, 166, 0.5);
}

.form-badge-l {
    background: rgba(255, 77, 79, 0.16);
    color: #ff4d4f;
    border: 1px solid rgba(255, 77, 79, 0.5);
}

.form-strip-row {
    display: flex;
    justify-content: space-around;
    align-items: flex-start;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px dashed rgba(0, 229, 255, 0.2);
}

.form-strip-team {
    display: flex;
    flex-direction: column;
    gap: 4px;
    align-items: center;
}

.form-strip-label {
    font-family: "Courier New", monospace;
    font-size: 0.58rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #9aa0a6;
}

.form-strip-badges {
    display: flex;
    gap: 3px;
}

/* --------------------------------------------------------------------
   Team Form & H2H tab · compact WayneLab tables and stats sub-box
   -------------------------------------------------------------------- */
.h2h-table-wrap {
    overflow-x: auto;
    border-radius: 12px;
    border: 1px solid rgba(0, 229, 255, 0.25);
    background: #050505;
}

.h2h-table {
    width: 100%;
    border-collapse: collapse;
}

.h2h-table th {
    background: #0d0d0d;
    color: #00e5ff;
    text-transform: uppercase;
    font-size: 0.68rem;
    letter-spacing: 0.06em;
    padding: 8px 10px;
    text-align: left;
    font-weight: 800;
}

.h2h-table td {
    padding: 7px 10px;
    font-size: 0.85rem;
    color: var(--clab-text);
    border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.h2h-result-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 24px;
    padding: 2px 8px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 0.72rem;
    font-family: "Courier New", monospace;
}

.form-stats-box {
    display: flex;
    gap: 10px;
    margin-top: 10px;
}

.form-stats-item {
    flex: 1;
    background: var(--clab-card);
    border: 1px solid rgba(0, 229, 255, 0.2);
    border-radius: 10px;
    padding: 8px 10px;
    text-align: center;
    backdrop-filter: blur(8px);
}

.form-stats-label {
    font-size: 0.62rem;
    text-transform: uppercase;
    color: #9aa0a6;
    letter-spacing: 0.05em;
    margin-bottom: 2px;
}

.form-stats-value {
    font-size: 1.15rem;
    font-weight: 900;
    color: #00e5ff;
    font-variant-numeric: tabular-nums;
}

/* --------------------------------------------------------------------
   Monte Carlo · "Computing" HUD (shown while the 10,000 paths run)
   -------------------------------------------------------------------- */
.mc-hud-wrap {
    position: relative;
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(0, 229, 255, 0.35);
    box-shadow: 0 0 30px rgba(0, 229, 255, 0.18);
    margin-bottom: 18px;
    background: #050505;
}

.mc-hud-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 10px;
    text-align: center;
    background: rgba(5, 5, 5, 0.35);
}

.mc-hud-label {
    font-family: "Courier New", monospace;
    font-size: 0.75rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #00e5ff;
    text-shadow: 0 0 8px rgba(0, 229, 255, 0.7);
}

.mc-hud-counter {
    font-family: "Courier New", monospace;
    font-size: 2.6rem;
    font-weight: 900;
    letter-spacing: 0.04em;
    font-variant-numeric: tabular-nums;
    background: linear-gradient(135deg, #00ff87, #00e5ff);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    text-shadow: 0 0 24px rgba(0, 255, 135, 0.35);
}

.mc-hud-sub {
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #9aa0a6;
}

.mc-hud-track {
    width: 80%;
    height: 8px;
    border-radius: 999px;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.08);
    margin-top: 4px;
}

.mc-hud-fill {
    height: 100%;
    width: 0%;
    border-radius: 999px;
    background: linear-gradient(90deg, #00ff87, #00e5ff);
    box-shadow: 0 0 12px rgba(0, 229, 255, 0.8);
    transition: width 0.05s linear;
}

/* --------------------------------------------------------------------
   Monte Carlo · Top Result HUD reveal card (gold/neon hero card)
   Compact single-screen HUD sizing: tight padding/margins so the full
   3-column post-simulation dashboard fits one viewport with no scroll.
   -------------------------------------------------------------------- */
.mc-highlight-card {
    border-radius: 16px;
    padding: 14px 16px;
    background:
        radial-gradient(circle at 50% 0%, rgba(0, 229, 255, 0.14), transparent 60%),
        linear-gradient(135deg, rgba(255, 214, 10, 0.12), rgba(0, 255, 135, 0.08));
    border: 1px solid #00e5ff;
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.5), 0 0 26px rgba(0, 229, 255, 0.22);
    margin-bottom: 8px;
    backdrop-filter: blur(10px);
    text-align: center;
    height: 100%;
}

.mc-highlight-label {
    font-family: "Courier New", monospace;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #00e5ff;
    font-weight: 800;
    text-shadow: 0 0 8px rgba(0, 229, 255, 0.6);
}

.mc-highlight-score {
    font-size: 2.7rem;
    font-weight: 900;
    letter-spacing: 0.02em;
    background: linear-gradient(135deg, #ffd60a, #00ff87 55%, #00e5ff);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin: 6px 0 4px 0;
    font-variant-numeric: tabular-nums;
    line-height: 1;
}

.mc-highlight-sub {
    font-family: "Courier New", monospace;
    font-size: 0.78rem;
    color: var(--clab-text);
    font-weight: 700;
    letter-spacing: 0.02em;
}

/* --------------------------------------------------------------------
   Monte Carlo · Top Alternative Outcomes ranking bars (ultra-thin)
   -------------------------------------------------------------------- */
.score-rank-item {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
}

.score-rank-badge {
    flex: 0 0 auto;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    font-size: 0.62rem;
    background: rgba(0, 229, 255, 0.12);
    border: 1px solid rgba(0, 229, 255, 0.5);
    color: #00e5ff;
}

.score-rank-body {
    flex: 1 1 auto;
    min-width: 0;
}

.score-rank-top {
    display: flex;
    justify-content: space-between;
    font-weight: 800;
    font-size: 0.78rem;
    color: var(--clab-text);
    margin-bottom: 2px;
    font-variant-numeric: tabular-nums;
}

.score-rank-track {
    width: 100%;
    height: 4px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.07);
    overflow: hidden;
}

.score-rank-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #00e5ff, #00ff87);
    box-shadow: 0 0 8px rgba(0, 229, 255, 0.5);
}

/* --------------------------------------------------------------------
   Monte Carlo · Micro-Events Intel grid (compact vertical stack)
   -------------------------------------------------------------------- */
.intel-card {
    border-radius: 12px;
    padding: 10px 15px;
    background: var(--clab-card);
    border: 1px solid rgba(0, 229, 255, 0.22);
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(10px);
    margin-bottom: 8px;
}

.intel-card-title {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #9aa0a6;
    font-weight: 800;
    margin-bottom: 6px;
}

.intel-metric-row {
    margin-bottom: 6px;
}

.intel-metric-row:last-child {
    margin-bottom: 0;
}

.intel-metric-top {
    display: flex;
    justify-content: space-between;
    font-size: 0.76rem;
    font-weight: 700;
    color: var(--clab-text);
    margin-bottom: 2px;
}

.intel-metric-value {
    font-weight: 900;
    font-variant-numeric: tabular-nums;
}

.intel-bar-track {
    width: 100%;
    height: 5px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.07);
    overflow: hidden;
}

.intel-bar-fill {
    height: 100%;
    border-radius: 999px;
}

/* --------------------------------------------------------------------
   Monte Carlo · Compact column header labels (replace st.markdown ##### to
   avoid Streamlit's default heading vertical margins eating screen space)
   -------------------------------------------------------------------- */
.mc-col-title {
    font-family: "Courier New", monospace;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #00e5ff;
    font-weight: 800;
    margin: 0 0 8px 0;
    text-shadow: 0 0 6px rgba(0, 229, 255, 0.45);
}

/* --------------------------------------------------------------------
   Monte Carlo · Compact pre-simulation block (banner + description)
   -------------------------------------------------------------------- */
.mc-intro-caption {
    font-size: 0.8rem;
    color: var(--clab-muted);
    margin-bottom: 4px;
    line-height: 1.35;
}

/* --------------------------------------------------------------------
   3-color 1X2 bar (Home · Draw · Away)
   -------------------------------------------------------------------- */
.three-way-bar-track {
    display: flex;
    width: 100%;
    height: 38px;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
}

.three-way-seg {
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 0.88rem;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}

.three-way-home {
    background: linear-gradient(135deg, var(--clab-accent-2), var(--clab-accent));
    color: #04140d;
}

.three-way-draw {
    background: linear-gradient(135deg, #ffd60a, #ffb703);
    color: #241a00;
}

.three-way-away {
    background: linear-gradient(135deg, #ff8a00, #ff2e63);
    color: #ffffff;
}

.three-way-legend {
    display: flex;
    justify-content: space-between;
    margin-top: 8px;
    font-size: 0.76rem;
    color: var(--clab-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
</style>
"""


def main() -> None:
    st.set_page_config(
        page_title="WayneLab · Football Intelligence",
        page_icon="🦇",
        layout="wide",
    )
    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    st.markdown(
        "# 🦇 WayneLab\n"
        "**Football Intelligence** — probabilistic analysis and match simulations "
        "powered by live Football-Data.org data."
    )

    if st.session_state.authenticated:
        with st.sidebar:
            st.success("Access authorized.")
            if st.button("Log Out"):
                st.session_state.authenticated = False
                st.rerun()
            st.markdown("---")
            sidebar_values = render_sidebar_controls()

        main_tab_analysis, main_tab_bankroll = st.tabs(
            ["⚽ Match Analysis", "📊 Bankroll & History Management"]
        )
        with main_tab_analysis:
            render_dashboard(sidebar_values)
        with main_tab_bankroll:
            render_bankroll_tab()
    else:
        render_login()


if __name__ == "__main__":
    main()
