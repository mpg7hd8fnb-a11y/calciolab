from __future__ import annotations

import hashlib
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
# League display names treated as national-team competitions: matches team
# xG estimation to a broader, cross-competition lookback (see
# fetch_team_recent_matches_extended) instead of the single-competition
# current/previous-season split used for club leagues, since national sides
# play far fewer fixtures per year and a strict season boundary does not
# apply to them.

NATIONAL_TEAM_MATCH_WINDOW = 10
# How many of a national team's most recent FINISHED matches (across ALL
# competitions — qualifiers, finals, Nations League, friendlies) to pull for
# Attack/Defense (alpha/beta) estimation, wider than the club-league lookback
# (8) to compensate for national teams' sparser annual fixture list.


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
    "SA": {"shots": 12.0, "shots_on_target": 4.1, "corners": 4.6, "cards": 2.3, "fouls": 12.8, "offsides": 2.1},
    "PL": {"shots": 12.5, "shots_on_target": 4.3, "corners": 5.0, "cards": 1.8, "fouls": 10.8, "offsides": 1.9},
    "ELC": {"shots": 11.8, "shots_on_target": 3.9, "corners": 4.8, "cards": 2.1, "fouls": 12.2, "offsides": 1.9},
    "PD": {"shots": 12.0, "shots_on_target": 4.0, "corners": 4.9, "cards": 2.4, "fouls": 13.0, "offsides": 2.0},
    "BL1": {"shots": 13.0, "shots_on_target": 4.5, "corners": 4.8, "cards": 2.0, "fouls": 11.5, "offsides": 2.2},
    "FL1": {"shots": 11.7, "shots_on_target": 3.9, "corners": 4.7, "cards": 2.2, "fouls": 12.4, "offsides": 1.9},
    "DED": {"shots": 13.2, "shots_on_target": 4.6, "corners": 5.2, "cards": 1.9, "fouls": 11.0, "offsides": 2.3},
    "PPL": {"shots": 11.5, "shots_on_target": 3.8, "corners": 4.5, "cards": 2.6, "fouls": 13.5, "offsides": 2.0},
    "CL": {"shots": 12.6, "shots_on_target": 4.4, "corners": 4.9, "cards": 1.7, "fouls": 10.5, "offsides": 1.8},
    # International matches: generally slightly fewer shots/corners than
    # club football (less cohesive attacking patterns, more cautious
    # setups), cards vary with the stakes of the fixture.
    "WC": {"shots": 11.0, "shots_on_target": 3.8, "corners": 4.3, "cards": 2.2, "fouls": 12.0, "offsides": 1.8},
    "EC": {"shots": 11.2, "shots_on_target": 3.9, "corners": 4.4, "cards": 2.3, "fouls": 12.2, "offsides": 1.8},
    "UNL": {"shots": 10.8, "shots_on_target": 3.6, "corners": 4.1, "cards": 2.0, "fouls": 12.0, "offsides": 1.7},
    "FRIENDLY": {"shots": 10.3, "shots_on_target": 3.4, "corners": 3.9, "cards": 1.5, "fouls": 10.8, "offsides": 1.6},
}

# --- Season Stats tab: proxy conversion factors ------------------------------
# Football-Data.org exposes no official Expected Goals, goalkeeper saves,
# offsides, corners/fouls "against", or yellow/red split. The Season Stats
# tab (render_season_stats_tab / compute_season_stats_summary) derives
# transparent, clearly-labelled estimates from data the provider DOES give
# (goals, shots-on-target baseline, league-baseline cards), using the same
# "league baseline scaled by team output" philosophy already used above for
# shots/corners/cards/fouls — never presented as literal provider data.
XG_PROXY_SHOT_CONVERSION_RATE = 0.32
# Typical professional-football conversion rate from a shot ON TARGET into a
# goal (~30-33% empirically across top leagues). Used as: xG proxy = Shots
# on Target x this rate — a standard, defensible xG approximation when no
# shot-quality (xG) data is available from the provider.

RED_CARD_SHARE_OF_TOTAL_CARDS = 0.045
# Fraction of the total-cards league baseline assumed to be red cards (straight
# reds + second yellows), typically 1 in ~20-25 match-cards in professional
# football. Used only to split the existing combined "cards" baseline into a
# Yellow/Red estimate for the Season Stats tab.

SIGNIFICANT_TREND_RELATIVE_THRESHOLD = 0.12
# Minimum relative change (12%) between a metric's SEASON average and its L5
# (last 5 games) average for the Season Stats tab to show a 🟢/🔴 trend
# badge next to the L5 figure — below this threshold the two windows are
# considered statistically indistinguishable given the underlying sample
# sizes, and no badge is shown (avoids flagging noise as a "trend").

# --- Season Stats tab: micro-event calibration (audited) --------------------
# Football-Data.org has no endpoint for shots/corners/cards/fouls/offsides at
# all (confirmed by inspecting every response this app receives from it) —
# there is no per-match "statistics array" to parse for these, only goals.
# The AUDITED bug was in how the estimate itself scaled with team quality:
# the old formula (clamp(0.88 + goals_per_match*0.08, 0.88, 1.12)) only ever
# moved a team's shots/SOT/offsides estimate +-12% away from the league
# baseline, REGARDLESS of how much a team actually out- or under-scored the
# league average — a team scoring nearly double the league average still
# barely cleared the baseline, which is exactly why top teams' figures came
# out looking "almost halved" versus Sofascore/Opta. Replaced below with a
# ratio-based calibration (team's actual goals/match vs LEAGUE_AVERAGE_
# GOALS_PER_TEAM) that scales much further for genuinely elite or genuinely
# weak sides, plus explicit realism floors so no metric can ever collapse
# below a sane professional-football minimum.
SHOT_CALIBRATION_FLOOR_FACTOR = 0.55
SHOT_CALIBRATION_CEILING_FACTOR = 1.75
SHOT_CALIBRATION_RATIO_SLOPE = 0.45
# factor = clamp(FLOOR + (goals_per_match / LEAGUE_AVERAGE_GOALS_PER_TEAM) *
# SLOPE, FLOOR, CEILING). At the league-average scoring rate the factor is
# exactly 1.0 (baseline unchanged); at ~2x the league average (a realistic
# elite-attack level) it reaches ~1.45; at 0 goals/match it bottoms out at
# the FLOOR (0.55) rather than the previous, far too shallow 0.88.

REALISM_FLOOR_TOTAL_SHOTS = 6.0
REALISM_FLOOR_SHOTS_ON_TARGET = 2.0
REALISM_FLOOR_SHOTS_ON_TARGET_ELITE = 4.0
REALISM_FLOOR_CORNERS_PER_MATCH = 3.0
REALISM_FLOOR_FOULS_PER_MATCH = 8.0
# SANITY CHECK floors (requested explicitly): no professional top-flight
# team's per-match average should realistically read below these levels —
# e.g. Shots on Target under 4.0 for a Tier 1/2 "Top Team", or Corners
# under 3.0 for ANY team, are treated as calibration failures and clamped
# up to these floors rather than displayed as-is.

# ==============================================================================
# OPTA/SOFASCORE TIER ALIGNMENT ENGINE
# ==============================================================================
# A further, TIER-PROPORTIONAL alignment layer on top of the goals-based
# SHOT_CALIBRATION_* factor above. The ratio-based calibration alone still
# under-shoots real Opta/Sofascore ranges for genuinely elite attacks (e.g.
# a PSG/Real Madrid/Inter-level Tier-1 side reads ~5.1-5.5 Shots on Target
# per match from goals alone, versus the ~6.5-8.0 real Opta/Sofascore range
# such sides actually post) — because a team's Tier (blasone + squad
# quality, via lookup_team_tier) carries signal about shot VOLUME and
# QUALITY that goals-per-match alone doesn't fully capture (an elite squad
# out-shoots its level even in games it doesn't convert clinically). This
# layer multiplies the ALREADY-calibrated shots-on-target/total-shots/
# offsides/fouls figures by a further factor keyed to the team's own Tier,
# proportional across all 5 Tiers, so a Tier-1 side lands in the real Opta
# range while a Tier-5 side is proportionally scaled down instead.
OPTA_ALIGNMENT_MULTIPLIERS: dict[int, float] = {
    1: 1.40,  # Title Contenders — Opta/Sofascore alignment target (e.g. PSG/Real Madrid/Inter-level Shots on Target ~6.5-8.0/match)
    2: 1.18,  # European Spot
    3: 1.00,  # Mid-Table (unchanged from the goals-based calibration)
    4: 0.88,  # Relegation Battle
    5: 0.75,  # Newly Promoted
}

OPTA_TOTAL_SHOTS_DAMPENING = 0.5
# Real Opta/Sofascore data shows shot VOLUME (Total Shots, Offsides, Fouls)
# varying far less by Tier than shot ACCURACY (Shots on Target) does — top
# teams create fewer, more clinical chances rather than proportionally many
# more shots. The full OPTA_ALIGNMENT_MULTIPLIERS factor is applied to
# Shots on Target; Total Shots, Offsides and Fouls use a DAMPENED version
# (effective_multiplier = 1 + (tier_multiplier - 1) * this fraction) so
# they move in the same direction without an unrealistic volume inflation.


def opta_alignment_multiplier(team_tier: int, dampen: bool = False) -> float:
    # Shared by both the Season Stats tab (compute_season_stats_summary)
    # and the match-analysis Analytics pipeline (build_match_model), so a
    # given team's Tier is aligned identically everywhere in the app.
    # Respects the sidebar's "Opta/Sofascore Calibration" toggle: off means
    # every metric falls back to the raw league-baseline estimate.
    if not st.session_state.get("opta_calibration_enabled", True):
        return 1.0
    tier_multiplier = OPTA_ALIGNMENT_MULTIPLIERS.get(team_tier, 1.0)
    if not dampen:
        return tier_multiplier
    return 1.0 + (tier_multiplier - 1.0) * OPTA_TOTAL_SHOTS_DAMPENING


def get_base_rating_weight() -> float:
    # Sidebar-adjustable Base/Form split (default 72%/28%, i.e.
    # BASE_RATING_WEIGHT) — reads live from session_state so every caller
    # (build_match_model, compute_season_stats_summary, the AI Tactical
    # Preview) stays in sync with the "Base Rating Weight" slider without
    # threading an extra parameter through each function signature.
    return st.session_state.get("base_rating_weight_pct", int(BASE_RATING_WEIGHT * 100)) / 100.0


def get_form_rating_weight() -> float:
    return 1.0 - get_base_rating_weight()


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
# Rating ELO di riferimento (centro scala), usato come ancoraggio per
# elo_expected_score e per i moltiplicatori derivati dal rating diff.

RATING_SCALE = 400.0
# Base della formula ELO standard (400 punti = fattore 10x nelle quote attese).

HOME_ADVANTAGE_RATING = 60.0
# Bonus di rating ELO per il fattore campo, usato per differenziare
# tiri/corner/cartellini in base al gap di rating (vedi rating_scaling_factors).
# NOTE: this is added only to the *local* rating_diff used for shots/corners/
# cards scaling — it is never added to rating_finale_home/away themselves, so
# it cannot inflate the Power Rating shown in the UI.

RATING_LAMBDA_SENSITIVITY = 0.0022
# Quanto un punto di differenza di rating ELO sposta, in scala esponenziale,
# tiri/corner/cartellini rispetto alla media osservata (vedi
# rating_scaling_factors). I gol attesi (xG) NON passano più da questa
# funzione: dalla Weighted Rating Engine (vedi BASE_RATING_WEIGHT/
# FORM_RATING_WEIGHT più sotto) sono generati direttamente dalla curva di
# conversione Rating→xG in build_match_model (SUPREMACY_RATING_SENSITIVITY/
# BASE_TOTAL_EXPECTED_GOALS/XG_HARD_CAP/XG_HARD_FLOOR).

# ==============================================================================
# WEIGHTED RATING ENGINE (70/30 MODEL) — Base Rating + Current Form Rating
# ==============================================================================
# Architettura a due componenti, sostituisce integralmente il vecchio motore
# Attacco_Finale × Difesa_Finale:
#   RATING FINALE = BASE_RATING_WEIGHT × Base Rating + FORM_RATING_WEIGHT × Current Form Rating
# Il BASE RATING (70-75%) riflette il blasone storico e SOPRATTUTTO la
# posizione/punti di campionato ottenuti nella STAGIONE PRECEDENTE (2025/26,
# vedi resolve_base_rating/fetch_previous_season_standings) — una big
# arrivata 6ª parte da una base da corsa Champions, non da Scudetto; una
# squadra salvatasi all'ultima giornata parte da una base di metà/bassa
# classifica, a prescindere dal blasone storico.
# Il CURRENT FORM RATING (25-30%) riflette ESCLUSIVAMENTE le partite della
# STAGIONE ATTUALE (2026/27, vedi compute_current_form_rating): nessun dato
# della stagione precedente vi confluisce — quel segnale vive solo nel Base
# Rating, tramite la classifica finale, mai nelle statistiche partita per
# partita usate per la Forma.
BASE_RATING_WEIGHT = 0.72
# Peso del Base Rating (blasone + stagione precedente) sul Rating finale —
# nel range 70-75% richiesto.

FORM_RATING_WEIGHT = 1.0 - BASE_RATING_WEIGHT
# Peso del Current Form Rating (sola stagione 2026/27) sul Rating finale —
# complementare a BASE_RATING_WEIGHT, quindi nel range 25-30% richiesto.

BLASONE_WEIGHT_IN_BASE = 0.30
# Quota del blasone storico (Team Tier dictionary) DENTRO il Base Rating.

PREVIOUS_SEASON_WEIGHT_IN_BASE = 1.0 - BLASONE_WEIGHT_IN_BASE
# Quota della posizione/punti di classifica 2025/26 DENTRO il Base Rating —
# la componente DOMINANTE (70%) come richiesto ('SOPRATTUTTO la posizione
# ottenuta nella stagione precedente'), quando la classifica finale è
# disponibile per quella squadra in quella competizione (vedi
# resolve_base_rating: altrimenti si ripiega sul solo blasone).

# --- xG GENERATION: curva di conversione Rating → Expected Goals ------------
XG_HARD_CAP = 2.50
# Tetto massimo assoluto per home_lambda/away_lambda, applicato come ULTIMO
# step della curva di conversione (dopo Base Rating, Current Form Rating,
# slider manuali e Affaticamento), qualunque sia il gap fra le due squadre —
# anche la prima contro l'ultima in classifica. Elimina matematicamente le
# code di Poisson irrealistiche per il calcio (4-0, 5-0, 6-0): i punteggi
# netti restano nell'intervallo credibile 2-0/3-0/3-1/2-1.

XG_HARD_FLOOR = 0.40
# Pavimento minimo per home_lambda/away_lambda, stesso step di XG_HARD_CAP:
# nessuna squadra scende sotto 0.40 xG attesi, per evitare 0-0 quasi certi
# altrettanto irrealistici quanto le goleade tennistiche.

BASE_TOTAL_EXPECTED_GOALS = 2.60
# Gol totali di partita 'di libro' (somma home_lambda + away_lambda) per un
# match STANDARD (nessuno dei tre Match Profile sotto si applica — vedi
# classify_match_profile) — coerente con la media empirica del calcio
# europeo. Alzato da 2.45 a 2.60: con il precedente valore la maggior parte
# dei match 'ordinari' collassava su xG compressi fra 1.00 e 1.30 a testa,
# rendendo l'1-0 il risultato Monte Carlo quasi sistematico anche per
# confronti reali fra squadre di medio livello — questo valore riporta la
# gamma di risultati verso la varietà realistica del calcio (0-0, 1-0, 1-1,
# 2-0, 2-1...) senza sconfinare nelle bande dedicate a Tactical/Big Match.

TOTAL_GOALS_MISMATCH_BONUS = 0.30
# Incremento massimo (fino a +0.30) dei gol totali attesi in funzione del
# gap qualitativo fra le due squadre (vedi pct_rating_distance in
# build_match_model), applicato SOLO al profilo STANDARD (i profili
# Tactical/Big Match/Mismatch hanno le proprie bande fisse dedicate — vedi
# sotto): un mismatch che non raggiunge la soglia MISMATCH_RATING_DISTANCE_
# THRESHOLD produce comunque in media qualche gol in più nel computo
# complessivo (la difesa più debole concede di più), fino a un totale 'di
# libro' di BASE_TOTAL_EXPECTED_GOALS + TOTAL_GOALS_MISMATCH_BONUS.

SUPREMACY_RATING_SENSITIVITY = 0.0025
# Converte linearmente il differenziale di Rating (fattore campo incluso)
# in 'supremazia' di gol (quanto home_lambda supera away_lambda prima delle
# bande/tetto/pavimento specifici del Match Profile): supremacy =
# SUPREMACY_RATING_SENSITIVITY × rating_diff. Usata da tutti e 4 i profili
# (STANDARD, Tactical, Big Match) per ripartire il totale di gol atteso fra
# le due squadre — il profilo Mismatch usa invece una propria interpolazione
# diretta (vedi MISMATCH_FAVORITE_XG_*/MISMATCH_UNDERDOG_XG_*), perché lì lo
# scarto assoluto richiesto è troppo ampio per una singola sensibilità
# lineare condivisa con gli altri profili.

BALANCED_MATCH_RATING_DISTANCE_THRESHOLD = 0.08
# Soglia (8%) di distanza percentuale fra i Rating finali (SENZA fattore
# campo) di home e away sotto la quale il match STANDARD è considerato
# 'Scontro tra pari livello' (vedi pct_rating_distance in build_match_model):
# al di sotto di questa soglia si applica un'ulteriore compressione della
# supremazia (BALANCED_MATCH_SUPREMACY_DAMPING), per restituire al Pareggio
# (X) e ai punteggi di misura (1-1, 1-0, 2-1) una probabilità concreta
# quando le due squadre sono realmente equivalenti. Non si applica ai
# profili Tactical/Big Match/Mismatch, che hanno le proprie bande dedicate.

