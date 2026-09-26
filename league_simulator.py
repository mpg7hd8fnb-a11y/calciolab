"""
league_simulator.py — WayneLab · 🏆 Matchday Live Simulator
Modulo indipendente e puramente additivo: riusa esclusivamente le funzioni
e i modelli già presenti in app.py (build_match_model, run_simulation,
fetch_league_teams, fetch_league_matches, fetch_team_crests) — nessuna
nuova logica statistica di forecast, solo una nuova UI "broadcast" pensata
per la registrazione di contenuti social (TikTok/Reels/Shorts).

⚠️ ENTERTAINMENT CALIBRATION LAYER
Questo modulo applica, SOLO al proprio interno, moltiplicatori di xG per
lega, un tetto sui punteggi estremi e un vincolo rigido sulla frequenza
degli 0-0 nell'arco di una giornata — pensati per il pacing dei video
social. Questi aggiustamenti NON toccano il motore Poisson/Dixon-Coles
usato dalle altre tab (Match Analysis, Value Betting, Monte Carlo
Simulator, Multi-Outcome): quelle restano il riferimento analitico
dell'app, invariate.
"""

from __future__ import annotations

import dataclasses
import time
from html import escape

import numpy as np
import streamlit as st
import streamlit.components.v1 as components

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

MDS_LAMBDA_CEILING = 3.2
# Tetto di sicurezza sugli xG DOPO l'applicazione del moltiplicatore di lega
# (e di un eventuale boost anti-0-0), per evitare lambda irrealistici.

MATCHDAY_ZERO_ZERO_HARD_CAP = 2
# HARD CAP: al massimo questo numero di 0-0 può comparire in un'intera
# giornata simulata (10 partite). Dal (HARD CAP + 1)-esimo 0-0 in poi, la
# partita viene ri-simulata con xG potenziati finché non produce almeno 1 gol.

MDS_ZERO_ZERO_BOOST_STEP = 0.25
# Incremento del moltiplicatore xG ad ogni tentativo di re-roll anti-0-0
# (es. 1° tentativo +25%, 2° tentativo +50%...), fino a MDS_LAMBDA_CEILING.

MDS_ZERO_ZERO_REROLL_ATTEMPTS = 6
# Numero massimo di re-roll (intera ri-simulazione Monte Carlo con xG
# potenziati) prima di forzare un fallback deterministico (1-0).


def _apply_league_calibration(
    league: str, home_lambda: float, away_lambda: float, extra_boost: float = 0.0
) -> tuple[float, float, float]:
    """Applica il moltiplicatore di lega (più un eventuale extra_boost per i
    re-roll anti-0-0) ai due xG, con tetto di sicurezza MDS_LAMBDA_CEILING.
    Ritorna (adj_home, adj_away, multiplier_used)."""
    base_multiplier = LEAGUE_GOAL_MULTIPLIERS.get(league, LEAGUE_GOAL_MULTIPLIER_DEFAULT)
    multiplier = base_multiplier + extra_boost
    adj_home = clamp(home_lambda * multiplier, 0.1, MDS_LAMBDA_CEILING)
    adj_away = clamp(away_lambda * multiplier, 0.1, MDS_LAMBDA_CEILING)
    return adj_home, adj_away, multiplier


def _cap_extreme_scores(home_goals: np.ndarray, away_goals: np.ndarray) -> None:
    """Realistic Score Cap: tronca in-place ogni partita simulata al
    massimo MDS_MAX_GOALS_PER_TEAM gol per squadra."""
    np.clip(home_goals, 0, MDS_MAX_GOALS_PER_TEAM, out=home_goals)
    np.clip(away_goals, 0, MDS_MAX_GOALS_PER_TEAM, out=away_goals)


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
        "home_goals": int(top_home),
        "away_goals": int(top_away),
        "home_prob": home_wins / n,
        "draw_prob": draws / n,
        "away_prob": away_wins / n,
    }


# ==============================================================================
# CSS — Obsidian / Electric Cyan Broadcast HUD (scoped, no clash with app.py)
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

/* --- Matchday Summary Badge Strip --------------------------------- */
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

