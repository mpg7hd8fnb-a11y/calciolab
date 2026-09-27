"""
league_simulator.py — WayneLab · 🏆 Matchday Live Simulator
Modulo indipendente e puramente additivo: riusa esclusivamente le funzioni
e i modelli già presenti in app.py (build_match_model, run_simulation,
fetch_league_teams, fetch_league_matches, fetch_team_crests) — nessuna
nuova logica statistica di forecast, solo una nuova UI "broadcast" pensata
per la registrazione di contenuti social (TikTok/Reels/Shorts).

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

NOVITÀ DI QUESTA VERSIONE:
  • Hard Cap Anti-Zero-Zero a livello di GIORNATA (max 2 × 0-0 su 10 match,
    con re-roll a xG boostato per il 3° 0-0 in poi).
  • "Smooth Broadcast Engine": overlay di analisi ad alto impatto seguito da
    una reveal a cascata delle card (fade-in sequenziale via CSS, un solo
    ciclo di rendering — niente refresh a scatti per ogni singola partita).
  • Badge di sintesi giornata (Total Goals / Avg Goals per Match / Home
    Win %) in stile neon Electric Cyan.
"""

from __future__ import annotations

import dataclasses
import time
from html import escape

import numpy as np
import streamlit as st

from app import (
    FOOTBALL_DATA_COMPETITIONS,
    FootballDataError,
    clamp,
    fetch_league_matches,
    fetch_team_crests,
    run_simulation,
    try_build_match_model,
)

MATCHDAY_ACCENT = "#00E5FF"
MATCHDAY_BG = "#050505"


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
# Tetto di sicurezza sugli xG DOPO l'applicazione del moltiplicatore di lega,
# per evitare che un cumulo di fattori (slider manuali + moltiplicatore lega)
# produca lambda irrealistici in ingresso alla simulazione.

MDS_ZERO_ZERO_RESAMPLE_ATTEMPTS = 25
# Tentativi massimi di resampling per singola partita simulata quando si
# deve escludere lo 0-0: evita loop infiniti in casi limite (xG quasi a 0).

MDS_ZERO_ZERO_MATCHDAY_CAP = 2
# HARD CAP GIORNATA: al massimo questo numero di 0-0 può comparire come
# punteggio rivelato nell'intera giornata simulata (tipicamente 10 match).
# Dal (CAP + 1)-esimo 0-0 in poi, il match viene ri-simulato forzando almeno
# un gol (vedi MDS_ZERO_ZERO_CAP_BOOST_MULTIPLIER). Attivo solo quando la
# calibrazione è abilitata: è un vincolo di pacing per i video, non una
# correzione statistica.
MDS_ZERO_ZERO_CAP_BOOST_MULTIPLIER = 1.6
# Boost temporaneo di xG usato SOLO per il re-roll anti-cap (non altera il
# punteggio delle partite già assegnate né i lambda del modello originale).

MDS_ANALYZING_SECONDS = 2.4
# Durata dell'overlay "ANALYZING 10,000 MONTE CARLO SCENARIOS..." mostrato
# una sola volta all'avvio della giornata (non per singolo match): il calcolo
# vero e proprio delle 10 simulazioni avviene sotto, in un unico passaggio.

MDS_CARD_STAGGER_SECONDS = 0.35
# Ritardo (via CSS animation-delay) tra la comparsa di una card e la
# successiva nella reveal a cascata. Puramente visivo: tutte le card sono
# già calcolate e inviate al browser in un solo rendering.


def _apply_league_calibration(league: str, home_lambda: float, away_lambda: float) -> tuple[float, float, float]:
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
    """Anti-Zero-Zero: per ogni partita simulata che risulta 0-0, ri-esegue
    l'estrazione Poisson (xG passati in argomento) fino a ottenere almeno 1
    gol complessivo, con un numero massimo di tentativi per evitare loop
    infiniti su xG estremamente bassi. Statisticamente equivale a
    condizionare la Poisson bivariata all'evento 'almeno un gol', non a una
    riscrittura arbitraria del risultato."""
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
            # Xg troppo basso per escludere lo 0-0 in modo credibile entro i
            # tentativi previsti: forza il minimo risultato non-0-0 realistico.
            home_goals[index] = 1
            away_goals[index] = 0


