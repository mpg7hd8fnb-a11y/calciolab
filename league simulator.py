"""
league_simulator.py — WayneLab · 🏆 Matchday Live Simulator
Modulo indipendente e puramente additivo: riusa esclusivamente le funzioni
e i modelli già presenti in app.py (build_match_model, run_simulation,
fetch_league_teams, fetch_league_matches, fetch_team_crests) — nessuna
nuova logica statistica di forecast, solo una nuova UI "broadcast" pensata
per la registrazione di contenuti social verticali (TikTok/Reels/Shorts).

⚠️ ENTERTAINMENT CALIBRATION LAYER
Questo modulo applica, SOLO al proprio interno, dei moltiplicatori di xG e
vincoli di punteggio pensati per rendere le simulazioni più dinamiche nei
video social. Questi aggiustamenti NON toccano in alcun modo il motore
Poisson/Dixon-Coles usato dalle altre tab (Match Analysis, Value Betting,
Monte Carlo Simulator, Multi-Outcome): le probabilità e i fair odds mostrati
lì restano il riferimento analitico dell'app. I moltiplicatori per lega qui
sotto sono valori di calibrazione discrezionali (non derivati da un feed
statistico verificato in tempo reale) — un utente può disattivarli con il
toggle in UI per vedere l'output non calibrato.

FIX CIRCULAR IMPORT
--------------------
Questo file NON contiene più, a livello di modulo, la riga
'from app import ...'. Se app.py importa league_simulator in testa al
proprio file (es. 'import league_simulator') per registrare la tab, e
league_simulator a sua volta importasse app allo stesso modo, si crea un
ciclo di import che Python non può risolvere (circular import). La
soluzione adottata è un IMPORT DIFFERITO ("lazy import"): le funzioni e le
variabili di app.py (FOOTBALL_DATA_COMPETITIONS, FootballDataError, clamp,
fetch_league_matches, fetch_team_crests, run_simulation,
try_build_match_model) vengono importate solo QUANDO
render_matchday_simulator_tab() viene effettivamente chiamata — non quando
questo modulo viene caricato — tramite _load_app_dependencies(). A quel
punto app.py è già stato completamente inizializzato, quindi il ciclo non
si verifica mai. In alternativa, per test o architetture più esplicite, le
stesse dipendenze possono essere passate a mano come argomento
`app_module` di render_matchday_simulator_tab(): in tal caso non avviene
alcun import di app.py da parte di questo file.

NOVITÀ FUNZIONALI (invariate rispetto alla versione precedente):
  • RESET RIGIDO DELLO STATO: al click su "SIMULATE FULL MATCHDAY", ogni
    chiave di st.session_state riconducibile a questo modulo (contenente
    "matchday", "mds" o "results") viene esplicitamente cancellata PRIMA di
    generare la nuova giornata.
  • ANTI-ZERO-ZERO A CICLO WHILE: le fixture vengono simulate una prima
    volta in un array temporaneo; se gli 0-0 rivelati sono più di
    MDS_ZERO_ZERO_MATCHDAY_CAP, un ciclo while applica un boost incrementale
    di +0.50 xG e ri-simula SOLO i match ancora 0-0, finché il totale della
    giornata non scende a <= cap (con un tetto di iterazioni di sicurezza).
  • MOTORE VISIVO "HUD BROADCAST" 9:16: hook iniziale animato (~2s), reveal
    delle card una alla volta con time.sleep(0.6) tra una e l'altra, e
    banner di riepilogo finale (Total Goals / Avg Goals / Home Wins %).
"""

from __future__ import annotations

import dataclasses
import time
from html import escape
from typing import Any, Callable

import numpy as np
import streamlit as st

MATCHDAY_ACCENT = "#00E5FF"
MATCHDAY_BG = "#050505"


