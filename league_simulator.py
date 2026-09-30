"""
league_simulator.py — WayneLab · 🏆 Matchday Live Simulator
Modulo COMPLETAMENTE STANDALONE: nessun import da altri moduli del
progetto ospitante, nessuna dipendenza esterna oltre alle librerie di
terze parti elencate sotto. Client dati, modello statistico e rendering
sono tutti definiti qui dentro. La funzione principale non richiede alcun
argomento: def render_matchday_simulator_tab() -> None.

CAMBIO DI ARCHITETTURA IN QUESTA VERSIONE: REVEAL VIA CSS, NON PIÙ time.sleep
------------------------------------------------------------------------------
Le versioni precedenti simulavano il "reveal a cascata" delle 10 card con un
ciclo Python `for ... time.sleep(0.6)`, scrivendo ogni frame su
st.empty()/st.container(). In produzione questo si è rivelato inaffidabile:
a seconda di come l'hosting gestisce il flush dei messaggi WebSocket verso
il browser (buffering lato proxy/CDN, o più in generale il modo in cui
Streamlit accoda gli aggiornamenti durante un singolo script run), i frame
intermedi possono non arrivare in tempo reale al client, e tutte le card
compaiono insieme a run terminato — il time.sleep lato server NON garantisce
un rendering incrementale lato browser.

La soluzione adottata qui è spostare TUTTA la coreografia temporale dal lato
server (Python) al lato client (CSS): l'hook e le 10 card vengono generati
in un SOLO blocco HTML/CSS (una sola chiamata a st.markdown(...,
unsafe_allow_html=True)), con animazioni CSS keyframe e un
`animation-delay` progressivo per ciascuna card. È il browser stesso, non
Streamlit, a scandire i tempi del reveal — quindi il risultato è identico
indipendentemente da qualunque comportamento di buffering del server.
Il ciclo Monte Carlo + hard-cap anti-0-0 resta un calcolo Python sincrono
(avviene prima di generare l'HTML, tutto in memoria); cambia solo COME il
risultato viene rivelato a schermo.

Timeline dell'animazione (puramente CSS):
    0.0s                → status bar mostra "⚡ WAYNELAB AI ENGINE — 10,000 MONTE CARLO RUNS..."
    MDS_HOOK_DURATION_SECONDS (1.8s) → il testo della status bar sfuma in
                          crossfade verso "✅ SIMULATION COMPLETE — N MATCHES"
                          (la barra stessa NON collassa più: resta ad
                          altezza fissa — vedi sotto); nello stesso istante
                          appare Card 1 (fade-in + slide-up)
    +0.6s dopo ogni card → Card 2, poi Card 3, ... fino a Card 10
    +0.6s dopo l'ultima card → banner di riepilogo finale

PREVIEW/STANDBY A GEOMETRIA IDENTICA (zero scroll durante la registrazione)
-----------------------------------------------------------------------------
Prima del click su SIMULATE, lo stesso placeholder (st.empty()) che poi
conterrà i risultati mostra uno stato di anteprima costruito con le
IDENTICHE classi CSS dello stato risultati: una status bar ad altezza fissa
(.mds-status-bar, statica invece che in crossfade), una .mds-cards-grid con
10 "card di anteprima" (stessa classe .mds-card, stesso .mds-score usato
per mostrare "VS" invece del punteggio, stesso .mds-pill usato per un tag
"BIG MATCH"/"IN ANALISI" invece dell'esito 1X2) e lo stesso banner
.mds-summary-wrap con valori segnaposto "—". Riusare pixel-per-pixel le
stesse classi, invece di un box di anteprima diverso, è ciò che garantisce
un'altezza identica al millimetro tra "prima" e "dopo" il click: cambia
solo il testo dentro le celle, mai le dimensioni delle celle stesse.

MODELLO STATISTICO LOCALE
--------------------------
try_build_match_model stima gli xG con un classico schema Poisson
"attack/defense" calcolato sulle partite concluse della competizione:
    home_lambda = league_avg_home_goals × home_attack(home) × away_defense(away)
    away_lambda = league_avg_away_goals × away_attack(away) × home_defense(home)
run_simulation esegue poi una Monte Carlo Poisson standard sui due lambda.
Motore indipendente, pensato solo per questa tab "broadcast".

DATI: DUE LIVELLI DI FALLBACK (nessuna chiamata di rete obbligatoria)
-----------------------------------------------------------------------
1) Se è disponibile una API key di Football-Data.org (st.secrets
   ["FOOTBALL_DATA_API_KEY"] oppure variabile d'ambiente
   FOOTBALL_DATA_API_KEY), fetch_league_matches/fetch_team_crests
   interrogano l'API reale.
2) Se la chiave manca, la rete non risponde, o l'API restituisce un
   errore, si passa AUTOMATICAMENTE a un dataset dimostrativo generato
   internamente (_DEMO_LEAGUE_DATA), così il modulo resta sempre
   eseguibile al 100% in autonomia, anche del tutto offline.

⚠️ ENTERTAINMENT CALIBRATION LAYER
Questo modulo applica, SOLO al proprio interno, moltiplicatori di xG e
vincoli di punteggio pensati per rendere le simulazioni più dinamiche nei
video social (TikTok/Reels/Shorts). Sono valori discrezionali di pacing,
non un feed statistico validato, e sono disattivabili dal toggle in UI.
Include l'ANTI-ZERO-ZERO A CICLO WHILE: le 10 fixture vengono simulate una
prima volta in un array temporaneo; se gli 0-0 rivelati sono più di 2, un
ciclo while applica un boost incrementale di +0.50 xG e ri-simula SOLO i
match ancora 0-0, finché il totale della giornata non scende a <= 2 (con
un tetto di iterazioni di sicurezza).
"""

from __future__ import annotations

