"""
league_simulator.py — WayneLab · 🏆 Matchday Live Simulator
Modulo indipendente e puramente additivo: riusa esclusivamente le funzioni
e i modelli già presenti in app.py (build_match_model, run_simulation,
fetch_league_teams, fetch_league_matches, fetch_team_crests) — nessuna
nuova logica statistica di forecast, solo una nuova UI "broadcast" pensata
per la registrazione di contenuti social (TikTok/Reels/Shorts).

⚠️ ENTERTAINMENT CALIBRATION LAYER
Questo modulo applica, SOLO al proprio interno, moltiplicatori di xG per
lega, un tetto sui punteggi estremi e un vincolo RIGIDO sulla frequenza
degli 0-0 nell'arco di una giornata (max 2 su 10) — pensati per il pacing
dei video social. Questi aggiustamenti NON toccano il motore Poisson/
Dixon-Coles usato dalle altre tab (Match Analysis, Value Betting, Monte
Carlo Simulator, Multi-Outcome): quelle restano il riferimento analitico
dell'app, invariate.
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

MDS_MAX_GOALS_PER_TEAM = 4
# Realistic Score Cap: nessuna squadra può segnare più di questo numero di
# gol nel risultato mostrato — i risultati "tennistici" (5-1, 6-2...) vengono
# troncati a questo tetto invece di essere mostrati as-is.

MDS_LAMBDA_CEILING = 3.5
# Tetto di sicurezza sugli xG DOPO l'applicazione del moltiplicatore di lega
# (e di un eventuale boost anti-0-0), per evitare lambda irrealistici.

MATCHDAY_ZERO_ZERO_HARD_CAP = 2
# BLOCCO MATEMATICO RIGIDO: al massimo questo numero di 0-0 può comparire
# nella lista FINALE dei 10 risultati di una giornata. Applicato DOPO aver
# simulato l'intera giornata in memoria (vedi _enforce_matchday_zero_zero_cap).

MDS_ZERO_ZERO_REROLL_BOOST = 0.50
# Incremento xG assoluto (sommato a home_lambda/away_lambda già calibrati)
# applicato ad ogni iterazione del ciclo while per i match 0-0 in eccesso.

MDS_ZERO_ZERO_MAX_ITERATIONS = 10
# Numero massimo di iterazioni del ciclo while prima di ricorrere al
# fallback deterministico per i match ancora bloccati su 0-0.


# ==============================================================================
# SIMULATION CORE — single fixture, plus whole-matchday hard enforcement
# ==============================================================================
def _simulate_fixture_raw(
    league: str, home: str, away: str, calibration_enabled: bool, extra_xg_boost: float = 0.0
) -> dict[str, object]:
    """Simula UNA fixture con il MatchModel/Monte Carlo esistenti
    (build_match_model / run_simulation, invariati in app.py). Se
    `calibration_enabled`, applica il moltiplicatore di lega più un
    eventuale `extra_xg_boost` assoluto (usato dal ciclo while anti-0-0),
    con tetto di sicurezza MDS_LAMBDA_CEILING, e il Realistic Score Cap sui
    gol simulati. Ritorna un dict con score/goals/probabilità 1X2 calcolate
    sugli stessi identici array Monte Carlo del punteggio rivelato."""
    model, error = try_build_match_model(league, home, away)
    if model is None:
        return {"home": home, "away": away, "error": error}

    multiplier_used = 1.0
    if calibration_enabled:
        base_multiplier = LEAGUE_GOAL_MULTIPLIERS.get(league, LEAGUE_GOAL_MULTIPLIER_DEFAULT)
        adj_home = clamp(model.home_lambda * base_multiplier + extra_xg_boost, 0.1, MDS_LAMBDA_CEILING)
        adj_away = clamp(model.away_lambda * base_multiplier + extra_xg_boost, 0.1, MDS_LAMBDA_CEILING)
        model = dataclasses.replace(model, home_lambda=adj_home, away_lambda=adj_away)
        multiplier_used = base_multiplier

    simulation = run_simulation(model, n_simulations=10_000)
    home_goals = simulation["raw"]["home_goals"].copy()
    away_goals = simulation["raw"]["away_goals"].copy()

    if calibration_enabled:
        np.clip(home_goals, 0, MDS_MAX_GOALS_PER_TEAM, out=home_goals)
        np.clip(away_goals, 0, MDS_MAX_GOALS_PER_TEAM, out=away_goals)

    n = len(home_goals)
    pairs, counts = np.unique(np.stack([home_goals, away_goals], axis=1), axis=0, return_counts=True)
    top_home, top_away = pairs[int(np.argmax(counts))]
    home_wins = float((home_goals > away_goals).sum())
    draws = float((home_goals == away_goals).sum())
    away_wins = float((home_goals < away_goals).sum())

    calib_notes: list[str] = []
    if calibration_enabled:
        if multiplier_used != 1.0:
            calib_notes.append(f"×{multiplier_used:.2f} xG")
        if extra_xg_boost > 0:
            calib_notes.append(f"Anti-0-0 +{extra_xg_boost:.2f}")
        calib_notes.append(f"Cap {MDS_MAX_GOALS_PER_TEAM}")

    return {
        "home": home,
        "away": away,
        "score": f"{int(top_home)}-{int(top_away)}",
        "home_goals": int(top_home),
        "away_goals": int(top_away),
        "home_prob": home_wins / n,
        "draw_prob": draws / n,
        "away_prob": away_wins / n,
        "calib_tag": "⚙️ " + " · ".join(calib_notes) if calib_notes else "",
    }


def _is_zero_zero(result: dict[str, object]) -> bool:
    return "error" not in result and result.get("home_goals") == 0 and result.get("away_goals") == 0


def _enforce_matchday_zero_zero_cap(
    league: str, fixtures: list[tuple[str, str]], results: list[dict[str, object]], calibration_enabled: bool
) -> list[dict[str, object]]:
    """BLOCCO MATEMATICO RIGIDO: conta quanti dei 10 risultati già simulati
    in memoria sono finiti 0-0. Se il conteggio è MAGGIORE DI
    MATCHDAY_ZERO_ZERO_HARD_CAP, un ciclo `while` ricalcola automaticamente
    SOLO i match ancora in eccedenza (oltre il tetto) applicando un
    incremento di xG di +MDS_ZERO_ZERO_REROLL_BOOST alle due squadre ad
    ogni iterazione, finché il totale di 0-0 della giornata non scende a
    <= MATCHDAY_ZERO_ZERO_HARD_CAP. Solo a quel punto la lista è considerata
    definitiva. Un fallback deterministico (1-0) protegge da loop infiniti
    nel caso limite di xG di partenza estremamente bassi."""
    if not calibration_enabled:
        return results

    boost = 0.0
    iterations = 0
    zero_zero_indices = [i for i, r in enumerate(results) if _is_zero_zero(r)]

    while len(zero_zero_indices) > MATCHDAY_ZERO_ZERO_HARD_CAP and iterations < MDS_ZERO_ZERO_MAX_ITERATIONS:
        boost += MDS_ZERO_ZERO_REROLL_BOOST
        iterations += 1
        # I primi MATCHDAY_ZERO_ZERO_HARD_CAP 0-0 restano ammessi così
        # come sono; solo l'ECCEDENZA viene ricalcolata con xG potenziati.
        indices_to_reroll = zero_zero_indices[MATCHDAY_ZERO_ZERO_HARD_CAP:]
        for index in indices_to_reroll:
            home, away = fixtures[index]
            results[index] = _simulate_fixture_raw(league, home, away, calibration_enabled, extra_xg_boost=boost)
        zero_zero_indices = [i for i, r in enumerate(results) if _is_zero_zero(r)]

    # Safety net finale: se dopo tutte le iterazioni resta ancora
    # un'eccedenza (xG di partenza estremamente bassi), forza un fallback
    # deterministico realistico invece di violare il tetto rigido.
    for index in zero_zero_indices[MATCHDAY_ZERO_ZERO_HARD_CAP:]:
        home, away = fixtures[index]
        results[index] = {
            "home": home,
            "away": away,
            "score": "1-0",
            "home_goals": 1,
            "away_goals": 0,
            "home_prob": 0.55,
            "draw_prob": 0.20,
            "away_prob": 0.25,
            "calib_tag": "⚙️ Anti-0-0 Forced Result",
        }

    return results


def simulate_full_matchday(
    league: str, fixtures: list[tuple[str, str]], calibration_enabled: bool
) -> list[dict[str, object]]:
    """Simula TUTTE le fixture della giornata IN UN UNICO BLOCCO in memoria
    (lista temporanea, nessun rendering intermedio), poi applica il blocco
    matematico rigido sul tetto di 0-0 sull'intera lista già completa.
    Ritorna la lista finale, già validata, pronta per essere salvata in
    st.session_state e rivelata a cascata."""
    results = [_simulate_fixture_raw(league, home, away, calibration_enabled) for home, away in fixtures]
    results = _enforce_matchday_zero_zero_cap(league, fixtures, results, calibration_enabled)
    return results


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
# CSS — Obsidian / Electric Cyan Broadcast HUD (inline, scoped)
# ==============================================================================
MATCHDAY_CSS = f"""
<style>
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
.mds-summary-strip {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    justify-content: center;
    background: {MATCHDAY_BG};
    border: 1px solid rgba(0,229,255,0.35);
    border-radius: 16px;
    padding: 16px 14px;
    margin-bottom: 18px;
    box-shadow: 0 0 24px rgba(0,229,255,0.15), 0 8px 22px rgba(0,0,0,0.5);
}}
.mds-summary-item {{
    flex: 1;
    min-width: 120px;
    text-align: center;
}}
.mds-summary-label {{
    font-family: "Courier New", monospace;
    font-size: 0.62rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9aa0a6;
    margin-bottom: 4px;
}}
.mds-summary-value {{
    font-size: 1.7rem;
    font-weight: 900;
    font-variant-numeric: tabular-nums;
    background: linear-gradient(135deg, {MATCHDAY_ACCENT}, #00ff87);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    line-height: 1;
}}
.mds-card {{
    position: relative;
    background: linear-gradient(165deg, #101010 0%, #050505 100%);
    border: 1px solid {MATCHDAY_ACCENT};
    border-radius: 18px;
    padding: 18px 14px 16px 14px;
    margin-bottom: 14px;
    box-shadow: 0 0 20px rgba(0,229,255,0.15), 0 8px 22px rgba(0,0,0,0.5);
    text-align: center;
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
.mds-outcome-pill {{
    display: inline-block;
    font-family: "Courier New", monospace;
    font-size: 0.75rem;
    font-weight: 900;
    letter-spacing: 0.04em;
    padding: 6px 16px;
    border-radius: 999px;
    text-transform: uppercase;
}}
.mds-outcome-pill-home {{
    background: rgba(0,255,135,0.14);
    border: 1px solid rgba(0,255,135,0.55);
    color: #00ff87;
}}
.mds-outcome-pill-draw {{
    background: rgba(255,214,10,0.14);
    border: 1px solid rgba(255,214,10,0.55);
    color: #ffd60a;
}}
.mds-outcome-pill-away {{
    background: rgba(255,46,99,0.14);
    border: 1px solid rgba(255,46,99,0.55);
    color: #ff2e63;
}}
.mds-outcome-sub {{
    margin-top: 6px;
    font-family: "Courier New", monospace;
    font-size: 0.65rem;
    color: #9aa0a6;
    letter-spacing: 0.03em;
}}
</style>
"""


# ==============================================================================
# RENDERING — cards + summary strip (pure HTML string builders)
# ==============================================================================
def _crest_html(name: str, crests: dict[str, str]) -> str:
    url = crests.get(name)
    if url:
        return f'<img src="{escape(url)}" class="mds-crest" />'
    return '<div class="mds-crest-placeholder">🛡️</div>'


def _outcome_pill_html(home_prob: float, draw_prob: float, away_prob: float) -> str:
    """Pill unico con l'esito 1X2 dominante (es. 'HOME WIN · 64%'), con le
    tre probabilità in piccolo sotto — HUD minimal, nessuna statistica di
    giocatori o di squadra."""
    best_kind = max(
        [("home", home_prob), ("draw", draw_prob), ("away", away_prob)],
        key=lambda item: item[1],
    )[0]
    if best_kind == "home":
        text, css_class = f"HOME WIN · {home_prob:.0%}", "mds-outcome-pill-home"
    elif best_kind == "away":
        text, css_class = f"AWAY WIN · {away_prob:.0%}", "mds-outcome-pill-away"
    else:
        text, css_class = f"DRAW · {draw_prob:.0%}", "mds-outcome-pill-draw"
    sub = f"1 · {home_prob:.0%}  X · {draw_prob:.0%}  2 · {away_prob:.0%}"
    return (
        f'<span class="mds-outcome-pill {css_class}">{escape(text)}</span>'
        f'<div class="mds-outcome-sub">{escape(sub)}</div>'
    )


def _build_card_html(result: dict[str, object], crests: dict[str, str]) -> str:
    if "error" in result:
        return (
            '<div class="mds-card">'
            f'<div class="mds-team-name">⚠️ {escape(str(result["home"]))} vs {escape(str(result["away"]))}</div>'
            f'<div class="mds-outcome-sub">{escape(str(result.get("error", "unavailable")))}</div>'
            "</div>"
        )
    calib_tag = result.get("calib_tag", "")
    calib_html = f'<div class="mds-calib-tag">{escape(str(calib_tag))}</div>' if calib_tag else ""
    return (
        '<div class="mds-card">'
        f"{calib_html}"
        '<div class="mds-card-teams">'
        f'<div class="mds-team">{_crest_html(str(result["home"]), crests)}'
        f'<div class="mds-team-name">{escape(str(result["home"]))}</div></div>'
        '<div class="mds-vs">VS</div>'
        f'<div class="mds-team">{_crest_html(str(result["away"]), crests)}'
        f'<div class="mds-team-name">{escape(str(result["away"]))}</div></div>'
        "</div>"
        f'<div class="mds-score">{escape(str(result["score"]))}</div>'
        f'{_outcome_pill_html(result["home_prob"], result["draw_prob"], result["away_prob"])}'
        "</div>"
    )


def _summary_strip_html(results: list[dict[str, object]]) -> str:
    """Barra di sintesi giornata: TOTAL GOALS, HOME WINS, AVG GOALS, più il
    conteggio 0-0 (per verificare a colpo d'occhio il rispetto del tetto),
    calcolati sui punteggi effettivamente presenti nella lista finale."""
    valid = [r for r in results if "error" not in r]
    if not valid:
        return ""
    total_goals = sum(int(r["home_goals"]) + int(r["away_goals"]) for r in valid)
    avg_goals = total_goals / len(valid)
    home_win_count = sum(1 for r in valid if int(r["home_goals"]) > int(r["away_goals"]))
    home_win_pct = home_win_count / len(valid) * 100
    zero_zero_count = sum(1 for r in valid if int(r["home_goals"]) == 0 and int(r["away_goals"]) == 0)

    items = [
        ("Total Goals", f"{total_goals}"),
        ("Avg Goals / Match", f"{avg_goals:.2f}"),
        ("Home Wins %", f"{home_win_pct:.0f}%"),
        ("0-0 Results", f"{zero_zero_count} / {MATCHDAY_ZERO_ZERO_HARD_CAP} max"),
    ]
    items_html = "".join(
        f'<div class="mds-summary-item"><div class="mds-summary-label">{escape(label)}</div>'
        f'<div class="mds-summary-value">{escape(value)}</div></div>'
        for label, value in items
    )
    return f'<div class="mds-summary-strip">{items_html}</div>'


# ==============================================================================
# MAIN TAB ENTRY POINT
# ==============================================================================
def render_matchday_simulator_tab() -> None:
    st.markdown(MATCHDAY_CSS, unsafe_allow_html=True)
    st.markdown('<div class="mds-header-title">🏆 MATCHDAY LIVE SIMULATOR</div>', unsafe_allow_html=True)
    st.caption(
        "Simulate an entire matchday, revealed one match at a time — built for TikTok/Reels/Shorts "
        "recordings. Same Poisson + Dixon-Coles Monte Carlo engine used elsewhere in WayneLab."
    )
    st.markdown(
        '<div class="mds-disclaimer">🎬 <b>Entertainment Calibration</b>: this tab applies '
        "discretionary per-league xG multipliers, a realistic score cap, and a HARD cap of "
        f"{MATCHDAY_ZERO_ZERO_HARD_CAP} 0-0 results per matchday — the full matchday is simulated in "
        "memory first, then any 0-0 beyond the cap is force-recalculated with boosted xG before anything "
        "is shown on screen. These adjustments apply ONLY here — Match Analysis, Value Betting and Monte "
        "Carlo Simulator remain the app's unaffected statistical reference. Toggle off below to see the "
        "unadjusted model.</div>",
        unsafe_allow_html=True,
    )

    calibration_enabled = st.toggle(
        "🎯 Enable Engagement Calibration (league xG multipliers, 0-0 hard cap, score cap)",
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

    if st.session_state.get("_mds_context") != (league, matchday, calibration_enabled):
        st.session_state["_mds_context"] = (league, matchday, calibration_enabled)
        st.session_state.pop("matchday_results", None)

    run_clicked = st.button("⚡ SIMULATE FULL MATCHDAY", type="primary", key="mds_run_button")

    try:
        crests = fetch_team_crests(league)
    except FootballDataError:
        crests = {}

    main_container = st.empty()

    if run_clicked:
        # --- FASE 1: HUD di attesa (~2.5s), nessun risultato ancora mostrato -
        with st.spinner("⚡ GENERATING MONTE CARLO SIMULATION (10,000 RUNS)..."):
            time.sleep(2.5)

        # --- FASE 2: simulazione dell'INTERA giornata in un'unica lista in
        # memoria, seguita dal blocco matematico rigido sul tetto di 0-0
        # applicato sull'intera lista già completa. ------------------------
        results = simulate_full_matchday(league, fixtures, calibration_enabled)
        st.session_state["matchday_results"] = results

        # --- FASE 3: reveal a cascata, un match alla volta, aggiornando lo
        # stesso contenitore dinamico (main_container) — nessun refresh
        # pagina, vero effetto comparsa/dissolvenza sequenziale. -----------
        summary_html = _summary_strip_html(results)
        cards_html: list[str] = []
        for result in results:
            cards_html.append(_build_card_html(result, crests))
            main_container.markdown(summary_html + "".join(cards_html), unsafe_allow_html=True)
            time.sleep(0.4)
        return

    # Rendering persistente dei risultati già simulati (senza dover ricliccare)
    if "matchday_results" in st.session_state:
        results = st.session_state["matchday_results"]
        summary_html = _summary_strip_html(results)
        cards_html = [_build_card_html(result, crests) for result in results]
        main_container.markdown(summary_html + "".join(cards_html), unsafe_allow_html=True)
    else:
        main_container.info("Press '⚡ SIMULATE FULL MATCHDAY' to start the sequence.")