# ==============================================================================
# DEPENDENCY INJECTION — nessun 'from app import ...' a livello di modulo
# ==============================================================================
@dataclasses.dataclass(frozen=True)
class AppDependencies:
    """Contenitore delle sole funzioni/variabili di app.py effettivamente
    usate da questo modulo. Costruito da _load_app_dependencies(), MAI
    importato direttamente in testa al file: questo è ciò che rompe il
    circular import."""

    FOOTBALL_DATA_COMPETITIONS: Any
    FootballDataError: type
    clamp: Callable[[float, float, float], float]
    fetch_league_matches: Callable[[str], list]
    fetch_team_crests: Callable[[str], dict]
    run_simulation: Callable[..., dict]
    try_build_match_model: Callable[[str, str, str], tuple]


def _load_app_dependencies(app_module: Any = None) -> AppDependencies:
    """Import DIFFERITO di app.py: eseguito solo quando la tab viene
    effettivamente renderizzata (dentro render_matchday_simulator_tab), non
    al caricamento di questo modulo. Se `app_module` viene passato
    esplicitamente (es. dai test, o da un chiamante che vuole evitare del
    tutto che questo file importi app.py), viene usato quello e non avviene
    alcun import."""
    if app_module is None:
        import app as app_module  # noqa: PLC0415 — import intenzionalmente locale

    return AppDependencies(
        FOOTBALL_DATA_COMPETITIONS=app_module.FOOTBALL_DATA_COMPETITIONS,
        FootballDataError=app_module.FootballDataError,
        clamp=app_module.clamp,
        fetch_league_matches=app_module.fetch_league_matches,
        fetch_team_crests=app_module.fetch_team_crests,
        run_simulation=app_module.run_simulation,
        try_build_match_model=app_module.try_build_match_model,
    )


# ==============================================================================
# ENTERTAINMENT CALIBRATION — league-level xG multipliers & score shaping
# ==============================================================================
# Valori discrezionali per pacing/engagement dei video, NON un feed di dati
# reali validato: mai presentati come i fair odds/probabilità ufficiali
# dell'app (quelli restano nelle altre tab, invariati).
LEAGUE_GOAL_MULTIPLIERS: dict[str, float] = {
    "England · Premier League": 1.18,
    "Italy · Serie A": 1.15,
    "Germany · Bundesliga": 1.20,
    "Spain · La Liga": 1.00,   # nessun aggiustamento: campionato tatticamente equilibrato
    "France · Ligue 1": 1.10,
}
LEAGUE_GOAL_MULTIPLIER_DEFAULT = 1.0

# Leghe in cui lo 0-0 viene escluso dalla distribuzione simulata di questo
# modulo (resampling verso un punteggio con almeno 1 gol), su richiesta
# esplicita per la Serie A. Aggiungere altre leghe qui se necessario.
LEAGUE_ZERO_ZERO_SUPPRESSED: set[str] = {"Italy · Serie A"}

MDS_MAX_GOALS_PER_TEAM = 4
# Realistic Score Cap: nessuna squadra può segnare più di questo numero di
# gol nel risultato mostrato — i risultati "tennistici" (5-1, 6-2...) vengono
# troncati a questo tetto invece di essere mostrati as-is.

MDS_LAMBDA_CEILING = 3.0
# Tetto di sicurezza sugli xG (dopo moltiplicatore di lega e/o boost
# anti-0-0), per evitare che un cumulo di fattori produca lambda
# irrealistici in ingresso alla simulazione.

MDS_ZERO_ZERO_RESAMPLE_ATTEMPTS = 25
# Tentativi massimi di resampling per singola partita simulata quando si
# deve escludere lo 0-0 a livello di singola lega: evita loop infiniti in
# casi limite (xG quasi a 0).

MDS_ZERO_ZERO_MATCHDAY_CAP = 2
# HARD CAP GIORNATA: al massimo questo numero di 0-0 può comparire come
# punteggio rivelato nell'intera giornata simulata (tipicamente 10 match).

MDS_ZERO_ZERO_BOOST_STEP = 0.50
# Incremento di xG (additivo, non moltiplicativo) applicato ad ogni giro del
# ciclo while anti-0-0 di giornata, SOLO ai match ancora 0-0 dopo il giro
# precedente. Cumulativo: al 2° giro un match ancora bloccato riceve +1.00
# totale, al 3° +1.50, ecc.

