from __future__ import annotations

import time
from html import escape

import pandas as pd
import streamlit as st

from app import (
    FOOTBALL_DATA_COMPETITIONS,
    FootballDataError,
    fetch_league_matches,
    fetch_team_crests,
    run_simulation,
    try_build_match_model,
)

MATCHDAY_ACCENT = "#00E5FF"
MATCHDAY_BG = "#050505"


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
.mds-progress-label {{
    font-family: "Courier New", monospace;
    font-size: 0.85rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {MATCHDAY_ACCENT};
    text-shadow: 0 0 8px rgba(0,229,255,0.6);
    text-align: center;
    margin-bottom: 8px;
    font-weight: 800;
}}
.mds-progress-track {{
    width: 100%;
    height: 10px;
    border-radius: 999px;
    background: rgba(255,255,255,0.07);
    overflow: hidden;
    margin-bottom: 4px;
}}
.mds-progress-fill {{
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, {MATCHDAY_ACCENT}, #00ff87);
    box-shadow: 0 0 12px rgba(0,229,255,0.8);
    transition: width 0.25s ease;
}}
.mds-card {{
    background: linear-gradient(165deg, #101010 0%, #050505 100%);
    border: 1px solid {MATCHDAY_ACCENT};
    border-radius: 18px;
    padding: 18px 14px 16px 14px;
    margin-bottom: 14px;
    box-shadow: 0 0 20px rgba(0,229,255,0.15), 0 8px 22px rgba(0,0,0,0.5);
    text-align: center;
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
# RENDERING — Broadcast HUD card + neon animated progress
# ==============================================================================
def _render_progress(placeholder, current: int, total: int, label: str) -> None:
    pct = (current / total) * 100 if total else 0
    placeholder.markdown(
        f'<div class="mds-wrap">'
        f'<div class="mds-progress-label">⚡ {escape(label)}</div>'
        f'<div class="mds-progress-track"><div class="mds-progress-fill" '
        f'style="width:{pct:.1f}%"></div></div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _crest_html(name: str, crests: dict[str, str]) -> str:
    url = crests.get(name)
    if url:
        return f'<img src="{escape(url)}" class="mds-crest" />'
    return '<div class="mds-crest-placeholder">🛡️</div>'


def _render_match_card(
    home: str, away: str, score_label: str, home_prob: float, draw_prob: float, away_prob: float, crests: dict[str, str]
) -> None:
    st.markdown(
        f'<div class="mds-card">'
        f'<div class="mds-card-teams">'
        f'<div class="mds-team">{_crest_html(home, crests)}'
        f'<div class="mds-team-name">{escape(home)}</div></div>'
        f'<div class="mds-vs">VS</div>'
        f'<div class="mds-team">{_crest_html(away, crests)}'
        f'<div class="mds-team-name">{escape(away)}</div></div>'
        f"</div>"
        f'<div class="mds-score">{escape(score_label)}</div>'
        f'<div class="mds-outcome-row">'
        f'<span class="mds-outcome-badge">1 · {home_prob:.0%}</span>'
        f'<span class="mds-outcome-badge">X · {draw_prob:.0%}</span>'
        f'<span class="mds-outcome-badge">2 · {away_prob:.0%}</span>'
        f"</div></div>",
        unsafe_allow_html=True,
    )


def _simulate_one_fixture(league: str, home: str, away: str) -> dict[str, object] | None:
    """Costruisce il MatchModel e lancia la Monte Carlo a 10.000 iterazioni
    già esistenti in app.py (build_match_model / run_simulation): nessuna
    nuova statistica, solo lettura del Top Result e delle probabilità 1X2
    già calcolate dal motore Poisson + Dixon-Coles."""
    model, error = try_build_match_model(league, home, away)
    if model is None:
        return {"error": error}
    simulation = run_simulation(model, n_simulations=10_000)
    top_result = simulation["top_result"]
    return {
        "score": str(top_result["Exact Score"]),
        "home_prob": model.home_win_prob,
        "draw_prob": model.draw_prob,
        "away_prob": model.away_win_prob,
    }


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
        "Simulate an entire matchday, one fixture at a time — built for TikTok/Reels/Shorts "
        "recordings. Same Poisson + Dixon-Coles Monte Carlo engine used everywhere else in WayneLab."
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

    if st.session_state.get("_mds_context") != (league, matchday):
        st.session_state["_mds_context"] = (league, matchday)
        st.session_state.pop("mds_results", None)

    run_clicked = st.button("⚡ SIMULATE FULL MATCHDAY", type="primary", key="mds_run_button")

    try:
        crests = fetch_team_crests(league)
    except FootballDataError:
        crests = {}

    if run_clicked:
        results: list[dict[str, object]] = []
        progress_placeholder = st.empty()
        cards_placeholder = st.container()
        total = len(fixtures)

        for index, (home, away) in enumerate(fixtures, start=1):
            _render_progress(progress_placeholder, index - 1, total, f"Simulating Match {index}/{total}...")
            time.sleep(0.6)  # effetto attesa/animazione prima della reveal
            outcome = _simulate_one_fixture(league, home, away)
            _render_progress(progress_placeholder, index, total, f"Match {index}/{total} simulated!")

            with cards_placeholder:
                if outcome is None or "error" in outcome:
                    st.warning(f"{home} vs {away}: {outcome.get('error', 'simulation unavailable')}")
                else:
                    _render_match_card(
                        home, away, outcome["score"],
                        outcome["home_prob"], outcome["draw_prob"], outcome["away_prob"],
                        crests,
                    )
            results.append({"home": home, "away": away, **(outcome or {})})
            time.sleep(0.3)

        progress_placeholder.empty()
        st.session_state["mds_results"] = results
        st.success(f"✅ Giornata {matchday} fully simulated — {total} matches.")
        return

    # Rendering persistente dei risultati già simulati (senza dover ricliccare)
    if "mds_results" in st.session_state:
        for outcome in st.session_state["mds_results"]:
            if "error" in outcome:
                st.warning(f"{outcome['home']} vs {outcome['away']}: {outcome['error']}")
            else:
                _render_match_card(
                    outcome["home"], outcome["away"], outcome["score"],
                    outcome["home_prob"], outcome["draw_prob"], outcome["away_prob"],
                    crests,
                )
    else:
        st.info("Press '⚡ SIMULATE FULL MATCHDAY' to start the sequence.")