def _empirical_score_and_outcomes(home_goals: np.ndarray, away_goals: np.ndarray) -> dict[str, object]:
    """Frequenze empiriche (post-calibrazione) del punteggio esatto più
    comune e delle probabilità 1X2, calcolate direttamente sugli stessi
    array Monte Carlo mostrati come risultato — così i badge 1X2 restano
    sempre coerenti col punteggio esatto rivelato in questo modulo."""
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


# ==============================================================================
# CSS — Obsidian / Electric Cyan Broadcast HUD (scoped, no clash with app.py)
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

/* ---- Smooth Broadcast Engine: analyzing overlay ---- */
.mds-analyzing-wrap {{
    background: {MATCHDAY_BG};
    border: 1px solid rgba(0,229,255,0.45);
    border-radius: 18px;
    padding: 26px 22px;
    margin-bottom: 16px;
    text-align: center;
    box-shadow: 0 10px 34px rgba(0,0,0,0.55), 0 0 30px rgba(0,229,255,0.14);
}}
.mds-analyzing-text {{
    font-family: "Courier New", monospace;
    font-size: 0.92rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 800;
    color: {MATCHDAY_ACCENT};
    text-shadow: 0 0 10px rgba(0,229,255,0.7);
    margin-bottom: 14px;
    animation: mdsPulse 1.1s ease-in-out infinite;
}}
.mds-analyzing-track {{
    width: 100%;
    height: 8px;
    border-radius: 999px;
    background: rgba(255,255,255,0.08);
    overflow: hidden;
}}
.mds-analyzing-fill {{
    height: 100%;
    width: 0%;
    border-radius: 999px;
    background: linear-gradient(90deg, {MATCHDAY_ACCENT}, #00ff87);
    box-shadow: 0 0 14px rgba(0,229,255,0.85);
    animation: mdsFill {MDS_ANALYZING_SECONDS}s cubic-bezier(0.22, 0.61, 0.36, 1) forwards;
}}
@keyframes mdsFill {{
    from {{ width: 0%; }}
    to {{ width: 100%; }}
}}
@keyframes mdsPulse {{
    0%, 100% {{ opacity: 0.55; }}
    50% {{ opacity: 1; }}
}}

/* ---- Matchday summary badge ---- */
.mds-summary-row {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: center;
    margin-bottom: 16px;
}}
.mds-summary-badge {{
    flex: 1;
    min-width: 130px;
    background: linear-gradient(165deg, #101010 0%, #050505 100%);
    border: 1px solid rgba(0,229,255,0.5);
    border-radius: 14px;
    padding: 10px 12px;
    text-align: center;
    box-shadow: 0 0 16px rgba(0,229,255,0.14), 0 6px 16px rgba(0,0,0,0.5);
}}
.mds-summary-value {{
    font-family: "Courier New", monospace;
    font-size: 1.4rem;
    font-weight: 900;
    color: {MATCHDAY_ACCENT};
    text-shadow: 0 0 10px rgba(0,229,255,0.6);
    line-height: 1.1;
}}
.mds-summary-label {{
    font-size: 0.66rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #9aa0a6;
    margin-top: 2px;
}}

/* ---- Match card, with cascade fade-in ---- */
.mds-card {{
    position: relative;
    background: linear-gradient(165deg, #101010 0%, #050505 100%);
    border: 1px solid {MATCHDAY_ACCENT};
    border-radius: 18px;
    padding: 18px 14px 16px 14px;
    margin-bottom: 14px;
    box-shadow: 0 0 20px rgba(0,229,255,0.15), 0 8px 22px rgba(0,0,0,0.5);
    text-align: center;
    opacity: 0;
    animation: mdsCardIn 0.55s ease forwards;
    animation-delay: var(--mds-delay, 0s);
}}
@keyframes mdsCardIn {{
    from {{ opacity: 0; transform: translateY(16px) scale(0.985); }}
    to {{ opacity: 1; transform: translateY(0) scale(1); }}
}}
.mds-calib-tag {{
    position: absolute;
    top: 10px;
    right: 12px;
    font-family: "Courier New", monospace;
    font-size: 0.6rem;
    letter-spacing: 0.03em;
    color: {MATCHDAY_ACCENT};
    opacity: 0.75;
}}
.mds-card-teams {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 14px;
}}
.mds-team {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    min-width: 0;
}}
.mds-crest {{
    width: 46px;
    height: 46px;
    object-fit: contain;
}}
.mds-crest-placeholder {{
    width: 46px;
    height: 46px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    opacity: 0.6;
}}
.mds-team-name {{
    font-weight: 800;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    color: #e0e0e0;
    text-align: center;
    overflow-wrap: break-word;
    line-height: 1.2;
    min-height: 2.1em;
}}
.mds-vs {{
    font-weight: 900;
    font-size: 0.8rem;
    color: {MATCHDAY_ACCENT};
    text-shadow: 0 0 8px rgba(0,229,255,0.6);
}}
.mds-score {{
    font-size: 2.6rem;
    font-weight: 900;
    letter-spacing: 0.05em;
    font-variant-numeric: tabular-nums;
    background: linear-gradient(135deg, {MATCHDAY_ACCENT}, #e0e0e0);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin: 12px 0 8px 0;
    line-height: 1;
}}
.mds-outcome-row {{
    display: flex;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
}}
.mds-outcome-badge {{
    font-family: "Courier New", monospace;
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid rgba(0,229,255,0.4);
    background: rgba(0,229,255,0.08);
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
</style>
"""


# ==============================================================================
# DATA HELPERS — pure grouping/reading, no new statistical logic
# ==============================================================================
def _available_matchdays(league: str) -> list[int]:
    """Legge il campo 'matchday' già restituito da Football-Data.org per
    ogni fixture (fetch_league_matches, invariata) e ne estrae l'elenco
    ordinato dei numeri di giornata disponibili per la competizione."""
    try:
        matches = fetch_league_matches(league)
    except FootballDataError:
        return []
    matchdays = sorted(
        {int(match["matchday"]) for match in matches if isinstance(match.get("matchday"), int)}
    )
    return matchdays


def _matchday_fixtures(league: str, matchday: int) -> list[tuple[str, str]]:
    """Elenco (home, away) delle fixture della giornata selezionata,
    filtrando le partite già recuperate da fetch_league_matches per il
    campo 'matchday' — nessuna nuova chiamata API, nessun nuovo modello."""
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
        home_name = home_team.get("name")
        away_name = away_team.get("name")
        if isinstance(home_name, str) and isinstance(away_name, str):
            fixtures.append((home_name, away_name))
    return fixtures


# ==============================================================================
# SIMULATION — per-fixture Monte Carlo + matchday-wide anti-zero-zero cap
# ==============================================================================
def _simulate_one_fixture(
    league: str,
    home: str,
    away: str,
    calibration_enabled: bool,
    enforce_zero_zero_cap: bool = False,
) -> dict[str, object] | None:
    """Costruisce il MatchModel esistente (try_build_match_model, invariato)
    e lancia la Monte Carlo a 10.000 iterazioni già presente in app.py
    (run_simulation). Se `calibration_enabled`, applica PRIMA della
    simulazione il moltiplicatore di xG di lega (con tetto di sicurezza) e,
    DOPO la simulazione, il Realistic Score Cap e — per le leghe
    configurate — l'esclusione dello 0-0 tramite resampling Poisson
    condizionato.

    Se `enforce_zero_zero_cap` è True (perché il MDS_ZERO_ZERO_MATCHDAY_CAP
    è già stato raggiunto in questa giornata) e il punteggio rivelato è
    comunque 0-0, esegue un ulteriore re-roll con xG boostato
    (MDS_ZERO_ZERO_CAP_BOOST_MULTIPLIER) per forzare almeno un gol — questo
    è un vincolo di pacing per la giornata nel suo complesso, non una
    correzione statistica sul singolo match.

    Le probabilità 1X2 mostrate sono sempre ricalcolate sugli stessi
    identici array usati per il punteggio rivelato, così badge e risultato
    restano coerenti fra loro."""
    model, error = try_build_match_model(league, home, away)
    if model is None:
        return {"error": error}

    if calibration_enabled:
        adj_home, adj_away, multiplier = _apply_league_calibration(league, model.home_lambda, model.away_lambda)
        model = dataclasses.replace(model, home_lambda=adj_home, away_lambda=adj_away)
    else:
        multiplier = 1.0

    simulation = run_simulation(model, n_simulations=10_000)
    home_goals = simulation["raw"]["home_goals"].copy()
    away_goals = simulation["raw"]["away_goals"].copy()

    calib_notes: list[str] = []
    rng = np.random.default_rng()

    if calibration_enabled:
        if multiplier != 1.0:
            calib_notes.append(f"×{multiplier:.2f} xG")
        if league in LEAGUE_ZERO_ZERO_SUPPRESSED:
            _suppress_zero_zero(rng, home_goals, away_goals, model.home_lambda, model.away_lambda)
            calib_notes.append("No 0-0")
        _cap_extreme_scores(home_goals, away_goals)
        calib_notes.append(f"Cap {MDS_MAX_GOALS_PER_TEAM}")

    outcome = _empirical_score_and_outcomes(home_goals, away_goals)

    if calibration_enabled and enforce_zero_zero_cap and outcome["score"] == "0-0":
        boosted_home = clamp(model.home_lambda * MDS_ZERO_ZERO_CAP_BOOST_MULTIPLIER, 0.1, MDS_LAMBDA_CEILING)
        boosted_away = clamp(model.away_lambda * MDS_ZERO_ZERO_CAP_BOOST_MULTIPLIER, 0.1, MDS_LAMBDA_CEILING)
        _suppress_zero_zero(rng, home_goals, away_goals, boosted_home, boosted_away)
        _cap_extreme_scores(home_goals, away_goals)
        outcome = _empirical_score_and_outcomes(home_goals, away_goals)
        calib_notes.append(f"0-0 cap ({MDS_ZERO_ZERO_MATCHDAY_CAP}/giornata)")

    outcome["calib_tag"] = "⚙️ " + " · ".join(calib_notes) if calib_notes else ""
    return outcome


def _run_full_matchday(
    league: str, fixtures: list[tuple[str, str]], calibration_enabled: bool
) -> list[dict[str, object]]:
    """Simula tutte le fixture della giornata in sequenza, applicando il
    MDS_ZERO_ZERO_MATCHDAY_CAP: i primi MDS_ZERO_ZERO_MATCHDAY_CAP punteggi
    0-0 rivelati sono ammessi normalmente; dal successivo in poi, il match
    viene ri-simulato con xG boostato per forzare almeno un gol. Nessun
    time.sleep qui: il calcolo avviene in un unico blocco, la messa in scena
    (overlay + reveal a cascata) è gestita separatamente in UI."""
    results: list[dict[str, object]] = []
    zero_zero_count = 0
    for home, away in fixtures:
        enforce_cap = zero_zero_count >= MDS_ZERO_ZERO_MATCHDAY_CAP
        outcome = _simulate_one_fixture(league, home, away, calibration_enabled, enforce_cap)
        if outcome is not None and "error" not in outcome and outcome.get("score") == "0-0":
            zero_zero_count += 1
        results.append({"home": home, "away": away, **(outcome or {})})
    return results


# ==============================================================================
# RENDERING — Smooth Broadcast Engine (analyzing overlay + cascade reveal)
# ==============================================================================
def _render_analyzing_overlay(placeholder) -> None:
    """Overlay unico ad alto impatto visivo mostrato UNA volta per l'intera
    giornata (non per singolo match): barra che si riempie via CSS in
    MDS_ANALYZING_SECONDS, nessun refresh Streamlit intermedio."""
    placeholder.markdown(
        f'<div class="mds-analyzing-wrap">'
        f'<div class="mds-analyzing-text">⚡ ANALYZING 10,000 MONTE CARLO SCENARIOS...</div>'
        f'<div class="mds-analyzing-track"><div class="mds-analyzing-fill"></div></div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_matchday_summary(results: list[dict[str, object]]) -> None:
    """Badge di sintesi giornata (Total Goals / Avg Goals per Match / Home
    Win %), calcolato sugli stessi punteggi rivelati nelle card — nessuna
    nuova fonte dati, solo un'aggregazione di quanto già simulato."""
    valid = [r for r in results if "error" not in r and "home_goals_total" in r]
    if not valid:
        return
    total_goals = sum(r["home_goals_total"] + r["away_goals_total"] for r in valid)
    avg_goals = total_goals / len(valid)
    home_wins = sum(1 for r in valid if r["home_goals_total"] > r["away_goals_total"])
    home_win_pct = (home_wins / len(valid)) * 100

    st.markdown(
        '<div class="mds-summary-row">'
        f'<div class="mds-summary-badge"><div class="mds-summary-value">{total_goals}</div>'
        f'<div class="mds-summary-label">Total Goals</div></div>'
        f'<div class="mds-summary-badge"><div class="mds-summary-value">{avg_goals:.2f}</div>'
        f'<div class="mds-summary-label">Avg Goals / Match</div></div>'
        f'<div class="mds-summary-badge"><div class="mds-summary-value">{home_win_pct:.0f}%</div>'
        f'<div class="mds-summary-label">Home Wins</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )


def _crest_html(name: str, crests: dict[str, str]) -> str:
    url = crests.get(name)
    if url:
        return f'<img src="{escape(url)}" class="mds-crest" />'
    return '<div class="mds-crest-placeholder">🛡️</div>'


def _outcome_pill_label(home_prob: float, draw_prob: float, away_prob: float) -> tuple[str, float]:
    """Riduce le 3 probabilità 1X2 a un'unica pill 'esito più probabile'
    (es. 'HOME WIN · 64%'), per una card più minimal/social-friendly."""
    best_label, best_prob = max(
        [("HOME WIN", home_prob), ("DRAW", draw_prob), ("AWAY WIN", away_prob)],
        key=lambda pair: pair[1],
    )
    return best_label, best_prob


def _render_match_card(
    home: str,
    away: str,
    score_label: str,
    home_prob: float,
    draw_prob: float,
    away_prob: float,
    crests: dict[str, str],
    calib_tag: str = "",
    delay_seconds: float = 0.0,
) -> None:
    calib_html = f'<div class="mds-calib-tag">{escape(calib_tag)}</div>' if calib_tag else ""
    best_label, best_prob = _outcome_pill_label(home_prob, draw_prob, away_prob)
    st.markdown(
        f'<div class="mds-card" style="--mds-delay:{delay_seconds:.2f}s">'
        f"{calib_html}"
        f'<div class="mds-card-teams">'
        f'<div class="mds-team">{_crest_html(home, crests)}'
        f'<div class="mds-team-name">{escape(home)}</div></div>'
        f'<div class="mds-vs">VS</div>'
        f'<div class="mds-team">{_crest_html(away, crests)}'
        f'<div class="mds-team-name">{escape(away)}</div></div>'
        f"</div>"
        f'<div class="mds-score">{escape(score_label)}</div>'
        f'<div class="mds-outcome-row">'
        f'<span class="mds-outcome-badge">{best_label} · {best_prob:.0%}</span>'
        f'<span class="mds-outcome-badge">1 · {home_prob:.0%}</span>'
        f'<span class="mds-outcome-badge">X · {draw_prob:.0%}</span>'
        f'<span class="mds-outcome-badge">2 · {away_prob:.0%}</span>'
        f"</div></div>",
        unsafe_allow_html=True,
    )


def _render_cards_cascade(results: list[dict[str, object]], crests: dict[str, str]) -> None:
    """Rendering in un solo passaggio di tutte le card, ciascuna con un
    animation-delay CSS crescente: il browser esegue la reveal a cascata
    (fade-in + slide-up) senza che Streamlit debba ridisegnare la pagina
    partita per partita."""
    for index, outcome in enumerate(results):
        if "error" in outcome:
            st.warning(f"{outcome['home']} vs {outcome['away']}: {outcome['error']}")
            continue
        _render_match_card(
            outcome["home"],
            outcome["away"],
            outcome["score"],
            outcome["home_prob"],
            outcome["draw_prob"],
            outcome["away_prob"],
            crests,
            outcome.get("calib_tag", ""),
            delay_seconds=index * MDS_CARD_STAGGER_SECONDS,
        )


# ==============================================================================
# MAIN TAB ENTRY POINT
# ==============================================================================
def render_matchday_simulator_tab() -> None:
    st.markdown(MATCHDAY_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="mds-header-title">🏆 MATCHDAY LIVE SIMULATOR</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Simulate an entire matchday in one smooth broadcast sequence — built for TikTok/Reels/Shorts "
        "recordings. Same Poisson + Dixon-Coles Monte Carlo engine used everywhere else in WayneLab."
    )
    st.markdown(
        '<div class="mds-disclaimer">🎬 <b>Entertainment Calibration</b>: this tab applies '
        "discretionary per-league xG multipliers and score-shaping rules (goal cap, 0-0 exclusion "
        "for select leagues, max 2×0-0 per matchday) tuned for social-video pacing. These adjustments "
        "apply ONLY here — the Match Analysis, Value Betting and Monte Carlo Simulator tabs remain "
        "unaffected and are the app's actual statistical reference. Turn the toggle off below to see "
        "the unadjusted model.</div>",
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
            options=list(FOOTBALL_DATA_COMPETITIONS),
            key="mds_league_select",
        )

    matchdays = _available_matchdays(league)
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

    fixtures = _matchday_fixtures(league, matchday)
    if not fixtures:
        st.info(f"No fixtures found for Giornata {matchday} in {league}.")
        return

    st.caption(f"📋 {len(fixtures)} fixtures loaded for Giornata {matchday}.")

    if st.session_state.get("_mds_context") != (league, matchday, calibration_enabled):
        st.session_state["_mds_context"] = (league, matchday, calibration_enabled)
        st.session_state.pop("mds_results", None)

    run_clicked = st.button("⚡ SIMULATE FULL MATCHDAY", type="primary", key="mds_run_button")

    try:
        crests = fetch_team_crests(league)
    except FootballDataError:
        crests = {}

    if run_clicked:
        # 1) Overlay unico ad alto impatto ("Smooth Broadcast Engine"),
        #    nessun refresh a scatti per singolo match.
        analyzing_placeholder = st.empty()
        _render_analyzing_overlay(analyzing_placeholder)
        time.sleep(MDS_ANALYZING_SECONDS)
        analyzing_placeholder.empty()

        # 2) Calcolo di tutta la giornata in un solo blocco (con hard cap
        #    anti-0-0 applicato in sequenza sulle fixture).
        results = _run_full_matchday(league, fixtures, calibration_enabled)
        st.session_state["mds_results"] = results

        # 3) Reveal: badge di sintesi + card a cascata, un solo rendering.
        _render_matchday_summary(results)
        _render_cards_cascade(results, crests)

        st.success(f"✅ Giornata {matchday} fully simulated — {len(fixtures)} matches.")
        return

    # Rendering persistente dei risultati già simulati (senza dover ricliccare)
    if "mds_results" in st.session_state:
        results = st.session_state["mds_results"]
        _render_matchday_summary(results)
        _render_cards_cascade(results, crests)
    else:
        st.info("Press '⚡ SIMULATE FULL MATCHDAY' to start the sequence.")