BALANCED_MATCH_SUPREMACY_DAMPING = 0.70
# Fattore di smorzamento aggiuntivo applicato alla 'supremazia' di gol
# (vedi SUPREMACY_RATING_SENSITIVITY) quando un match STANDARD ricade sotto
# BALANCED_MATCH_RATING_DISTANCE_THRESHOLD, per contenere ulteriormente lo
# scarto di xG fra le due squadre nei confronti realmente equilibrati.

BALANCED_MATCH_TOTAL_EXPECTED_GOALS = 1.95
# Gol totali di partita 'di libro' usati SOLO per i match STANDARD
# considerati 'Scontro tra pari livello' (pct_rating_distance sotto
# BALANCED_MATCH_RATING_DISTANCE_THRESHOLD), al posto di
# BASE_TOTAL_EXPECTED_GOALS. Con la matematica di Poisson, il Pareggio (X)
# smette di essere un esito macro davvero competitivo non appena i lambda di
# entrambe le squadre superano ~1.0 xG a testa — BASE_TOTAL_EXPECTED_GOALS
# (2.60, ≈1.30 a testa) supera sistematicamente quella soglia, così anche
# due squadre di Rating IDENTICO finivano quasi sempre con una vittoria
# (casa o trasferta) come esito Monte Carlo più frequente, mai il Pareggio.
# Con questo totale più basso (≈0.95-1.05 a testa dopo il fattore campo), il
# Pareggio torna a essere uno degli esiti macro (1X2) principali — non
# necessariamente sempre il più probabile, ma sempre competitivo — e 0-0/1-1
# tornano a figurare fra i risultati esatti più frequenti in assoluto, non
# solo all'interno del gruppo dominante.

# ==============================================================================
# DYNAMIC MATCH PROFILES — 3 curve di conversione Rating→xG dedicate
# ==============================================================================
# Oltre al profilo STANDARD (i quattro parametri sopra), il motore riconosce
# 3 tipologie di confronto esplicite, ciascuna con la propria banda di xG per
# squadra, così lo spettro di risultati Monte Carlo varia realisticamente in
# base al TIPO di partita invece di restare sempre compresso in un'unica
# fascia stretta — vedi classify_match_profile in build_match_model.
BIG_MATCH_RATING_THRESHOLD = 1580.0
# Entrambi i Rating (SENZA fattore campo) devono superare questa soglia
# perché il match sia classificato HIGH-PROFILE BIG MATCH (Profilo B) — il
# controllo è INDIVIDUALE su home E away (non sulla media), così un solo top
# club abbinato a una squadra debole non genera falsamente un 'big match'.

TACTICAL_SCORING_TEMPO_THRESHOLD = 1.10
# Media gol segnati a partita nella stagione corrente (2026/27, sola
# Current Form — vedi LiveTeamStats.goals_for/matches): se ENTRAMBE le
# squadre sono a questa soglia o sotto, il match è classificato LOW-SCORING/
# TACTICAL (Profilo A). Con zero partite giocate quest'anno si usa
# LEAGUE_AVERAGE_GOALS_PER_TEAM come tempo neutro (né basso né alto), così
# una squadra non ancora scesa in campo non attiva falsamente il profilo.

MISMATCH_RATING_DISTANCE_THRESHOLD = 0.20
# Distanza percentuale di Rating (stessa metrica di pct_rating_distance,
# SENZA fattore campo) oltre la quale il match è classificato MISMATCHED /
# HIGH-TIER VS LOW-TIER (Profilo C) — controllato PRIMA degli altri due
# profili: un vero scontro impari prevale sempre sulla classificazione
# 'Big Match' o 'Tactical', qualunque sia il tempo di gioco o il Rating
# assoluto delle due squadre.

MISMATCH_MAX_INTENSITY_DISTANCE = 0.45
# Distanza di Rating oltre la quale l'intensità del Mismatch (vedi
# MISMATCH_RATING_DISTANCE_THRESHOLD) è considerata 'massima' (100%): fra la
# soglia di ingresso e questo valore, il tetto della favorita e il pavimento
# della sfavorita scalano linearmente dai bordi più miti ai più estremi delle
# rispettive forbici (vedi MISMATCH_FAVORITE_XG_*/MISMATCH_UNDERDOG_XG_*).

# --- Bande di xG per-squadra specifiche di ciascun Match Profile -----------
TACTICAL_XG_MIN = 0.70
TACTICAL_XG_MAX = 0.95
TACTICAL_TOTAL_EXPECTED_GOALS = 1.70
# Profilo A (Low-Scoring/Tactical, es. Parma vs Monza): xG per squadra
# contenuti in [0.70, 0.95], totale 'di libro' 1.70 — fa emergere con
# naturalezza 0-0, 1-0, 1-1 senza bisogno di forzature a valle.

BIG_MATCH_XG_MIN = 1.75
BIG_MATCH_XG_MAX = 2.20
BIG_MATCH_TOTAL_EXPECTED_GOALS = 3.90
# Profilo B (High-Profile Big Match, es. Barcelona vs Real Madrid): xG
# per squadra alzati in [1.75, 2.20], totale 'di libro' 3.90 — favorisce
# simulazioni spettacolari (2-2, 2-1, 3-2, 3-1) fra due Top Team.

MISMATCH_FAVORITE_XG_MIN = 2.65
MISMATCH_FAVORITE_XG_MAX = 2.85
MISMATCH_UNDERDOG_XG_MIN = 0.45
MISMATCH_UNDERDOG_XG_MAX = 0.65
# Profilo C (Mismatched / High-Tier vs Low-Tier, es. Inter vs Monza,
# Arsenal vs Coventry): tetto della favorita in [2.65, 2.85] (interpolato
# sull'intensità del gap, vedi MISMATCH_MAX_INTENSITY_DISTANCE), sfavorita
# tenuta bassa in [0.45, 0.65] — sposta il risultato Monte Carlo più
# probabile su esiti netti e realistici (3-0, 3-1, 2-0), MAI su un 1-0
# risicato né su goleade tennistiche tipo 5-0/6-0.

SHOT_RATING_DAMPING = 0.7
# I tiri (fatti/in porta) seguono il gap di rating con un'intensità inferiore
#
# ai gol (che dipendono anche da efficienza/episodi), da qui lo smorzamento.

CORNER_RATING_DAMPING = 0.35
# I corner sono più legati al possesso palla che al gap di qualità puro:
# smorzamento più marcato rispetto ai tiri.

CARD_UNDERDOG_BONUS = 0.25
# Quota aggiuntiva di cartellini per la squadra più debole, che difende più
# a lungo e commette più falli tattici contro un avversario superiore.

# --- Time-Decay per i dati storici (ora usato SOLO dallo shrinkage del
# Current Form Rating e dal blend Tier/Stats di tiri-corner-cartellini: i
# dati della stagione precedente NON confluiscono più nelle statistiche
# partita per partita — vivono solo nel Base Rating, vedi
# resolve_base_rating/fetch_previous_season_standings) --------------------
EARLY_SEASON_MATCHDAY_THRESHOLD = 10
# Dalla Giornata 10 (N partite REALI giocate nella stagione corrente, un
# campione minimo di 10-15 partite come richiesto) si usa il 100% dei dati/
# statistiche reali per il blend Tier/Stats di tiri-corner-cartellini (vedi
# dynamic_decay_weights) — questo, insieme allo shrinkage di REGRESSION_TO_
# MEAN_SAMPLE_SIZE applicato al Current Form Rating (vedi _shrink_to_mean),
# è la doppia barriera che impedisce a 2-3 risultati estremi di sbilanciare
# il Rating sopra quello di una big con un campione più ampio e affidabile.

REGRESSION_TO_MEAN_SAMPLE_SIZE = 6.0
# Numero di partite (stagione corrente) oltre il quale il moltiplicatore
# Attacco/Difesa del Current Form Rating, calcolato dalle statistiche
# osservate, viene usato al 100% del suo valore grezzo. Con un campione più
# piccolo, il moltiplicatore viene 'ristretto' (shrinkage Bayesiano) verso
# 1.0 (la media di lega) in proporzione al campione disponibile — vedi
# _shrink_to_mean. Con zero partite giocate quest'anno lo shrinkage riporta
# il moltiplicatore esattamente a 1.0, così il Current Form Rating collassa
# sul rating neutro di lega (BASE_RATING=1500) e il Rating finale coincide
# di fatto col solo Base Rating (Fascia/stagione precedente) — esattamente
# il comportamento atteso prima che una squadra abbia giocato.

CLUB_MATCH_LOOKBACK = 15
# Massimo numero di partite CORRENTI (stagione 2026/27) recuperate per
# ogni squadra di club, usate esclusivamente per il Current Form Rating e le
# statistiche di tiri/corner/cartellini — alzato da 8 a 15 per garantire un
# campione minimo di 10-15 partite come richiesto, riducendo ulteriormente
# la sensibilità del rating a 2-3 risultati anomali isolati (si veda anche
# REGRESSION_TO_MEAN_SAMPLE_SIZE, che agisce sullo stesso problema da un
# angolo complementare). La stagione precedente non usa più questo lookback
# per le statistiche: la sua unica fonte è ora la classifica finale (vedi
# fetch_previous_season_standings), letta per intero.

LEAGUE_AVERAGE_GOALS_PER_TEAM = 1.35
# Gol attesi 'di libro' per una squadra media in una singola partita di
# massima serie: fattore di normalizzazione del moltiplicatore Attacco/Difesa
# usato dal Current Form Rating (vedi _stats_multiplier/compute_current_
# form_rating) — i gol attesi finali (xG) sono generati dalla curva Rating→
# xG (BASE_TOTAL_EXPECTED_GOALS/SUPREMACY_RATING_SENSITIVITY), non più da un
# prodotto diretto Attacco×Difesa.

# --- Slider manuali "Impatto Mercato" e "Impatto Infortuni" -------------------
MARKET_FACTOR_BOUNDS = (-0.20, 0.20)
# Range consentito per lo slider 'Fattore Mercato' (-20% / +20%).

INJURY_FACTOR_BOUNDS = (-0.30, 0.30)
# Range consentito per lo slider 'Impatto Infortuni / Titolari Assenti'
# (-30% / +30%).

# --- Forma recente come moltiplicatore dinamico (Form Amplifier) -------------
FORM_DEFENSE_TRANSFER = 0.7
# Quota dell'effetto Form Factor trasferita anche alla Difesa (in direzione
# opposta): una squadra in ottima forma (Form Factor > 1.0) migliora anche la
# propria fase difensiva, ma in misura più contenuta rispetto all'attacco —
# vedi l'applicazione in build_match_model, che moltiplica direttamente
# Attacco_Finale per il Form Factor e Difesa_Finale per un fattore simmetrico
# smorzato da questo coefficiente. Alzato da 0.6 a 0.7 (DYNAMIC FORM &
# MOMENTUM): la fase difensiva deve risentire quasi quanto l'attacco del
# momento di forma, così una Big in crisi concede di più oltre a segnare
# meno, invece di restare quasi impermeabile solo perché di Fascia alta.

# --- Correzione Dixon-Coles -----------------------------------------------------
DIXON_COLES_RHO = -0.09
# Parametro ρ di Dixon-Coles (Dixon & Coles, 1997): corregge la Poisson
# bivariata indipendente sui 4 risultati a basso punteggio (0-0, 1-0, 0-1, 1-1),
# dove nella realtà i pareggi/risultati bassi sono leggermente più frequenti di
# quanto preveda il semplice prodotto di due Poisson indipendenti. Ridotto in
# magnitudine da -0.13 a -0.09 (resta nel range tipico della letteratura,
# -0.08/-0.20): il boost su τ(1,1) passa da ×1.13 a ×1.09, riducendo la
# tendenza del modello ad 'attirare' verso l'1-1 i risultati quando gli xG
# delle due squadre sono vicini, senza eliminare la correzione Dixon-Coles
# (che resta scientificamente corretta e necessaria).


# --- 1. DIZIONARIO FASCE DI FORZA (TEAM TIERS) --------------------------------
TEAM_TIER_PROFILES: dict[int, dict[str, float]] = {
    1: {"rating": 1750.0, "attack": 1.35, "defense": 0.70},  # Top / Titolo
    2: {"rating": 1600.0, "attack": 1.15, "defense": 0.85},  # Europa
    3: {"rating": 1480.0, "attack": 1.00, "defense": 1.00},  # Metà classifica
    4: {"rating": 1380.0, "attack": 0.85, "defense": 1.15},  # Salvezza
    5: {"rating": 1280.0, "attack": 0.75, "defense": 1.30},  # Neopromosse
}

TEAM_TIER_DEFAULT = 3
# Fallback esplicito per una squadra non trovata nel dizionario: Tier 3
# (Base Rating 1480) — MAI il vecchio default piatto 1500.

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


def _stats_multiplier(value_per_match: float) -> float:
    """Converts a raw per-match value (goals scored or conceded per game)
    into a multiplier relative to the league average
    (LEAGUE_AVERAGE_GOALS_PER_TEAM), clamped to a sane [0.3, 3.0] range."""
    return clamp(value_per_match / LEAGUE_AVERAGE_GOALS_PER_TEAM, 0.3, 3.0)


def _stats_rating(attack_mult: float, defense_mult: float) -> float:
    """Converts an Attack/Defense multiplier pair into an absolute rating
    centered on BASE_RATING (the league average, 1500) — used by
    compute_current_form_rating so the Current Form Rating reflects only
    this season's on-pitch output, independent of blasone or Base Rating."""
    return BASE_RATING + (RATING_SCALE / 2) * (attack_mult - 1.0) - (RATING_SCALE / 2) * (defense_mult - 1.0)


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
    da applicare a tiri/corner/cartellini. `damping` attenua l'effetto a
    seconda della metrica: < 1.0 per metriche meno legate al puro gap di
    qualità (es. corner). I gol attesi (xG) non passano da questa funzione:
    sono generati dalla curva di conversione Rating→xG in build_match_model
    (vedi SUPREMACY_RATING_SENSITIVITY)."""
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
    clean_sheets: int = 0
    """Numero di partite della stagione corrente (2026/27) concluse senza
    subire gol (conceded == 0) — dato REALE, contato direttamente sui
    risultati restituiti dall'API, non stimato su baseline di lega."""


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


def _regulation_time_score(score: dict[str, object]) -> tuple[float | None, float | None]:
    # NORMALIZATION TO 90 REGULATION MINUTES (+ stoppage time): most
    # competitions in this app are pure round-robin leagues (SA, PL, PD,
    # BL1, FL1, DED, PPL, ELC) where extra time/penalties never occur, but
    # the knockout stages of CL/WC/EC/UNL can go beyond 90 minutes.
    # Football-Data.org exposes the 90-minute score separately as
    # "regularTime" for exactly those ties (fullTime there reflects the
    # extra-time-inclusive result, and any penalty shootout lives in its
    # own "penalties" field, never merged into goal counts). Preferring
    # regularTime when present — and falling back to fullTime for every
    # normal match, where the two are identical — keeps every goal-based
    # average in this app scoped to regulation play only, per-match.
    regular_time = score.get("regularTime")
    if isinstance(regular_time, dict):
        home_reg = _number(regular_time.get("home"))
        away_reg = _number(regular_time.get("away"))
        if home_reg is not None and away_reg is not None:
            return home_reg, away_reg
    full_time = score.get("fullTime")
    if not isinstance(full_time, dict):
        return None, None
    return _number(full_time.get("home")), _number(full_time.get("away"))


def _match_has_final_score(match: dict[str, object]) -> bool:
    score = match.get("score")
    if not isinstance(score, dict):
        return False
    home_goals, away_goals = _regulation_time_score(score)
    return home_goals is not None and away_goals is not None


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


def _safe_average(total: float, count: float, fallback: float = 0.0) -> float:
    """Like _average, but returns `fallback` instead of raising when count
    is zero — used for the shots/corners/cards/fouls Tier/Stats blend
    (dynamic_decay_weights), where a team with zero current-season matches
    simply gets 0% weight on the raw stats side (100% Tier baseline), so
    the exact raw value is irrelevant as long as computing it doesn't
    crash the whole match analysis."""
    if count <= 0:
        return fallback
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


QUICK_PRESET_OPTIONS = [
    "🔧 Manual Selection",
    "🎭 Big Match Spectacle",
    "⚖️ Tactical Battle",
    "⚔️ Mismatch",
]
# SMART MATCH SELECTOR presets: each narrows the "Match of the Day" dropdown
# to fixtures whose two teams' blasone TIER (lookup_team_tier — a cheap,
# no-API-call lookup, unlike a full live-stats fetch) fits that archetype,
# so picking a preset stays instant even before any match-specific data is
# loaded. This is a lightweight PRE-FILTER on the fixture list, distinct
# from — and a cheaper cousin of — the live, goals-driven Match Profile
# classification (classify_match_profile) computed once a specific match is
# actually analyzed.


def build_fixture_options(calendar_df: pd.DataFrame) -> list[tuple[str, str, str]]:
    # (label, home_team, away_team) tuples for the "Match of the Day"
    # dropdown, built from the competition's full fixture list
    # (calendar_frame) — upcoming fixtures are listed first, then finished
    # ones, so a fresh preseason calendar (all SCHEDULED) and a nearly
    # completed season (mostly FINISHED) both produce a sensible, non-empty
    # selector.
    options: list[tuple[str, str, str]] = []
    upcoming_rows = calendar_df[calendar_df["Status"] != "Finished"]
    finished_rows = calendar_df[calendar_df["Status"] == "Finished"].iloc[::-1]  # most recent finished first
    for _, row in pd.concat([upcoming_rows, finished_rows]).iterrows():
        home_name = str(row["Home"]).strip()
        away_name = str(row["Away"]).strip()
        if not home_name or not away_name:
            continue
        date_text = str(row["Date"]).strip() or "TBD"
        status_text = str(row["Status"])
        label = f"{home_name} vs {away_name} — {date_text} ({status_text})"
        options.append((label, home_name, away_name))
    return options