MDS_ZERO_ZERO_MAX_BOOST_ROUNDS = 15
# Tetto di sicurezza sul numero di giri del ciclo while, per evitare loop
# infiniti in casi limite (xG di partenza estremamente bassi su più match
# contemporaneamente).

MDS_HOOK_SECONDS = 2.0
# Durata del banner hook iniziale "⚡ WAYNELAB AI ENGINE" — i primi 2 secondi
# di video, prima che compaia la prima card.

MDS_CARD_REVEAL_DELAY_SECONDS = 0.6
# Ritardo REALE (time.sleep) tra la comparsa di una card e la successiva:
# è il ritmo di registrazione per i video social, non un'animazione CSS.


def _apply_league_calibration(
    league: str, home_lambda: float, away_lambda: float, clamp: Callable[[float, float, float], float]
) -> tuple[float, float, float]:
    """Applica il moltiplicatore di lega ai due xG, con un tetto di
    sicurezza (MDS_LAMBDA_CEILING). Ritorna (adj_home, adj_away,
    multiplier_used) per poter mostrare il fattore applicato in UI."""
    multiplier = LEAGUE_GOAL_MULTIPLIERS.get(league, LEAGUE_GOAL_MULTIPLIER_DEFAULT)
    adj_home = clamp(home_lambda * multiplier, 0.1, MDS_LAMBDA_CEILING)
    adj_away = clamp(away_lambda * multiplier, 0.1, MDS_LAMBDA_CEILING)
    return adj_home, adj_away, multiplier


def _cap_extreme_scores(home_goals: np.ndarray, away_goals: np.ndarray) -> None:
    """Realistic Score Cap: tronca in-place ogni partita simulata al
    massimo MDS_MAX_GOALS_PER_TEAM gol per squadra."""
    np.clip(home_goals, 0, MDS_MAX_GOALS_PER_TEAM, out=home_goals)
    np.clip(away_goals, 0, MDS_MAX_GOALS_PER_TEAM, out=away_goals)


def _suppress_zero_zero(
    rng: np.random.Generator, home_goals: np.ndarray, away_goals: np.ndarray, home_lambda: float, away_lambda: float
) -> None:
    """Anti-Zero-Zero per singola lega: per ogni partita simulata che
    risulta 0-0, ri-esegue l'estrazione Poisson (xG passati in argomento)
    fino a ottenere almeno 1 gol complessivo, con un numero massimo di
    tentativi per evitare loop infiniti su xG estremamente bassi.
    Statisticamente equivale a condizionare la Poisson bivariata all'evento
    'almeno un gol', non a una riscrittura arbitraria del risultato."""
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
            # xG troppo basso per escludere lo 0-0 in modo credibile entro i
            # tentativi previsti: forza il minimo risultato non-0-0 realistico.
            home_goals[index] = 1
            away_goals[index] = 0


def _empirical_score_and_outcomes(home_goals: np.ndarray, away_goals: np.ndarray) -> dict[str, object]:
    """Frequenze empiriche (post-calibrazione) del punteggio esatto più
    comune e delle probabilità 1X2, calcolate direttamente sugli stessi
    array Monte Carlo mostrati come risultato — così la pill 1X2 resta
    sempre coerente col punteggio esatto rivelato in questo modulo."""
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
    """Determina la pill 1X2 da mostrare in card in base al punteggio
    EFFETTIVAMENTE rivelato (non al solo esito più probabile in astratto):
    ritorna (codice, probabilità) dove codice è '1' (casa), 'X' (pareggio)
    o '2' (trasferta), e la probabilità è quella calcolata sugli stessi
    array Monte Carlo per quell'esito."""
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

/* ---- Hook iniziale (primi 2 secondi) ---- */
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

/* ---- Match card: Obsidian HUD ---- */
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
    left: 50%;
    transform: translateX(-50%);
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