import dataclasses
import os
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
    None (invece di sollevare un'eccezione) se non configurata."""
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


# ==============================================================================
# MODELLO STATISTICO — Poisson attack/defense + prior di forza per club
# ==============================================================================
@dataclasses.dataclass(frozen=True)
class MatchModel:
    home_team: str
    away_team: str
    home_lambda: float
    away_lambda: float


MDS_MODEL_DEFAULT_HOME_AVG = 1.45
MDS_MODEL_DEFAULT_AWAY_AVG = 1.15
# NB: il floor/ceiling degli xG finali (dopo prior di forza e calibrazione di
# lega) sono MDS_LAMBDA_FLOOR / MDS_LAMBDA_CEILING, definiti più sotto nella
# sezione di calibrazione gol.

# ------------------------------------------------------------------------------
# PRIOR DI FORZA PER CLUB (locale, editabile, NON un feed di rating live)
# ------------------------------------------------------------------------------
# Il problema segnalato ("Frosinone batte Napoli") nasce dal fatto che, con
# uno storico di partite concluse ancora scarso (inizio stagione, o il
# dataset demo), gli attack/defense ratio osservati per ogni squadra
# convergono verso 1.0 (la media di lega) per mancanza di campione — quindi
# il modello tratta big e piccole quasi allo stesso modo. Questo dizionario
# fornisce un PRIOR di forza per un elenco di club noti dei 5 campionati
# supportati, su una scala 1 (più forte) – 5 (più debole): il prior viene
# fuso con i dati osservati tramite uno shrinkage bayesiano (vedi
# _blended_strength) che dà sempre più peso ai risultati reali man mano che
# se ne accumulano. Sono valori manuali indicativi pensati per separare in
# modo credibile big/medie/piccole quando i dati storici non bastano ancora
# a farlo da soli — vanno aggiornati a mano se la realtà cambia (promozioni,
# retrocessioni, mercato), non sono derivati da un servizio di rating.
CLUB_STRENGTH_TIER: dict[str, dict[str, int]] = {
    "Italy · Serie A": {
        "Napoli": 1, "SSC Napoli": 1, "Inter Milan": 1, "FC Internazionale Milano": 1,
        "Juventus FC": 1, "AC Milan": 1,
        "AS Roma": 2, "Atalanta BC": 2, "SS Lazio": 2, "ACF Fiorentina": 2, "Bologna FC 1909": 2,
        "Torino FC": 3, "Udinese Calcio": 3, "Genoa CFC": 3, "Hellas Verona FC": 3, "US Lecce": 3,
        "Cagliari Calcio": 4, "Empoli FC": 4, "Parma Calcio 1913": 4, "Como 1907": 4,
        "US Sassuolo Calcio": 4,
        "Frosinone Calcio": 5, "US Salernitana 1919": 5, "Venezia FC": 5, "Pisa Sporting Club": 5,
    },
    "England · Premier League": {
        "Manchester City FC": 1, "Arsenal FC": 1, "Liverpool FC": 1,
        "Chelsea FC": 2, "Manchester United FC": 2, "Tottenham Hotspur FC": 2, "Newcastle United FC": 2,
        "Aston Villa FC": 2,
        "Brighton & Hove Albion FC": 3, "West Ham United FC": 3, "Crystal Palace FC": 3,
        "Fulham FC": 3, "Brentford FC": 3, "Everton FC": 3, "Wolverhampton Wanderers FC": 3,
        "Bournemouth AFC": 4, "AFC Bournemouth": 4, "Nottingham Forest FC": 4, "Leicester City FC": 4,
        "Ipswich Town FC": 5, "Southampton FC": 5, "Burnley FC": 5, "Luton Town FC": 5,
    },
    "Germany · Bundesliga": {
        "FC Bayern München": 1, "Bayer 04 Leverkusen": 1,
        "Borussia Dortmund": 2, "RB Leipzig": 2, "VfB Stuttgart": 2, "Eintracht Frankfurt": 2,
        "SC Freiburg": 3, "VfL Wolfsburg": 3, "Borussia Mönchengladbach": 3, "1. FSV Mainz 05": 3,
        "TSG 1899 Hoffenheim": 3, "SV Werder Bremen": 3, "1. FC Union Berlin": 3,
        "FC Augsburg": 4, "1. FC Heidenheim 1846": 4, "VfL Bochum 1848": 4,
        "Holstein Kiel": 5, "1. FC Köln": 5, "SV Darmstadt 98": 5,
    },
    "Spain · La Liga": {
        "Real Madrid CF": 1, "FC Barcelona": 1,
        "Club Atlético de Madrid": 2, "Athletic Club": 2, "Real Sociedad de Fútbol": 2, "Real Betis Balompié": 2,
        "Villarreal CF": 3, "Valencia CF": 3, "CA Osasuna": 3, "RC Celta de Vigo": 3,
        "Sevilla FC": 3, "RCD Mallorca": 3, "Girona FC": 3,
        "Getafe CF": 4, "Deportivo Alavés": 4, "Rayo Vallecano de Madrid": 4, "UD Las Palmas": 4,
        "CD Leganés": 5, "RCD Espanyol de Barcelona": 5, "Real Valladolid CF": 5,
    },
    "France · Ligue 1": {
        "Paris Saint-Germain FC": 1,
        "AS Monaco FC": 2, "Olympique de Marseille": 2, "LOSC Lille": 2, "Stade Brestois 29": 2,
        "OGC Nice": 3, "Olympique Lyonnais": 3, "RC Lens": 3, "Stade Rennais FC 1901": 3,
        "Racing Club de Strasbourg Alsace": 3, "Toulouse FC": 3,
        "Nantes": 4, "FC Nantes": 4, "AJ Auxerre": 4, "Angers SCO": 4,
        "AS Saint-Étienne": 5, "Le Havre AC": 5, "Montpellier HSC": 5,
    },
}

# Moltiplicatori di attacco/difesa associati a ciascun tier (1 = più forte).
# Attacco > 1 = segna più della media; difesa > 1 = concede più della media
# (quindi è "leaky", non forte in difesa) — per questo alle squadre forti
# (tier 1) corrisponde un valore di difesa BASSO.
_TIER_ATTACK_PRIOR: dict[int, float] = {1: 1.55, 2: 1.25, 3: 1.00, 4: 0.80, 5: 0.62}
_TIER_DEFENSE_PRIOR: dict[int, float] = {1: 0.68, 2: 0.85, 3: 1.00, 4: 1.20, 5: 1.42}
_DEFAULT_TIER = 3

MDS_RATING_SHRINKAGE_MATCHES = 6
# Numero di partite (in un dato contesto casa/trasferta) oltre il quale il
# modello si fida ORMAI QUASI SOLO dei dati osservati e sempre meno del
# prior di tier. Con meno partite, il prior pesa di più: proprio la
# situazione (inizio stagione, dataset demo) in cui nascevano gli upset
# implausibili.
MDS_STRENGTH_GAIN = 1.15
# Esponente applicato al rapporto di forza fuso (prior+osservato) per
# accentuare leggermente il gap tra big e underdog invece di appiattirlo.


def _normalize_external_rating(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Normalizza un rating esterno (scala lo-hi, tipicamente 0-100) in
    [0, 1]."""
    if hi <= lo:
        return 0.5
    return clamp((float(value) - lo) / (hi - lo), 0.0, 1.0)


def _external_team_prior(entry: dict) -> tuple[float, float]:
    """CONTRATTO DATI ESTERNI (da app.py via teams_data/ratings_df): per
    ogni squadra ci si aspetta un record con chiavi (tutte opzionali tranne
    almeno una tra 'attack'/'overall'):
        {"attack": 0-100, "defense": 0-100, "overall": 0-100, "form": 0-100}
    'overall' fa da fallback per attack/defense se mancanti; 'form' è un
    modificatore opzionale (forma recente) applicato sopra l'attack/defense
    di base. Non conoscendo lo schema esatto già in uso in app.py, questo è
    il contratto che questo file si aspetta: se i vostri rating usano nomi o
    scale diverse, o normalizzali prima di passarli qui, o fatemelo sapere e
    adatto questa funzione.
    Ritorna (attack_multiplier, defense_multiplier) nello stesso spazio del
    prior di tier locale (~0.60 debole .. ~1.60 forte per l'attacco, inverso
    per la difesa)."""
    attack_raw = entry.get("attack", entry.get("overall", 50))
    defense_raw = entry.get("defense", entry.get("overall", 50))
    form_raw = entry.get("form")

    attack_norm = _normalize_external_rating(attack_raw)
    defense_norm = _normalize_external_rating(defense_raw)

    attack_prior = 0.60 + attack_norm * 1.00       # 0.60 .. 1.60
    defense_prior = 1.60 - defense_norm * 1.00     # 1.60 (debole) .. 0.60 (forte)

    if form_raw is not None:
        form_norm = _normalize_external_rating(form_raw)
        form_factor = 0.88 + form_norm * 0.24      # 0.88 .. 1.12
        attack_prior *= form_factor
        defense_prior /= form_factor

    return attack_prior, defense_prior


def _lookup_external_team_entry(teams_data: dict | None, ratings_df, team: str) -> dict | None:
    """Cerca il record di rating esterno per `team`, prima in `teams_data`
    (dict {nome_squadra: record}), poi in `ratings_df` (oggetto DataFrame-
    like con colonne tipo 'team'/'team_name'/'squad'/'club' + rating).
    Nessun import di pandas: se `ratings_df` è un vero DataFrame, i suoi
    stessi metodi (.to_dict) sono già disponibili senza bisogno di
    importare la libreria qui."""
    if teams_data:
        entry = teams_data.get(team)
        if entry is None:
            team_lower = team.lower()
            for name, data in teams_data.items():
                if isinstance(name, str) and name.lower() == team_lower:
                    entry = data
                    break
        if isinstance(entry, dict):
            return entry

    if ratings_df is not None:
        try:
            records = ratings_df.to_dict("records") if hasattr(ratings_df, "to_dict") else list(ratings_df)
        except Exception:
            records = []
        team_lower = team.lower()
        for row in records:
            if not isinstance(row, dict):
                continue
            name = row.get("team") or row.get("team_name") or row.get("squad") or row.get("club")
            if isinstance(name, str) and name.lower() == team_lower:
                return row

    return None


def _team_prior_strength(
    league: str, team: str, teams_data: dict | None = None, ratings_df=None
) -> tuple[float, float]:
    """Prior (attack, defense) per una squadra. Priorità:
    1) dati REALI esterni (teams_data/ratings_df, se passati da app.py e se
       contengono questa squadra) — vedi _external_team_prior per il
       contratto atteso;
    2) altrimenti, il tier di forza locale (CLUB_STRENGTH_TIER), con
       fallback a un confronto case-insensitive per substring e infine al
       tier di default (3, forza media) se la squadra non è nota."""
    external_entry = _lookup_external_team_entry(teams_data, ratings_df, team)
    if external_entry is not None:
        try:
            return _external_team_prior(external_entry)
        except (TypeError, ValueError):
            pass  # record esterno malformato: ricadi sul tier locale

    tiers = CLUB_STRENGTH_TIER.get(league, {})
    tier = tiers.get(team)
    if tier is None:
        team_lower = team.lower()
        for known_name, known_tier in tiers.items():
            known_lower = known_name.lower()
            if known_lower in team_lower or team_lower in known_lower:
                tier = known_tier
                break
    if tier is None:
        tier = _DEFAULT_TIER
    return _TIER_ATTACK_PRIOR[tier], _TIER_DEFENSE_PRIOR[tier]


def _blended_strength(n_matches: int, observed_ratio: float, prior_ratio: float) -> float:
    """Shrinkage bayesiano semplice: con pochi precedenti (n_matches basso)
    il prior (esterno se disponibile, altrimenti di tier) pesa di più; con
    uno storico consistente, il modello converge verso il rapporto
    osservato. Il risultato finale viene poi leggermente accentuato da
    MDS_STRENGTH_GAIN per mantenere una separazione realistica tra squadre
    di livello diverso."""
    weight = min(1.0, n_matches / MDS_RATING_SHRINKAGE_MATCHES)
    blended = weight * observed_ratio + (1 - weight) * prior_ratio
    return blended ** MDS_STRENGTH_GAIN


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


def _team_home_attack(
    finished: list[dict], team: str, league_home_avg: float, league: str, teams_data=None, ratings_df=None
) -> float:
    matches = [m for m in finished if m["home"] == team]
    attack_prior, _ = _team_prior_strength(league, team, teams_data, ratings_df)
    if not matches or league_home_avg <= 0:
        return attack_prior
    observed = (sum(m["home_goals"] for m in matches) / len(matches)) / league_home_avg
    return _blended_strength(len(matches), observed, attack_prior)


def _team_away_attack(
    finished: list[dict], team: str, league_away_avg: float, league: str, teams_data=None, ratings_df=None
) -> float:
    matches = [m for m in finished if m["away"] == team]
    attack_prior, _ = _team_prior_strength(league, team, teams_data, ratings_df)
    if not matches or league_away_avg <= 0:
        return attack_prior
    observed = (sum(m["away_goals"] for m in matches) / len(matches)) / league_away_avg
    return _blended_strength(len(matches), observed, attack_prior)


def _team_home_defense(
    finished: list[dict], team: str, league_away_avg: float, league: str, teams_data=None, ratings_df=None
) -> float:
    matches = [m for m in finished if m["home"] == team]
    _, defense_prior = _team_prior_strength(league, team, teams_data, ratings_df)
    if not matches or league_away_avg <= 0:
        return defense_prior
    observed = (sum(m["away_goals"] for m in matches) / len(matches)) / league_away_avg
    return _blended_strength(len(matches), observed, defense_prior)


def _team_away_defense(
    finished: list[dict], team: str, league_home_avg: float, league: str, teams_data=None, ratings_df=None
) -> float:
    matches = [m for m in finished if m["away"] == team]
    _, defense_prior = _team_prior_strength(league, team, teams_data, ratings_df)
    if not matches or league_home_avg <= 0:
        return defense_prior
    observed = (sum(m["home_goals"] for m in matches) / len(matches)) / league_home_avg
    return _blended_strength(len(matches), observed, defense_prior)


def try_build_match_model(
    league: str, home: str, away: str, teams_data: dict | None = None, ratings_df=None
) -> tuple[MatchModel | None, str | None]:
    """`teams_data`/`ratings_df` sono opzionali e vengono passati da chi
    chiama (in ultima istanza, render_matchday_simulator_tab, a sua volta
    chiamato da app.py con i dati reali di rating/forma — vedi il contratto
    in _external_team_prior). Se assenti, si ricade sul prior di tier
    locale (CLUB_STRENGTH_TIER)."""
    try:
        matches = fetch_league_matches(league)
    except FootballDataError as exc:
        return None, str(exc)

    finished = _finished_matches(matches)
    league_home_avg, league_away_avg = _league_average_goals(finished)

    home_attack = _team_home_attack(finished, home, league_home_avg, league, teams_data, ratings_df)
    away_defense = _team_away_defense(finished, away, league_home_avg, league, teams_data, ratings_df)
    away_attack = _team_away_attack(finished, away, league_away_avg, league, teams_data, ratings_df)
    home_defense = _team_home_defense(finished, home, league_away_avg, league, teams_data, ratings_df)

    home_lambda = clamp(league_home_avg * home_attack * away_defense, MDS_LAMBDA_FLOOR, MDS_LAMBDA_CEILING)
    away_lambda = clamp(league_away_avg * away_attack * home_defense, MDS_LAMBDA_FLOOR, MDS_LAMBDA_CEILING)

    return MatchModel(home_team=home, away_team=away, home_lambda=home_lambda, away_lambda=away_lambda), None


def run_simulation(model: MatchModel, n_simulations: int = 10_000) -> dict[str, dict[str, np.ndarray]]:
    rng = np.random.default_rng()
    home_goals = rng.poisson(max(model.home_lambda, 0.01), size=n_simulations)
    away_goals = rng.poisson(max(model.away_lambda, 0.01), size=n_simulations)
    return {"raw": {"home_goals": home_goals, "away_goals": away_goals}}

# ==============================================================================
# CALIBRAZIONE GOL — range xG realistico, no "risultati tennistici"
# ==============================================================================
# NOTA IMPORTANTE: i moltiplicatori qui sotto erano originariamente pensati
# per "eccitare" i video social gonfiando gli xG (fino a ×1.20). Questo va
# in conflitto diretto con l'obiettivo di realismo richiesto ora (niente
# 5-3, 6-2, 4-4 "di massa"), quindi li ho ridotti drasticamente: restano
# solo micro-aggiustamenti di stile di gioco per lega, non più un boost di
# spettacolarità. Se preferisci lo spettacolo puro alla plausibilità, dimmelo
# e li rialzo di nuovo — ma le due cose sono in tensione tra loro.
LEAGUE_GOAL_MULTIPLIERS: dict[str, float] = {
    "England · Premier League": 1.04,
    "Italy · Serie A": 1.00,
    "Germany · Bundesliga": 1.05,
    "Spain · La Liga": 1.00,
    "France · Ligue 1": 1.02,
}
LEAGUE_GOAL_MULTIPLIER_DEFAULT = 1.0

LEAGUE_ZERO_ZERO_SUPPRESSED: set[str] = {"Italy · Serie A"}

MDS_MAX_GOALS_PER_TEAM = 4
# HARD CAP per squadra: ogni singola simulazione Monte Carlo viene troncata
# (np.clip) a questo valore. Questo garantisce 0% di probabilità — non solo
# "<1%" — che una squadra mostri più di 4 gol nel punteggio rivelato: un
# vincolo più stringente di quanto richiesto, applicato allo stesso modo a
# tutti e 10.000 i campioni Monte Carlo di ogni match, PRIMA che venga letto
# il punteggio più frequente.

MDS_LAMBDA_FLOOR = 0.75
MDS_LAMBDA_CEILING = 2.30
# Range di xG (lambda Poisson) per squadra dopo calibrazione di lega: anche
# il top team più forte non supera 2.30 di xG atteso, anche l'underdog più
# debole non scende sotto 0.75. Combinato con il cap sui gol qui sopra e col
# prior di forza per club, questo sposta la distribuzione dei punteggi verso
# risultati "normali" (2-1, 3-1, 1-2, 2-2, 3-0) invece che verso i blowout.

MDS_ZERO_ZERO_RESAMPLE_ATTEMPTS = 25

MDS_ZERO_ZERO_MATCHDAY_CAP = 2
# HARD CAP GIORNATA: al massimo questo numero di 0-0 può comparire come
# punteggio rivelato nell'intera giornata simulata.

MDS_ZERO_ZERO_BOOST_STEP = 0.50
# Incremento di xG (additivo, cumulativo) applicato ad ogni giro del ciclo
# while anti-0-0 di giornata, SOLO ai match ancora 0-0.

MDS_ZERO_ZERO_MAX_BOOST_ROUNDS = 15

# --- Timeline dell'animazione CSS (vedi docstring in testa al file) ---
MDS_HOOK_DURATION_SECONDS = 1.8
# Tempo totale per cui l'hook resta a schermo (visibile ~1.5s, poi una
# breve fase di dissolvenza/collasso): è anche l'istante in cui compare la
# prima card.
MDS_CARD_STAGGER_SECONDS = 0.6
# Intervallo, in secondi, tra la comparsa di una card e la successiva.


def _apply_league_calibration(league: str, home_lambda: float, away_lambda: float) -> tuple[float, float, float]:
    multiplier = LEAGUE_GOAL_MULTIPLIERS.get(league, LEAGUE_GOAL_MULTIPLIER_DEFAULT)
    adj_home = clamp(home_lambda * multiplier, MDS_LAMBDA_FLOOR, MDS_LAMBDA_CEILING)
    adj_away = clamp(away_lambda * multiplier, MDS_LAMBDA_FLOOR, MDS_LAMBDA_CEILING)
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
# CSS — Obsidian / Electric Cyan Broadcast HUD (9:16), reveal via keyframes
# ==============================================================================
MATCHDAY_CSS = f"""
<style>
.mds-wrap {{
    background: {MATCHDAY_BG};
    border: 1px solid rgba(0,229,255,0.35);
    border-radius: 12px;
    padding: 8px 10px;
    margin-bottom: 8px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.5), 0 0 14px rgba(0,229,255,0.10);
}}