/* --- Broadcast Match Cards, with staggered fade-in cascade --------- */
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
    transform: translateY(14px);
    animation: mds-fade-in 0.55s ease forwards;
}}
@keyframes mds-fade-in {{
    from {{ opacity: 0; transform: translateY(14px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
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
# SIMULATION — sequential fixture loop + matchday-wide anti-zero-zero cap
# ==============================================================================
def _simulate_one_fixture(
    league: str, home: str, away: str, calibration_enabled: bool, zero_zero_count: int
) -> tuple[dict[str, object] | None, int]:
    """Simula una singola fixture con il MatchModel/Monte Carlo esistenti
    (build_match_model / run_simulation, invariati). Se `calibration_enabled`
    e il conteggio corrente di 0-0 nella giornata (`zero_zero_count`) ha già
    raggiunto MATCHDAY_ZERO_ZERO_HARD_CAP, un risultato 0-0 viene ri-simulato
    da zero con xG progressivamente potenziati (MDS_ZERO_ZERO_BOOST_STEP per
    tentativo) finché non produce almeno un gol, o dopo
    MDS_ZERO_ZERO_REROLL_ATTEMPTS tentativi forza un fallback 1-0.
    Ritorna (outcome, nuovo_zero_zero_count)."""
    model, error = try_build_match_model(league, home, away)
    if model is None:
        return {"error": error}, zero_zero_count

    base_home_lambda, base_away_lambda = model.home_lambda, model.away_lambda
    multiplier = 1.0
    outcome: dict[str, object] | None = None
    forced_reroll = False

    attempts = MDS_ZERO_ZERO_REROLL_ATTEMPTS if calibration_enabled else 1
    for attempt in range(attempts):
        extra_boost = MDS_ZERO_ZERO_BOOST_STEP * attempt if forced_reroll or attempt > 0 else 0.0

        if calibration_enabled:
            adj_home, adj_away, multiplier = _apply_league_calibration(
                league, base_home_lambda, base_away_lambda, extra_boost=extra_boost
            )
            sim_model = dataclasses.replace(model, home_lambda=adj_home, away_lambda=adj_away)
        else:
            sim_model = model

        simulation = run_simulation(sim_model, n_simulations=10_000)
        home_goals = simulation["raw"]["home_goals"].copy()
        away_goals = simulation["raw"]["away_goals"].copy()

        if calibration_enabled:
            _cap_extreme_scores(home_goals, away_goals)

        outcome = _empirical_score_and_outcomes(home_goals, away_goals)
        is_zero_zero = outcome["home_goals"] == 0 and outcome["away_goals"] == 0

        if not calibration_enabled or not is_zero_zero:
            break

        if zero_zero_count < MATCHDAY_ZERO_ZERO_HARD_CAP:
            # Ancora sotto il tetto di giornata: questo 0-0 è ammesso, non
            # serve alcun re-roll.
            break

        # Tetto di giornata già raggiunto: questo 0-0 va ri-simulato con xG
        # potenziati al prossimo giro del ciclo.
        forced_reroll = True

    if outcome is None:
        return {"error": "Simulation failed."}, zero_zero_count

    if forced_reroll and outcome["home_goals"] == 0 and outcome["away_goals"] == 0:
        # Tutti i tentativi di re-roll hanno comunque prodotto 0-0 (xG di
        # partenza estremamente bassi): fallback deterministico all'esito
        # minimo non-0-0 realistico, con probabilità 1X2 coerenti.
        outcome = {
            "score": "1-0",
            "home_goals": 1,
            "away_goals": 0,
            "home_prob": 0.55,
            "draw_prob": 0.20,
            "away_prob": 0.25,
        }

    calib_notes: list[str] = []
    if calibration_enabled:
        if multiplier != LEAGUE_GOAL_MULTIPLIERS.get(league, LEAGUE_GOAL_MULTIPLIER_DEFAULT):
            calib_notes.append(f"×{multiplier:.2f} xG")
        if forced_reroll:
            calib_notes.append("Anti-0-0 Re-Roll")
        calib_notes.append(f"Cap {MDS_MAX_GOALS_PER_TEAM}")
    outcome["calib_tag"] = "⚙️ " + " · ".join(calib_notes) if calib_notes else ""

    new_zero_zero_count = zero_zero_count + (
        1 if outcome["home_goals"] == 0 and outcome["away_goals"] == 0 else 0
    )
    return outcome, new_zero_zero_count


# ==============================================================================
# RENDERING — Smooth Broadcast Engine (CSS-driven, no per-card reruns)
# ==============================================================================
def _render_scanning_overlay(duration_seconds: float = 2.6) -> None:
    """⚙️ Overlay 'ANALYZING 10,000 MONTE CARLO SCENARIOS...': animazione
    interamente client-side (canvas 'digital rain' + conto alla rovescia
    JS via requestAnimationFrame), identica nello spirito all'HUD Monte
    Carlo già usato altrove nell'app ma incapsulata qui per restare
    self-contained. Nessun rerun Streamlit durante l'animazione: Python si
    limita ad attendere la stessa durata prima di procedere al calcolo
    reale, che avviene subito dopo in un colpo solo."""
    placeholder = st.empty()
    duration_ms = int(duration_seconds * 1000)
    with placeholder:
        components.html(
            f"""
            <div style="position:relative;height:170px;border-radius:16px;overflow:hidden;
                        border:1px solid {MATCHDAY_ACCENT};background:{MATCHDAY_BG};
                        box-shadow:0 0 28px rgba(0,229,255,0.18);">
              <canvas id="mdsCanvas" style="display:block;width:100%;height:170px;"></canvas>
              <div style="position:absolute;inset:0;display:flex;flex-direction:column;
                          align-items:center;justify-content:center;gap:8px;text-align:center;
                          background:rgba(5,5,5,0.35);">
                <div style="font-family:'Courier New',monospace;font-size:0.78rem;letter-spacing:0.18em;
                            text-transform:uppercase;color:{MATCHDAY_ACCENT};
                            text-shadow:0 0 8px rgba(0,229,255,0.7);">
                  ⚡ ANALYZING 10,000 MONTE CARLO SCENARIOS
                </div>
                <div id="mdsCounter" style="font-family:'Courier New',monospace;font-size:2.2rem;
                            font-weight:900;background:linear-gradient(135deg,#00ff87,{MATCHDAY_ACCENT});
                            -webkit-background-clip:text;background-clip:text;color:transparent;">0%</div>
                <div style="width:75%;height:7px;border-radius:999px;overflow:hidden;
                            background:rgba(255,255,255,0.08);">
                  <div id="mdsFill" style="height:100%;width:0%;border-radius:999px;
                            background:linear-gradient(90deg,#00ff87,{MATCHDAY_ACCENT});
                            box-shadow:0 0 12px rgba(0,229,255,0.8);"></div>
                </div>
              </div>
            </div>
            <script>
            const canvas = document.getElementById('mdsCanvas');
            const ctx = canvas.getContext('2d');
            function resize() {{ canvas.width = canvas.clientWidth; canvas.height = canvas.clientHeight; }}
            resize();
            window.addEventListener('resize', resize);
            const glyphs = '01λβαΣΔ⚽01λβαΣΔ01';
            const fontSize = 13;
            let columns = Math.floor(canvas.width / fontSize) || 20;
            let drops = new Array(columns).fill(1);
            function drawRain() {{
                ctx.fillStyle = 'rgba(5,5,5,0.18)';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = '{MATCHDAY_ACCENT}';
                ctx.font = fontSize + 'px monospace';
                for (let i = 0; i < drops.length; i++) {{
                    const glyph = glyphs[Math.floor(Math.random() * glyphs.length)];
                    ctx.fillText(glyph, i * fontSize, drops[i] * fontSize);
                    if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
                    drops[i]++;
                }}
            }}
            setInterval(drawRain, 45);

            const durationMs = {duration_ms};
            const counterEl = document.getElementById('mdsCounter');
            const fillEl = document.getElementById('mdsFill');
            const startTime = performance.now();
            function tick(now) {{
                const progress = Math.min((now - startTime) / durationMs, 1);
                const pct = Math.floor(progress * 100);
                counterEl.textContent = pct + '%';
                fillEl.style.width = pct + '%';
                if (progress < 1) requestAnimationFrame(tick);
            }}
            requestAnimationFrame(tick);
            </script>
            """,
            height=170,
        )
    time.sleep(duration_seconds)
    placeholder.empty()


def _crest_html(name: str, crests: dict[str, str]) -> str:
    url = crests.get(name)
    if url:
        return f'<img src="{escape(url)}" class="mds-crest" />'
    return '<div class="mds-crest-placeholder">🛡️</div>'


def _outcome_pill(home: str, away: str, home_prob: float, draw_prob: float, away_prob: float) -> str:
    """Pill unico con l'esito 1X2 dominante (es. 'HOME WIN · 64%'),
    con probabilità secondarie in piccolo sotto, come richiesto per un HUD
    minimal e d'impatto."""
    best = max(
        [("home", home_prob, home), ("draw", draw_prob, "DRAW"), ("away", away_prob, away)],
        key=lambda item: item[1],
    )
    kind, probability, _label = best
    if kind == "home":
        text, css_class = f"HOME WIN · {probability:.0%}", "mds-outcome-pill-home"
    elif kind == "away":
        text, css_class = f"AWAY WIN · {probability:.0%}", "mds-outcome-pill-away"
    else:
        text, css_class = f"DRAW · {probability:.0%}", "mds-outcome-pill-draw"
    sub = f"1 · {home_prob:.0%}  X · {draw_prob:.0%}  2 · {away_prob:.0%}"
    return (
        f'<span class="mds-outcome-pill {css_class}">{escape(text)}</span>'
        f'<div class="mds-outcome-sub">{escape(sub)}</div>'
    )


def _build_card_html(
    home: str,
    away: str,
    score_label: str,
    home_prob: float,
    draw_prob: float,
    away_prob: float,
    crests: dict[str, str],
    calib_tag: str,
    animation_delay_seconds: float,
) -> str:
    calib_html = f'<div class="mds-calib-tag">{escape(calib_tag)}</div>' if calib_tag else ""
    return (
        f'<div class="mds-card" style="animation-delay:{animation_delay_seconds:.2f}s">'
        f"{calib_html}"
        f'<div class="mds-card-teams">'
        f'<div class="mds-team">{_crest_html(home, crests)}'
        f'<div class="mds-team-name">{escape(home)}</div></div>'
        f'<div class="mds-vs">VS</div>'
        f'<div class="mds-team">{_crest_html(away, crests)}'
        f'<div class="mds-team-name">{escape(away)}</div></div>'
        f"</div>"
        f'<div class="mds-score">{escape(score_label)}</div>'
        f"{_outcome_pill(home, away, home_prob, draw_prob, away_prob)}"
        f"</div>"
    )


def _render_cascading_cards(results: list[dict[str, object]], crests: dict[str, str], stagger_seconds: float = 0.4) -> None:
    """Renderizza TUTTE le card in un unico blocco HTML/CSS: la cascata di
    fade-in è gestita interamente da animation-delay per card (CSS puro),
    così l'intera sequenza scorre fluida lato browser senza alcun rerun
    Streamlit intermedio — nessuno scatto, nessun ricaricamento di pagina."""
    cards_html: list[str] = []
    for index, outcome in enumerate(results):
        delay = index * stagger_seconds
        if "error" in outcome:
            cards_html.append(
                f'<div class="mds-card" style="animation-delay:{delay:.2f}s">'
                f'<div class="mds-team-name">⚠️ {escape(outcome["home"])} vs {escape(outcome["away"])}</div>'
                f'<div class="mds-outcome-sub">{escape(str(outcome.get("error", "unavailable")))}</div>'
                f"</div>"
            )
            continue
        cards_html.append(
            _build_card_html(
                outcome["home"], outcome["away"], outcome["score"],
                outcome["home_prob"], outcome["draw_prob"], outcome["away_prob"],
                crests, outcome.get("calib_tag", ""), delay,
            )
        )
    st.markdown("".join(cards_html), unsafe_allow_html=True)


def _render_summary_strip(results: list[dict[str, object]]) -> None:
    """Badge di sintesi giornata: Total Goals, Avg Goals/Match, Home Wins %
    — calcolati sui punteggi effettivamente rivelati nelle card."""
    valid = [r for r in results if "error" not in r]
    if not valid:
        return
    total_goals = sum(r["home_goals"] + r["away_goals"] for r in valid)
    avg_goals = total_goals / len(valid)
    home_win_count = sum(1 for r in valid if r["home_goals"] > r["away_goals"])
    home_win_pct = home_win_count / len(valid) * 100
    zero_zero_count = sum(1 for r in valid if r["home_goals"] == 0 and r["away_goals"] == 0)

    items = [
        ("Total Goals", f"{total_goals}"),
        ("Avg Goals / Match", f"{avg_goals:.2f}"),
        ("Home Wins %", f"{home_win_pct:.0f}%"),
        ("0-0 Results", f"{zero_zero_count}"),
    ]
    items_html = "".join(
        f'<div class="mds-summary-item"><div class="mds-summary-label">{escape(label)}</div>'
        f'<div class="mds-summary-value">{escape(value)}</div></div>'
        for label, value in items
    )
    st.markdown(f'<div class="mds-summary-strip">{items_html}</div>', unsafe_allow_html=True)


# ==============================================================================
# MAIN TAB ENTRY POINT
# ==============================================================================
def render_matchday_simulator_tab() -> None:
    st.markdown(MATCHDAY_CSS, unsafe_allow_html=True)
    st.markdown('<div class="mds-header-title">🏆 MATCHDAY LIVE SIMULATOR</div>', unsafe_allow_html=True)
    st.caption(
        "Simulate an entire matchday, revealed as a smooth cascading broadcast sequence — built for "
        "TikTok/Reels/Shorts recordings. Same Poisson + Dixon-Coles Monte Carlo engine used elsewhere in WayneLab."
    )
    st.markdown(
        '<div class="mds-disclaimer">🎬 <b>Entertainment Calibration</b>: this tab applies '
        "discretionary per-league xG multipliers, a realistic score cap, and a hard cap of "
        f"{MATCHDAY_ZERO_ZERO_HARD_CAP} 0-0 results per matchday (excess 0-0 outcomes are automatically "
        "re-simulated with boosted xG). These adjustments apply ONLY here — Match Analysis, Value Betting "
        "and Monte Carlo Simulator remain the app's unaffected statistical reference. Toggle off below to "
        "see the unadjusted model.</div>",
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
        st.session_state.pop("mds_results", None)

    run_clicked = st.button("⚡ SIMULATE FULL MATCHDAY", type="primary", key="mds_run_button")

    try:
        crests = fetch_team_crests(league)
    except FootballDataError:
        crests = {}

    if run_clicked:
        # --- Fase 1: overlay ad alto impatto visivo (~2.6s), nessun rerun --
        _render_scanning_overlay(duration_seconds=2.6)

        # --- Fase 2: simulazione sequenziale reale, in un colpo solo -------
        # (il vincolo anti-0-0 è per costruzione sequenziale: il contatore
        # di giornata avanza fixture per fixture).
        results: list[dict[str, object]] = []
        zero_zero_running_count = 0
        for home, away in fixtures:
            outcome, zero_zero_running_count = _simulate_one_fixture(
                league, home, away, calibration_enabled, zero_zero_running_count
            )
            results.append({"home": home, "away": away, **(outcome or {})})

        st.session_state["mds_results"] = results

        # --- Fase 3: reveal a cascata, CSS-driven, un solo rendering -------
        _render_summary_strip(results)
        _render_cascading_cards(results, crests, stagger_seconds=0.4)
        return

    # Rendering persistente dei risultati già simulati (senza dover ricliccare)
    if "mds_results" in st.session_state:
        results = st.session_state["mds_results"]
        _render_summary_strip(results)
        _render_cascading_cards(results, crests, stagger_seconds=0.4)
    else:
        st.info("Press '⚡ SIMULATE FULL MATCHDAY' to start the sequence.")