def filter_fixtures_by_preset(
    fixtures: list[tuple[str, str, str]], preset: str
) -> list[tuple[str, str, str]]:
    if preset == "🎭 Big Match Spectacle":
        return [f for f in fixtures if lookup_team_tier(f[1]) <= 2 and lookup_team_tier(f[2]) <= 2]
    if preset == "⚖️ Tactical Battle":
        return [
            f
            for f in fixtures
            if lookup_team_tier(f[1]) >= 3
            and lookup_team_tier(f[2]) >= 3
            and abs(lookup_team_tier(f[1]) - lookup_team_tier(f[2])) <= 1
        ]
    if preset == "⚔️ Mismatch":
        return [f for f in fixtures if abs(lookup_team_tier(f[1]) - lookup_team_tier(f[2])) >= 2]
    return fixtures


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


# ==============================================================================
# PLAYER ENGINE — Key Players & Anytime Goalscorer probabilities
# ==============================================================================
# Football-Data.org's /teams/{id} endpoint DOES return a real first-team
# squad (name + position, no stats), used whenever it's available — real
# player NAMES are always preferred over invented ones. It has NO player-
# level ratings, goals, scoring-probability, or injury data at all, so the
# FC-style Overall Rating and the Anytime Goalscorer % shown in the UI are
# ALWAYS algorithmically generated from data this app already has (Team
# Power Rating, Role, this match's xG), never presented as literal
# provider/Opta/Sofascore data. When the squad endpoint is unavailable
# (rate limit, plan tier, empty response), generic role-archetype
# placeholders are shown instead of a real name — this app never invents a
# specific person's identity to fill a gap in the data.
KEY_PLAYER_MAX_CARDS = 3

# AUDITED FIX: Football-Data.org frequently returns COARSE position labels
# — "Attacker", "Midfielder", "Defender", "Goalkeeper" — rather than
# granular ones ("Centre-Forward", "Right Winger"...). The previous
# classifier only matched "forward"/"striker" substrings, so a player
# literally tagged "Attacker" fell through to a generic bucket instead of
# being recognized as a Striker, while "Midfielder" always matched —
# explaining why midfielders dominated the Key Players list almost
# exclusively. Fixed below by matching "attack" too, and by checking the
# more specific "attacking midfield" BEFORE the broad "attack"/"forward"
# check so a genuine attacking midfielder isn't mis-tagged as a Striker.
ROLE_XG_SHARE: dict[str, float] = {
    "Striker": 0.42,
    "Winger": 0.20,
    "Attacking Midfielder": 0.20,
    "Midfielder": 0.08,
    "Defender": 0.02,
}
# Individual (not aggregate-category) share of the TEAM's match xG used for
# ONE selected player's Anytime Goalscorer Poisson calculation — calibrated
# so the role ORDERING mirrors the requested 70/20/8/2 split (Forwards
# collectively dominate a team's scoring, Wingers/CAM next, Central
# Midfielders a distant third, Defenders almost never) while still reading
# as realistic PER-PLAYER percentages (e.g. a lead striker in a big match
# can clear 50%+, matching real Anytime Goalscorer market pricing).

ROLE_OVERALL_RANGE: dict[str, tuple[int, int]] = {
    "Striker": (72, 91),
    "Winger": (70, 88),
    "Attacking Midfielder": (68, 85),
    "Midfielder": (65, 83),
    "Defender": (62, 80),
}
# AUDITED FIX: a single shared 72-91 range for EVERY role meant a good-but-
# not-world-class attacking midfielder or central midfielder at a highly
# rated club (e.g. a Roma/Atalanta-level "Pellegrini"/"Koopmeiners" type
# profile) could read as an unrealistic 88-91 "world class" Overall purely
# because their CLUB's Power Rating was high. Each role now has its own
# ceiling — only a Striker can ever reach 91, an Attacking/Central
# Midfielder tops out at 85/83 — which is what keeps that kind of player
# realistically in the 78-83 band instead.

STAR_PLAYER_OVERALL_OVERRIDES: dict[str, int] = {
    "kylian mbappé": 91,
    "kylian mbappe": 91,
    "erling haaland": 91,
    "vinícius júnior": 90,
    "vinicius junior": 90,
    "vinícius jr.": 90,
    "vinicius jr": 90,
    "jude bellingham": 90,
    "lionel messi": 90,
}
# A small, manually-curated table for a handful of truly world-class
# players whose general caliber is stable, widely-published public
# knowledge (unlike day-to-day injury status, NEVER inferred or guessed
# here) — matched case-insensitively against the real Football-Data.org
# squad name. Every other player, including very good but non-elite names,
# is rated purely by the formulaic Team Power Rating x Role Range model
# above, which is what keeps a club's #2/#3 attacking option from
# incorrectly reading as "world class" just because the club itself is.

EXCLUDED_PLAYERS: set[str] = set()
# Manually-maintained exclusion list (lower-cased full names) for players
# who should NEVER be offered as a Key Player/Anytime Goalscorer card —
# e.g. long-term injuries, suspensions, or players no longer first-team
# regulars for 2026/27. Football-Data.org has NO live injury/availability
# feed of any kind, so this list is intentionally left EMPTY by default:
# populate it yourself with names you can verify are unavailable right
# now (operator-maintained, not automatically fetched or inferred) —
# fabricating specific real-world injury claims without a verified source
# would risk misinforming users about real people. Example of the expected
# format (commented out): {"example player name"}.

GENERIC_KEY_PLAYER_ARCHETYPES: tuple[tuple[str, str], ...] = (
    ("Lead Striker (Generated)", "Striker"),
    ("Creative Playmaker (Generated)", "Attacking Midfielder"),
    ("Wide Threat (Generated)", "Winger"),
)
# Used only when Football-Data.org's squad endpoint is unavailable for a
# team, OR as a last-resort guarantee that at least one Striker is always
# present (see select_key_players): generic ROLE labels (not a specific
# person's name), so a missing API response is never papered over with a
# fabricated human identity.


def classify_player_role(position: str) -> str:
    # Maps a raw Football-Data.org "position" string (which may be coarse,
    # e.g. just "Attacker") to one of the ROLE_XG_SHARE/ROLE_OVERALL_RANGE
    # buckets. Order matters: the more specific "attacking midfield" check
    # runs BEFORE the broad "attack"/"forward"/"striker" check, so a real
    # attacking midfielder isn't mis-classified as a Striker.
    position_lower = (position or "").lower()
    if "attacking midfield" in position_lower or "second striker" in position_lower:
        return "Attacking Midfielder"
    if "wing" in position_lower:
        return "Winger"
    if "forward" in position_lower or "striker" in position_lower or "attack" in position_lower:
        return "Striker"
    if "midfield" in position_lower:
        return "Midfielder"
    if "back" in position_lower or "defence" in position_lower or "defender" in position_lower:
        return "Defender"
    if "keeper" in position_lower or "goalkeeper" in position_lower:
        return "Goalkeeper"
    return "Midfielder"  # unrecognized/blank position: safest neutral default


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_team_squad(league: str, team_name: str) -> tuple[dict[str, str], ...]:
    # Real squad list (name + position) straight from Football-Data.org's
    # /teams/{id} endpoint — raises FootballDataError for any failure
    # (fallback team roster with a negative synthetic ID, API/plan
    # limitation, empty response), so the caller falls back to generic
    # role archetypes rather than ever crashing the Key Players section.
    team_map = dict(fetch_league_teams(league))
    team_id = next((id_ for id_, name in team_map.items() if name == team_name), None)
    if team_id is None or team_id < 0:
        raise FootballDataError(f"No live Football-Data.org team ID available for {team_name}.")
    payload = _football_data_request(f"/teams/{team_id}")
    squad = payload.get("squad", [])
    if not isinstance(squad, list):
        raise FootballDataError(f"Football-Data.org returned no squad data for {team_name}.")
    players = tuple(
        {"name": player.get("name"), "position": player.get("position") or ""}
        for player in squad
        if isinstance(player, dict) and isinstance(player.get("name"), str) and player.get("name")
    )
    if not players:
        raise FootballDataError(f"Football-Data.org squad list is empty for {team_name}.")
    return players


def select_key_players(squad: tuple[dict[str, str], ...]) -> list[dict[str, object]]:
    # ROLE-WEIGHTED SELECTION (Forwards first): buckets every eligible
    # squad member by role, excludes goalkeepers and anyone in
    # EXCLUDED_PLAYERS, then builds the 3 Key Player slots by DRAWING FROM
    # STRIKERS FIRST (up to 2, satisfying "always 1-2 forwards among the
    # top 3"), filling any remaining slots from Winger/Attacking
    # Midfielder, then Midfielder, then any extra Strikers, then Defender.
    # A hard guarantee at the end injects a generated Striker if the real
    # squad data genuinely contained none.
    buckets: dict[str, list[str]] = {"Striker": [], "Winger": [], "Attacking Midfielder": [], "Midfielder": [], "Defender": []}
    seen_names: set[str] = set()
    for player in squad:
        name = player.get("name")
        if not name or name in seen_names:
            continue
        if name.strip().lower() in EXCLUDED_PLAYERS:
            continue
        role = classify_player_role(player.get("position", ""))
        if role == "Goalkeeper" or role not in buckets:
            continue
        buckets[role].append(name)
        seen_names.add(name)

    selected: list[tuple[str, str]] = []  # (name, role)

    for name in buckets["Striker"][:2]:
        selected.append((name, "Striker"))

    fill_order = [
        ("Winger", buckets["Winger"]),
        ("Attacking Midfielder", buckets["Attacking Midfielder"]),
        ("Midfielder", buckets["Midfielder"]),
        ("Striker", buckets["Striker"][len(selected):]),
        ("Defender", buckets["Defender"]),
    ]
    chosen_names = {name for name, _role in selected}
    for role, names in fill_order:
        for name in names:
            if len(selected) >= KEY_PLAYER_MAX_CARDS:
                break
            if name in chosen_names:
                continue
            selected.append((name, role))
            chosen_names.add(name)
        if len(selected) >= KEY_PLAYER_MAX_CARDS:
            break

    if not any(role == "Striker" for _name, role in selected):
        # Hard guarantee: real squad data contained no recognizable
        # Striker at all — inject a generated one at the front rather than
        # ever showing a Key Players list with zero forwards.
        selected = [("Lead Striker (Generated)", "Striker")] + selected
        selected = selected[:KEY_PLAYER_MAX_CARDS]

    return [{"name": name, "role": role, "generated": "(Generated)" in name} for name, role in selected]


def generate_archetype_key_players() -> list[dict[str, object]]:
    return [{"name": name, "role": role, "generated": True} for name, role in GENERIC_KEY_PLAYER_ARCHETYPES]


def _stable_name_jitter(name: str, spread: int = 2) -> int:
    # Deterministic +-spread jitter derived from the player's own name (a
    # stable hash, not Python's random module), so the same player's
    # Overall Rating doesn't flicker between reruns/page refreshes.
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()
    return (int(digest[:2], 16) % (2 * spread + 1)) - spread


def generate_player_overall_rating(team_power_rating: float, role: str, player_name: str) -> int:
    # FC/Ultimate-Team-style Overall, generated per ROLE-SPECIFIC ceiling
    # (see ROLE_OVERALL_RANGE) from the TEAM's own Global Power Rating,
    # with a small deterministic per-player jitter — UNLESS the player is
    # in STAR_PLAYER_OVERALL_OVERRIDES, in which case that fixed, publicly-
    # known rating is used directly regardless of club/role. Always a
    # generated estimate outside the star-player table — Football-Data.org
    # has no player-level ratings of any kind.
    override = STAR_PLAYER_OVERALL_OVERRIDES.get(player_name.strip().lower())
    if override is not None:
        return override
    range_min, range_max = ROLE_OVERALL_RANGE.get(role, (65, 83))
    normalized = clamp((team_power_rating - 1150.0) / (1850.0 - 1150.0), 0.0, 1.0)
    base_rating = range_min + normalized * (range_max - range_min)
    jitter = _stable_name_jitter(player_name)
    return int(clamp(base_rating + jitter, 55.0, 91.0))


def generate_player_goal_probability(team_lambda: float, role: str) -> float:
    # Anytime Goalscorer probability = 1 - P(0 goals), Poisson on the
    # player's SHARE of the team's own match xG for their role (see
    # ROLE_XG_SHARE) — an estimate, not a real per-player xG feed
    # (Football-Data.org has none).
    xg_share = ROLE_XG_SHARE.get(role, 0.05)
    player_lambda = max(team_lambda * xg_share, 0.0)
    return clamp(1.0 - math.exp(-player_lambda), 0.0, 0.97)


def build_key_players_for_team(
    league: str, team_name: str, team_lambda: float, team_power_rating: float
) -> tuple[list[dict[str, object]], bool]:
    # Returns (player_cards, used_real_squad_data). Real Football-Data.org
    # names are preferred; generic role archetypes silently fill any gap
    # (missing squad entirely, or fewer than KEY_PLAYER_MAX_CARDS eligible
    # players found) so the section always renders exactly 3 cards, always
    # with at least 1-2 Strikers among them.
    try:
        squad = fetch_team_squad(league, team_name)
        key_players = select_key_players(squad)
    except FootballDataError:
        key_players = []

    used_real_squad_data = len(key_players) >= KEY_PLAYER_MAX_CARDS and not any(p["generated"] for p in key_players)
    if len(key_players) < KEY_PLAYER_MAX_CARDS:
        key_players = key_players + generate_archetype_key_players()[: KEY_PLAYER_MAX_CARDS - len(key_players)]

    cards: list[dict[str, object]] = []
    for player in key_players[:KEY_PLAYER_MAX_CARDS]:
        cards.append(
            {
                "name": player["name"],
                "role": player["role"],
                "overall": generate_player_overall_rating(team_power_rating, player["role"], player["name"]),
                "goal_probability": generate_player_goal_probability(team_lambda, player["role"]),
                "xg_share": ROLE_XG_SHARE.get(player["role"], 0.05),
                "generated": player["generated"],
            }
        )
    return cards, used_real_squad_data

@st.cache_data(ttl=300, show_spinner=False)
def fetch_team_season_matches(league: str, team_name: str) -> tuple[dict[str, object], ...]:
    # AUDIT-GRADE, UNCAPPED fetch: every 'FINISHED' 2026/27 match for
    # `team_name` in `league` ONLY — no CLUB_MATCH_LOOKBACK slicing. That
    # cap exists solely to keep the Weighted Rating Engine's Current Form
    # Rating stable (fetch_team_live_stats/compute_current_form_rating) and
    # is correct for that purpose, but it silently truncated the "season
    # average" shown in the Season Stats tab to a rolling last-15-games
    # window once a team had played more than that many matches this
    # season (exactly the PSG-vs-Sofascore discrepancy this fix addresses).
    # Season Stats must divide by the REAL number of matches played, so it
    # gets its own uncapped source instead of reusing LiveTeamStats.matches.
    # Sorted most-recent-first (same convention as fetch_league_matches),
    # scoped to the SELECTED COMPETITION ONLY (Football-Data.org's
    # /competitions/{code}/matches endpoint never mixes in other
    # competitions a club also plays, e.g. Champions League fixtures never
    # leak into a Ligue 1 lookup) and to FINISHED matches only (postponed/
    # scheduled/cancelled fixtures have no fullTime score and are dropped
    # by _match_has_final_score).
    team_map = dict(fetch_league_teams(league))
    team_id = next((id_ for id_, name in team_map.items() if name == team_name), None)
    if team_id is None:
        raise FootballDataError(f"The team {team_name} is not available in Football-Data.org.")

    if is_national_team_competition(league):
        # National teams have no meaningful "all matches in this
        # competition" concept (a single tournament's own fixture list is
        # often near-empty between windows) — reuse the same broader,
        # cross-competition lookback already used elsewhere for them.
        try:
            source_matches = fetch_team_recent_matches_extended(league, team_name, limit=50)
        except FootballDataError:
            source_matches = fetch_league_matches(league)
        expected_competition_code = None  # national-team lookback is intentionally cross-competition
    else:
        source_matches = fetch_league_matches(league)
        # RIGID SINGLE-COMPETITION FILTER: /competitions/{code}/matches
        # already scopes the request to this league alone (a domestic cup,
        # a European cup, or a friendly can never be returned here), but we
        # additionally cross-check each match's own "competition.code"
        # field when the payload provides one, as a belt-and-suspenders
        # guarantee that no Coppa Italia/Champions League/friendly fixture
        # can ever leak into a league-scoped season average.
        expected_competition_code = FOOTBALL_DATA_COMPETITIONS[league]

    return tuple(
        match
        for match in source_matches
        if _match_has_final_score(match)
        and (
            expected_competition_code is None
            or not isinstance(match.get("competition"), dict)
            or match["competition"].get("code") == expected_competition_code
        )
        and (
            match["homeTeam"].get("id") == team_id
            or match["awayTeam"].get("id") == team_id
            or match["homeTeam"].get("name") == team_name
            or match["awayTeam"].get("name") == team_name
        )
    )