/* ---- Status bar ad ALTEZZA FISSA: usata sia in standby sia nei risultati,
   cosi il blocco in cima alla griglia occupa sempre lo stesso spazio
   (requisito "zero scroll" — vedi note nella docstring del modulo). Nei
   risultati, il messaggio "analyzing" e quello "completato" si alternano
   con un crossfade (opacity) DENTRO questa altezza fissa, invece che con
   un collasso dell'intero blocco come nelle versioni precedenti. ---- */
.mds-status-bar {{
    position: relative;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: {MATCHDAY_BG};
    border: 1px solid rgba(0,229,255,0.55);
    border-radius: 10px;
    margin-bottom: 8px;
    overflow: hidden;
    box-shadow: 0 6px 18px rgba(0,0,0,0.55), 0 0 16px rgba(0,229,255,0.16);
}}
.mds-status-text {{
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-family: "Courier New", monospace;
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: {MATCHDAY_ACCENT};
    text-shadow: 0 0 8px rgba(0,229,255,0.5);
    white-space: nowrap;
    padding: 0 10px;
}}
.mds-status-dot {{
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: {MATCHDAY_ACCENT};
    animation: mdsPulse 1.4s ease-in-out infinite;
}}
.mds-status-analyzing {{
    opacity: 1;
    animation: mdsStatusOut {MDS_HOOK_DURATION_SECONDS}s ease forwards;
}}
.mds-status-done {{
    opacity: 0;
    animation: mdsStatusIn {MDS_HOOK_DURATION_SECONDS}s ease forwards;
}}
@keyframes mdsStatusOut {{
    0%   {{ opacity: 1; }}
    75%  {{ opacity: 1; }}
    100% {{ opacity: 0; }}
}}
@keyframes mdsStatusIn {{
    0%   {{ opacity: 0; }}
    75%  {{ opacity: 0; }}
    100% {{ opacity: 1; }}
}}
@keyframes mdsPulse {{
    0%, 100% {{ opacity: 0.6; }}
    50% {{ opacity: 1; }}
}}