/* ---- Banner di riepilogo finale ---- */
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
</style>
"""


# ==============================================================================
# DATA HELPERS — pure grouping/reading, no new statistical logic
# ==============================================================================
def _available_matchdays(league: str, deps: AppDependencies) -> list[int]:
    """Legge il campo 'matchday' già restituito da Football-Data.org per
    ogni fixture (deps.fetch_league_matches, invariata) e ne estrae l'elenco
    ordinato dei numeri di giornata disponibili per la competizione."""
    try:
        matches = deps.fetch_league_matches(league)
    except deps.FootballDataError:
        return []
    matchdays = sorted(
        {int(match["matchday"]) for match in matches if isinstance(match.get("matchday"), int)}
    )
    return matchdays


def _matchday_fixtures(league: str, matchday: int, deps: AppDependencies) -> list[tuple[str, str]]:
    """Elenco (home, away) delle fixture della giornata selezionata,
    filtrando le partite già recuperate da deps.fetch_league_matches per il
    campo 'matchday' — nessuna nuova chiamata API, nessun nuovo modello."""
    try:
        matches = deps.fetch_league_matches(league)
    except deps.FootballDataError:
        return []
    fixtures: list[tuple[str, str]] = []
    for match in matches:
        if match.get("matchday") != matchday:
            continue
        home_team = match.get("homeTeam", {})
        away_team = match.get("awayTeam", {})
        if not isinstance(home_team, dict) or not isinstance(away_team, dict):
            continue
        home_name = home_team.get("name")
        away_name = away_team.get("name")
        if isinstance(home_name, str) and isinstance(away_name, str):
            fixtures.append((home_name, away_name))
    return fixtures


# ==============================================================================
# SIMULATION — raw fixture pass + matchday-wide anti-zero-zero while-loop
# ==============================================================================
def _simulate_fixture_raw(league: str, home: str, away: str, calibration_enabled: bool, deps: AppDependencies):
    """Costruisce il MatchModel esistente (deps.try_build_match_model,
    invariato), applica (se abilitata) la calibrazione di lega, lancia la
    Monte Carlo a 10.000 iterazioni già presente in app.py
    (deps.run_simulation) e applica il Realistic Score Cap + la
    soppressione 0-0 specifica di lega. Ritorna il model calibrato (serve
    per un eventuale boost anti-0-0 di giornata) e gli array grezzi
    home/away, così il chiamante può ricalcolare solo i match che restano
    0-0 dopo il primo giro."""
    model, error = deps.try_build_match_model(league, home, away)
    if model is None:
        return None, error, None, None, []

    if calibration_enabled:
        adj_home, adj_away, multiplier = _apply_league_calibration(
            league, model.home_lambda, model.away_lambda, deps.clamp
        )
        model = dataclasses.replace(model, home_lambda=adj_home, away_lambda=adj_away)
    else:
        multiplier = 1.0

    simulation = deps.run_simulation(model, n_simulations=10_000)
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
    league: str, fixtures: list[tuple[str, str]], calibration_enabled: bool, deps: AppDependencies
) -> list[dict[str, object]]:
    """1) Simula tutte le fixture in un array temporaneo (`results`).
    2) Se calibrazione abilitata e gli 0-0 rivelati sono > MDS_ZERO_ZERO_
       MATCHDAY_CAP, esegue un ciclo while: ad ogni giro incrementa di
       MDS_ZERO_ZERO_BOOST_STEP l'xG (cumulativo) SOLO dei match ancora 0-0
       e li ri-simula da zero (nuova Monte Carlo a 10.000 iterazioni sul
       model boostato), finché il conteggio non scende a <= cap o si
       raggiunge il tetto di sicurezza MDS_ZERO_ZERO_MAX_BOOST_ROUNDS."""
    results: list[dict[str, object]] = []
    fixture_state: list[dict[str, object] | None] = []

    for home, away in fixtures:
        model, error, home_goals, away_goals, calib_notes = _simulate_fixture_raw(
            league, home, away, calibration_enabled, deps
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
            zero_zero_indices = [
                i for i, r in enumerate(results) if "error" not in r and r.get("score") == "0-0"
            ]
            if len(zero_zero_indices) <= MDS_ZERO_ZERO_MATCHDAY_CAP:
                break

            rounds += 1
            cumulative_boost += MDS_ZERO_ZERO_BOOST_STEP
            rng = np.random.default_rng()

            for i in zero_zero_indices:
                state = fixture_state[i]
                base_model = state["model"]
                boosted_home = deps.clamp(base_model.home_lambda + cumulative_boost, 0.1, MDS_LAMBDA_CEILING)
                boosted_away = deps.clamp(base_model.away_lambda + cumulative_boost, 0.1, MDS_LAMBDA_CEILING)
                boosted_model = dataclasses.replace(base_model, home_lambda=boosted_home, away_lambda=boosted_away)

                simulation = deps.run_simulation(boosted_model, n_simulations=10_000)
                home_goals = simulation["raw"]["home_goals"].copy()
                away_goals = simulation["raw"]["away_goals"].copy()
                _cap_extreme_scores(home_goals, away_goals)

                # Sicurezza aggiuntiva: se anche dopo il boost restasse uno
                # 0-0 residuo, lo condizioniamo comunque ad almeno un gol.
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
    """Hook da social mostrato nei primi MDS_HOOK_SECONDS secondi, prima
    della prima card: titolo pulsante + sottotitolo + barra che si riempie
    via CSS, pensato per essere il primo frame del video."""
    placeholder.markdown(
        f'<div class="mds-hook-wrap">'
        f'<div class="mds-hook-title">⚡ WAYNELAB AI ENGINE</div>'
        f'<div class="mds-hook-subtitle">Running 10,000 Monte Carlo Simulations...</div>'
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
    """Card 'Obsidian HUD': loghi grandi, risultato centrale bold ad
    altissimo contrasto, unica pill 1X2 in basso. Nessuna statistica o
    testo superfluo."""
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


def _render_matchday_summary(results: list[dict[str, object]]) -> None:
    """Banner di riepilogo finale: Total Goals, Avg Goals/Match e Home
    Wins %, calcolati sugli stessi punteggi rivelati nelle card — nessuna
    nuova fonte dati, solo un'aggregazione di quanto già simulato."""
    valid = [r for r in results if "error" not in r and "home_goals_total" in r]
    if not valid:
        return
    total_goals = sum(r["home_goals_total"] + r["away_goals_total"] for r in valid)
    avg_goals = total_goals / len(valid)
    home_wins = sum(1 for r in valid if r["home_goals_total"] > r["away_goals_total"])
    home_win_pct = (home_wins / len(valid)) * 100

    st.markdown(
        '<div class="mds-summary-wrap">'
        '<div class="mds-summary-title">📊 Matchday Summary</div>'
        '<div class="mds-summary-row">'
        f'<div class="mds-summary-badge"><div class="mds-summary-value">{total_goals}</div>'
        f'<div class="mds-summary-label">Total Goals</div></div>'
        f'<div class="mds-summary-badge"><div class="mds-summary-value">{avg_goals:.2f}</div>'
        f'<div class="mds-summary-label">Avg Goals</div></div>'
        f'<div class="mds-summary-badge"><div class="mds-summary-value">{home_win_pct:.0f}%</div>'
        f'<div class="mds-summary-label">Home Wins %</div></div>'
        "</div></div>",
        unsafe_allow_html=True,
    )