@st.cache_data(ttl=300, show_spinner=False)
def fetch_team_live_stats(league: str, team_name: str) -> LiveTeamStats:
    """CURRENT-SEASON-ONLY statistics for `team_name`: goals, the shots/
    corners/cards/fouls baseline, Recent Form and the Current Form Rating
    input are all derived EXCLUSIVELY from 2026/27 FINISHED fixtures — see
    the Weighted Rating Engine notes above BASE_RATING_WEIGHT/
    FORM_RATING_WEIGHT. The previous season's signal (2025/26) is no
    longer blended into these match-level statistics at all: it flows
    only into the Base Rating, via the final league standings (see
    resolve_base_rating/fetch_previous_season_standings), keeping the two
    data-frames — 'last season's final table' and 'this season's games' —
    strictly separate, as required."""
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
        # instead — still exclusively "current" fixtures (qualifiers,
        # finals, Nations League, friendlies already played), never a
        # blend with a "previous campaign" concept that doesn't cleanly
        # exist for national sides.
        try:
            extended_matches = fetch_team_recent_matches_extended(league, team_name)
            current_fixtures = _team_fixtures(extended_matches)[:NATIONAL_TEAM_MATCH_WINDOW]
        except FootballDataError:
            current_fixtures = _team_fixtures(fetch_league_matches(league))[:NATIONAL_TEAM_MATCH_WINDOW]
    else:
        current_fixtures = _team_fixtures(fetch_league_matches(league))[:CLUB_MATCH_LOOKBACK]

    # Partite REALI disputate nella stagione in corso: base per la Modalità
    # Inizio Stagione (vedi EARLY_SEASON_MATCHDAY_THRESHOLD) e per lo
    # shrinkage del Current Form Rating (vedi REGRESSION_TO_MEAN_SAMPLE_SIZE).
    current_season_matches = len(current_fixtures)

    goals_for = goals_against = 0.0
    home_matches = away_matches = 0.0
    clean_sheets = 0
    recent_results: list[str] = []
    recent_points: list[int] = []
    recent_match_details: list[dict[str, object]] = []

    for fixture_item in current_fixtures:
        home_data = fixture_item.get("homeTeam", {})
        away_data = fixture_item.get("awayTeam", {})
        score = fixture_item.get("score", {})
        home_goals_reg, away_goals_reg = _regulation_time_score(score) if isinstance(score, dict) else (None, None)
        is_home = home_data.get("id") == team_id
        scored = home_goals_reg if is_home else away_goals_reg
        conceded = away_goals_reg if is_home else home_goals_reg
        if scored is None or conceded is None:
            continue

        goals_for += scored
        goals_against += conceded
        if conceded == 0:
            clean_sheets += 1
        if is_home:
            home_matches += 1
        else:
            away_matches += 1

        # Form Factor: le prime FORM_MATCHES_WINDOW partite (la lista è già
        # ordinata dalla più recente), tutte di stagione corrente.
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

    baseline = MICRO_EVENT_BASELINES[FOOTBALL_DATA_COMPETITIONS[league]]
    # The provider has no micro-event endpoint. Scale the transparent baseline
    # slightly with recent scoring, while keeping the source distinction clear.
    # With zero matches played yet this season, keep the baseline unscaled
    # (scoring_factor=1.0) rather than dividing by zero — the Dynamic Decay
    # Tier/Stats blend downstream gives this raw value 0% weight anyway.
    scoring_factor = clamp(0.88 + (goals_for / matches) * 0.08, 0.88, 1.12) if matches > 0 else 1.0
    form_factor = compute_form_factor(recent_points)

    return LiveTeamStats(
        team_id=team_id,
        team_name=team_name,
        matches=matches,
        home_matches=home_matches,
        away_matches=away_matches,
        goals_for=goals_for,
        goals_against=goals_against,
        home_goals_for=0.0,
        home_goals_against=0.0,
        away_goals_for=0.0,
        away_goals_against=0.0,
        total_shots=baseline["shots"] * scoring_factor * matches,
        shots_on_target=baseline["shots_on_target"] * scoring_factor * matches,
        corners=baseline["corners"] * matches,
        cards=baseline["cards"] * matches,
        fouls=baseline["fouls"] * matches,
        recent_form=tuple(recent_results),
        recent_matches=tuple(recent_match_details),
        form_factor=form_factor,
        current_season_matches=current_season_matches,
        clean_sheets=clean_sheets,
    )


@st.cache_data(ttl=300, show_spinner=False)
def fetch_previous_season_standings(league: str) -> dict[str, dict[str, float]]:
    """Fetches the FINAL league table of the PREVIOUS season (2025/26) via
    Football-Data.org's dedicated /standings endpoint (the overall 'TOTAL'
    table) — the dominant signal for each team's Base Rating (see
    resolve_base_rating). Returns {team_name: {"position", "points",
    "played", "total_teams"}}. Raises FootballDataError if the API/tier
    cannot provide it (season not covered on the plan in use, or a network
    failure) — callers fall back gracefully to the pure blasone (Team
    Tier) rating in that case, exactly like every other data source in
    this app."""
    competition_code = FOOTBALL_DATA_COMPETITIONS[league]
    previous_season = current_season_start() - 1
    payload = _football_data_request(
        f"/competitions/{competition_code}/standings",
        {"season": previous_season},
    )
    standings = payload.get("standings", [])
    if not isinstance(standings, list):
        raise FootballDataError(f"No previous-season standings available for {league}.")

    table_rows: list[dict[str, object]] = []
    for group in standings:
        if not isinstance(group, dict):
            continue
        # "TOTAL" is the overall regular-season table; HOME/AWAY splits (and
        # any per-group tables in cup-style competitions) are skipped in
        # favor of the single overall final ranking.
        if group.get("type") != "TOTAL":
            continue
        for row in group.get("table", []) or []:
            if not isinstance(row, dict):
                continue
            team = row.get("team", {})
            team_name = team.get("name") if isinstance(team, dict) else None
            position = row.get("position")
            points = row.get("points")
            played = row.get("playedGames")
            if isinstance(team_name, str) and isinstance(position, int):
                table_rows.append(
                    {
                        "name": team_name,
                        "position": position,
                        "points": float(points) if isinstance(points, (int, float)) else 0.0,
                        "played": int(played) if isinstance(played, int) else 0,
                    }
                )

    if not table_rows:
        raise FootballDataError(f"Previous-season table is empty for {league}.")

    total_teams = len(table_rows)
    return {
        row["name"]: {
            "position": row["position"],
            "points": row["points"],
            "played": row["played"],
            "total_teams": total_teams,
        }
        for row in table_rows
    }


def previous_season_position_rating(position: int, total_teams: int) -> float:
    """Maps a previous-season FINAL league position to a rating on the same
    1280-1750 scale as TEAM_TIER_PROFILES (1st place → ~1750, last place →
    ~1280) via linear interpolation on finishing-position percentile. This
    is the DOMINANT signal inside a team's Base Rating (see
    resolve_base_rating): a club that actually finished mid-table last
    season starts this season with a mid-table Base Rating regardless of
    historical blasone — e.g. a team finishing 6th gets a Champions-
    contention Base Rating rather than a title-race one; a team that
    survived on the final matchday gets a bottom-half Base Rating."""
    if total_teams <= 1:
        return TEAM_TIER_PROFILES[TEAM_TIER_DEFAULT]["rating"]
    percentile = clamp((position - 1) / (total_teams - 1), 0.0, 1.0)  # 0 = 1st place, 1 = last
    top_rating = TEAM_TIER_PROFILES[1]["rating"]
    bottom_rating = TEAM_TIER_PROFILES[5]["rating"]
    return top_rating - (top_rating - bottom_rating) * percentile


def resolve_base_rating(league: str, team: str) -> tuple[float, str]:
    """BASE RATING (BASE_RATING_WEIGHT, 70-75% of the final Weighted
    Rating): blends the team's historical blasone (Team Tier dictionary,
    lookup_team_tier) with its PREVIOUS-SEASON (2025/26) final league
    position — the DOMINANT component inside the Base Rating
    (PREVIOUS_SEASON_WEIGHT_IN_BASE, 70% of it) whenever that final table
    is available for this team in this competition. Falls back to pure
    blasone when it isn't (promoted from a division/league not tracked
    here, national-team competition, or an API/tier limitation) — in that
    fallback case the Base Rating is, appropriately, exactly the old Team
    Tier rating. Returns (base_rating, source_label) for transparency in
    the engine note."""
    blasone_rating = team_tier_profile(team)["rating"]
    if is_national_team_competition(league):
        return blasone_rating, "blasone only (national team)"
    try:
        standings = fetch_previous_season_standings(league)
    except FootballDataError:
        return blasone_rating, "blasone only (2025/26 table unavailable)"
    row = standings.get(team)
    if row is None:
        return blasone_rating, "blasone only (not in 2025/26 table)"
    previous_season_rating = previous_season_position_rating(int(row["position"]), int(row["total_teams"]))
    base_rating = (
        BLASONE_WEIGHT_IN_BASE * blasone_rating
        + PREVIOUS_SEASON_WEIGHT_IN_BASE * previous_season_rating
    )
    return base_rating, f"2025/26 finish {int(row['position'])}/{int(row['total_teams'])}"


def compute_current_form_rating(stats: "LiveTeamStats") -> float:
    """CURRENT FORM RATING (FORM_RATING_WEIGHT, 25-30% of the final
    Weighted Rating): reflects EXCLUSIVELY the team's on-pitch output in
    the CURRENT season (2026/27) — goals scored/conceded per match this
    season, converted into a rating centered on the league average
    (BASE_RATING=1500), completely independent of blasone or of last
    season's standing (that signal lives only in the Base Rating — see
    resolve_base_rating). With a small sample of matches played so far,
    the estimate is shrunk toward the neutral league average via
    _shrink_to_mean (same Bayesian-style safeguard used elsewhere in the
    engine), so 1-2 flukey results early in the season cannot swing
    25-30% of a team's rating; with zero matches played, the Form
    component is fully neutral (1500) and the Weighted Rating collapses
    onto the Base Rating alone — exactly the intended behaviour before a
    team has played a single game this season."""
    if stats.matches <= 0:
        return BASE_RATING
    attack_multiplier = _shrink_to_mean(_stats_multiplier(stats.goals_for / stats.matches), stats.matches)
    defense_multiplier = _shrink_to_mean(_stats_multiplier(stats.goals_against / stats.matches), stats.matches)
    return _stats_rating(attack_multiplier, defense_multiplier)


def team_current_scoring_tempo(stats: "LiveTeamStats") -> float:
    """Current-season (2026/27 only) goals-scored-per-match tempo for a
    team, used exclusively to classify the LOW-SCORING/TACTICAL Match
    Profile (see classify_match_profile). Falls back to the neutral league
    average when the team hasn't played yet this season, so an empty
    sample never falsely looks 'defensive'."""
    if stats.matches <= 0:
        return LEAGUE_AVERAGE_GOALS_PER_TEAM
    return stats.goals_for / stats.matches


def classify_match_profile(
    rating_home: float,
    rating_away: float,
    pct_rating_distance: float,
    home_scoring_tempo: float,
    away_scoring_tempo: float,
) -> str:
    """DYNAMIC MATCH PROFILES: classifies the fixture into one of the three
    dedicated xG bands (see the constants above BIG_MATCH_RATING_THRESHOLD)
    plus a 'standard' fallback, so the Rating->xG curve stops averaging
    every kind of match toward the same narrow band. Checked in priority
    order:
    1) 'mismatch' — a real quality gap (>= MISMATCH_RATING_DISTANCE_
       THRESHOLD) between the two Ratings takes precedence over the other
       profiles: a lopsided Big-vs-minnow fixture should never come out
       tactically tight nor an open shootout on both ends.
    2) 'big_match' — both Ratings individually clear BIG_MATCH_RATING_
       THRESHOLD (checked on EACH side, not the average, so one strong
       team paired with a weak one cannot masquerade as two Big teams).
    3) 'tactical' — both teams' actual current-season scoring tempo sits
       at or below TACTICAL_SCORING_TEMPO_THRESHOLD goals/game.
    4) 'standard' — none of the above; the general-purpose curve applies
       (BASE_TOTAL_EXPECTED_GOALS, TOTAL_GOALS_MISMATCH_BONUS,
       BALANCED_MATCH_RATING_DISTANCE_THRESHOLD/SUPREMACY_DAMPING)."""
    if pct_rating_distance >= MISMATCH_RATING_DISTANCE_THRESHOLD:
        return "mismatch"
    if rating_home >= BIG_MATCH_RATING_THRESHOLD and rating_away >= BIG_MATCH_RATING_THRESHOLD:
        return "big_match"
    if home_scoring_tempo <= TACTICAL_SCORING_TEMPO_THRESHOLD and away_scoring_tempo <= TACTICAL_SCORING_TEMPO_THRESHOLD:
        return "tactical"
    return "standard"