/* ---- Griglia delle 10 card: 2 colonne di default, 3 su schermi larghi ---- */
.mds-cards-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
    margin-bottom: 8px;
}}
@media (min-width: 700px) {{
    .mds-cards-grid {{
        grid-template-columns: repeat(3, 1fr);
    }}
}}

/* ---- Match card: compatta, fade-in + slide-up con animation-delay ---- */
.mds-card {{
    position: relative;
    background: {MATCHDAY_BG};
    border: 1px solid {MATCHDAY_ACCENT};
    border-radius: 10px;
    padding: 8px 6px 20px 6px;
    box-shadow: 0 0 12px rgba(0,229,255,0.14), 0 4px 12px rgba(0,0,0,0.5);
    text-align: center;
    opacity: 0;
    animation: mdsCardIn 0.4s ease forwards;
    animation-delay: var(--mds-delay, 0s);
    min-width: 0;
}}
@keyframes mdsCardIn {{
    from {{ opacity: 0; transform: translateY(10px) scale(0.98); }}
    to   {{ opacity: 1; transform: translateY(0) scale(1); }}
}}
.mds-calib-tag {{
    position: absolute;
    top: 3px;
    left: 5px;
    font-family: "Courier New", monospace;
    font-size: 0.44rem;
    letter-spacing: 0.02em;
    color: {MATCHDAY_ACCENT};
    opacity: 0.65;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: calc(100% - 10px);
}}
.mds-card-teams {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
}}
.mds-team {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
    min-width: 0;
}}
.mds-crest {{
    width: 28px;
    height: 28px;
    object-fit: contain;
}}
.mds-crest-placeholder {{
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    opacity: 0.6;
}}
.mds-team-name {{
    font-weight: 800;
    font-size: 0.56rem;
    text-transform: uppercase;
    letter-spacing: 0.01em;
    color: #f5f5f5;
    text-align: center;
    overflow-wrap: break-word;
    line-height: 1.1;
    min-height: 1.3em;
}}
.mds-score {{
    font-size: 1.55rem;
    font-weight: 900;
    letter-spacing: 0.03em;
    font-variant-numeric: tabular-nums;
    background: linear-gradient(135deg, {MATCHDAY_ACCENT}, #ffffff);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin: 0 2px;
    line-height: 1;
    white-space: nowrap;
}}
.mds-pill {{
    position: absolute;
    bottom: 5px;
    right: 6px;
    font-family: "Courier New", monospace;
    font-size: 0.56rem;
    font-weight: 800;
    letter-spacing: 0.02em;
    padding: 2px 7px;
    border-radius: 999px;
    border: 1px solid rgba(0,229,255,0.55);
    background: rgba(0,229,255,0.10);
    color: {MATCHDAY_ACCENT};
    white-space: nowrap;
}}
.mds-header-title {{
    font-family: "Courier New", monospace;
    font-size: 0.85rem;
    font-weight: 900;
    letter-spacing: 0.08em;
    color: {MATCHDAY_ACCENT};
    text-transform: uppercase;
    text-shadow: 0 0 8px rgba(0,229,255,0.5);
    margin-bottom: 2px;
}}
.mds-disclaimer {{
    font-size: 0.60rem;
    color: #9aa0a6;
    line-height: 1.25;
    margin: 2px 0 8px 0;
    padding: 5px 8px;
    border-left: 2px solid {MATCHDAY_ACCENT};
    background: rgba(0,229,255,0.05);
    border-radius: 5px;
}}

/* ---- Pill "big match" nelle card di standby: stessa classe .mds-pill,
   solo leggermente più opaca per distinguerla visivamente da un esito
   reale già rivelato ---- */
.mds-pill-preview {{
    opacity: 0.85;
}}

/* ---- Banner di riepilogo finale: appare per ultimo, via animation-delay ---- */
.mds-summary-wrap {{
    background: {MATCHDAY_BG};
    border: 1px solid {MATCHDAY_ACCENT};
    border-radius: 12px;
    padding: 8px 10px;
    margin-top: 2px;
    box-shadow: 0 0 16px rgba(0,229,255,0.18), 0 4px 14px rgba(0,0,0,0.55);
    opacity: 0;
    animation: mdsCardIn 0.4s ease forwards;
    animation-delay: var(--mds-delay, 0s);
}}
.mds-summary-title {{
    font-family: "Courier New", monospace;
    font-size: 0.62rem;
    font-weight: 900;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    color: {MATCHDAY_ACCENT};
    text-align: center;
    margin-bottom: 6px;
    text-shadow: 0 0 6px rgba(0,229,255,0.5);
}}
.mds-summary-row {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    justify-content: center;
}}
.mds-summary-badge {{
    flex: 1;
    min-width: 90px;
    background: #0a0a0a;
    border: 1px solid rgba(0,229,255,0.5);
    border-radius: 10px;
    padding: 5px 8px;
    text-align: center;
}}
.mds-summary-value {{
    font-family: "Courier New", monospace;
    font-size: 0.95rem;
    font-weight: 900;
    color: {MATCHDAY_ACCENT};
    text-shadow: 0 0 8px rgba(0,229,255,0.6);
    line-height: 1.1;
}}
.mds-summary-label {{
    font-size: 0.50rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #9aa0a6;
    margin-top: 1px;
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
# (calcolo Python sincrono, invariato: cambia solo come viene poi mostrato)
# ==============================================================================
def _simulate_fixture_raw(
    league: str, home: str, away: str, calibration_enabled: bool, teams_data=None, ratings_df=None
):
    model, error = try_build_match_model(league, home, away, teams_data, ratings_df)
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


def _run_full_matchday(
    league: str,
    fixtures: list[tuple[str, str]],
    calibration_enabled: bool,
    teams_data: dict | None = None,
    ratings_df=None,
) -> list[dict[str, object]]:
    """1) Simula tutte le fixture in un array temporaneo (`results`), usando
       i rating reali (teams_data/ratings_df) se passati da app.py, oppure
       il prior di tier locale come fallback.
    2) Se calibrazione abilitata e gli 0-0 rivelati sono > MDS_ZERO_ZERO_
       MATCHDAY_CAP (2), un ciclo while incrementa di MDS_ZERO_ZERO_BOOST_
       STEP (+0.50) l'xG (cumulativo) SOLO dei match ancora 0-0 e li
       ri-simula da zero, finché il conteggio non scende a <= 2 o si
       raggiunge il tetto di sicurezza MDS_ZERO_ZERO_MAX_BOOST_ROUNDS.
    Tutto questo avviene qui, PRIMA che una sola riga di HTML venga
    generata: il reveal a cascata (gestito interamente da CSS più sotto)
    parte solo a calcolo completato."""
    results: list[dict[str, object]] = []
    fixture_state: list[dict[str, object] | None] = []

    for home, away in fixtures:
        model, error, home_goals, away_goals, calib_notes = _simulate_fixture_raw(
            league, home, away, calibration_enabled, teams_data, ratings_df
        )
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
                boosted_home = clamp(base_model.home_lambda + cumulative_boost, MDS_LAMBDA_FLOOR, MDS_LAMBDA_CEILING)
                boosted_away = clamp(base_model.away_lambda + cumulative_boost, MDS_LAMBDA_FLOOR, MDS_LAMBDA_CEILING)
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
# RENDERING — un unico blocco HTML, reveal scandito da CSS animation-delay
# ==============================================================================
def _crest_html(name: str, crests: dict[str, str]) -> str:
    url = crests.get(name)
    if url:
        return f'<img src="{escape(url)}" class="mds-crest" />'
    return '<div class="mds-crest-placeholder">🛡️</div>'


def _status_bar_standby_html() -> str:
    """Status bar per lo stato di PREVIEW, ad altezza fissa (.mds-status-bar,
    34px) — la STESSA identica classe/altezza usata nello stato risultati
    (_status_bar_running_html), così questo blocco non introduce alcuna
    differenza di altezza tra i due stati."""
    return (
        '<div class="mds-status-bar">'
        '<div class="mds-status-text"><span class="mds-status-dot"></span>'
        "SIMULATORE GIORNATA LIVE • PRONTO ALL'AVVIO</div>"
        "</div>"
    )


def _status_bar_running_html(n_matches: int) -> str:
    """Status bar per lo stato RISULTATI: stessa altezza fissa di
    _status_bar_standby_html, ma con due testi sovrapposti che si alternano
    in crossfade (mdsStatusOut / mdsStatusIn, durata MDS_HOOK_DURATION_
    SECONDS) invece che con un collasso dell'intero blocco — è questo il
    meccanismo che garantisce l'altezza identica al millimetro tra standby
    e risultati richiesta: l'hook non sparisce più, semplicemente il testo
    al suo interno cambia."""
    return (
        '<div class="mds-status-bar">'
        '<div class="mds-status-text mds-status-analyzing">⚡ WAYNELAB AI ENGINE — '
        "10,000 MONTE CARLO RUNS...</div>"
        f'<div class="mds-status-text mds-status-done">✅ SIMULATION COMPLETE — {n_matches} MATCHES</div>'
        "</div>"
    )


def _team_tier_for_display(league: str, team: str) -> int:
    """Tier grezzo (1-5) di una squadra, solo per etichettare le card di
    ANTEPRIMA come 'big match' quando coinvolgono un club di tier 1-2 —
    puramente estetico, non influenza la simulazione."""
    tiers = CLUB_STRENGTH_TIER.get(league, {})
    tier = tiers.get(team)
    if tier is None:
        team_lower = team.lower()
        for known_name, known_tier in tiers.items():
            known_lower = known_name.lower()
            if known_lower in team_lower or team_lower in known_lower:
                tier = known_tier
                break
    return tier if tier is not None else _DEFAULT_TIER


def _preview_card_html(home: str, away: str, league: str, crests: dict[str, str]) -> str:
    """Card di ANTEPRIMA per lo stato di standby: usa esattamente le stesse
    classi CSS (.mds-card, .mds-card-teams, .mds-team, .mds-score, .mds-pill)
    della card di risultato in _match_card_html — non una card diversa. È
    proprio questo riuso 1:1 delle stesse classi, dentro la stessa
    .mds-cards-grid, a garantire che standby e risultati abbiano
    ESATTAMENTE la stessa geometria: cambia solo il contenuto testuale
    (nomi + 'VS' invece di nomi + punteggio; 'BIG MATCH'/'IN ANALISI'
    invece dell'esito 1X2), non le dimensioni della cella."""
    best_tier = min(_team_tier_for_display(league, home), _team_tier_for_display(league, away))
    tag = "🔥 BIG MATCH" if best_tier <= 2 else "IN ANALISI"
    return (
        '<div class="mds-card">'
        '<div class="mds-card-teams">'
        f'<div class="mds-team">{_crest_html(home, crests)}'
        f'<div class="mds-team-name">{escape(home)}</div></div>'
        '<div class="mds-score">VS</div>'
        f'<div class="mds-team">{_crest_html(away, crests)}'
        f'<div class="mds-team-name">{escape(away)}</div></div>'
        "</div>"
        f'<div class="mds-pill mds-pill-preview">{tag}</div>'
        "</div>"
    )


def _standby_summary_html() -> str:
    """Placeholder del banner di riepilogo per lo stato standby: stessa
    classe .mds-summary-wrap e stessa struttura a badge di _summary_html,
    con valori segnaposto ('—') al posto dei numeri reali — di nuovo, per
    garantire la stessa identica altezza tra i due stati."""
    return (
        '<div class="mds-summary-wrap">'
        '<div class="mds-summary-title">📊 Matchday Summary</div>'
        '<div class="mds-summary-row">'
        '<div class="mds-summary-badge"><div class="mds-summary-value">—</div>'
        '<div class="mds-summary-label">Total Goals</div></div>'
        '<div class="mds-summary-badge"><div class="mds-summary-value">—</div>'
        '<div class="mds-summary-label">Avg Goals / Match</div></div>'
        "</div></div>"
    )


def _build_standby_html(league: str, fixtures: list[tuple[str, str]], crests: dict[str, str]) -> str:
    """Assembla l'intero stato di PREVIEW/STANDBY: status bar (altezza
    fissa) + griglia di 10 card di anteprima (stesse classi CSS delle card
    di risultato) + banner di riepilogo segnaposto (stessa classe del
    riepilogo reale). Il risultato è, geometricamente, un layout identico a
    _build_broadcast_html a parità di numero di fixture — cambia solo il
    contenuto testuale delle celle, mai le loro dimensioni."""
    parts: list[str] = [_status_bar_standby_html(), '<div class="mds-cards-grid">']
    for home, away in fixtures:
        parts.append(_preview_card_html(home, away, league, crests))
    parts.append("</div>")
    parts.append(_standby_summary_html())
    return "".join(parts)


def _match_card_html(home: str, away: str, outcome: dict[str, object], crests: dict[str, str], delay_seconds: float) -> str:
    """Markup di una singola card, con --mds-delay impostato inline: è
    questo valore (non un time.sleep) a determinare quando la card appare,
    tramite `animation-delay: var(--mds-delay, 0s)` definito in .mds-card."""
    calib_tag = outcome.get("calib_tag", "")
    calib_html = f'<div class="mds-calib-tag">{escape(calib_tag)}</div>' if calib_tag else ""
    pill_code, pill_prob = _revealed_outcome_pill(outcome)
    return (
        f'<div class="mds-card" style="--mds-delay:{delay_seconds:.2f}s">'
        f"{calib_html}"
        f'<div class="mds-card-teams">'
        f'<div class="mds-team">{_crest_html(home, crests)}'
        f'<div class="mds-team-name">{escape(home)}</div></div>'
        f'<div class="mds-score">{escape(outcome["score"])}</div>'
        f'<div class="mds-team">{_crest_html(away, crests)}'
        f'<div class="mds-team-name">{escape(away)}</div></div>'
        f"</div>"
        f'<div class="mds-pill">{pill_code} · {pill_prob:.0%}</div>'
        f"</div>"
    )


def _error_card_html(home: str, away: str, error: str | None, delay_seconds: float) -> str:
    message = escape(error or "simulazione non disponibile")
    return (
        f'<div class="mds-card" style="--mds-delay:{delay_seconds:.2f}s; text-align:left;">'
        f'<div class="mds-team-name" style="color:#ffb020;">⚠️ {escape(home)} vs {escape(away)}</div>'
        f'<div style="color:#d8dadc; font-size:0.85rem; margin-top:6px;">{message}</div>'
        f"</div>"
    )


def _summary_html(results: list[dict[str, object]], delay_seconds: float) -> str:
    valid = [r for r in results if "error" not in r and "home_goals_total" in r]
    if not valid:
        return ""
    total_goals = sum(r["home_goals_total"] + r["away_goals_total"] for r in valid)
    avg_goals = total_goals / len(valid)

    return (
        f'<div class="mds-summary-wrap" style="--mds-delay:{delay_seconds:.2f}s">'
        '<div class="mds-summary-title">📊 Matchday Summary</div>'
        '<div class="mds-summary-row">'
        f'<div class="mds-summary-badge"><div class="mds-summary-value">{total_goals}</div>'
        f'<div class="mds-summary-label">Total Goals</div></div>'
        f'<div class="mds-summary-badge"><div class="mds-summary-value">{avg_goals:.2f}</div>'
        f'<div class="mds-summary-label">Avg Goals / Match</div></div>'
        "</div>"
        "</div>"
    )


def _build_broadcast_html(results: list[dict[str, object]], crests: dict[str, str]) -> str:
    """Assembla status bar + 10 card + banner di riepilogo in UN SOLO
    blocco HTML. Le card sono avvolte in un contenitore `.mds-cards-grid`
    (grid CSS a 2 colonne, 3 su schermi larghi) cosi da restare compatte
    per le riprese 9:16 invece di impilarsi una sopra l'altra. Ogni card
    porta il proprio `--mds-delay` calcolato qui in Python (aritmetica
    pura, nessuna attesa reale), ma è il CSS — non Python — a far scorrere
    il tempo e a rivelare gli elementi uno alla volta nel browser. Card
    i-esima (0-based): delay = MDS_HOOK_DURATION_SECONDS + i ×
    MDS_CARD_STAGGER_SECONDS, cosi la spaziatura RELATIVA tra una card e la
    successiva è sempre di 0.6s. La status bar (_status_bar_running_html)
    ha ALTEZZA FISSA identica a quella dello stato standby: non collassa
    più a fine animazione, cambia solo il testo al suo interno — è questo
    che garantisce l'altezza identica al millimetro tra i due stati."""
    parts: list[str] = [_status_bar_running_html(len(results)), '<div class="mds-cards-grid">']

    for index, outcome in enumerate(results):
        delay = MDS_HOOK_DURATION_SECONDS + index * MDS_CARD_STAGGER_SECONDS
        if "error" in outcome:
            parts.append(_error_card_html(outcome["home"], outcome["away"], outcome.get("error"), delay))
        else:
            parts.append(_match_card_html(outcome["home"], outcome["away"], outcome, crests, delay))

    parts.append("</div>")

    summary_delay = MDS_HOOK_DURATION_SECONDS + len(results) * MDS_CARD_STAGGER_SECONDS
    parts.append(_summary_html(results, summary_delay))

    return "".join(parts)


# ==============================================================================
# MAIN TAB ENTRY POINT — nessun parametro, nessuna dipendenza esterna
# ==============================================================================
def render_matchday_simulator_tab(teams_data: dict | None = None, ratings_df=None) -> None:
    """Entry point della tab.

    `teams_data` / `ratings_df` sono OPZIONALI e vengono passati da chi
    chiama questa funzione (tipicamente app.py) — non da un import: questo
    file non importa mai nulla da app.py, quindi nessun circular import è
    possibile. Se app.py li passa, i rating/forma reali vengono usati per
    calcolare gli xG; se restano None, si ricade sul prior di tier interno
    (CLUB_STRENGTH_TIER), bilanciato ma non basato su dati live.

    Contratto atteso per `teams_data`: dict {nome_squadra: record}, dove
    record è un dict con chiavi 'attack', 'defense', 'overall' (0-100) e
    opzionalmente 'form' (0-100). 'ratings_df' è lo stesso concetto ma come
    oggetto DataFrame-like con una colonna nome-squadra ('team'/'team_name'/
    'squad'/'club') e le stesse colonne di rating. Vedi _external_team_prior
    per i dettagli esatti della conversione. Se lo schema reale di app.py è
    diverso, adattalo prima di passarlo qui, o comunica i nomi di colonna
    reali per un adattamento mirato.

    LAYOUT COMPATTO (zero-scroll): header + toggle su un'unica riga, info di
    dettaglio dentro un expander chiuso di default, selettori campionato/
    giornata + pulsante SIMULATE su un'unica riga. Lo stato standby e la
    griglia dei risultati condividono lo STESSO st.empty(): al click,
    l'interfaccia non cresce di un pixel in più, si limita a sostituire il
    contenuto del placeholder in-place — nessuno scroll aggiuntivo per la
    registrazione video."""
    st.markdown(MATCHDAY_CSS, unsafe_allow_html=True)

    header_col, toggle_col = st.columns([2, 1])
    with header_col:
        st.markdown('<div class="mds-header-title">🏆 MATCHDAY LIVE SIMULATOR</div>', unsafe_allow_html=True)
    with toggle_col:
        calibration_enabled = st.toggle(
            "🎯 Calibration", value=True, key="mds_calibration_enabled", label_visibility="visible"
        )

    with st.expander("ℹ️ Modello & calibrazione", expanded=False):
        st.caption(
            "Standalone HUD Broadcast engine — reveal a cascata gestito interamente via CSS, non da "
            "timer lato server. Il modello Poisson attack/defense usa i rating reali passati da app.py "
            "(teams_data/ratings_df) quando disponibili, altrimenti un prior di forza per club interno "
            "con shrinkage bayesiano — così i big non perdono in modo implausibile contro le piccole. "
            f"xG per squadra vincolato tra {MDS_LAMBDA_FLOOR:.2f} e {MDS_LAMBDA_CEILING:.2f}, "
            f"nessuna squadra può mostrare più di {MDS_MAX_GOALS_PER_TEAM} gol nel punteggio rivelato."
        )
        st.markdown(
            '<div class="mds-disclaimer">🎬 <b>Entertainment Calibration</b>: this tab applies '
            "light per-league xG multipliers and score-shaping rules (goal cap, 0-0 exclusion for "
            "select leagues, max 2×0-0 per matchday via an xG boost loop) tuned for realistic, "
            "social-friendly pacing. Turn the toggle above off to see the model without calibration."
            "</div>",
            unsafe_allow_html=True,
        )

    col_league, col_matchday, col_button = st.columns([2, 2, 2])
    with col_league:
        league = st.selectbox(
            "Competition",
            options=list(FOOTBALL_DATA_COMPETITIONS),
            key="mds_league_select",
            label_visibility="collapsed",
        )

    matchdays = _available_matchdays(league)
    with col_matchday:
        if matchdays:
            matchday = st.selectbox(
                "Matchday",
                options=matchdays,
                format_func=lambda n: f"Giornata {n}",
                key="mds_matchday_select",
                label_visibility="collapsed",
            )
        else:
            st.warning("No live matchday data available for this competition.")
            return

    fixtures = _matchday_fixtures(league, matchday)
    if not fixtures:
        st.info(f"No fixtures found for Giornata {matchday} in {league}.")
        return

    with col_button:
        run_clicked = st.button(
            "⚡ SIMULATE", type="primary", key="mds_run_button", use_container_width=True
        )

    try:
        crests = fetch_team_crests(league)
    except FootballDataError:
        crests = {}

    # PREVIEW / RISULTATI: un solo st.empty() condiviso. Prima del click
    # mostra lo stato di standby; al click, il contenuto dello STESSO
    # placeholder viene sostituito con la griglia — l'interfaccia resta
    # fissa nello stesso punto dello schermo, nessuno scroll aggiuntivo.
    results_area = st.empty()

    if run_clicked:
        # RESET DELLO STATO AL CLICK.
        st.session_state.pop("simulated_results", None)
        st.session_state.pop("matchday_data", None)
        for key in list(st.session_state.keys()):
            if "matchday" in key or "mds" in key or "results" in key:
                del st.session_state[key]

        # 1) Simulazione completa della giornata, calcolata INTERAMENTE IN
        #    MEMORIA (rating esterni + hard cap anti-0-0 a ciclo while
        #    inclusi — vedi _run_full_matchday). Nessun output a schermo
        #    ancora.
        results = _run_full_matchday(league, fixtures, calibration_enabled, teams_data, ratings_df)

        # 2) UN SOLO blocco HTML con hook + 10 card + riepilogo, ciascuno con
        #    il proprio animation-delay calcolato in Python ma ESEGUITO dal
        #    browser via CSS: è questo, e non un ciclo time.sleep, a
        #    produrre il reveal a cascata — quindi è immune a qualunque
        #    comportamento di buffering lato server/hosting. Sostituisce lo
        #    stato di standby nello stesso placeholder.
        broadcast_html = _build_broadcast_html(results, crests)
        results_area.markdown(broadcast_html, unsafe_allow_html=True)
    else:
        results_area.markdown(_build_standby_html(league, fixtures, crests), unsafe_allow_html=True)
