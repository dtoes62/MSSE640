"""
Coffee Shop Chaos — Barista Basics
===================================
A Streamlit app that teaches software testing techniques through
the chaos of a coffee shop counter.

Run with:  streamlit run app.py
"""

import random
from datetime import datetime

import streamlit as st
import pandas as pd

from menu import (
    DRINK_BASES, DRINK_EMOJIS, MILK_TYPES, MILK_EMOJIS,
    FLAVOR_SYRUPS, SYRUP_EMOJIS, TOPPINGS, TOPPING_EMOJIS,
    DRINK_RECIPES, PLANT_MILKS, CAFFEINE_PER_SHOT, HALL_OF_SHAME,
)
from rules import (
    Order, evaluate_order, overall_severity,
    fired_rule_ids, Severity, TestType, DECISION_TABLE,
)
from pairwise import (
    generate_pairwise_cases, brute_force_count,
    pairwise_count, run_all_pairwise,
)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Coffee Shop Chaos — Barista Basics",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS — dark wood counter aesthetic ────────────────────────────────────────

st.markdown("""
<style>
/* ── Overall background ── */
.stApp { background-color: #1a0d05; }
section[data-testid="stSidebar"] { background-color: #2c1810; }

/* ── Station cards (columns get a wood-panel look) ── */
div[data-testid="column"] > div:first-child {
    background: linear-gradient(175deg, #3d1f0a 0%, #2a1406 100%);
    border-radius: 14px;
    border: 1px solid #5c3317;
    border-top: 5px solid #8B4513;
    padding: 16px 14px 20px 14px;
    min-height: 480px;
}

/* ── Station headers ── */
.station-header {
    text-align: center;
    margin-bottom: 10px;
}
.station-icon { font-size: 2.6em; display: block; text-align: center; }
.station-title {
    color: #f5c842;
    font-weight: 700;
    font-size: 1.05em;
    text-align: center;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin: 4px 0 2px 0;
}
.step-badge {
    display: inline-block;
    background: #f5c842;
    color: #1a0d05;
    border-radius: 20px;
    padding: 1px 10px;
    font-size: 0.72em;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 0 auto 8px auto;
}
.station-desc {
    color: #b89070;
    font-size: 0.78em;
    text-align: center;
    margin-bottom: 10px;
    font-style: italic;
}

/* ── Order ticket ── */
.order-ticket {
    background: #fffef0;
    border: 2px dashed #8B4513;
    border-radius: 10px;
    padding: 18px 20px;
    font-family: 'Courier New', monospace;
    color: #1a0d05;
    font-size: 0.9em;
    line-height: 1.7;
}
.ticket-title {
    font-size: 1.1em;
    font-weight: 900;
    text-align: center;
    border-bottom: 2px solid #8B4513;
    padding-bottom: 6px;
    margin-bottom: 10px;
    letter-spacing: 2px;
}

/* ── QA label pill ── */
.qa-pill {
    display: inline-block;
    background: #003322;
    color: #00ff88;
    border: 1px solid #00ff88;
    border-radius: 12px;
    padding: 1px 8px;
    font-family: monospace;
    font-size: 0.75em;
    font-weight: 700;
    margin-right: 6px;
    vertical-align: middle;
}

/* ── Status banner ── */
.status-pass    { background:#134e13; color:#7eff7e; border-radius:10px; padding:14px 20px; font-size:1.2em; font-weight:700; }
.status-warning { background:#4e3a00; color:#ffe066; border-radius:10px; padding:14px 20px; font-size:1.2em; font-weight:700; }
.status-invalid { background:#4e0d0d; color:#ff6b6b; border-radius:10px; padding:14px 20px; font-size:1.2em; font-weight:700; }

/* ── Hall of Shame card ── */
.shame-card {
    background: linear-gradient(135deg, #2c0a0a, #3d1505);
    border: 1px solid #8B0000;
    border-left: 5px solid #cc2200;
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 16px;
}
.shame-name  { color: #ff6b6b; font-size: 1.1em; font-weight: 800; }
.shame-sub   { color: #b89070; font-size: 0.82em; font-style: italic; }
.shame-story { color: #e0c0a0; font-size: 0.88em; margin-top: 8px; line-height: 1.6; }

/* ── BtB game ── */
.btb-order-card {
    background: linear-gradient(135deg, #0a1a2c, #051525);
    border: 2px solid #1a6699;
    border-radius: 12px;
    padding: 20px;
    font-family: 'Courier New', monospace;
    color: #a0d4ff;
    font-size: 0.95em;
    line-height: 2;
}
.btb-title {
    color: #66ccff;
    font-size: 1.1em;
    font-weight: 900;
    letter-spacing: 1px;
    border-bottom: 1px solid #1a6699;
    padding-bottom: 8px;
    margin-bottom: 12px;
}

/* ── EC zone badges ── */
.ec-valid   { background:#134e13; color:#7eff7e; border-radius:8px; padding:2px 10px; font-size:0.82em; font-weight:700; }
.ec-warning { background:#4e3a00; color:#ffe066; border-radius:8px; padding:2px 10px; font-size:0.82em; font-weight:700; }
.ec-invalid { background:#4e0d0d; color:#ff6b6b; border-radius:8px; padding:2px 10px; font-size:0.82em; font-weight:700; }

/* ── BV zone bar labels ── */
.bv-zone { font-family:monospace; font-size:0.82em; color:#b89070; }

/* ── Streamlit overrides ── */
/* Radio option labels — white and legible */
.stRadio label { color: #ffffff !important; font-size: 1.05em !important; font-weight: 500 !important; }
/* All widget labels (sliders, etc.) */
label[data-testid="stWidgetLabel"] p { color: #ffffff !important; font-size: 1.05em !important; font-weight: 600 !important; }
/* Caption text — brighter so it's readable on dark background */
.stCaption p { color: #f0d0a8 !important; font-size: 0.9em !important; }
/* QA Mode toggle — bigger label, white text */
div[data-testid="stToggle"] { transform: scale(1.15); transform-origin: right center; }
div[data-testid="stToggle"] label { color: #f5f0e8 !important; font-size: 1.1em !important; font-weight: 700 !important; }
/* All markdown paragraph text — white throughout the app */
div[data-testid="stMarkdownContainer"] p { color: #f5f0e8 !important; font-size: 1.0em; }
/* Order ticket — dark text on white background */
.order-ticket, .order-ticket b, .order-ticket * { color: #1a0d05 !important; }
/* Dialog popout — dark background matching the counter theme */
div[data-testid="stModal"] > div,
div[role="dialog"] { background-color: #1e0f05 !important; color: #f5f0e8 !important; }
div[role="dialog"] * { color: #f5f0e8; }
h1, h2, h3 { color: #f5c842 !important; }
.stTabs [data-baseweb="tab"] { color: #b89070; }
.stTabs [aria-selected="true"] { color: #f5c842 !important; border-bottom: 2px solid #f5c842; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

def _init_state():
    defaults = {
        "order_log":        [],
        "last_order":       None,
        "last_results":     [],
        "qa_mode":          False,
        "btb_order":        None,
        "btb_revealed":     False,
        "btb_score":        {"correct": 0, "total": 0},
        "pw_cases":         None,
        "pw_results":       None,
        "shame_loaded":     None,
        "counter_reset_v":  0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ── Helpers ───────────────────────────────────────────────────────────────────

def severity_icon(s: Severity) -> str:
    return {"pass": "✅", "warning": "⚠️", "invalid": "❌"}[s.value]

def severity_coffee(s: Severity) -> str:
    return {"pass": "☕", "warning": "😬", "invalid": "💀"}[s.value]

def severity_html_class(s: Severity) -> str:
    return f"status-{s.value}"

def qa_pill(test_type: TestType, rule_id: str) -> str:
    return f'<span class="qa-pill">{test_type.value}</span><span class="qa-pill">Rule {rule_id}</span>'

def render_results(results, qa_mode: bool):
    """Render rule results as Streamlit expanders with optional QA labels."""
    if not results:
        st.success("☕ All checks passed. The barista approves. Beautiful drink.")
        return
    for r in results:
        if r.severity == Severity.INVALID:
            with st.expander(f"❌ {r.title}", expanded=True):
                if qa_mode:
                    st.markdown(qa_pill(r.test_type, r.rule_id), unsafe_allow_html=True)
                st.markdown(f"**{r.description}**")
                st.markdown(r.detail)
        elif r.severity == Severity.WARNING:
            with st.expander(f"⚠️ {r.title}", expanded=True):
                if qa_mode:
                    st.markdown(qa_pill(r.test_type, r.rule_id), unsafe_allow_html=True)
                st.markdown(f"**{r.description}**")
                st.markdown(r.detail)

def order_from_dict(d: dict) -> Order:
    return Order(**d)

def log_order(order: Order, results, tag: str = ""):
    sev = overall_severity(results)
    st.session_state.order_log.append({
        "Time":       datetime.now().strftime("%H:%M:%S"),
        "Tag":        tag,
        "Drink":      order.drink_base,
        "Milk":       order.milk_type,
        "Syrup":      f"{order.syrup} ×{order.syrup_pumps}" if order.syrup != "None" else "None",
        "Topping":    order.topping,
        "Temp °F":    order.temperature,
        "Shots":      order.shots,
        "Caffeine":   f"{order.caffeine_mg}mg",
        "Status":     sev.value.upper(),
        "Rules":      ", ".join(r.rule_id for r in results) or "—",
        "Techniques": ", ".join(sorted(set(r.test_type.value for r in results))) or "—",
    })


# ── Counter station widget ────────────────────────────────────────────────────

def station_header(icon: str, title: str, step: str, desc: str):
    st.markdown(
        f'<div class="station-header">'
        f'<span class="station-icon">{icon}</span>'
        f'<div class="step-badge">{step}</div>'
        f'<div class="station-title">{title}</div>'
        f'<div class="station-desc">{desc}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Order Results dialog (popout) ────────────────────────────────────────────

@st.dialog("☕  Order Results", width="large")
def show_order_results_dialog():
    order   = st.session_state.last_order
    results = st.session_state.last_results
    qa_mode = st.session_state.qa_mode
    if not order:
        st.write("No order to display.")
        return

    sev = overall_severity(results)

    # ── Status banner ─────────────────────────────────────────────────────────
    icons = {
        "pass":    "✅  PERFECT ORDER — The barista is happy!",
        "warning": "⚠️  QUESTIONABLE ORDER — Proceed with caution",
        "invalid": "❌  ORDER REJECTED — This drink cannot be made",
    }
    coffee = severity_coffee(sev)
    st.markdown(
        f'<div class="{severity_html_class(sev)}" style="font-size:1.3em; padding:16px 22px; margin-bottom:14px;">'
        f'{coffee}&nbsp;&nbsp;{icons[sev.value]}</div>',
        unsafe_allow_html=True,
    )

    # ── Two-column: ticket + rule results ─────────────────────────────────────
    d_left, d_right = st.columns([1, 2])

    with d_left:
        pumps_str = f" x{order.syrup_pumps}" if order.syrup != "None" else ""
        st.markdown(f"""
        <div class="order-ticket" style="font-size:1.0em;">
        <div class="ticket-title">ORDER TICKET</div>
        <b>Drink:</b> {DRINK_EMOJIS[order.drink_base]} {order.drink_base}<br>
        <b>Milk:</b> {MILK_EMOJIS[order.milk_type]} {order.milk_type}<br>
        <b>Syrup:</b> {SYRUP_EMOJIS[order.syrup]} {order.syrup}{pumps_str}<br>
        <b>Topping:</b> {TOPPING_EMOJIS[order.topping]} {order.topping}<br>
        <b>Temp:</b> {order.temperature}&deg;F<br>
        <b>Shots:</b> {order.shots}<br>
        <b>Caffeine:</b> {order.caffeine_mg}mg<br>
        <hr style="border-color:#8B4513; margin:8px 0">
        <b>Status:</b> {severity_icon(sev)} {sev.value.upper()}
        </div>
        """, unsafe_allow_html=True)

    with d_right:
        st.markdown("#### What the rules say:")
        render_results(results, qa_mode)

    # ── Clear & close ─────────────────────────────────────────────────────────
    st.divider()
    if st.button("🗑️  Clear & Start New Order", type="primary", use_container_width=True):
        st.session_state.last_order     = None
        st.session_state.last_results   = []
        st.session_state.counter_reset_v += 1   # forces all counter widgets to reset
        st.rerun()


# ── Header bar ────────────────────────────────────────────────────────────────

hcol1, hcol2 = st.columns([5, 1])
with hcol1:
    st.markdown("# ☕ Coffee Shop Chaos — Barista Basics")
    st.markdown("Master the art of coffee. Break the rules. Learn why testing matters.")
with hcol2:
    st.session_state.qa_mode = st.toggle(
        "🔬 QA Mode",
        value=st.session_state.qa_mode,
        help="QA Mode labels every rule result with its testing technique and rule ID.",
    )

qa_mode = st.session_state.qa_mode
st.divider()


# ── Main tabs ─────────────────────────────────────────────────────────────────

(
    tab_counter,
    tab_btb,
    tab_shame,
    tab_ec,
    tab_bv,
    tab_dt,
    tab_pw,
    tab_log,
) = st.tabs([
    "🧑‍🍳 Barista Counter",
    "💥 Break the Barista",
    "🏆 Hall of Shame",
    "📊 Equivalence Classes",
    "📏 Boundary Values",
    "📋 Decision Table",
    "🔬 Pairwise Testing",
    "📝 Test Case Log",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — BARISTA COUNTER
# ══════════════════════════════════════════════════════════════════════════════

with tab_counter:
    st.markdown("### 🏪 The Counter — Build Your Order")
    st.markdown("Work left to right through each station, then fire the order.")

    # Versioned key suffix — incremented on clear to reset all widgets
    v = st.session_state.counter_reset_v

    # Pre-fill from Hall of Shame if one was loaded
    shame_defaults = st.session_state.shame_loaded or {}

    # ── 5 counter stations ────────────────────────────────────────────────────
    s1, s2, s3, s4, s5 = st.columns(5)

    with s1:
        station_header("🔩", "Espresso Machine", "Step 1", "Choose your drink")
        drink_base = st.radio(
            "drink_base",
            DRINK_BASES,
            index=DRINK_BASES.index(shame_defaults.get("drink_base", "Latte")),
            format_func=lambda d: f"{DRINK_EMOJIS[d]}  {d}",
            label_visibility="collapsed",
            key=f"c_drink_{v}",
        )
        recipe = DRINK_RECIPES[drink_base]
        st.caption(f"_{recipe['description']}_")
        if qa_mode:
            st.caption(f"🔬 EC: drink_base in {{{', '.join(DRINK_BASES[:3])}...}}")

    with s2:
        station_header("🥛", "Milk Station", "Step 2", "Choose your milk")
        milk_type = st.radio(
            "milk_type",
            MILK_TYPES,
            index=MILK_TYPES.index(shame_defaults.get("milk_type", "Whole Milk")),
            format_func=lambda m: f"{MILK_EMOJIS[m]}  {m}",
            label_visibility="collapsed",
            key=f"c_milk_{v}",
        )
        if milk_type in PLANT_MILKS:
            st.caption("🌱 Plant-based — heat sensitive above 180°F")
        elif milk_type == "None":
            st.caption("🚫 No milk selected")
        if qa_mode:
            ec_class = "Plant Milk (temp sensitive)" if milk_type in PLANT_MILKS else (
                "No Milk (invalid for some drinks)" if milk_type == "None" else "Standard Milk"
            )
            st.caption(f"🔬 EC class: {ec_class}")

    with s3:
        station_header("🍯", "Syrup Rack", "Step 3", "Add a flavor")
        syrup_default = shame_defaults.get("syrup", "None")
        syrup = st.radio(
            "syrup",
            FLAVOR_SYRUPS,
            index=FLAVOR_SYRUPS.index(syrup_default),
            format_func=lambda s: f"{SYRUP_EMOJIS[s]}  {s}",
            label_visibility="collapsed",
            key=f"c_syrup_{v}",
        )
        if syrup != "None":
            pumps_default = shame_defaults.get("syrup_pumps", 3)
            syrup_pumps = st.slider(
                "Pumps", 0, 15,
                value=int(pumps_default),
                help="0-6 = Valid | 7-10 = Warning | >10 = Invalid",
                key=f"c_pumps_{v}",
            )
            pump_zone = (
                "Valid (0-6)" if syrup_pumps <= 6
                else "Warning (7-10)" if syrup_pumps <= 10
                else "Invalid (>10)"
            )
            st.caption(f"Pump zone: {pump_zone}")
        else:
            syrup_pumps = 0
        if syrup == "Lemon/Citrus":
            st.caption("Acidic syrup — dangerous with milk!")
        if qa_mode and syrup != "None":
            st.caption("🔬 BV: syrup_pumps boundaries at 6|7 and 10|11")

    with s4:
        station_header("🧁", "Topping Bar", "Step 4", "Finish it off")
        topping_default = shame_defaults.get("topping", "None")
        topping = st.radio(
            "topping",
            TOPPINGS,
            index=TOPPINGS.index(topping_default),
            format_func=lambda t: f"{TOPPING_EMOJIS[t]}  {t}",
            label_visibility="collapsed",
            key=f"c_topping_{v}",
        )
        if topping == "Foam":
            st.caption("Foam collapses on iced drinks (<50°F)")
        if qa_mode:
            st.caption("🔬 DT: Foam+Iced triggers Rule R5b")

    with s5:
        station_header("⚙️", "Controls", "Step 5", "Dial in your specs")
        temp_default = shame_defaults.get("temperature", 155)
        temperature = st.slider(
            "Temperature (°F)", 32, 212, int(temp_default),
            help="Iced ~35 | Warm ~120 | Hot ~155-170 | Danger >180 for plant milks",
            key=f"c_temp_{v}",
        )
        shots_default = shame_defaults.get("shots", 2)
        shots = st.slider(
            "Espresso Shots", 1, 6, int(shots_default),
            help="Each shot = 75mg caffeine | Warning >400mg | Invalid >600mg",
            key=f"c_shots_{v}",
        )
        caffeine = shots * CAFFEINE_PER_SHOT
        caf_label = (
            "Safe" if caffeine <= 400
            else "High" if caffeine <= 600
            else "Danger"
        )
        st.metric("Caffeine", f"{caffeine}mg", delta=caf_label, delta_color=(
            "normal" if caffeine <= 400 else "inverse"
        ))
        if qa_mode:
            st.caption("🔬 BV: caffeine boundaries at 400|401 and 600|601 mg")

    # Clear shame pre-fill after rendering
    if st.session_state.shame_loaded:
        st.session_state.shame_loaded = None

    st.divider()

    # ── Order button + re-open last results ───────────────────────────────────
    btn_col, view_col = st.columns([3, 1])
    with btn_col:
        fire = st.button("🎯  Fire the Order!", type="primary", use_container_width=True)
    with view_col:
        view_last = (
            st.button("📋 View Last Results", use_container_width=True)
            if st.session_state.last_order else None
        )

    if fire:
        order = Order(drink_base, milk_type, syrup, syrup_pumps, topping, temperature, shots)
        results = evaluate_order(order)
        st.session_state.last_order   = order
        st.session_state.last_results = results
        log_order(order, results, tag="counter")
        show_order_results_dialog()

    if view_last and st.session_state.last_order:
        show_order_results_dialog()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — BREAK THE BARISTA
# ══════════════════════════════════════════════════════════════════════════════

with tab_btb:
    st.markdown("### 💥 Break the Barista — Prediction Game")
    st.markdown(
        "A random order appears. Read it carefully. "
        "Predict whether the barista can make it — **VALID**, **WARNING**, or **INVALID**. "
        "Reveal to see if you're right and which rules fired."
    )

    score = st.session_state.btb_score
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("🏆 Score", f"{score['correct']} / {score['total']}")
    sc2.metric("✅ Correct", score["correct"])
    pct = int(score["correct"] / score["total"] * 100) if score["total"] else 0
    sc3.metric("📊 Accuracy", f"{pct}%")

    st.divider()

    gen_col, _ = st.columns([2, 3])
    with gen_col:
        if st.button("🎲 Generate Random Order", type="primary", use_container_width=True):
            from menu import DRINK_BASES, MILK_TYPES, FLAVOR_SYRUPS, TOPPINGS
            import random
            st.session_state.btb_order = Order(
                drink_base  = random.choice(DRINK_BASES),
                milk_type   = random.choice(MILK_TYPES),
                syrup       = random.choice(FLAVOR_SYRUPS),
                syrup_pumps = random.randint(0, 15),
                topping     = random.choice(TOPPINGS),
                temperature = random.randint(32, 212),
                shots       = random.randint(1, 6),
            )
            st.session_state.btb_revealed = False

    if st.session_state.btb_order:
        o = st.session_state.btb_order
        pumps_str = f" ×{o.syrup_pumps}" if o.syrup != "None" else ""

        left, right = st.columns([1, 1])

        with left:
            st.markdown(f"""
            <div class="btb-order-card">
            <div class="btb-title">📋 CUSTOMER ORDER TICKET</div>
            <b>Drink:</b>   {DRINK_EMOJIS[o.drink_base]} {o.drink_base}<br>
            <b>Milk:</b>    {MILK_EMOJIS[o.milk_type]} {o.milk_type}<br>
            <b>Syrup:</b>   {SYRUP_EMOJIS[o.syrup]} {o.syrup}{pumps_str}<br>
            <b>Topping:</b> {TOPPING_EMOJIS[o.topping]} {o.topping}<br>
            <b>Temp:</b>    {o.temperature}°F<br>
            <b>Shots:</b>   {o.shots} &nbsp;({o.caffeine_mg}mg caffeine)<br>
            </div>
            """, unsafe_allow_html=True)

        with right:
            if not st.session_state.btb_revealed:
                st.markdown("#### 🤔 Your Prediction")
                prediction = st.radio(
                    "What will this order be?",
                    ["✅ VALID — No problems", "⚠️ WARNING — Proceed with caution", "❌ INVALID — Can't make it"],
                    key="btb_prediction",
                )
                if st.button("🔍 Reveal Answer", type="primary", use_container_width=True):
                    actual_results = evaluate_order(o)
                    actual_sev     = overall_severity(actual_results)

                    # Score update
                    st.session_state.btb_score["total"] += 1
                    predicted_map = {"✅ VALID — No problems": "pass",
                                     "⚠️ WARNING — Proceed with caution": "warning",
                                     "❌ INVALID — Can't make it": "invalid"}
                    predicted_key = predicted_map[prediction]
                    correct = predicted_key == actual_sev.value
                    if correct:
                        st.session_state.btb_score["correct"] += 1

                    st.session_state.btb_revealed_results  = actual_results
                    st.session_state.btb_revealed_correct  = correct
                    st.session_state.btb_revealed          = True
                    log_order(o, actual_results, tag="break-the-barista")
                    st.rerun()

            else:
                results = st.session_state.get("btb_revealed_results", [])
                correct = st.session_state.get("btb_revealed_correct", False)
                sev     = overall_severity(results)

                if correct:
                    st.success("🎉 Correct! You read the rules right.")
                else:
                    st.error(f"❌ Wrong! The actual result was **{sev.value.upper()}**.")

                render_results(results, qa_mode)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — HALL OF SHAME
# ══════════════════════════════════════════════════════════════════════════════

with tab_shame:
    st.markdown("### 🏆 Hall of Shame — Famous Disasters")
    st.markdown(
        "These are legendary orders. Each one illustrates a different testing concept. "
        "Click **Load to Counter** to analyze one yourself."
    )

    for entry in HALL_OF_SHAME:
        o = order_from_dict(entry["order"])
        results = evaluate_order(o)
        sev     = overall_severity(results)

        sh_left, sh_right = st.columns([3, 2])
        with sh_left:
            st.markdown(f"""
            <div class="shame-card">
            <div class="shame-name">{entry['name']}</div>
            <div class="shame-sub">{entry['subtitle']}</div>
            <div class="shame-story">{entry['story']}</div>
            </div>
            """, unsafe_allow_html=True)

        with sh_right:
            # Mini order summary + results
            pumps_str = f" ×{o.syrup_pumps}" if o.syrup != "None" else ""
            st.markdown(f"""
            <div class="order-ticket" style="font-size:0.8em">
            <b>{DRINK_EMOJIS[o.drink_base]} {o.drink_base}</b><br>
            {MILK_EMOJIS[o.milk_type]} {o.milk_type} &nbsp;|&nbsp; {SYRUP_EMOJIS[o.syrup]} {o.syrup}{pumps_str}<br>
            {TOPPING_EMOJIS[o.topping]} {o.topping} &nbsp;|&nbsp; {o.temperature}°F &nbsp;|&nbsp; {o.shots} shot(s)<br>
            <b>Status: {severity_icon(sev)} {sev.value.upper()}</b>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")
            for r in results:
                if qa_mode:
                    st.markdown(
                        f'<span class="qa-pill">{r.test_type.value}</span> <b>{r.title}</b>',
                        unsafe_allow_html=True,
                    )
                else:
                    icon = "❌" if r.severity == Severity.INVALID else "⚠️"
                    st.markdown(f"{icon} **{r.title}**")
                st.markdown(r.detail)

            if st.button(f"Load to Counter ↗", key=f"load_{entry['name']}"):
                st.session_state.shame_loaded = entry["order"]
                st.switch_page  # not available in all versions — use workaround below

        st.divider()

    st.info("💡 Tip: Use **Load to Counter** then switch to the **Barista Counter** tab to interact with the order.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — EQUIVALENCE CLASSES
# ══════════════════════════════════════════════════════════════════════════════

with tab_ec:
    st.markdown("### 📊 Equivalence Class Partitions")
    st.markdown(
        "Equivalence Class testing groups inputs into partitions where every value "
        "in a partition is expected to behave the same way. Testing one value from each "
        "partition is sufficient — you don't need to test every value."
    )

    order = st.session_state.last_order

    ec_data = {
        "Syrup Pumps": [
            ("0 – 6 pumps",  "Valid",   "VALID",   lambda o: o.syrup != "None" and o.syrup_pumps <= 6),
            ("7 – 10 pumps", "Warning", "WARNING",  lambda o: 6 < o.syrup_pumps <= 10),
            ("> 10 pumps",   "Invalid", "INVALID",  lambda o: o.syrup_pumps > 10),
            ("No syrup",     "Valid",   "VALID",   lambda o: o.syrup == "None"),
        ],
        "Milk Type": [
            ("Dairy / Half&Half",  "Standard",    "VALID",   lambda o: o.milk_type in ("Whole Milk","Skim Milk","Half & Half")),
            ("Plant-based",        "Heat-sensitive","WARNING",lambda o: o.milk_type in PLANT_MILKS),
            ("None",               "No milk",      "VALID",   lambda o: o.milk_type == "None"),
        ],
        "Caffeine (Shots)": [
            ("0 – 400 mg",   "Safe",    "VALID",   lambda o: o.caffeine_mg <= 400),
            ("401 – 600 mg", "Warning", "WARNING",  lambda o: 400 < o.caffeine_mg <= 600),
            ("> 600 mg",     "Danger",  "INVALID",  lambda o: o.caffeine_mg > 600),
        ],
        "Syrup Type": [
            ("Non-acidic syrup", "Safe",      "VALID",   lambda o: o.syrup != "None" and o.syrup not in ("Lemon/Citrus",)),
            ("Acidic syrup",     "Curdling risk","INVALID",lambda o: o.syrup in ("Lemon/Citrus",)),
            ("None",             "No syrup",  "VALID",   lambda o: o.syrup == "None"),
        ],
    }

    for param_name, classes in ec_data.items():
        st.markdown(f"#### {param_name}")
        cols = st.columns(len(classes))
        for i, (range_label, class_name, zone, predicate) in enumerate(classes):
            active = order and predicate(order)
            zone_class = {"VALID": "ec-valid", "WARNING": "ec-warning", "INVALID": "ec-invalid"}[zone]
            highlight = "border: 2px solid #f5c842;" if active else ""
            current_label = "<br><b style=\"color:#f5c842\">&larr; current</b>" if active else ""
            with cols[i]:
                st.markdown(
                    f'<div style="background:#2a1406; border-radius:10px; padding:12px; '
                    f'text-align:center; {highlight}">'
                    f'<span class="{zone_class}">{zone}</span><br>'
                    f'<b style="color:#e0c0a0">{class_name}</b><br>'
                    f'<span style="color:#b89070; font-size:0.82em">{range_label}</span>'
                    f'{current_label}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        st.markdown("")

    if not order:
        st.info("💡 Place an order on the **Barista Counter** tab to highlight your current equivalence classes.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — BOUNDARY VALUES
# ══════════════════════════════════════════════════════════════════════════════

with tab_bv:
    st.markdown("### 📏 Boundary Value Analysis")
    st.markdown(
        "Boundary Value Analysis tests the edges between equivalence classes — "
        "the exact values where behavior changes. Bugs most commonly lurk at boundaries."
    )

    order = st.session_state.last_order

    def bv_gauge(label, value, boundaries, zones, unit=""):
        """Render a boundary value zone diagram."""
        st.markdown(f"**{label}** — Current value: `{value}{unit}`")
        zone_colors = {"VALID": "#134e13", "WARNING": "#4e3a00", "INVALID": "#4e0d0d"}
        zone_text   = {"VALID": "#7eff7e", "WARNING": "#ffe066", "INVALID": "#ff6b6b"}

        html = '<div style="display:flex; gap:4px; margin:8px 0 4px 0;">'
        for (lo, hi, zone, zlabel) in zones:
            active = lo <= value <= hi
            border = "border: 3px solid #f5c842;" if active else "border: 1px solid #444;"
            html += (
                f'<div style="flex:1; background:{zone_colors[zone]}; {border} '
                f'border-radius:8px; padding:8px 4px; text-align:center;">'
                f'<span style="color:{zone_text[zone]}; font-weight:700; font-size:0.85em">{zone}</span><br>'
                f'<span style="color:#ccc; font-size:0.75em">{lo}–{hi}{unit}</span><br>'
                f'<span style="color:#b89070; font-size:0.72em">{zlabel}</span>'
            )
            here_label = "<br><b style=\"color:#f5c842; font-size:0.8em\">&#9650; HERE</b>" if active else ""
            html += (
                f'{here_label}'
                f'</div>'
            )
        html += "</div>"

        # Boundary markers
        bv_html = "<div style='display:flex; gap:4px; font-size:0.75em; color:#b89070; margin-bottom:14px;'>"
        for b_val, b_label in boundaries:
            bv_html += f'<span style="flex:1; text-align:center">⬆ <b>{b_val}{unit}</b><br>{b_label}</span>'
        bv_html += "</div>"

        st.markdown(html + bv_html, unsafe_allow_html=True)

    val_pumps = order.syrup_pumps if order else 3
    val_temp  = order.temperature if order else 155
    val_caf   = order.caffeine_mg if order else 150

    bv_gauge(
        "Syrup Pumps", val_pumps,
        boundaries=[(6, "VALID→WARN"), (7, "WARN starts"), (10, "WARN→INVALID"), (11, "INVALID starts")],
        zones=[(0, 6, "VALID", "Normal"), (7, 10, "WARNING", "Sweet"), (11, 15, "INVALID", "Overflow")],
    )

    bv_gauge(
        "Temperature", val_temp,
        boundaries=[(49, "Iced→Normal"), (50, "Normal starts"), (180, "Safe max"), (181, "Plant milk risk")],
        zones=[(32, 49, "WARNING", "Iced"), (50, 180, "VALID", "Normal range"), (181, 212, "WARNING", "Too hot (plant milk)")],
        unit="°F",
    )

    bv_gauge(
        "Caffeine", val_caf,
        boundaries=[(400, "Safe max"), (401, "Warn starts"), (600, "Warn max"), (601, "Danger")],
        zones=[(0, 400, "VALID", "Safe"), (401, 600, "WARNING", "High"), (601, 900, "INVALID", "Danger")],
        unit="mg",
    )

    st.markdown("---")
    st.markdown("#### 🎯 Classic Boundary Test Values to Try")
    bv_examples = {
        "Pumps": ["6 (max valid)", "7 (first warning)", "10 (max warning)", "11 (first invalid)"],
        "Temp °F": ["180 (last safe for plant milk)", "181 (first warning for plant milk)", "50 (iced boundary)", "49 (iced warning)"],
        "Caffeine": ["400mg = 5 shots (max valid)", "401mg ≈ 6 shots (first warning)", "601mg (invalid threshold)"],
    }
    for param, vals in bv_examples.items():
        st.markdown(f"**{param}:** " + " | ".join(f"`{v}`" for v in vals))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — DECISION TABLE
# ══════════════════════════════════════════════════════════════════════════════

with tab_dt:
    st.markdown("### 📋 Decision Table")
    st.markdown(
        "A Decision Table maps combinations of conditions to actions. "
        "Each row is a rule. When all conditions in a row match, the action fires. "
        "Rows highlighted in gold currently match your last order."
    )

    order = st.session_state.last_order
    fired = fired_rule_ids(order) if order else set()

    # Build display DataFrame (strip lambdas)
    display_rows = []
    for row in DECISION_TABLE:
        display_rows.append({
            "Rule":         row["Rule"],
            "Condition A":  row["Condition A"],
            "Condition B":  row["Condition B"],
            "Action":       row["Action"],
            "Technique":    row["Test Technique"],
            "Fired?":       "🔥 YES" if row["Rule"] in fired else "—",
        })

    df = pd.DataFrame(display_rows)

    def highlight_fired(row):
        if row["Fired?"] == "🔥 YES":
            return ["background-color: #3d2e00; color: #ffe066; font-weight: bold"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df.style.apply(highlight_fired, axis=1),
        use_container_width=True,
        height=420,
        hide_index=True,
    )

    if not order:
        st.info("💡 Place an order on the **Barista Counter** tab to highlight the matching decision table rows.")

    with st.expander("📖 How to read a Decision Table"):
        st.markdown("""
        <div style="color:#f5f0e8;">

        - **Each row = one rule.** All conditions in a row must be true for the action to fire.
        - **Conditions** are the input factors (milk type, syrup, temperature, etc.)
        - **Actions** are the outcomes — VALID, WARNING, or INVALID.
        - **Multiple rows can fire simultaneously** — the worst severity wins.
        - **Unfired rows** represent test cases for the sunny-day path.

        The Decision Table is one of the most powerful tools for specifying complex business logic
        because it makes every combination explicit. Missing rows = untested scenarios.

        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — PAIRWISE TESTING
# ══════════════════════════════════════════════════════════════════════════════

with tab_pw:
    st.markdown("### 🔬 Pairwise (All-Pairs) Testing")
    st.markdown(
        "Most bugs are triggered by the **interaction of two parameters**, not by a single parameter alone. "
        "Pairwise testing generates the minimum set of test cases that covers every possible pair of values "
        "at least once — dramatically fewer cases than full factorial."
    )

    bf  = brute_force_count()
    pw  = pairwise_count()
    pct = round((1 - pw / bf) * 100, 1)

    m1, m2, m3 = st.columns(3)
    m1.metric("🔢 Full Factorial", f"{bf:,}", help="All combinations of all EC representative values")
    m2.metric("✂️ Pairwise Cases", pw, help="Minimum cases to cover all 2-way interactions")
    m3.metric("📉 Reduction", f"{pct}%", help="How much smaller the pairwise set is")

    st.markdown("")
    st.info(
        f"**{bf:,} combinations** reduced to **{pw} test cases** — "
        f"covering all 2-way interactions with {pct}% fewer tests."
    )

    with st.expander("🧮 How are these numbers calculated?"):
        st.markdown("""
        **EC representative values used (not full ranges):**

        | Parameter | Representatives | Count |
        |---|---|---|
        | Drink Base | All 8 drinks | 8 |
        | Milk Type | All 8 milks | 8 |
        | Flavor Syrup | All 11 syrups | 11 |
        | Topping | All 7 toppings | 7 |
        | Syrup Pumps | 0, 3, 6, 7, 10, 11, 15 (boundary reps) | 7 |
        | Temperature | 32, 50, 100, 180, 181, 212 (boundary reps) | 6 |
        | Shots | 1, 2, 3, 5, 6 (boundary reps) | 5 |

        Full factorial: **8 × 8 × 11 × 7 × 7 × 6 × 5 = {:,}**

        This first shows why EC partitioning is done *before* pairwise — without EC reps,
        numeric parameters would have up to 181 values each, making full-factorial millions of tests.
        """.format(bf))

    st.divider()

    if st.button("🎲 Generate Pairwise Test Suite", type="primary"):
        with st.spinner("Generating pairwise covering array..."):
            cases = generate_pairwise_cases()
            results = run_all_pairwise(cases)
            st.session_state.pw_cases   = cases
            st.session_state.pw_results = results

    if st.session_state.pw_results:
        cases   = st.session_state.pw_cases
        results = st.session_state.pw_results

        # Summary counts
        pass_count = sum(1 for _, r in results if overall_severity(r) == Severity.PASS)
        warn_count = sum(1 for _, r in results if overall_severity(r) == Severity.WARNING)
        fail_count = sum(1 for _, r in results if overall_severity(r) == Severity.INVALID)

        pc1, pc2, pc3 = st.columns(3)
        pc1.metric("✅ Pass", pass_count)
        pc2.metric("⚠️ Warning", warn_count)
        pc3.metric("❌ Invalid", fail_count)

        # Table
        rows = []
        for i, (order, res) in enumerate(results, 1):
            sev = overall_severity(res)
            rows.append({
                "#":         i,
                "Drink":     order.drink_base,
                "Milk":      order.milk_type,
                "Syrup":     f"{order.syrup} ×{order.syrup_pumps}" if order.syrup != "None" else "None",
                "Topping":   order.topping,
                "Temp°F":    order.temperature,
                "Shots":     order.shots,
                "Status":    severity_icon(sev) + " " + sev.value.upper(),
                "Rules":     ", ".join(r.rule_id for r in res) or "—",
            })

        df_pw = pd.DataFrame(rows)

        def color_status(row):
            if "INVALID" in row["Status"]:
                return ["background-color:#4e0d0d"] * len(row)
            if "WARNING" in row["Status"]:
                return ["background-color:#3d2e00"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df_pw.style.apply(color_status, axis=1),
            use_container_width=True,
            height=500,
            hide_index=True,
        )

        csv = df_pw.to_csv(index=False)
        st.download_button(
            "⬇️ Download Pairwise Test Suite (CSV)",
            data=csv,
            file_name="pairwise_test_suite.csv",
            mime="text/csv",
            type="primary",
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 — TEST CASE LOG
# ══════════════════════════════════════════════════════════════════════════════

with tab_log:
    st.markdown("### 📝 Test Case Log")
    st.markdown("Every order placed across all tabs is recorded here — your personal test report.")

    if not st.session_state.order_log:
        st.info("No orders placed yet. Head to the Barista Counter or Break the Barista to start testing.")
    else:
        df_log = pd.DataFrame(st.session_state.order_log)

        def color_log_status(row):
            s = row.get("Status", "")
            if s == "INVALID":
                return ["background-color:#4e0d0d"] * len(row)
            if s == "WARNING":
                return ["background-color:#3d2e00"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df_log.style.apply(color_log_status, axis=1),
            use_container_width=True,
            height=400,
            hide_index=True,
        )

        lc1, lc2, lc3 = st.columns(3)
        lc1.metric("Total Orders", len(df_log))
        lc2.metric("❌ Invalid", len(df_log[df_log["Status"] == "INVALID"]))
        lc3.metric("⚠️ Warning", len(df_log[df_log["Status"] == "WARNING"]))

        csv = df_log.to_csv(index=False)
        col_dl, col_clr = st.columns([2, 1])
        with col_dl:
            st.download_button(
                "⬇️ Export Test Case Log (CSV)",
                data=csv,
                file_name="barista_test_log.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with col_clr:
            if st.button("🗑️ Clear Log", use_container_width=True):
                st.session_state.order_log = []
                st.rerun()