def compute_season_stats_summary(league: str, team: str) -> dict[str, object]:
    # Builds the full "Season Stats 2026/27" metric set for one team,
    # independent of any match/opponent (unlike build_match_model, which
    # always needs a home AND an away side).
    #
    # season totals/averages and the L5 window are derived from
    # fetch_team_season_matches — the UNCAPPED, FINISHED-only,
    # competition-scoped match list — instead of the (intentionally capped,
    # for Rating-Engine stability) LiveTeamStats used elsewhere. The Global
    # Power Rating shown here still comes from fetch_team_live_stats/
    # resolve_base_rating/compute_current_form_rating (the Rating Engine's
    # own, deliberately smoothed pipeline, untouched by this tab) so it
    # stays identical in methodology to the match-analysis page.
    #
    # PARSING: goals are read straight off each match's own home/away team
    # IDs (is_home = home_data.get("id") == team_id, checked before ANY
    # value is pulled), never off a fixed array position or the opponent's
    # figure — the exact requirement of "verify home/away before extracting
    # the value". Football-Data.org returns exactly one score object per
    # match (no separate per-team statistics array to index into), so there
    # is no "wrong array element" failure mode possible here; this loop is
    # the single source of truth for that parsing step, reused by both the
    # season and the L5 windows below.
    #
    # MICRO-EVENT CALIBRATION (audited): shots/corners/cards/fouls/offsides
    # have no Football-Data.org endpoint at all, so they are estimated from
    # the league baseline (MICRO_EVENT_BASELINES) via a ratio-based
    # calibration factor tied to the team's REAL goals-for/against average
    # for that window (see SHOT_CALIBRATION_RATIO_SLOPE) — recalibrated to
    # scale meaningfully further for genuinely elite or genuinely weak
    # sides than the old, far too narrow +-12% band, plus explicit realism
    # floors (REALISM_FLOOR_*) so no metric can ever read below a sane
    # professional-football minimum. Every value is rounded to exactly 2
    # decimals. Tagged "live" (direct Football-Data.org results) or
    # "estimate" (baseline-derived) — the UI must only ever present
    # "estimate" metrics with a visible label, never as literal provider data.
    season_matches_raw = fetch_team_season_matches(league, team)

    team_map = dict(fetch_league_teams(league))
    team_id = next((id_ for id_, name in team_map.items() if name == team), None)

    match_log: list[dict[str, object]] = []
    season_goals_for = 0.0
    season_goals_against = 0.0
    season_clean_sheets = 0
    for fixture_item in season_matches_raw:
        home_data = fixture_item.get("homeTeam", {})
        away_data = fixture_item.get("awayTeam", {})
        score = fixture_item.get("score", {})
        home_goals_reg, away_goals_reg = _regulation_time_score(score) if isinstance(score, dict) else (None, None)
        # Explicit home/away check BEFORE extracting the value — never a
        # fixed array position, never the opponent's figure.
        is_home = home_data.get("id") == team_id
        scored = home_goals_reg if is_home else away_goals_reg
        conceded = away_goals_reg if is_home else home_goals_reg
        if scored is None or conceded is None:
            continue
        season_goals_for += scored
        season_goals_against += conceded
        if conceded == 0:
            season_clean_sheets += 1
        opponent_name = str((away_data if is_home else home_data).get("name", "Unknown"))
        if scored > conceded:
            result = "W"
        elif scored == conceded:
            result = "D"
        else:
            result = "L"
        match_log.append(
            {
                "date": str(fixture_item.get("utcDate", ""))[:10],
                "venue": "Home" if is_home else "Away",
                "opponent": opponent_name,
                "scored": scored,
                "conceded": conceded,
                "result": result,
            }
        )
    # fetch_team_season_matches already returns matches most-recent-first
    # (same convention as fetch_league_matches), so match_log preserves that
    # chronological-reverse order without any extra sorting needed.
    matches = float(len(match_log))
    finished_match_count = len(match_log)  # exact FINISHED count for the audit panel

    # Global Power Rating: unchanged Rating-Engine pipeline (deliberately
    # uses the capped, smoothed LiveTeamStats — not part of this audit).
    rating_stats = fetch_team_live_stats(league, team)
    base_rating, base_source = resolve_base_rating(league, team)
    form_rating = compute_current_form_rating(rating_stats)
    power_rating = get_base_rating_weight() * base_rating + get_form_rating_weight() * form_rating

    baseline = MICRO_EVENT_BASELINES[FOOTBALL_DATA_COMPETITIONS[league]]
    team_tier = lookup_team_tier(team)
    is_top_team_tier = team_tier in (1, 2)
    shots_on_target_floor = REALISM_FLOOR_SHOTS_ON_TARGET_ELITE if is_top_team_tier else REALISM_FLOOR_SHOTS_ON_TARGET
    opta_sot_multiplier = opta_alignment_multiplier(team_tier)
    opta_volume_multiplier = opta_alignment_multiplier(team_tier, dampen=True)

    def _calibration_factor(goals_per_match: float) -> float:
        ratio = goals_per_match / LEAGUE_AVERAGE_GOALS_PER_TEAM if LEAGUE_AVERAGE_GOALS_PER_TEAM > 0 else 1.0
        return clamp(
            SHOT_CALIBRATION_FLOOR_FACTOR + ratio * SHOT_CALIBRATION_RATIO_SLOPE,
            SHOT_CALIBRATION_FLOOR_FACTOR,
            SHOT_CALIBRATION_CEILING_FACTOR,
        )

    def _build_window(goals_for_avg: float, goals_against_avg: float) -> dict[str, float]:
        # Builds one full set of PER-MATCH AVERAGES (sanity-checked against
        # the realism floors and rounded to exactly 2 decimals) for ONE
        # time window (SEASON or L5), given that window's real goals-for/
        # against average. Shared by both windows so Season and L5 always
        # use identical calibration logic — only their input goals differ,
        # which is exactly what lets the L5 window show a genuine trend.
        scoring_factor = _calibration_factor(goals_for_avg)
        conceding_factor = _calibration_factor(goals_against_avg)
        # Discipline moves the OPPOSITE way from attacking dominance: a
        # team that controls the ball more (high scoring_factor) commits
        # fewer fouls/cards but, by drawing more fouls in the final third,
        # is fouled MORE (fouls_suffered ties directly to scoring_factor
        # instead) — a standard, defensible football tactical pattern.
        discipline_factor = clamp(
            2.0 - scoring_factor, SHOT_CALIBRATION_FLOOR_FACTOR, SHOT_CALIBRATION_CEILING_FACTOR
        )

        # OPTA/SOFASCORE TIER ALIGNMENT: applied on top of the goals-based
        # calibration above (opta_sot_multiplier full-strength for Shots on
        # Target, opta_volume_multiplier dampened for Total Shots/Offsides/
        # Fouls) — see OPTA_ALIGNMENT_MULTIPLIERS. Applied only to the
        # team's OWN attacking-side figures (Shots on Target/Total Shots
        # for, Offsides, Fouls Suffered); the "against" figures the team
        # faces (Shots on Target Against, Fouls Committed) instead scale
        # INVERSELY with the SAME tier multiplier, since an elite squad
        # both creates more chances of its own AND concedes proportionally
        # fewer to the opposition.
        total_shots_avg = max(baseline["shots"] * scoring_factor * opta_volume_multiplier, REALISM_FLOOR_TOTAL_SHOTS)
        shots_on_target_avg = max(
            baseline["shots_on_target"] * scoring_factor * opta_sot_multiplier, shots_on_target_floor
        )
        shots_on_target_against_avg = max(
            baseline["shots_on_target"] * conceding_factor / opta_sot_multiplier, REALISM_FLOOR_SHOTS_ON_TARGET
        )
        xg_for_avg = shots_on_target_avg * XG_PROXY_SHOT_CONVERSION_RATE
        xg_against_avg = shots_on_target_against_avg * XG_PROXY_SHOT_CONVERSION_RATE
        saves_avg = max(shots_on_target_against_avg - goals_against_avg, 0.0)
        corners_for_avg = max(baseline["corners"] * scoring_factor, REALISM_FLOOR_CORNERS_PER_MATCH)
        corners_against_avg = max(baseline["corners"] * conceding_factor, REALISM_FLOOR_CORNERS_PER_MATCH)
        fouls_committed_avg = max(
            baseline["fouls"] * discipline_factor / opta_volume_multiplier, REALISM_FLOOR_FOULS_PER_MATCH
        )
        fouls_suffered_avg = max(
            baseline["fouls"] * scoring_factor * opta_volume_multiplier, REALISM_FLOOR_FOULS_PER_MATCH
        )
        offsides_avg = baseline["offsides"] * scoring_factor * opta_volume_multiplier
        cards_avg = baseline["cards"] * discipline_factor
        red_cards_avg = cards_avg * RED_CARD_SHARE_OF_TOTAL_CARDS
        yellow_cards_avg = cards_avg - red_cards_avg

        return {
            "xg_for": round(xg_for_avg, 2),
            "xg_against": round(xg_against_avg, 2),
            "total_shots": round(total_shots_avg, 2),
            "shots_on_target": round(shots_on_target_avg, 2),
            "saves": round(saves_avg, 2),
            "offsides": round(offsides_avg, 2),
            "corners_for": round(corners_for_avg, 2),
            "corners_against": round(corners_against_avg, 2),
            "fouls_committed": round(fouls_committed_avg, 2),
            "fouls_suffered": round(fouls_suffered_avg, 2),
            "yellow_cards": round(yellow_cards_avg, 2),
            "red_cards": round(red_cards_avg, 2),
        }

    season_goals_for_avg = season_goals_for / matches if matches > 0 else 0.0
    season_goals_against_avg = season_goals_against / matches if matches > 0 else 0.0
    season_clean_sheets_avg = season_clean_sheets / matches if matches > 0 else 0.0
    season_window = _build_window(season_goals_for_avg, season_goals_against_avg)

    # --- L5: exactly the last 5 (or fewer, never padded) FINISHED matches --
    l5_entries = match_log[:FORM_MATCHES_WINDOW]
    l5_count = len(l5_entries)
    l5_goals_for_avg = sum(float(m["scored"]) for m in l5_entries) / l5_count if l5_count > 0 else 0.0
    l5_goals_against_avg = sum(float(m["conceded"]) for m in l5_entries) / l5_count if l5_count > 0 else 0.0
    l5_clean_sheets_avg = (
        sum(1 for m in l5_entries if float(m["conceded"]) == 0) / l5_count if l5_count > 0 else 0.0
    )
    l5_window = _build_window(l5_goals_for_avg, l5_goals_against_avg) if l5_count > 0 else season_window

    return {
        "team": team,
        "matches": finished_match_count,
        "l5_matches": l5_count,
        "power_rating": power_rating,
        "base_rating": base_rating,
        "base_source": base_source,
        "form_rating": form_rating,
        "match_log": match_log,
        "offense": [
            ("Goals Scored", round(season_goals_for_avg, 2), round(l5_goals_for_avg, 2), "live", True),
            ("Expected Goals (xG) For", season_window["xg_for"], l5_window["xg_for"], "estimate", True),
            ("Total Shots", season_window["total_shots"], l5_window["total_shots"], "estimate", True),
            ("Shots on Target", season_window["shots_on_target"], l5_window["shots_on_target"], "estimate", True),
            ("Offsides", season_window["offsides"], l5_window["offsides"], "estimate", False),
        ],
        "defense": [
            ("Goals Conceded", round(season_goals_against_avg, 2), round(l5_goals_against_avg, 2), "live", False),
            ("Expected Goals (xG) Against", season_window["xg_against"], l5_window["xg_against"], "estimate", False),
            ("Goalkeeper Saves", season_window["saves"], l5_window["saves"], "estimate", True),
            ("Clean Sheets", round(season_clean_sheets_avg, 2), round(l5_clean_sheets_avg, 2), "live", True),
        ],
        "discipline": [
            ("Corners For", season_window["corners_for"], l5_window["corners_for"], "estimate", True),
            ("Corners Against", season_window["corners_against"], l5_window["corners_against"], "estimate", False),
            ("Fouls Committed", season_window["fouls_committed"], l5_window["fouls_committed"], "estimate", False),
            ("Fouls Suffered", season_window["fouls_suffered"], l5_window["fouls_suffered"], "estimate", True),
            ("Yellow Cards", season_window["yellow_cards"], l5_window["yellow_cards"], "estimate", False),
            ("Red Cards", season_window["red_cards"], l5_window["red_cards"], "estimate", False),
        ],
    }


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


# --- Form Factor (componente dinamica del Global Power Rating) --------------
# Le medie usate finora (fino a 8 partite, non pesate) non distinguono una
# squadra che sta attraversando un buon momento da una in crisi di risultati.
# Il Form Factor pesa i risultati più recenti più di quelli lontani e produce
# il moltiplicatore dinamico usato da global_power_rating() sopra.
FORM_MATCHES_WINDOW = 5
# Numero di partite recenti considerate nel calcolo del Form Factor.

FORM_RECENCY_WEIGHTS: tuple[float, ...] = (1.0, 0.85, 0.7, 0.55, 0.4)
# Peso decrescente per ciascuna delle ultime FORM_MATCHES_WINDOW partite,
# dalla più recente alla meno recente.

FORM_FACTOR_MIN = 0.72
FORM_FACTOR_MAX = 1.28
# DYNAMIC FORM & MOMENTUM: range allargato da 0.85-1.15 a 0.72-1.28 — il
# momento di forma recente (ultime FORM_MATCHES_WINDOW partite, tipicamente
# 5-8) deve poter pesare più del solo nome/blasone della squadra. Una Big in
# crisi di risultati (striscia di sconfitte/pareggi, xG realizzato basso)
# subisce ora una penalizzazione di Attacco/Difesa (e, tramite l'aggiornamento
# di rating_finale in build_match_model, anche del Global Power Rating
# mostrato in UI) fino al 28% invece del 15% precedente — abbastanza da farla
# scendere realisticamente di una Fascia effettiva contro un avversario in
# salute. Simmetricamente, una squadra di media/bassa classifica in un momento
# di grande forma vede il proprio moltiplicatore di Attacco/Difesa crescere
# fino al 28%, rendendola competitiva o perfino favorita (1-0, 2-1, pareggio)
# contro una Big appannata.


def compute_form_factor(
    recent_points: Sequence[int], season_weights: Sequence[float] | None = None
) -> float:
    """Form Factor dinamico: calcola un moltiplicatore intorno a 1.0 pesando
    i punti (Vittoria=3, Pareggio=1, Sconfitta=0) delle ultime partite con
    FORM_RECENCY_WEIGHTS. `season_weights` è mantenuto per compatibilità di
    firma ma nella pipeline attuale riceve sempre None (default: peso 1.0
    per ogni partita): fetch_team_live_stats alimenta questa funzione
    esclusivamente con le ultime partite della STAGIONE CORRENTE, mai con
    un blend con la stagione precedente (quel segnale vive solo nel Base
    Rating — vedi resolve_base_rating). Una squadra in ottima forma recente
    arriva fino a FORM_FACTOR_MAX, una in crisi di risultati scende fino a
    FORM_FACTOR_MIN. Senza dati recenti restituisce 1.0 (nessuna correzione)."""
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

    # --- 1. Statistiche grezze di stagione corrente (tiri, corner, cartellini,
    # falli). I gol per/contro NON alimentano più questo step: confluiscono
    # ora esclusivamente nel Current Form Rating (vedi
    # compute_current_form_rating, chiamato più sotto), che legge
    # home_stats/away_stats direttamente. _safe_average evita un crash se
    # una squadra non ha ancora giocato nessuna partita in questa stagione
    # (early preseason): i tiri/tiri in porta ricevono comunque peso 0% nel
    # blend di Fascia più sotto, corner/cartellini/falli usano la baseline
    # di lega come fallback realistico. -----------------------------------
    micro_baseline_for_fallback = MICRO_EVENT_BASELINES[FOOTBALL_DATA_COMPETITIONS[league]]
    home_sot_raw = _safe_average(home_stats.shots_on_target, home_stats.matches)
    away_sot_raw = _safe_average(away_stats.shots_on_target, away_stats.matches)
    home_shots_raw = _safe_average(home_stats.total_shots, home_stats.matches)
    away_shots_raw = _safe_average(away_stats.total_shots, away_stats.matches)
    home_corners_raw = _safe_average(home_stats.corners, home_stats.matches, fallback=micro_baseline_for_fallback["corners"])
    away_corners_raw = _safe_average(away_stats.corners, away_stats.matches, fallback=micro_baseline_for_fallback["corners"])
    home_cards_raw = _safe_average(home_stats.cards, home_stats.matches, fallback=micro_baseline_for_fallback["cards"])
    away_cards_raw = _safe_average(away_stats.cards, away_stats.matches, fallback=micro_baseline_for_fallback["cards"])
    fouls = _safe_average(home_stats.fouls, home_stats.matches, fallback=micro_baseline_for_fallback["fouls"])
    fouls += _safe_average(away_stats.fouls, away_stats.matches, fallback=micro_baseline_for_fallback["fouls"])

    # --- 2. WEIGHTED RATING ENGINE (70/30 MODEL) -------------------------------
    # RATING FINALE = BASE_RATING_WEIGHT x Base Rating (blasone + classifica
    # finale 2025/26, dominata da quest'ultima) + FORM_RATING_WEIGHT x
    # Current Form Rating (sola stagione 2026/27) — vedi resolve_base_rating
    # / compute_current_form_rating e le relative costanti di peso.
    early_season = is_early_season_match(home_stats, away_stats)

    home_tier = team_tier_profile(home)
    away_tier = team_tier_profile(away)
    home_tier_number = lookup_team_tier(home)
    away_tier_number = lookup_team_tier(away)
    home_tier_weight, home_stats_weight = dynamic_decay_weights(home_stats.current_season_matches)
    away_tier_weight, away_stats_weight = dynamic_decay_weights(away_stats.current_season_matches)

    home_base_rating, home_base_source = resolve_base_rating(league, home)
    away_base_rating, away_base_source = resolve_base_rating(league, away)
    home_form_rating = compute_current_form_rating(home_stats)
    away_form_rating = compute_current_form_rating(away_stats)

    rating_finale_home = get_base_rating_weight() * home_base_rating + get_form_rating_weight() * home_form_rating
    rating_finale_away = get_base_rating_weight() * away_base_rating + get_form_rating_weight() * away_form_rating

    # --- 3. Slider manuali (Mercato/Infortuni) + Indice di Affaticamento &
    # Turnover (Fase 2), SOMMATI fra loro (nessuno sovrascrive l'altro) e
    # collassati in un UNICO shift di Rating (positivo = squadra rinforzata
    # su entrambe le fasi, negativo = indebolita su entrambe) — coerente col
    # fatto che il nuovo motore genera gli xG da un singolo Rating anziché
    # da moltiplicatori separati di Attacco/Difesa come in passato. --------
    combined_adjustment_home = manual_factor_home + (fatigue_attack_malus_home - fatigue_defense_malus_home) / 2
    combined_adjustment_away = manual_factor_away + (fatigue_attack_malus_away - fatigue_defense_malus_away) / 2
    rating_finale_home += combined_adjustment_home * RATING_SCALE
    rating_finale_away += combined_adjustment_away * RATING_SCALE

    # --- 4. xG GENERATION: curva di conversione Rating -> Expected Goals ------
    # rating_diff include il fattore campo (HOME_ADVANTAGE_RATING) SOLO per
    # calcolare la 'supremazia' di gol fra le due squadre; pct_rating_distance
    # (usata sia per classificare uno 'Scontro tra pari livello' nel profilo
    # STANDARD sia per il profilo MISMATCH) si basa invece sui Rating grezzi,
    # SENZA fattore campo, per riflettere il solo gap di qualità reale fra le
    # due squadre.
    rating_diff = (rating_finale_home + HOME_ADVANTAGE_RATING) - rating_finale_away
    average_rating = max((rating_finale_home + rating_finale_away) / 2, 1.0)
    pct_rating_distance = clamp(abs(rating_finale_home - rating_finale_away) / average_rating, 0.0, 1.0)
    supremacy = SUPREMACY_RATING_SENSITIVITY * rating_diff

    # DYNAMIC MATCH PROFILES (vedi classify_match_profile): sceglie quale
    # delle 3 bande dedicate — Tactical (A), Big Match (B), Mismatch (C) —
    # applicare, con un profilo STANDARD di ripiego per tutto il resto.
    home_scoring_tempo = team_current_scoring_tempo(home_stats)
    away_scoring_tempo = team_current_scoring_tempo(away_stats)
    match_profile = classify_match_profile(
        rating_finale_home, rating_finale_away, pct_rating_distance, home_scoring_tempo, away_scoring_tempo
    )

    if match_profile == "tactical":
        # Profilo A — LOW-SCORING/TACTICAL (es. Parma vs Monza): xG per
        # squadra contenuti in [0.70, 0.95], per far emergere con
        # naturalezza 0-0/1-0/1-1.
        total_expected_goals = TACTICAL_TOTAL_EXPECTED_GOALS
        home_lambda = clamp(total_expected_goals / 2 + supremacy / 2, TACTICAL_XG_MIN, TACTICAL_XG_MAX)
        away_lambda = clamp(total_expected_goals / 2 - supremacy / 2, TACTICAL_XG_MIN, TACTICAL_XG_MAX)
    elif match_profile == "big_match":
        # Profilo B — HIGH-PROFILE BIG MATCH (es. Barcelona vs Real
        # Madrid): xG per squadra alzati in [1.75, 2.20], per favorire
        # simulazioni spettacolari (2-2, 2-1, 3-2, 3-1).
        total_expected_goals = BIG_MATCH_TOTAL_EXPECTED_GOALS
        home_lambda = clamp(total_expected_goals / 2 + supremacy / 2, BIG_MATCH_XG_MIN, BIG_MATCH_XG_MAX)
        away_lambda = clamp(total_expected_goals / 2 - supremacy / 2, BIG_MATCH_XG_MIN, BIG_MATCH_XG_MAX)
    elif match_profile == "mismatch":
        # Profilo C — MISMATCHED / HIGH-TIER VS LOW-TIER (es. Inter vs
        # Monza, Arsenal vs Coventry): tetto della favorita in
        # [2.65, 2.85], sfavorita in [0.45, 0.65], interpolati linearmente
        # sull'intensità del gap fra MISMATCH_RATING_DISTANCE_THRESHOLD (il
        # bordo più mite di ciascuna forbice) e MISMATCH_MAX_INTENSITY_
        # DISTANCE (il bordo più estremo) — indipendente dal totale/
        # supremacy condivisi con gli altri profili, perché lo scarto
        # assoluto richiesto qui è troppo ampio per la stessa sensibilità
        # lineare.
        intensity_span = max(MISMATCH_MAX_INTENSITY_DISTANCE - MISMATCH_RATING_DISTANCE_THRESHOLD, 1e-9)
        mismatch_intensity = clamp(
            (pct_rating_distance - MISMATCH_RATING_DISTANCE_THRESHOLD) / intensity_span, 0.0, 1.0
        )
        favorite_lambda = MISMATCH_FAVORITE_XG_MIN + (MISMATCH_FAVORITE_XG_MAX - MISMATCH_FAVORITE_XG_MIN) * mismatch_intensity
        underdog_lambda = MISMATCH_UNDERDOG_XG_MAX - (MISMATCH_UNDERDOG_XG_MAX - MISMATCH_UNDERDOG_XG_MIN) * mismatch_intensity
        if rating_diff >= 0:
            home_lambda, away_lambda = favorite_lambda, underdog_lambda
        else:
            home_lambda, away_lambda = underdog_lambda, favorite_lambda
    else:
        # Profilo STANDARD (ripiego): curva generale già in uso, ma con un
        # totale gol dedicato e più basso per gli 'Scontri tra pari livello'
        # (vedi BALANCED_MATCH_TOTAL_EXPECTED_GOALS) — non solo supremacy
        # smorzata sopra un totale comunque alto, che altrimenti manteneva
        # entrambi i lambda sopra la soglia ~1.0 dove il Pareggio smette di
        # essere un esito macro competitivo con la Poisson.
        is_balanced_matchup = pct_rating_distance < BALANCED_MATCH_RATING_DISTANCE_THRESHOLD
        if is_balanced_matchup:
            supremacy *= BALANCED_MATCH_SUPREMACY_DAMPING
            total_expected_goals = BALANCED_MATCH_TOTAL_EXPECTED_GOALS
        else:
            total_expected_goals = BASE_TOTAL_EXPECTED_GOALS + TOTAL_GOALS_MISMATCH_BONUS * pct_rating_distance
        home_lambda = clamp(total_expected_goals / 2 + supremacy / 2, XG_HARD_FLOOR, XG_HARD_CAP)
        away_lambda = clamp(total_expected_goals / 2 - supremacy / 2, XG_HARD_FLOOR, XG_HARD_CAP)

    is_balanced_matchup = match_profile == "standard" and pct_rating_distance < BALANCED_MATCH_RATING_DISTANCE_THRESHOLD

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
    # OPTA/SOFASCORE TIER ALIGNMENT (shared with the Season Stats tab — see
    # opta_alignment_multiplier): lifts Shots on Target for genuinely elite
    # sides into the real Opta/Sofascore range, with Total Shots getting the
    # dampened version since shot VOLUME varies far less by Tier than shot
    # ACCURACY does in real data.
    home_opta_sot_mult = opta_alignment_multiplier(home_tier_number)
    away_opta_sot_mult = opta_alignment_multiplier(away_tier_number)
    home_opta_volume_mult = opta_alignment_multiplier(home_tier_number, dampen=True)
    away_opta_volume_mult = opta_alignment_multiplier(away_tier_number, dampen=True)
    home_shots = max(home_shots_blended * shot_boost * home_opta_volume_mult, 1.0)
    away_shots = max(away_shots_blended * shot_suppress * away_opta_volume_mult, 1.0)
    home_sot = max(home_sot_blended * shot_boost * home_opta_sot_mult, 0.3)
    away_sot = max(away_sot_blended * shot_suppress * away_opta_sot_mult, 0.3)
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
    engine_note += (
        f" · Weighted Rating: {home} Base {home_base_rating:.0f}/Form {home_form_rating:.0f} "
        f"({home_base_source}), {away} Base {away_base_rating:.0f}/Form {away_form_rating:.0f} "
        f"({away_base_source})"
    )
    match_profile_labels = {
        "tactical": "🔒 Low-Scoring/Tactical",
        "big_match": "🔥 High-Profile Big Match",
        "mismatch": "⚔️ Mismatched (High-Tier vs Low-Tier)",
        "standard": "⚖️ Standard",
    }
    engine_note += f" · Match Profile: {match_profile_labels.get(match_profile, match_profile.title())}"
    if is_balanced_matchup:
        engine_note += f" · 🤝 Balanced Matchup: Rating gap {pct_rating_distance:.1%} (<{BALANCED_MATCH_RATING_DISTANCE_THRESHOLD:.0%})"
    if match_profile == "standard" and (home_lambda >= XG_HARD_CAP or away_lambda >= XG_HARD_CAP):
        engine_note += f" · 🧢 xG Realism Cap active (max {XG_HARD_CAP:.2f} xG/team)"
    if match_profile == "standard" and (home_lambda <= XG_HARD_FLOOR or away_lambda <= XG_HARD_FLOOR):
        engine_note += f" · 🧊 xG Realism Floor active (min {XG_HARD_FLOOR:.2f} xG/team)"

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
# Preset Multi-Outcome groups: popular combinations of exact scores on
# which bookmakers often offer a single odds ('combined multi-goal/outcome').
# Each entry lists the 'Home-Away' scores included in the group.