# ==============================================================================
# MAIN TAB ENTRY POINT
# ==============================================================================
def render_matchday_simulator_tab(app_module: Any = None) -> None:
    """Entry point chiamato da app.py (es. 'league_simulator.render_matchday_
    simulator_tab()' dentro la tab dedicata). Non importa app.py a livello
    di modulo: la dipendenza viene risolta qui dentro, al momento della
    chiamata, tramite _load_app_dependencies — questo è ciò che elimina il
    circular import. `app_module` è opzionale e serve solo per iniezione
    esplicita (test, o per evitare del tutto l'auto-import di app.py)."""
    deps = _load_app_dependencies(app_module)

    st.markdown(MATCHDAY_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="mds-header-title">🏆 MATCHDAY LIVE SIMULATOR</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "HUD Broadcast engine, built for TikTok/Reels/Shorts recordings (9:16) — one match revealed "
        "at a time. Same Poisson + Dixon-Coles Monte Carlo engine used everywhere else in WayneLab."
    )
    st.markdown(
        '<div class="mds-disclaimer">🎬 <b>Entertainment Calibration</b>: this tab applies '
        "discretionary per-league xG multipliers and score-shaping rules (goal cap, 0-0 exclusion "
        "for select leagues, max 2×0-0 per matchday via an xG boost loop) tuned for social-video "
        "pacing. These adjustments apply ONLY here — the Match Analysis, Value Betting and Monte "
        "Carlo Simulator tabs remain unaffected and are the app's actual statistical reference. Turn "
        "the toggle off below to see the unadjusted model.</div>",
        unsafe_allow_html=True,
    )

    calibration_enabled = st.toggle(
        "🎯 Enable Engagement Calibration (league xG multipliers, 0-0 cap, score cap)",
        value=True,
        key="mds_calibration_enabled",
    )

    col_league, col_matchday = st.columns(2)
    with col_league:
        league = st.selectbox(
            "Competition",
            options=list(deps.FOOTBALL_DATA_COMPETITIONS),
            key="mds_league_select",
        )

    matchdays = _available_matchdays(league, deps)
    with col_matchday:
        if matchdays:
            matchday = st.selectbox(
                "Matchday",
                options=matchdays,
                format_func=lambda n: f"Giornata {n}",
                key="mds_matchday_select",
            )
        else:
            st.warning("No live matchday data available for this competition.")
            return

    fixtures = _matchday_fixtures(league, matchday, deps)
    if not fixtures:
        st.info(f"No fixtures found for Giornata {matchday} in {league}.")
        return

    st.caption(f"📋 {len(fixtures)} fixtures loaded for Giornata {matchday}.")

    run_clicked = st.button("⚡ SIMULATE FULL MATCHDAY", type="primary", key="mds_run_button")

    try:
        crests = deps.fetch_team_crests(league)
    except deps.FootballDataError:
        crests = {}

    if run_clicked:
        # --------------------------------------------------------------------
        # RESET RIGIDO DELLO STATO (passaggio critico): cancella ESPLICITAMENTE
        # qualunque chiave di session_state riconducibile a questo modulo,
        # cosi la UI non mostra mai card o dati residui di una simulazione
        # precedente. NB: il filtro è basato su substring molto ampio
        # ("matchday" / "mds" / "results") e cancella quindi anche le chiavi
        # dei widget di questa tab (toggle/selectbox) — è voluto: garantisce
        # che l'intera sezione riparta da uno stato pulito ad ogni simulazione.
        # I valori già letti in questa run (calibration_enabled, league,
        # matchday) restano validi per l'esecuzione corrente.
        # --------------------------------------------------------------------
        for key in list(st.session_state.keys()):
            if "matchday" in key or "mds" in key or "results" in key:
                del st.session_state[key]

        # 1) Hook da social: primo frame ad alto impatto, ~2s prima della
        #    prima card (tempo reale, pensato per la registrazione).
        hook_placeholder = st.empty()
        _render_hook_banner(hook_placeholder)
        time.sleep(MDS_HOOK_SECONDS)
        hook_placeholder.empty()

        # 2) Simulazione completa della giornata con hard cap anti-0-0 a
        #    ciclo while (vedi _run_full_matchday).
        results = _run_full_matchday(league, fixtures, calibration_enabled, deps)

        # 3) Reveal sequenziale REALE: una card alla volta.
        cards_container = st.container()
        for index, outcome in enumerate(results):
            with cards_container:
                if "error" in outcome:
                    st.warning(f"{outcome['home']} vs {outcome['away']}: {outcome['error']}")
                else:
                    _render_match_card(outcome["home"], outcome["away"], outcome, crests)
            if index < len(results) - 1:
                time.sleep(MDS_CARD_REVEAL_DELAY_SECONDS)

        # 4) Banner di riepilogo finale.
        _render_matchday_summary(results)
        st.success(f"✅ Giornata {matchday} fully simulated — {len(fixtures)} matches.")