MULTI_ESITO_CUSTOM_LABEL = "🎯 Custom Multi-Outcome"
# Special entry in the selector that activates the multiselect for manually
# picking exact scores (see render_multi_esito_tab).


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


def render_season_stats_tab() -> None:
    # Standalone team-stats archive: its own Competition/Team dropdowns,
    # independent of whichever match is selected on the Match Analysis page
    # (unique widget keys prefixed season_stats_ avoid clashing with the
    # main dashboard's league_select/home_select/away_select).
    st.markdown(
        "### 📊 Season Stats 2026/27\n"
        "Full per-team statistical archive for the current season: Season Average vs L5 Form Trend "
        "(last 5 games), per match."
    )

    col_league, col_team = st.columns(2)
    with col_league:
        season_stats_league = st.selectbox(
            "Competition",
            options=list(FOOTBALL_DATA_COMPETITIONS),
            key="season_stats_league",
        )

    try:
        team_rows = fetch_league_teams(season_stats_league)
    except FootballDataError as error:
        st.error(f"Football-Data.org unavailable: {error}")
        return
    teams = [name for _, name in team_rows]
    if not teams:
        st.warning("No teams available for this competition.")
        return

    if st.session_state.get("_season_stats_last_league") != season_stats_league:
        st.session_state["_season_stats_last_league"] = season_stats_league
        st.session_state["season_stats_team"] = teams[0]

    with col_team:
        season_stats_team = st.selectbox("Team", options=teams, key="season_stats_team")

    try:
        crests = fetch_team_crests(season_stats_league)
    except FootballDataError:
        crests = {}

    try:
        summary = compute_season_stats_summary(season_stats_league, season_stats_team)
    except FootballDataError as error:
        st.error(f"Football-Data.org data unavailable: {error}")
        return

    # --- Compact team banner: crest, name, matches played, Power Rating ---
    st.markdown("---")
    banner_crest_col, banner_name_col, banner_matches_col, banner_rating_col = st.columns([0.6, 2, 1.2, 1.2])
    with banner_crest_col:
        if crests.get(season_stats_team):
            st.image(crests[season_stats_team], width=64)
    with banner_name_col:
        st.markdown(f'<div class="team-name">{escape(season_stats_team)}</div>', unsafe_allow_html=True)
        st.caption(f"{season_stats_league} · Season 2026/27 · L5 window: {int(summary['l5_matches'])} games")
    with banner_matches_col:
        st.metric("Matches Played", f"{int(summary['matches'])}")
    with banner_rating_col:
        st.metric("Global Power Rating", f"{summary['power_rating']:.0f}")

    if summary["matches"] == 0:
        st.info(
            f"{season_stats_team} has not played a FINISHED match yet in the 2026/27 season — "
            "these figures will populate as fixtures are completed."
        )

    # --- Metric grids (Offense / Defense & Goalkeeping / Discipline & Set Pieces) --
    # Each card shows the SEASON average and the L5 (last 5 games) average
    # side by side, with a 🟢/🔴 WayneLab neon trend badge next to the L5
    # figure whenever the two windows diverge by more than
    # SIGNIFICANT_TREND_RELATIVE_THRESHOLD — green when the L5 trend moves
    # in the direction that's good for the team on that metric
    # (higher_is_better), red when it moves the other way. No badge at all
    # means the recent form is statistically in line with the season.
    def _trend_badge(season_avg: float, l5_avg: float, higher_is_better: bool) -> str:
        reference = max(abs(season_avg), 1e-6)
        relative_change = (l5_avg - season_avg) / reference
        if abs(relative_change) < SIGNIFICANT_TREND_RELATIVE_THRESHOLD:
            return ""
        improving = relative_change > 0 if higher_is_better else relative_change < 0
        return " 🟢" if improving else " 🔴"

    def _render_section(title: str, rows: list[tuple[str, float, float, str, bool]], columns: int) -> None:
        st.markdown(f"##### {title}")
        cards = []
        for label, season_avg, l5_avg, source_tag, higher_is_better in rows:
            tag_suffix = " 📡" if source_tag == "live" else " 🧮"
            badge = _trend_badge(season_avg, l5_avg, higher_is_better)
            value_text = f"{season_avg:.2f} Season | {l5_avg:.2f} L5{badge}"
            cards.append((label + tag_suffix, value_text))
        render_metric_cards(cards, columns=columns)

    _render_section("⚔️ Offense", summary["offense"], columns=3)
    _render_section("🛡️ Defense & Goalkeeping", summary["defense"], columns=2)
    _render_section("🟨 Discipline & Set Pieces", summary["discipline"], columns=3)

    st.caption(
        "📡 Live data, sourced directly from Football-Data.org results · 🧮 Estimate — Football-Data.org "
        "exposes no endpoint for this metric, so it is derived from the same transparent league baselines "
        "used elsewhere in the app (shots/corners/cards/fouls/offsides) plus a standard shot-on-target-to-goal "
        "conversion rate for xG, never presented as literal provider data. · 🟢/🔴 next to the L5 figure = the "
        "last-5-games trend is a significant improvement/decline versus the season average for that metric."
    )

    with st.expander("🔍 Data Integrity & Match Log", expanded=False):
        st.markdown(
            f"**FINISHED matches detected by the API for {escape(season_stats_team)} in "
            f"{escape(season_stats_league)} (2026/27):** {int(summary['matches'])}"
        )
        st.caption(
            "Season averages above = Sum(metric) / this exact count. If this number looks lower than what "
            "you see on an official source, the match is most likely still SCHEDULED/POSTPONED rather than "
            "FINISHED in Football-Data.org's data, or was played in a different competition than the one "
            "selected here (e.g. a Champions League fixture doesn't count toward a Ligue 1 average, by design)."
        )
        match_log = summary.get("match_log", [])
        if not match_log:
            st.info("No FINISHED matches on record yet for this team in this competition.")
        else:
            log_frame = pd.DataFrame(
                [
                    {
                        "Date": entry["date"] or "n/a",
                        "Venue": entry["venue"],
                        "Opponent": entry["opponent"],
                        "Score": f"{int(entry['scored'])}-{int(entry['conceded'])}",
                        "Result": entry["result"],
                    }
                    for entry in match_log
                ]
            )
            st.caption(f"L5 Form Trend above uses the top {min(5, len(match_log))} rows of this table (most recent first).")
            st.dataframe(log_frame, use_container_width=True, hide_index=True)

    st.markdown(
        '<div class="wl-data-disclaimer">ℹ️ Note: Data provided via Football-Data.org. Event definitions '
        '(shots on target, fouls) may slightly vary from Opta/Sofascore standard providers.</div>',
        unsafe_allow_html=True,
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
# Tiri totali stimati per ogni gol atteso (alpha), usato come fallback se
# non viene passata una lambda tiri esplicita al motore live.

LIVE_SOT_PER_GOAL_RATIO = 3.0
# Tiri in porta stimati per ogni gol atteso (alpha), fallback analogo a
# LIVE_SHOTS_PER_GOAL_RATIO per i tiri in porta.

LIVE_CORNER_BASE_LAMBDA = 5.0
# Corner attesi di fallback per singola squadra (se non derivati dal
# MatchModel), usati per calibrare la probabilità di corner per minuto.

LIVE_CARD_YELLOW_TO_RED_RATIO = 0.06
# Quota di ammonizioni che, nel motore live, degenera in un'espulsione
# diretta (evento raro ma realistico).

LIVE_MATCH_ANIMATION_DELAY_SECONDS = 0.11
# Pausa (in secondi) fra un minuto simulato e il successivo durante
# l'animazione 'Cronaca Diretta': 90 minuti × 0.11s ≈ 10 secondi reali totali,
# calibrati per una clip breve e ad alto impatto da registrare per i social
# (TikTok/Reels/Shorts) senza tempi morti.


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


def attribute_goal_scorers(
    events: list[dict[str, object]],
    home_players: list[dict[str, object]],
    away_players: list[dict[str, object]],
) -> list[dict[str, object]]:
    # POST-HOC attribution layer on top of simulate_single_match's existing
    # per-minute Bernoulli engine (unchanged): for every simulated 'goal'
    # event, draws WHICH Key Player scored it via a weighted random pick
    # over that team's 3 FC Cards (weighted by each player's own
    # ROLE_XG_SHARE), plus an "Unlisted Player" catch-all bucket for the
    # portion of the team's attack not attributed to a tracked Key Player —
    # a real squad has more than 3 possible scorers, so the 3 named cards
    # should not win every single goal.
    scorers: list[dict[str, object]] = []
    for event in events:
        if event.get("type") != "goal":
            continue
        team = event["team"]
        players = home_players if team == "home" else away_players
        names = [player["name"] for player in players]
        weights = [float(player["xg_share"]) for player in players]
        tracked_total = sum(weights)
        unlisted_weight = max(1.0 - tracked_total, 0.05)
        names = names + ["Unlisted Player"]
        weights = weights + [unlisted_weight]
        scorer_name = random.choices(names, weights=weights, k=1)[0]
        scorers.append({"minute": int(event["minute"]), "team": team, "scorer": scorer_name})
    return scorers


def determine_match_mvp(
    goal_scorers: list[dict[str, object]],
    home_players: list[dict[str, object]],
    away_players: list[dict[str, object]],
    home_goals: int,
    away_goals: int,
    home: str,
    away: str,
) -> dict[str, object]:
    # MVP = the tracked Key Player with the most simulated goals (ties
    # broken by higher generated Overall); if none of the 3 tracked cards
    # per side found the net, falls back to the highest-Overall Key Player
    # on the side that didn't lose (a draw defaults to home).
    tracked_by_name = {player["name"]: player for player in home_players + away_players}
    goal_counts: dict[str, int] = {}
    for scorer_event in goal_scorers:
        name = scorer_event["scorer"]
        if name in tracked_by_name:
            goal_counts[name] = goal_counts.get(name, 0) + 1

    if goal_counts:
        best_name = max(goal_counts, key=lambda name: (goal_counts[name], tracked_by_name[name]["overall"]))
        player = tracked_by_name[best_name]
        goals = goal_counts[best_name]
        return {
            "name": best_name,
            "role": player["role"],
            "overall": player["overall"],
            "reason": f"{goals} goal{'s' if goals > 1 else ''} in this simulation",
        }

    pool, team_label = (home_players, home) if home_goals >= away_goals else (away_players, away)
    best = max(pool, key=lambda player: player["overall"])
    return {
        "name": best["name"],
        "role": best["role"],
        "overall": best["overall"],
        "reason": f"top performer for {team_label}",
    }


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


def render_top_result_highlight_card(
    score_label: str, probability: float, simulations_count: int, total_simulations: int = 10_000
) -> None:
    """🏆 HUD reveal card for the 'Top Result' emerging from the Monte
    Carlo paths: giant gold/neon score front and center, with the
    confidence percentage in evidence — built to be the first thing a
    viewer's eye lands on when the simulation finishes."""
    st.markdown(
        '<div class="mc-highlight-card">'
        f'<div class="mc-highlight-label">🏆 TOP RESULT · {total_simulations:,} SIMULATIONS</div>'
        f'<div class="mc-highlight-score">{escape(score_label)}</div>'
        f'<div class="mc-highlight-sub">Confidence: {probability:.1%} · {simulations_count:,} / {total_simulations:,} paths</div>'
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


def render_fc_player_card(player: dict[str, object]) -> None:
    # FC/Ultimate-Team-style player card: giant neon Overall, role label,
    # name, and a "GOAL CHANCE" neon progress bar with the Anytime
    # Goalscorer probability — the 🧮 tag marks a generated role archetype
    # (no real squad name available), 📡 marks a real Football-Data.org
    # squad name (Overall/goal% are still always generated either way —
    # see build_key_players_for_team).
    source_tag = "🧮" if player["generated"] else "📡"
    goal_pct = float(player["goal_probability"])
    bar_width = clamp(goal_pct * 100, 3.0, 100.0)
    st.markdown(
        f'<div class="fc-player-card"><div class="fc-player-source-tag">{source_tag}</div>'
        f'<div class="fc-player-overall">{int(player["overall"])}</div>'
        f'<div class="fc-player-role">{escape(str(player["role"]))}</div>'
        f'<div class="fc-player-name">{escape(str(player["name"]))}</div>'
        f'<div class="fc-player-progress-label">⚽ {goal_pct:.0%} Goal Chance</div>'
        '<div class="fc-player-progress-track">'
        f'<div class="fc-player-progress-fill" style="width:{bar_width:.1f}%"></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )


def render_key_players_section(
    model: MatchModel, league: str, home: str, away: str
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    # "⭐ KEY PLAYERS & GOAL PROBABILITIES": compact, single-screen block —
    # 2 stacked rows of 3 cards (Home, then Away) rather than a 6-wide
    # grid, so it stays legible on a narrow vertical video frame. Returns
    # the computed (home_players, away_players) so callers (the FC
    # Simulator's goal-scorer attribution) reuse the exact same cards
    # rather than recomputing/re-rolling them.
    st.markdown('<div class="mc-col-title">⭐ KEY PLAYERS & GOAL PROBABILITIES</div>', unsafe_allow_html=True)

    home_players, _home_live = build_key_players_for_team(league, home, model.home_lambda, model.home_rating)
    away_players, _away_live = build_key_players_for_team(league, away, model.away_lambda, model.away_rating)

    st.caption(f"🏠 {home}")
    home_cols = st.columns(KEY_PLAYER_MAX_CARDS)
    for col, player in zip(home_cols, home_players):
        with col:
            render_fc_player_card(player)

    st.caption(f"✈️ {away}")
    away_cols = st.columns(KEY_PLAYER_MAX_CARDS)
    for col, player in zip(away_cols, away_players):
        with col:
            render_fc_player_card(player)

    st.caption(
        "📡 Real squad name from Football-Data.org · 🧮 Generic role archetype (squad data unavailable) · "
        "Overall Rating and Goal Probability are always generated (from Team Power Rating and this match's "
        "xG by role) — Football-Data.org has no player-level ratings or scoring data of any kind."
    )
    return home_players, away_players


def render_mvp_card(mvp: dict[str, object]) -> None:
    st.markdown(
        '<div class="fc-mvp-card">'
        '<div class="fc-mvp-label">👑 Match MVP</div>'
        f'<div class="fc-mvp-name">{escape(str(mvp["name"]))}</div>'
        f'<div class="fc-mvp-sub">{escape(str(mvp["role"]))} · Overall {int(mvp["overall"])} · {escape(str(mvp["reason"]))}</div>'
        '</div>',
        unsafe_allow_html=True,
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


def render_live_match_tab(model: MatchModel, league: str, home: str, away: str) -> None:
    """🎮 FC Simulator: the PRIMARY, spectacular home for Key Player FC
    Cards, Anytime Goalscorer probabilities, the minute-by-minute live
    chronicle, simulated goal scorers/minutes and a Match MVP card.
    Entertainment module independent from the analytical engine: the
    reference probabilities remain the Poisson/Dixon-Coles ones from the
    other tabs — this is an illustrative single-match simulation, not a
    forecast source."""
    st.markdown(
        "### 🎮 FC Simulator\n"
        "Key Players, Anytime Goalscorer odds, and a full minute-by-minute simulation — the showcase tab for "
        "social video. Expected goals and cards are calibrated on the same match Global Power Rating, but this "
        "is an illustrative simulation of ONE match; it does not replace the Poisson/Dixon-Coles/Monte Carlo "
        "forecasts from the other tabs."
    )

    st.markdown("---")
    home_players, away_players = render_key_players_section(model, league, home, away)
    st.markdown("---")

    if st.session_state.get("live_match_teams") != (home, away):
        # Selected teams changed: the previous simulation is no longer
        # relevant and must be cleared to avoid showing a scoreboard for a
        # different match than the one currently being analyzed.
        st.session_state.pop("live_match_result", None)
        st.session_state.pop("live_match_chronicle", None)
        st.session_state.pop("live_match_goal_scorers", None)
        st.session_state.pop("live_match_mvp", None)
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

        # Attribute each simulated goal to one of the 6 tracked FC Cards
        # (or an "Unlisted Player"), then derive First Goal Scorer / MVP —
        # reuses the SAME home_players/away_players shown in the pre-match
        # showcase above (both deterministic given this match, so they
        # match exactly what the viewer already saw).
        goal_scorers = attribute_goal_scorers(result["events"], home_players, away_players)
        mvp = determine_match_mvp(
            goal_scorers, home_players, away_players, live_home_goals, live_away_goals, home, away
        )

        st.session_state["live_match_result"] = result
        st.session_state["live_match_chronicle"] = chronicle
        st.session_state["live_match_goal_scorers"] = goal_scorers
        st.session_state["live_match_mvp"] = mvp

    if "live_match_result" not in st.session_state:
        st.info("Press '▶️ Start Match Simulation' to send the two teams onto the pitch.")
        return

    result = st.session_state["live_match_result"]
    stats = result["stats"]
    goal_scorers = st.session_state.get("live_match_goal_scorers", [])
    mvp = st.session_state.get("live_match_mvp")

    st.markdown("---")
    st.markdown("## 🏆 Final Scoreboard")
    render_broadcast_scoreboard(home, away, stats["home_goals"], stats["away_goals"], "FT 90'+")

    st.markdown("#### ⚽ Goal Timeline & MVP")
    col_timeline, col_mvp = st.columns([1.4, 1])
    with col_timeline:
        if not goal_scorers:
            st.info("No goals in this simulation.")
        else:
            first_scorer = goal_scorers[0]
            first_team_name = home if first_scorer["team"] == "home" else away
            st.markdown(
                f'<div class="fc-goal-timeline-item">🥇 <b>First Goal:</b> {escape(str(first_scorer["scorer"]))} '
                f"({escape(first_team_name)}) — {first_scorer['minute']}'</div>",
                unsafe_allow_html=True,
            )
            timeline_html = "".join(
                f'<div class="fc-goal-timeline-item">⚽ {scorer_event["minute"]}\' — '
                f'{escape(str(scorer_event["scorer"]))} '
                f'({escape(home if scorer_event["team"] == "home" else away)})</div>'
                for scorer_event in goal_scorers
            )
            st.markdown(timeline_html, unsafe_allow_html=True)
    with col_mvp:
        if mvp is not None:
            render_mvp_card(mvp)

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
    if mvp is not None:
        social_rows.append(("👑 Match MVP", f"{mvp['name']} ({mvp['role']})"))
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
        "probabilities used in the other tabs (Poisson/Dixon-Coles remain the analytical reference). "
        "Goal scorers, First Goal and MVP are drawn from the Key Players' generated goal shares, not real "
        "player data."
    )




# ==============================================================================
# FASE 1: VALUE BETTING & UX — Kelly Criterion + Heatmap dei Mercati
# ==============================================================================
# Estensione puramente additiva: non modifica Power Rating, TEAM_TIERS,
# Dixon-Coles, Dynamic Decay né alcun calcolo di xG esistente. Riusa solo le
# probabilità già calcolate da match_outcome_probabilities/
# goal_market_probabilities per garantire coerenza con le altre schede.
KELLY_FRACTION = 0.25
# Quarter Kelly: frazione conservativa applicata al Kelly Criterion pieno
# per contenere la varianza sul bankroll (Fractional Kelly Stake).

HEATMAP_HIGH_THRESHOLD = 0.70
# Soglia Heatmap 'Verde Chiaro/Smeraldo': probabilità >= 70%.

HEATMAP_MID_THRESHOLD = 0.50
# Soglia Heatmap 'Giallo/Arancione': probabilità fra 50% e 69%. Sotto il
# 50% la cella è 'Rosso/Grigio'.


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
# Raggruppamento dei mercati Kelly per famiglia correlata: usato per
# escludere Value Bet duplicate/correlate (es. Over 2.5 e Under 2.5, o due
# esiti dello stesso 1X2) dall'ordinamento e dal box Best Value Bet — solo la
# scommessa con lo Stake Kelly più alto del gruppo viene mantenuta.


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
# Mappatura campionato interno -> sport key di The Odds API. Se la lega
# selezionata non è mappata, get_live_odds ripiega automaticamente su None
# (inserimento manuale).

ODDS_API_MARKET_MAP: dict[str, tuple[str, str]] = {
    "kelly_home": ("h2h", "home"),
    "kelly_draw": ("h2h", "draw"),
    "kelly_away": ("h2h", "away"),
    "kelly_over25": ("totals", "Over"),
    "kelly_under25": ("totals", "Under"),
    "kelly_gg": ("btts", "Yes"),
    "kelly_ng": ("btts", "No"),
}
# Mappatura chiave mercato Kelly interna -> (mercato The Odds API, esito).


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
# < 72 ore (≤3 giorni) dall'ultimo impegno ufficiale: malus attacco -8%.
FATIGUE_DEFENSE_MALUS_SHORT_REST = 0.08
# < 72 ore: malus difesa (vulnerabilità difensiva) +8% (concede di più).

FATIGUE_ATTACK_MALUS_MID_REST = -0.04
# Tra 72 e 96 ore (4 giorni) dall'ultimo impegno: malus attacco -4%.
FATIGUE_DEFENSE_MALUS_MID_REST = 0.04
# Tra 72 e 96 ore: malus difesa +4%.

FATIGUE_TRAVEL_ATTACK_MALUS = -0.03
# Trasferta europea/viaggio lungo nei 4 giorni precedenti: malus
# aggiuntivo attacco -3% (si somma al malus da giorni di riposo).
FATIGUE_TRAVEL_DEFENSE_MALUS = 0.03
# Trasferta europea/viaggio lungo: malus aggiuntivo difesa +3%.

TURNOVER_LEVELS: dict[str, float] = {
    "No rotation": 0.0,
    "Partial rotation (-3%)": -0.03,
    "Heavy rotation (-7%)": -0.07,
}
# Malus attacco per il Livello di Turnover Previsto in formazione.

TURNOVER_DEFENSE_FACTOR = 0.5
# Quota del malus di turnover che si riflette anche sulla vulnerabilità
# difensiva: una formazione rimaneggiata concede di più, ma in misura minore
# rispetto a quanto perde in fase offensiva.

FATIGUE_ALERT_THRESHOLD = 0.05
# Soglia (5%) di malus complessivo sull'attacco oltre la quale mostrare il
# badge di allerta affaticamento nell'interfaccia.


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


TOP_RESULT_DOMINANCE_MARGIN = 0.05
# Soglia (5 punti percentuali) di margine fra l'esito macro 1X2 più
# probabile e il secondo classificato, oltre la quale il Monte Carlo 'Top
# Result' (vedi run_simulation) viene forzato a un punteggio esatto coerente
# con quell'esito macro (Smart Display) anche se non è il punteggio esatto
# più frequente in assoluto. SOTTO questa soglia — cioè in un match
# genuinamente equilibrato, dove Casa/Pareggio/Trasferta sono vicini fra
# loro — si mostra invece il punteggio esatto realmente più frequente senza
# alcuna forzatura: per un match equilibrato questo è spesso 0-0 o 1-1, ed è
# esattamente il comportamento realistico richiesto (il Pareggio deve poter
# emergere come Top Result quando lo è davvero, non essere sistematicamente
# scavalcato da un risultato di Vittoria Casa/Trasferta che vince il 'voto'
# macro per una manciata di decimi di punto percentuale).


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

    # --- Frequenze 1X2 (pesate Dixon-Coles) osservate nelle 10.000 simulazioni:
    # servono a validare che la probabilità analitica (Poisson bivariata +
    # Dixon-Coles) e quella simulata dal motore Monte Carlo raccontino lo
    # stesso match, E a determinare l'esito macro (1/X/2) dominante per la
    # selezione "Smart Display" del Top Result qui sotto.
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

    # --- SMART DISPLAY: il "Top Result" mostrato nell'HUD principale deve
    # essere COERENTE con l'esito macro 1X2 dominante SOLO quando quell'esito
    # è DAVVERO dominante (margine >= TOP_RESULT_DOMINANCE_MARGIN sul secondo
    # classificato) — es. una Vittoria Casa al 55% contro un Pareggio al 25%,
    # dove il singolo punteggio esatto più probabile in assoluto può comunque
    # risultare un 1-1 per pura frammentazione statistica dei tanti punteggi
    # di Vittoria Casa (1-0, 2-0, 2-1, 3-1...) — mostrare comunque l'1-1 come
    # "Top Result" in quel caso sarebbe fuorviante. In un match GENUINAMENTE
    # equilibrato (Casa/Pareggio/Trasferta vicini fra loro, margine sotto la
    # soglia) si mostra invece il punteggio esatto realmente più frequente
    # SENZA alcuna forzatura: per un match equilibrato questo è spesso 0-0 o
    # 1-1, ed è esattamente il comportamento richiesto — il Pareggio deve
    # poter emergere come Top Result quando lo è davvero, non essere
    # sistematicamente scavalcato da una Vittoria che vince il 'voto' macro
    # per una manciata di decimi di punto percentuale.
    top_score_overall, top_weight_overall = max(weighted_scores.items(), key=lambda item: item[1])

    macro_outcome_weights = {"home": home_wins, "draw": draws, "away": away_wins}
    dominant_macro_outcome = max(macro_outcome_weights, key=macro_outcome_weights.get)
    sorted_macro_weights = sorted(macro_outcome_weights.values(), reverse=True)
    dominant_macro_margin = (sorted_macro_weights[0] - sorted_macro_weights[1]) / total_weight

    def _score_matches_macro_outcome(score: tuple[int, int], macro_outcome: str) -> bool:
        h_goal, a_goal = score
        if macro_outcome == "home":
            return h_goal > a_goal
        if macro_outcome == "away":
            return h_goal < a_goal
        return h_goal == a_goal

    if dominant_macro_margin < TOP_RESULT_DOMINANCE_MARGIN or _score_matches_macro_outcome(
        top_score_overall, dominant_macro_outcome
    ):
        # Match equilibrato (nessun esito macro chiaramente dominante), o il
        # punteggio esatto più frequente in assoluto è già coerente con
        # l'esito macro dominante: nessuna forzatura necessaria, si mostra
        # il vero Top Result.
        top_result_score, top_result_weight = top_score_overall, top_weight_overall
    else:
        # Un esito macro è chiaramente dominante (>= 5pp) ma il punteggio
        # esatto più frequente in assoluto appartiene a un gruppo diverso
        # (frammentazione): si sceglie il punteggio più probabile ALL'INTERNO
        # del gruppo dominante, per un Top Result coerente col pronostico.
        dominant_group_scores = {
            score: weight
            for score, weight in weighted_scores.items()
            if _score_matches_macro_outcome(score, dominant_macro_outcome)
        }
        if dominant_group_scores:
            top_result_score, top_result_weight = max(dominant_group_scores.items(), key=lambda item: item[1])
        else:
            # Fallback di sicurezza (non dovrebbe mai accadere con 10,000
            # path): nessun punteggio simulato ricade nel gruppo dominante.
            top_result_score, top_result_weight = top_score_overall, top_weight_overall

    top_result = {
        "Exact Score": f"{top_result_score[0]}-{top_result_score[1]}",
        "Simulations": int(round(top_result_weight)),
        "Probability": top_result_weight / total_weight,
    }

    # Elenco (più ampio del solo Top 5) degli altri punteggi esatti più
    # frequenti in assoluto, usato per le "Alternative Frequencies": include
    # deliberatamente anche punteggi fuori dal gruppo dominante (es. l'1-1
    # quando la Vittoria Casa è l'esito scelto come Top Result) così restano
    # visibili come frequenze secondarie invece di sparire dall'HUD.
    top_scores = sorted(weighted_scores.items(), key=lambda item: item[1], reverse=True)[:8]
    score_rows = [
        {
            "Exact Score": f"{h_goal}-{a_goal}",
            "Simulations": int(round(weight)),
            "Probability": weight / total_weight,
        }
        for (h_goal, a_goal), weight in top_scores
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
        "top_result": top_result,
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
        '<div class="wl-login-card">'
        '<div class="wl-login-badge">🦇</div>'
        '<div class="wl-login-title">WAYNELAB</div>'
        '<div class="wl-login-subtitle">FOOTBALL INTELLIGENCE</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    _, login_col, _ = st.columns([1, 1.2, 1])
    with login_col:
        with st.form("login_form", clear_on_submit=False):
            password = st.text_input(
                "Access Password",
                type="password",
                placeholder="Enter access password",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)
        if submitted:
            if password == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid password.")


def render_sidebar_controls() -> dict[str, object]:
    """Manual sidebar sliders: Market Factor (-20%/+20%) and Injury/Missing
    Starters Impact (-30%/+30%), for home and away, plus the Fatigue &
    Rotation Index (Phase 2). Values increase/decrease the Power Index and
    expected attack/defense BEFORE the xG, shots and probability calculation
    (see build_match_model)."""
    st.markdown("### ⚙️ Simulation & Calibration")
    with st.expander("Simulation & Calibration", expanded=False):
        st.caption("Advanced engine parameters — the central dashboard stays focused on the HUD.")
        st.select_slider(
            "Monte Carlo Iterations",
            options=[1_000, 2_500, 5_000, 10_000, 20_000],
            value=10_000,
            key="mc_iterations",
            help="More iterations = smoother probabilities, slower simulation.",
        )
        st.slider(
            "Base Rating Weight (2025/26 Season)",
            60,
            80,
            int(BASE_RATING_WEIGHT * 100),
            format="%d%%",
            key="base_rating_weight_pct",
            help="Remaining weight goes to Current Form (2026/27). Default 72% / 28%.",
        )
        st.toggle(
            "Opta/Sofascore Calibration",
            value=True,
            key="opta_calibration_enabled",
            help="Tier-based alignment of shots/corners/fouls toward real Opta/Sofascore ranges. "
            "Off = raw league-baseline estimates only.",
        )

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
        "mc_iterations": st.session_state.get("mc_iterations", 10_000),
        "base_rating_weight_pct": st.session_state.get("base_rating_weight_pct", int(BASE_RATING_WEIGHT * 100)),
        "opta_calibration_enabled": st.session_state.get("opta_calibration_enabled", True),
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


# ==============================================================================
# AI TACTICAL PREVIEW — stat-driven, TV-analyst-style match narrative
# ==============================================================================
# Purely additive, purely a PRESENTATION layer: reads exclusively from
# figures the engine has already computed for this match (Weighted Rating
# 70/30 Base/Form split, xG, 1X2, exact-score probabilities, micro-events,
# L5 recent form) — no invented data, no new statistical model, and no
# external API call required (a deterministic Python template generator,
# so the tab is always available even without an LLM key configured,
# unlike the separate "Intelligence Analysis Report" which prefers an LLM
# when one is configured — this one is intentionally always-template so
# the tactical narrative is 100% reproducible from the visible numbers).
def _tactical_form_letters(stats: "LiveTeamStats | None") -> str | None:
    if stats is None or not stats.recent_form:
        return None
    return "".join(stats.recent_form[:FORM_MATCHES_WINDOW])


def _tactical_form_phrase(letters: str | None, team_name: str) -> str:
    if not letters:
        return f"{escape(team_name)} have no completed fixtures on record yet this season to read form from"
    wins, draws, losses = letters.count("W"), letters.count("D"), letters.count("L")
    record = f"{wins}W-{draws}D-{losses}L"
    if wins >= 4:
        mood = "red-hot"
    elif losses >= 3 and wins <= 1:
        mood = "under real pressure"
    else:
        mood = "steady, if unspectacular"
    return f"{escape(team_name)} arrive {mood} across their last {len(letters)} ({record})"


def _tactical_trend_phrase(base_rating: float, form_rating: float) -> str:
    diff = form_rating - base_rating
    if diff > 40:
        return "and their current output is actually running ahead of their season-long level"
    if diff < -40:
        return "though their current output has dipped below their season-long level"
    return "and their current output is broadly tracking their season-long level"


def generate_tactical_preview(model: MatchModel, league: str, home: str, away: str) -> dict[str, str]:
    try:
        home_stats: LiveTeamStats | None = fetch_team_live_stats(league, home)
    except FootballDataError:
        home_stats = None
    try:
        away_stats: LiveTeamStats | None = fetch_team_live_stats(league, away)
    except FootballDataError:
        away_stats = None

    home_base_rating, _home_base_source = resolve_base_rating(league, home)
    away_base_rating, _away_base_source = resolve_base_rating(league, away)
    home_form_rating = compute_current_form_rating(home_stats) if home_stats is not None else home_base_rating
    away_form_rating = compute_current_form_rating(away_stats) if away_stats is not None else away_base_rating

    home_favored = model.home_win_prob >= model.away_win_prob
    favorite, underdog = (home, away) if home_favored else (away, home)
    favorite_rating = model.home_rating if home_favored else model.away_rating
    underdog_rating = model.away_rating if home_favored else model.home_rating
    favorite_lambda = model.home_lambda if home_favored else model.away_lambda
    underdog_lambda = model.away_lambda if home_favored else model.home_lambda

    outcome_probs = sorted([model.home_win_prob, model.draw_prob, model.away_win_prob], reverse=True)
    is_tight_match = (outcome_probs[0] - outcome_probs[1]) < 0.08

    home_letters = _tactical_form_letters(home_stats)
    away_letters = _tactical_form_letters(away_stats)

    tactical_read = " ".join(
        [
            f"{escape(favorite)} go into this one as the stronger side on the Weighted Rating Engine, "
            f"posting a Global Power Rating of {favorite_rating:.0f} against {escape(underdog)}'s "
            f"{underdog_rating:.0f} — a gap built 70% on where each side finished last season and 30% on "
            f"what they've shown so far this campaign.",
            f"{_tactical_form_phrase(home_letters, home)}, {_tactical_trend_phrase(home_base_rating, home_form_rating)}.",
            f"{_tactical_form_phrase(away_letters, away)}, {_tactical_trend_phrase(away_base_rating, away_form_rating)}.",
            (
                "With so little separating the two sides in the model, expect a cagey opening exchange before "
                "either side properly commits numbers forward."
                if is_tight_match
                else (
                    f"The gap is real enough that {escape(favorite)} should dictate the game's early tempo, "
                    f"with {escape(underdog)} needing a disciplined start to stay in it."
                )
            ),
        ]
    )

    matchup_analysis = " ".join(
        [
            f"On the numbers, {escape(favorite)}'s attack projects for {favorite_lambda:.2f} expected goals in "
            f"this fixture, the higher of the two lambdas, against a {escape(underdog)} side projected for "
            f"{underdog_lambda:.2f}.",
            f"The model expects {model.shots_total_lambda:.0f} shots across the 90 minutes and "
            f"{model.corners_total_lambda:.1f} corners, with {escape(home)} sending "
            f"{model.home_shots_on_target_lambda:.1f} on target at the {escape(away)} goal and {escape(away)} "
            f"replying with {model.away_shots_on_target_lambda:.1f} of their own.",
            (
                f"{escape(underdog)} aren't without teeth here — an expected-goals read above 1.00 means "
                f"they're a live threat on the break, not merely making up the numbers."
                if underdog_lambda >= 1.0
                else (
                    f"{escape(underdog)}'s own attacking output projects modestly, which should keep "
                    f"{escape(favorite)} comfortable if they take their early sight of goal."
                )
            ),
        ]
    )

    top_scores = exact_score_probabilities(model.home_lambda, model.away_lambda, max_goals=6)[:3]
    top_score_label, top_score_prob = top_scores[0] if top_scores else ("N/A", 0.0)
    monte_carlo_scenario_parts = [
        f"Running the Poisson + Dixon-Coles engine across the full scoreline grid, {top_score_label} emerges as "
        f"the single most likely outcome at {top_score_prob:.1%}, with the macro market reading "
        f"{model.home_win_prob:.0%} {escape(home)}, {model.draw_prob:.0%} Draw, {model.away_win_prob:.0%} "
        f"{escape(away)}."
    ]
    if len(top_scores) > 1:
        alt_label, alt_prob = top_scores[1]
        monte_carlo_scenario_parts.append(
            f"The next-closest scenario, {alt_label} at {alt_prob:.1%}, is never far behind — Dixon-Coles "
            f"nudges the model toward tighter scorelines whenever the gap between the two sides isn't "
            f"overwhelming, keeping low-scoring alternatives firmly in play."
        )
    if len(top_scores) > 2:
        third_label, third_prob = top_scores[2]
        monte_carlo_scenario_parts.append(
            f"A {third_label} finish rounds out the top three at {third_prob:.1%}, the kind of scoreline that "
            f"stays live for as long as the first goal doesn't arrive early."
        )
    monte_carlo_scenario = " ".join(monte_carlo_scenario_parts)

    return {
        "tactical_read": tactical_read,
        "matchup_analysis": matchup_analysis,
        "monte_carlo_scenario": monte_carlo_scenario,
    }


def render_tactical_card(title: str, body_text: str) -> None:
    st.markdown(
        f'<div class="tactical-card"><div class="tactical-card-title">{escape(title)}</div>'
        f'<div class="tactical-card-body">{body_text}</div></div>',
        unsafe_allow_html=True,
    )


def render_tactical_preview_tab(model: MatchModel, league: str, home: str, away: str) -> None:
    st.markdown(
        "### 📝 AI Tactical Preview\n"
        "A stat-driven tactical read of this fixture, generated from the same Weighted Rating Engine, xG model "
        "and Poisson + Dixon-Coles projections used throughout WayneLab."
    )
    preview = generate_tactical_preview(model, league, home, away)
    render_tactical_card("🧠 Key Tactical Read", preview["tactical_read"])
    render_tactical_card("⚔️ Matchup Analysis", preview["matchup_analysis"])
    render_tactical_card("🎯 Monte Carlo Projection & Scenario", preview["monte_carlo_scenario"])
    st.caption(
        "Generated entirely from this match's own engine outputs (Weighted Rating 70/30, xG, 1X2, exact-score "
        "probabilities) — a deterministic tactical narrative, not a live external AI call."
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
    col_league, col_preset = st.columns([2, 1.3])
    with col_league:
        league = st.selectbox(
            "Competition",
            options=list(FOOTBALL_DATA_COMPETITIONS),
            key="league_select",
        )
    with col_preset:
        preset = st.selectbox(
            "Quick Preset",
            options=QUICK_PRESET_OPTIONS,
            key="quick_preset",
            help="Narrows Match of the Day to fixtures matching that archetype (by Team Tier).",
        )

    try:
        team_rows = fetch_league_teams(league)
    except FootballDataError as error:
        st.error(f"Football-Data.org unavailable: {error}")
        team_rows = ()

    teams = [name for _, name in team_rows]

    if len(teams) < 2:
        st.warning("Football-Data.org did not return two available teams.")
        return

    try:
        calendar = calendar_frame(league)
    except FootballDataError as error:
        st.error(f"Football-Data.org fixtures unavailable: {error}")
        calendar = pd.DataFrame(columns=["Date", "Status", "Home", "Away"])

    all_fixture_options = build_fixture_options(calendar)
    preset_fixture_options = filter_fixtures_by_preset(all_fixture_options, preset)
    manual_label = "🔧 Custom Matchup (pick teams manually)"

    # Reset the Match of the Day pick whenever the competition or preset
    # changes, so a stale fixture from a different context is never shown.
    selector_context = (league, preset)
    if st.session_state.get("_match_selector_context") != selector_context:
        st.session_state["_match_selector_context"] = selector_context
        st.session_state["match_of_day_select"] = (
            preset_fixture_options[0][0] if preset_fixture_options else manual_label
        )

    match_labels = [label for label, _h, _a in preset_fixture_options] + [manual_label]
    if not preset_fixture_options:
        st.caption(f"No fixtures currently match '{preset}' in this competition — pick teams manually below.")
    selected_match_label = st.selectbox("📅 Match of the Day", options=match_labels, key="match_of_day_select")

    if selected_match_label == manual_label:
        with st.expander("🔧 Manual Team Selection", expanded=True):
            if st.session_state.get("_last_league") != league:
                st.session_state["_last_league"] = league
                st.session_state["home_select"] = teams[0]
                st.session_state["away_select"] = teams[1]
            col_home, col_away = st.columns(2)
            with col_home:
                home = st.selectbox("Home Team", options=teams, key="home_select")
            with col_away:
                away = st.selectbox("Away Team", options=teams, key="away_select")
    else:
        home, away = next(
            (h, a) for label, h, a in preset_fixture_options if label == selected_match_label
        )
        st.caption(f"🏠 {home}  ·  ✈️ {away}")

    with st.expander("📅 2026/27 Season Fixtures & Status", expanded=False):
        try:
            status_text = (
                f"Football-Data.org: {len(teams)} teams loaded · "
                f"{competition_season_status(league)}. "
                "Micro-events estimated on league baseline."
            )
            st.caption(status_text)
        except FootballDataError as error:
            st.warning(f"Season status unavailable: {error}")
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
        tab_tactical_preview,
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
            "📝 AI Tactical Preview",
            "📊 Team Form & H2H",
            "📊 Goal Stats & Markets",
            "📊 Charts Dashboard & Micro-Events",
            "🎯 Multi-Outcome & Value Bet Analyzer",
            "💰 Value Betting & Heatmap",
            "Monte Carlo Simulator (10,000 Matches)",
            "🎮 FC Simulator",
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

    with tab_tactical_preview:
        render_tactical_preview_tab(model, league, home, away)

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
        mc_iterations_preview = int(st.session_state.get("mc_iterations", 10_000))
        st.markdown(
            f'<div class="mc-intro-caption">{mc_iterations_preview:,} independent Poisson-distributed matches, weighted with the '
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

        mc_iterations = int(st.session_state.get("mc_iterations", 10_000))
        montecarlo_button_label = (
            f"🔁 Relaunch {mc_iterations:,} Monte Carlo Simulations"
            if "montecarlo_result" in st.session_state
            else f"▶️ Run {mc_iterations:,} Monte Carlo Simulations"
        )
        run_clicked = st.button(montecarlo_button_label, type="primary", key="simulate_button")

        if run_clicked:
            render_monte_carlo_computing_hud(total_paths=mc_iterations, duration_seconds=2.6)
            st.session_state["montecarlo_result"] = run_simulation(model, n_simulations=mc_iterations)

        if "montecarlo_result" not in st.session_state:
            st.info(f"Press the button to launch {mc_iterations:,} Monte Carlo simulations for this match.")
        else:
            simulation = st.session_state["montecarlo_result"]
            score_frame: pd.DataFrame = simulation["scores"]
            outcome_frame: pd.DataFrame = simulation["outcomes"]
            raw = simulation["raw"]

            outcome_probabilities = {
                str(row["Outcome"]): float(row["Probability"]) for _, row in outcome_frame.iterrows()
            }
            # SMART DISPLAY: the Top Result shown in the hero card is the
            # exact score already selected (in run_simulation) to be
            # coherent with the dominant 1X2 outcome — not necessarily the
            # single most frequent exact score overall (which, for
            # evenly-matched teams, is very often a flat 1-1).
            top_score_row = simulation["top_result"]
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
                    total_simulations=mc_iterations,
                )

            with col_alt_frequencies:
                st.markdown('<div class="mc-col-title">📊 ALTERNATIVE FREQUENCIES</div>', unsafe_allow_html=True)
                # Exclude the score already shown as the Top Result so it is
                # not duplicated here — any other frequent score (including
                # a 1-1 that was not chosen as the dominant-outcome Top
                # Result) still surfaces as a secondary frequency.
                alt_score_frame = score_frame[
                    score_frame["Exact Score"] != top_score_row["Exact Score"]
                ].reset_index(drop=True)
                render_score_frequency_ranking(
                    alt_score_frame.head(5),
                    reference_probability=float(top_score_row["Probability"]),
                    start_rank=2,
                )

            with col_micro_intel:
                st.markdown('<div class="mc-col-title">📡 MICRO-EVENTS INTEL</div>', unsafe_allow_html=True)
                render_micro_events_intel_column(intel)

            st.caption(
                f"⚙️ {mc_iterations:,} / {mc_iterations:,} paths computed for {home} vs {away} · "
                "synced with the Dixon-Coles matrix above."
            )
            st.caption("⭐ Key Players & Goal Probabilities now live in the 🎮 FC Simulator tab.")

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
        render_live_match_tab(model, league, home, away)


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

.wl-login-card {
    max-width: 420px;
    margin: 8vh auto 24px auto;
    text-align: center;
    padding: 36px 28px 28px 28px;
    border-radius: 20px;
    background: linear-gradient(160deg, rgba(18, 18, 18, 0.82) 0%, rgba(5, 5, 5, 0.95) 100%);
    border: 1px solid rgba(0, 229, 255, 0.35);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.55), 0 0 30px rgba(0, 229, 255, 0.12);
    backdrop-filter: blur(10px);
}

.wl-login-badge {
    font-size: 2.6rem;
    line-height: 1;
    margin-bottom: 6px;
    filter: drop-shadow(0 0 12px rgba(0, 229, 255, 0.45));
}

.wl-login-title {
    font-size: 1.7rem;
    font-weight: 900;
    letter-spacing: 0.14em;
    background: linear-gradient(135deg, #00e5ff, #e0e0e0);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.wl-login-subtitle {
    margin-top: 4px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: #9aa0a6;
}

.wl-data-disclaimer {
    margin-top: 14px;
    padding: 10px 14px;
    border-radius: 8px;
    background: #0a0a0a;
    border-left: 3px solid #00e5ff;
    font-size: 0.76rem;
    line-height: 1.4;
    color: #9aa0a6;
}

.tactical-card {
    background: linear-gradient(160deg, rgba(18, 18, 18, 0.88) 0%, rgba(5, 5, 5, 0.97) 100%);
    border: 1px solid rgba(0, 229, 255, 0.35);
    border-radius: 16px;
    padding: 18px 22px;
    margin-bottom: 16px;
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 26px rgba(0, 0, 0, 0.45), 0 0 20px rgba(0, 229, 255, 0.08);
}

.tactical-card-title {
    font-size: 1.02rem;
    font-weight: 900;
    letter-spacing: 0.04em;
    color: #00e5ff;
    text-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
    margin-bottom: 10px;
    text-transform: uppercase;
}

.tactical-card-body {
    font-size: 0.93rem;
    line-height: 1.65;
    color: #e0e0e0;
}

.fc-player-card {
    position: relative;
    background: linear-gradient(165deg, #101010 0%, #050505 100%);
    border: 1px solid #00e5ff;
    border-radius: 14px;
    padding: 14px 8px 12px 8px;
    text-align: center;
    box-shadow: 0 0 18px rgba(0, 229, 255, 0.18), 0 6px 18px rgba(0, 0, 0, 0.5);
    margin-bottom: 10px;
    min-height: 148px;
}

.fc-player-source-tag {
    position: absolute;
    top: 6px;
    right: 8px;
    font-size: 0.62rem;
    opacity: 0.75;
}

.fc-player-overall {
    font-size: 1.9rem;
    font-weight: 900;
    font-variant-numeric: tabular-nums;
    color: #00e5ff;
    text-shadow: 0 0 10px rgba(0, 229, 255, 0.6);
    line-height: 1;
}

.fc-player-role {
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #9aa0a6;
    margin-top: 3px;
}

.fc-player-name {
    font-size: 0.85rem;
    font-weight: 800;
    color: #e0e0e0;
    margin-top: 8px;
    line-height: 1.25;
    min-height: 2.1em;
}

.fc-player-goal-badge {
    margin-top: 9px;
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(0, 255, 135, 0.12);
    border: 1px solid rgba(0, 255, 135, 0.45);
    color: #00ff87;
    font-weight: 800;
    font-size: 0.76rem;
    font-variant-numeric: tabular-nums;
}

.fc-player-progress-label {
    margin-top: 10px;
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.03em;
    color: #00ff87;
    text-transform: uppercase;
}

.fc-player-progress-track {
    margin-top: 4px;
    width: 100%;
    height: 7px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.08);
    overflow: hidden;
}

.fc-player-progress-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #00e5ff, #00ff87);
    box-shadow: 0 0 8px rgba(0, 255, 135, 0.6);
}

.fc-mvp-card {
    background: linear-gradient(155deg, rgba(255, 214, 10, 0.14), rgba(5, 5, 5, 0.97));
    border: 1px solid #ffd60a;
    border-radius: 16px;
    padding: 16px 18px;
    text-align: center;
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.5), 0 0 22px rgba(255, 214, 10, 0.18);
    margin-bottom: 12px;
}

.fc-mvp-label {
    font-size: 0.72rem;
    font-weight: 900;
    letter-spacing: 0.14em;
    color: #ffd60a;
    text-transform: uppercase;
}

.fc-mvp-name {
    font-size: 1.5rem;
    font-weight: 900;
    color: #ffffff;
    margin: 6px 0 2px 0;
}

.fc-mvp-sub {
    font-size: 0.8rem;
    color: #e0e0e0;
    font-weight: 600;
}

.fc-goal-timeline-item {
    padding: 6px 0;
    border-bottom: 1px dashed rgba(255, 255, 255, 0.08);
    font-size: 0.85rem;
    color: #e0e0e0;
}

.fc-goal-timeline-item:last-child {
    border-bottom: none;
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

    if st.session_state.authenticated:
        st.markdown(
            "# 🦇 WayneLab\n"
            "**Football Intelligence** — probabilistic analysis and match simulations "
            "powered by live Football-Data.org data."
        )
        with st.sidebar:
            st.success("Access authorized.")
            if st.button("Log Out"):
                st.session_state.authenticated = False
                st.rerun()
            st.markdown("---")
            sidebar_values = render_sidebar_controls()

        main_tab_analysis, main_tab_season_stats, main_tab_bankroll = st.tabs(
            ["⚽ Match Analysis", "📊 Season Stats 2026/27", "📊 Bankroll & History Management"]
        )
        with main_tab_analysis:
            render_dashboard(sidebar_values)
        with main_tab_season_stats:
            render_season_stats_tab()
        with main_tab_bankroll:
            render_bankroll_tab()
    else:
        render_login()


if __name__ == "__main__":
    main()
