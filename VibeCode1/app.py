"""
Coffee Shop Chaos — Barista Basics
===================================
A Streamlit app that teaches software testing techniques through
the chaos of a coffee shop counter.

Run with:  streamlit run app.py
"""

import itertools
import random
from datetime import datetime

import streamlit as st
import pandas as pd

from menu import (
    DRINK_BASES, DRINK_EMOJIS, MILK_TYPES, MILK_EMOJIS,
    FLAVOR_SYRUPS, SYRUP_EMOJIS, TOPPINGS, TOPPING_EMOJIS,
    DRINK_RECIPES, PLANT_MILKS, ACID_SYRUPS, CAFFEINE_PER_SHOT, HALL_OF_SHAME,
)
from rules import (
    Order, evaluate_order, overall_severity,
    fired_rule_ids, Severity, TestType, DECISION_TABLE,
)
from pairwise import (
    generate_pairwise_cases, brute_force_count,
    pairwise_count, run_all_pairwise,
    PAIRWISE_PARAMETERS,
)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Coffee Shop Chaos — Barista Basics",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
        "cf_covered_rules": set(),
        "df_var_seen": {
            "drink_base": set(), "milk_type": set(), "syrup": set(),
            "syrup_pumps": set(), "topping": set(), "temperature": set(), "shots": set(),
        },
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

def qa_pill(test_type: TestType, rule_id: str) -> str:
    return f"`{test_type.value}` `Rule {rule_id}`"

def render_results(results, qa_mode: bool):
    """Render rule results as Streamlit expanders with optional QA labels."""
    if not results:
        st.success("☕ All checks passed. The barista approves. Beautiful drink.")
        return
    for r in results:
        if r.severity == Severity.INVALID:
            with st.expander(f"❌ {r.title}", expanded=True):
                if qa_mode:
                    st.markdown(qa_pill(r.test_type, r.rule_id))
                st.markdown(f"**{r.description}**")
                st.markdown(r.detail)
        elif r.severity == Severity.WARNING:
            with st.expander(f"⚠️ {r.title}", expanded=True):
                if qa_mode:
                    st.markdown(qa_pill(r.test_type, r.rule_id))
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
    for r in results:
        st.session_state.cf_covered_rules.add(r.rule_id)
    _dv = st.session_state.df_var_seen
    _dv["drink_base"].add(order.drink_base)
    _dv["milk_type"].add(order.milk_type)
    _dv["syrup"].add(order.syrup)
    _dv["syrup_pumps"].add(order.syrup_pumps)
    _dv["topping"].add(order.topping)
    _dv["temperature"].add(order.temperature)
    _dv["shots"].add(order.shots)


# ── State transition helper ───────────────────────────────────────────────────

# Maps each rule to the stations it involves (used to color state nodes).
_ST_RULE_STATIONS = {
    "R1":  {"milk", "syrup"},
    "R2":  {"milk", "specs"},
    "R3a": {"syrup"},
    "R3b": {"syrup"},
    "R4a": {"specs"},
    "R4b": {"specs"},
    "R5a": {"drink", "specs"},
    "R5b": {"topping", "specs"},
    "R6a": {"drink", "milk"},
    "R6b": {"drink", "specs"},
    "R6c": {"drink", "milk"},
}


def _sm_substates(drink_base, milk_type, syrup, syrup_pumps, topping, temperature, shots):
    """
    Classify each order parameter into a named substate and detect
    conflicting state transitions.  Returns (substates_dict, invalid_list, warning_list).
    """
    caffeine = shots * CAFFEINE_PER_SHOT

    # ── Drink substate ────────────────────────────────────────────────────────
    if drink_base in ("Espresso", "Americano"):
        d_sub, d_label = "no_milk_drink",  "No-milk family"
    elif drink_base == "Affogato":
        d_sub, d_label = "affogato",        "Ice-cream drink"
    else:
        d_sub, d_label = "milk_required",   "Milk-required drink"

    # ── Milk substate ─────────────────────────────────────────────────────────
    if milk_type == "None":
        m_sub, m_label = "no_milk", "No milk selected"
    elif milk_type in PLANT_MILKS:
        m_sub, m_label = "plant",   "Plant-based milk"
    else:
        m_sub, m_label = "dairy",   "Dairy / Half&Half"

    # ── Syrup substate ────────────────────────────────────────────────────────
    if syrup == "None" or syrup_pumps == 0:
        s_sub, s_label = "no_syrup",  "No syrup"
    elif syrup in ACID_SYRUPS:
        s_sub, s_label = "acid",      f"Acidic syrup ({syrup})"
    elif syrup_pumps > 10:
        s_sub, s_label = "overflow",  f"Pump overflow ({syrup_pumps} pumps)"
    elif syrup_pumps > 6:
        s_sub, s_label = "sweet",     f"Sweet zone ({syrup_pumps} pumps)"
    else:
        s_sub, s_label = "safe",      f"Normal ({syrup_pumps} pumps)"

    # ── Topping substate ──────────────────────────────────────────────────────
    if topping == "Foam":
        t_sub, t_label = "foam", "Foam topping"
    elif topping == "None":
        t_sub, t_label = "none", "No topping"
    else:
        t_sub, t_label = "safe", "Standard topping"

    # ── Specs substate ────────────────────────────────────────────────────────
    if temperature < 50:
        p_sub = "iced"
    elif temperature > 180:
        p_sub = "very_hot"
    else:
        p_sub = "normal"

    substates = {
        "drink":   (d_sub, d_label, drink_base),
        "milk":    (m_sub, m_label, milk_type),
        "syrup":   (s_sub, s_label, f"{syrup} ×{syrup_pumps}" if syrup != "None" else "None"),
        "topping": (t_sub, t_label, topping),
        "specs":   (p_sub, f"{temperature}°F / {shots} shots ({caffeine}mg)", f"{temperature}°F · {shots} shots"),
    }

    # ── Transition conflict detection ─────────────────────────────────────────
    invalids = []
    sm_warnings = []

    if s_sub == "acid" and m_sub != "no_milk":
        invalids.append({
            "rule": "R1",
            "transition": "MILK_ADDED → ACID_SYRUP_ADDED",
            "stations":   "Milk Station → Syrup Rack",
            "desc":       "Acid syrup combined with milk creates a curdling reaction.",
            "st_case":    "Test: acid syrup + any milk → INVALID transition",
        })
    if m_sub == "plant" and p_sub == "very_hot":
        sm_warnings.append({
            "rule": "R2",
            "transition": "PLANT_MILK_SET → TEMP_ABOVE_180",
            "stations":   "Milk Station → Controls",
            "desc":       "Plant milk + temperature > 180°F causes heat-shock separation.",
            "st_case":    "Test: plant milk + temp > 180°F → WARNING transition",
        })
    if s_sub == "overflow":
        invalids.append({
            "rule": "R3b",
            "transition": "NORMAL_PUMP → PUMP_OVERFLOW",
            "stations":   "Syrup Rack",
            "desc":       f"Pump count {syrup_pumps} crossed the 10→11 boundary into INVALID zone.",
            "st_case":    "Test: pump count > 10 → INVALID, regardless of syrup type",
        })
    elif s_sub == "sweet":
        sm_warnings.append({
            "rule": "R3a",
            "transition": "NORMAL_PUMP → SWEET_ZONE",
            "stations":   "Syrup Rack",
            "desc":       f"Pump count {syrup_pumps} crossed the 6→7 boundary into WARNING zone.",
            "st_case":    "Test: pump count 7–10 → WARNING transition",
        })
    if caffeine > 600:
        invalids.append({
            "rule": "R4b",
            "transition": "SAFE_CAFFEINE → CAFFEINE_CRITICAL",
            "stations":   "Controls",
            "desc":       f"{caffeine}mg exceeds the 600mg → INVALID threshold.",
            "st_case":    "Test: shots causing >600mg caffeine → INVALID",
        })
    elif caffeine > 400:
        sm_warnings.append({
            "rule": "R4a",
            "transition": "SAFE_CAFFEINE → CAFFEINE_WARNING",
            "stations":   "Controls",
            "desc":       f"{caffeine}mg is in the 401–600mg WARNING zone.",
            "st_case":    "Test: shots causing 401–600mg caffeine → WARNING",
        })
    if d_sub == "affogato" and temperature > 140:
        sm_warnings.append({
            "rule": "R5a",
            "transition": "AFFOGATO_DRINK → TEMP_ABOVE_140",
            "stations":   "Espresso Machine → Controls",
            "desc":       f"Affogato at {temperature}°F — espresso will incinerate the ice cream.",
            "st_case":    "Test: Affogato + temp > 140°F → WARNING transition",
        })
    if t_sub == "foam" and p_sub == "iced":
        sm_warnings.append({
            "rule": "R5b",
            "transition": "FOAM_TOPPING → ICED_TEMP",
            "stations":   "Topping Bar → Controls",
            "desc":       f"Foam topping + {temperature}°F — foam collapses on iced drinks.",
            "st_case":    "Test: Foam + temp < 50°F → WARNING transition",
        })
    if d_sub == "milk_required" and m_sub == "no_milk":
        invalids.append({
            "rule": "R6a",
            "transition": "MILK_REQUIRED_DRINK → NO_MILK_SELECTED",
            "stations":   "Espresso Machine → Milk Station",
            "desc":       f"{drink_base} requires milk; NO_MILK state is invalid for this drink.",
            "st_case":    f"Test: {drink_base} + milk=None → INVALID transition",
        })
    if drink_base == "Flat White" and shots < 2:
        sm_warnings.append({
            "rule": "R6b",
            "transition": "FLAT_WHITE_DRINK → INSUFFICIENT_SHOTS",
            "stations":   "Espresso Machine → Controls",
            "desc":       f"Flat White with {shots} shot(s) violates the 2-shot recipe minimum.",
            "st_case":    "Test: Flat White + 1 shot → WARNING transition",
        })
    if d_sub == "no_milk_drink" and m_sub != "no_milk":
        sm_warnings.append({
            "rule": "R6c",
            "transition": "NO_MILK_DRINK → MILK_ADDED",
            "stations":   "Espresso Machine → Milk Station",
            "desc":       f"{drink_base} is traditionally served without milk — non-canonical state.",
            "st_case":    f"Test: {drink_base} + any milk → WARNING transition",
        })

    return substates, invalids, sm_warnings


# ── Counter station widget ────────────────────────────────────────────────────

def station_header(icon: str, title: str, step: str, desc: str):
    st.markdown(f"### {icon} {title}")
    st.caption(f"**{step}** — {desc}")


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
    msg = f"{coffee}  {icons[sev.value]}"
    if sev == Severity.PASS:
        st.success(msg)
    elif sev == Severity.WARNING:
        st.warning(msg)
    else:
        st.error(msg)

    # ── Two-column: ticket + rule results ─────────────────────────────────────
    d_left, d_right = st.columns([1, 2])

    with d_left:
        pumps_str = f" x{order.syrup_pumps}" if order.syrup != "None" else ""
        with st.container(border=True):
            st.markdown("**ORDER TICKET**")
            st.divider()
            st.markdown(f"**Drink:** {DRINK_EMOJIS[order.drink_base]} {order.drink_base}")
            st.markdown(f"**Milk:** {MILK_EMOJIS[order.milk_type]} {order.milk_type}")
            st.markdown(f"**Syrup:** {SYRUP_EMOJIS[order.syrup]} {order.syrup}{pumps_str}")
            st.markdown(f"**Topping:** {TOPPING_EMOJIS[order.topping]} {order.topping}")
            st.markdown(f"**Temp:** {order.temperature}°F")
            st.markdown(f"**Shots:** {order.shots}")
            st.markdown(f"**Caffeine:** {order.caffeine_mg}mg")
            st.divider()
            st.markdown(f"**Status:** {severity_icon(sev)} {sev.value.upper()}")

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
        with st.container(border=True):
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
        with st.container(border=True):
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
        with st.container(border=True):
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
        with st.container(border=True):
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
        with st.container(border=True):
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

    # ── State Machine View ────────────────────────────────────────────────────
    with st.expander("🔀 State Machine View — Order Compatibility Tracker"):
        st.markdown(
            "State transition testing models a system as a series of **states** connected by "
            "**transitions**. A transition is invalid when combining two individually-valid states "
            "creates a conflict. The nodes below show your current order as a state machine path — "
            "red means an INVALID transition was detected, amber means a WARNING transition."
        )

        _sm_sub, _sm_inv, _sm_warn = _sm_substates(
            drink_base, milk_type, syrup, syrup_pumps, topping, temperature, shots
        )

        # Determine which station keys are touched by detected conflicts
        _inv_stations  = set()
        _warn_stations = set()
        for _t in _sm_inv:
            _inv_stations.update(_ST_RULE_STATIONS.get(_t["rule"], set()))
        for _t in _sm_warn:
            _warn_stations.update(_ST_RULE_STATIONS.get(_t["rule"], set()))

        _sm_node_defs = [
            ("🔩", "Espresso\nMachine", "drink"),
            ("🥛", "Milk\nStation",     "milk"),
            ("🍯", "Syrup\nRack",       "syrup"),
            ("🧁", "Topping\nBar",      "topping"),
            ("⚙️",  "Controls",         "specs"),
        ]

        _sm_cols = st.columns(6)
        for _ci, (_icon, _name, _key) in enumerate(_sm_node_defs):
            _, _lbl, _val = _sm_sub[_key]
            _body = f"**{_icon} {_name}**\n\n`{_val}`\n\n*{_lbl}*"
            with _sm_cols[_ci]:
                if _key in _inv_stations:
                    st.error(_body)
                elif _key in _warn_stations:
                    st.warning(_body)
                else:
                    st.success(_body)

        with _sm_cols[5]:
            if _sm_inv:
                st.error("**⛔ OUTCOME**\n\n`INVALID`\n\n*Conflict detected*")
            elif _sm_warn:
                st.warning("**⚠️ OUTCOME**\n\n`WARNING`\n\n*Tension detected*")
            else:
                st.success("**✅ OUTCOME**\n\n`VALID`\n\n*All compatible*")

        st.markdown("")

        if _sm_inv or _sm_warn:
            st.markdown("#### Detected Transition Issues")
            for _t in _sm_inv:
                st.error(
                    f"**❌ `{_t['transition']}`** — Rule {_t['rule']}\n\n"
                    f"*Stations: {_t['stations']}*\n\n"
                    f"{_t['desc']}\n\n"
                    f"🧪 {_t['st_case']}"
                )
            for _t in _sm_warn:
                st.warning(
                    f"**⚠️ `{_t['transition']}`** — Rule {_t['rule']}\n\n"
                    f"*Stations: {_t['stations']}*\n\n"
                    f"{_t['desc']}\n\n"
                    f"🧪 {_t['st_case']}"
                )
        else:
            st.success("✅ All state transitions are compatible — no conflicts in the current order.")

        with st.expander("💡 About State Transition Testing"):
            st.markdown("""
            **State Transition Testing** models a system as a finite state machine:

            - **States** represent the system's current condition (e.g. `PLANT_MILK_SET`, `ACID_SYRUP_ADDED`)
            - **Transitions** are inputs that move the system from one state to another
            - **Invalid transitions** occur when a valid state + a valid input creates an incompatible combined state
            - **Sneak paths** are transitions that should be blocked but pass through unchecked

            A key insight: each ingredient selection may be *individually valid*, but **combining two valid
            states can produce an invalid result**. This is distinct from boundary value analysis
            (single-parameter edges) and equivalence class testing (single-parameter partitions).
            State transition testing asks: *"What happens when this state meets that state?"*

            A complete state transition test suite covers:
            - Every valid transition (happy path through all stations)
            - Every invalid transition (the conflicts shown above)
            - Every state reachable from all possible transition sequences (state coverage)
            """)

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
            with st.container(border=True):
                st.markdown("**📋 CUSTOMER ORDER TICKET**")
                st.divider()
                st.markdown(f"**Drink:** {DRINK_EMOJIS[o.drink_base]} {o.drink_base}")
                st.markdown(f"**Milk:** {MILK_EMOJIS[o.milk_type]} {o.milk_type}")
                st.markdown(f"**Syrup:** {SYRUP_EMOJIS[o.syrup]} {o.syrup}{pumps_str}")
                st.markdown(f"**Topping:** {TOPPING_EMOJIS[o.topping]} {o.topping}")
                st.markdown(f"**Temp:** {o.temperature}°F")
                st.markdown(f"**Shots:** {o.shots} ({o.caffeine_mg}mg caffeine)")

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
            with st.container(border=True):
                st.markdown(f"#### {entry['name']}")
                st.caption(entry['subtitle'])
                st.markdown(entry['story'])

        with sh_right:
            pumps_str = f" ×{o.syrup_pumps}" if o.syrup != "None" else ""
            with st.container(border=True):
                st.markdown(f"**{DRINK_EMOJIS[o.drink_base]} {o.drink_base}**")
                st.caption(
                    f"{MILK_EMOJIS[o.milk_type]} {o.milk_type} | "
                    f"{SYRUP_EMOJIS[o.syrup]} {o.syrup}{pumps_str}"
                )
                st.caption(
                    f"{TOPPING_EMOJIS[o.topping]} {o.topping} | "
                    f"{o.temperature}°F | {o.shots} shot(s)"
                )
                st.markdown(f"**Status: {severity_icon(sev)} {sev.value.upper()}**")
            st.markdown("")
            for r in results:
                if qa_mode:
                    st.markdown(f"`{r.test_type.value}` **{r.title}**")
                else:
                    icon = "❌" if r.severity == Severity.INVALID else "⚠️"
                    st.markdown(f"{icon} **{r.title}**")
                st.markdown(r.detail)

            if st.button(f"Load to Counter ↗", key=f"load_{entry['name']}"):
                st.session_state.shame_loaded = entry["order"]
                st.switch_page  # not available in all versions — use workaround below

            # State transition annotation
            _, _hs_inv, _hs_warn = _sm_substates(
                o.drink_base, o.milk_type, o.syrup, o.syrup_pumps,
                o.topping, o.temperature, o.shots,
            )
            if _hs_inv or _hs_warn:
                _hs_key = (_hs_inv + _hs_warn)[0]
                _hs_icon = "❌" if _hs_inv else "⚠️"
                st.markdown("---")
                st.markdown("**🔀 State Transition Catch:**")
                st.caption(
                    f"{_hs_icon} `{_hs_key['transition']}` — Rule {_hs_key['rule']}"
                )
                st.caption(f"🧪 {_hs_key['st_case']}")

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
            with cols[i]:
                current_note = "\n\n**← current**" if active else ""
                content = f"**{class_name}**\n\n{range_label}{current_note}"
                if zone == "VALID":
                    st.success(content)
                elif zone == "WARNING":
                    st.warning(content)
                else:
                    st.error(content)
        st.markdown("")

    if not order:
        st.info("💡 Place an order on the **Barista Counter** tab to highlight your current equivalence classes.")

    # ── Data Flow: Def-Use Paths ───────────────────────────────────────────────
    st.divider()
    st.markdown("### 📡 Data Flow: Def-Use Paths")
    st.markdown(
        "Data flow testing tracks each variable from its **definition** (where it is assigned) "
        "to every **use** (each rule or calculation that reads it). "
        "A **def-use pair (DU-pair)** is one such path. "
        "The *All-Uses* criterion requires every DU-pair to be exercised — "
        "every variable must reach every downstream rule at least once across the test suite."
    )

    _DF_VARS = [
        # (variable, station#, station name, use type, downstream rule IDs)
        ("drink_base",  "1", "Espresso Machine", "p-use",          ["R5a", "R6a", "R6b", "R6c"]),
        ("milk_type",   "2", "Milk Station",     "p-use",          ["R1",  "R2",  "R6a", "R6c"]),
        ("syrup",       "3", "Syrup Rack",       "p-use",          ["R1",  "R3a", "R3b"]),
        ("syrup_pumps", "3", "Pump Slider",      "p-use",          ["R3a", "R3b"]),
        ("topping",     "4", "Topping Bar",      "p-use",          ["R5b"]),
        ("temperature", "5", "Temp Slider",      "p-use",          ["R2",  "R5a", "R5b"]),
        ("shots",       "5", "Shots → caffeine", "c-use + p-use",  ["R4a", "R4b", "R6b"]),
    ]

    _df_covered    = st.session_state.cf_covered_rules
    _df_table_rows = []
    for _v, _stn, _stn_name, _use_type, _rules in _DF_VARS:
        _cov  = [r for r in _rules if r in _df_covered]
        _n, _c = len(_rules), len(_cov)
        _pct  = int(_c / _n * 100)
        _df_table_rows.append({
            "Variable":      _v,
            "DEF — Station": f"Stn {_stn} ({_stn_name})",
            "USE → Rules":   ", ".join(_rules),
            "Use Type":      _use_type,
            "DU-Pairs":      _n,
            "Covered":       _c,
            "Coverage":      f"{_pct}%",
        })

    def _style_du(row):
        pct = int(row["Coverage"].replace("%", ""))
        if pct == 100:
            return ["background-color:#d1e7dd"] * len(row)
        if pct > 0:
            return ["background-color:#fff3cd"] * len(row)
        return ["background-color:#f8d7da"] * len(row)

    st.dataframe(
        pd.DataFrame(_df_table_rows).style.apply(_style_du, axis=1),
        use_container_width=True,
        hide_index=True,
        height=280,
    )

    _total_du   = sum(len(r[-1]) for r in _DF_VARS)
    _covered_du = sum(1 for r in _DF_VARS for rule in r[-1] if rule in _df_covered)
    _du_pct     = int(_covered_du / _total_du * 100) if _total_du else 0

    st.progress(
        _du_pct / 100,
        text=f"All-Uses DU-Pair Coverage: {_covered_du}/{_total_du} pairs exercised ({_du_pct}%)",
    )

    if not st.session_state.order_log:
        st.info("💡 Place orders on the Barista Counter to start tracking DU-pair coverage.")

    with st.expander("💡 About Data Flow Testing"):
        st.markdown("""
        **Data flow testing** maps every variable through its full lifecycle:

        - **DEF** — where the variable is assigned (e.g., `milk_type` is defined when the Milk Station widget is set)
        - **USE** — where the value is read: a **p-use** is in a predicate (`if milk_type in PLANT_MILKS`)
          and a **c-use** is in a calculation (`caffeine_mg = shots × 75`)
        - **DU-pair** — one specific path from a single DEF to a single USE

        **Coverage criteria (weakest → strongest):**
        - *All-Defs* — every variable reaches at least one use (trivially met after one order)
        - *All-Uses* — every variable reaches every downstream use (tracked above)
        - *All-DU-Paths* — every path from each DEF to each USE (often exponential; impractical)

        The table tracks the **All-Uses** criterion. `milk_type` has four downstream rules
        (R1, R2, R6a, R6c). Achieving 100% DU-pair coverage for `milk_type` requires orders
        that exercise all four rules — which means testing multiple distinct values of `milk_type`,
        not just one representative per session.

        This is what separates data flow from equivalence class testing: EC picks one value
        per partition; data flow testing asks whether every **downstream rule** that reads the
        variable has been exercised, regardless of which specific value triggered it.
        """)


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
        zone_cols = st.columns(len(zones))
        for i, (lo, hi, zone, zlabel) in enumerate(zones):
            active = lo <= value <= hi
            with zone_cols[i]:
                here = "\n\n**▲ HERE**" if active else ""
                content = f"**{zone}**\n\n`{lo}–{hi}{unit}`\n\n{zlabel}{here}"
                if zone == "VALID":
                    st.success(content)
                elif zone == "WARNING":
                    st.warning(content)
                else:
                    st.error(content)

        bv_cols = st.columns(len(boundaries))
        for i, (b_val, b_label) in enumerate(boundaries):
            with bv_cols[i]:
                st.caption(f"⬆ **{b_val}{unit}** | {b_label}")
        st.markdown("")

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
            return ["background-color: #fff3cd; color: #664d03; font-weight: bold"] * len(row)
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
        - **Each row = one rule.** All conditions in a row must be true for the action to fire.
        - **Conditions** are the input factors (milk type, syrup, temperature, etc.)
        - **Actions** are the outcomes — VALID, WARNING, or INVALID.
        - **Multiple rows can fire simultaneously** — the worst severity wins.
        - **Unfired rows** represent test cases for the sunny-day path.

        The Decision Table is one of the most powerful tools for specifying complex business logic
        because it makes every combination explicit. Missing rows = untested scenarios.
        """)

    # ── Control Flow: Branch Coverage ─────────────────────────────────────────
    st.divider()
    st.markdown("### 🔀 Control Flow: Branch Coverage")
    st.markdown(
        "Control flow testing asks whether your test suite has traversed **every decision branch** "
        "in the code. Each business rule is a branch — full branch coverage requires triggering "
        "every rule at least once across your orders. The table below tracks your **session-wide** "
        "coverage, accumulating across all orders placed on any tab."
    )

    _cf_all_ids   = [row["Rule"] for row in DECISION_TABLE]
    _cf_covered   = st.session_state.cf_covered_rules
    _cf_num       = len(set(_cf_all_ids).intersection(_cf_covered))
    _cf_total     = len(_cf_all_ids)
    _cf_pct       = int(_cf_num / _cf_total * 100) if _cf_total else 0

    st.progress(
        _cf_pct / 100,
        text=f"Session Branch Coverage: {_cf_num} / {_cf_total} branches triggered ({_cf_pct}%)",
    )

    if _cf_pct == 100:
        st.success("🏆 100% Branch Coverage achieved! Every rule has been triggered at least once.")
    elif not st.session_state.order_log:
        st.info("💡 Place orders on the Barista Counter or Break the Barista to start accumulating branch coverage.")

    # Determine unreachable branches dynamically from UI slider ceiling
    _MAX_SHOTS_CAFFEINE = 6 * CAFFEINE_PER_SHOT  # slider max is 6 shots
    _unreachable = set()
    if _MAX_SHOTS_CAFFEINE <= 600:
        _unreachable.add("R4b")   # >600mg threshold is above the UI ceiling

    _branch_hints = {
        "R1":  "Lemon/Citrus syrup + any milk",
        "R2":  "Oat / Almond / Soy / Coconut milk + temperature > 180°F",
        "R3a": "Any syrup + 7–10 pumps",
        "R3b": "Any syrup + 11–15 pumps",
        "R4a": "6 shots → 450mg (sits in the 401–600mg warning zone)",
        "R4b": f"UI ceiling is {_MAX_SHOTS_CAFFEINE}mg — never reaches the 601mg threshold",
        "R5a": "Affogato + temperature > 140°F",
        "R5b": "Foam topping + temperature < 50°F",
        "R6a": "Latte / Cappuccino / Mocha / Macchiato / Flat White + milk = None",
        "R6b": "Flat White + 1 shot",
        "R6c": "Espresso or Americano + any milk",
    }

    branch_rows = []
    for _cf_row in DECISION_TABLE:
        _rid  = _cf_row["Rule"]
        _hit  = _rid in _cf_covered
        _dead = _rid in _unreachable
        if _dead:
            status = "🚫 Unreachable"
            hint   = f"Unreachable — {_branch_hints.get(_rid, '—')}"
        elif _hit:
            status = "✅ Covered"
            hint   = "Covered"
        else:
            status = "❌ Not Hit"
            hint   = f"Try: {_branch_hints.get(_rid, '—')}"
        branch_rows.append({
            "Hit":                    status,
            "Rule":                   _rid,
            "Condition A":            _cf_row["Condition A"],
            "Condition B":            _cf_row["Condition B"],
            "How to trigger / Status": hint,
        })

    st.dataframe(
        pd.DataFrame(branch_rows),
        use_container_width=True,
        hide_index=True,
        height=400,
    )

    with st.expander("💡 About Control Flow Testing"):
        st.markdown("""
        **Control flow testing** analyzes the logical paths through source code:

        - **Branch coverage** — every decision point has been taken both TRUE (fires) and FALSE
          (passes through) at least once across the test suite
        - **Statement coverage** — every line of code has been executed
        - **Path coverage** — every unique end-to-end path tested (often exponential; impractical)

        In this rule engine, each check function is a decision point. Branch coverage asks:
        *"Have I given the system an order that fires this rule, and an order that doesn't?"*

        The 🚫 **Unreachable Branch** (R4b) is a real structural finding — the UI caps shots at 6
        (max 450mg), so the >600mg INVALID threshold can never be reached from the counter.
        A control flow analysis exposed a gap between the specification (the rule exists) and the
        implementation (the UI never exercises it). This is precisely the kind of dead code or
        configuration mismatch that structural testing is designed to uncover.
        """)


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
    st.markdown("### 🔽 From 85 Million to 99 — The Reduction Story")
    st.markdown(
        "Three techniques stack to make the test suite feasible. "
        "Each stage eliminates redundancy while preserving full bug-detection power."
    )

    _raw_counts = {
        "Drink Base":   8,
        "Milk Type":    8,
        "Flavor Syrup": 11,
        "Topping":      7,
        "Syrup Pumps":  16,
        "Temperature":  181,
        "Shots":        6,
    }
    _ec_counts = {
        "Drink Base":   8,
        "Milk Type":    8,
        "Flavor Syrup": 11,
        "Topping":      7,
        "Syrup Pumps":  7,
        "Temperature":  6,
        "Shots":        5,
    }
    _raw_total = 1
    for v in _raw_counts.values():
        _raw_total *= v

    _total_pairs = sum(
        len(a) * len(b)
        for a, b in itertools.combinations(PAIRWISE_PARAMETERS.values(), 2)
    )

    _f1, _f2, _f3 = st.columns(3)
    with _f1:
        with st.container(border=True):
            st.markdown("#### ① Raw Input Space")
            st.metric("Combinations", f"{_raw_total:,}")
            st.caption(
                "Full cartesian product of every integer value across all parameter ranges. "
                "Temperature alone spans 181 values (32–212°F); pumps span 16 (0–15)."
            )
    with _f2:
        with st.container(border=True):
            st.markdown("#### ② Equivalence Class Partitioning")
            st.metric("Combinations", f"{bf:,}", delta=f"-{_raw_total - bf:,}", delta_color="inverse")
            st.caption(
                "Numeric parameters collapsed to boundary-representative values. "
                "181 temperatures → 6 reps; 16 pump values → 7 reps."
            )
    with _f3:
        with st.container(border=True):
            st.markdown("#### ③ Pairwise Selection")
            st.metric("Test Cases", str(pw), delta=f"-{bf - pw:,}", delta_color="inverse")
            st.caption(
                f"Minimum set covering all {_total_pairs:,} unique 2-way parameter-value pairs "
                f"across the 7 parameters."
            )

    with st.expander("📐 Per-parameter breakdown"):
        _ec_reps_desc = {
            "Drink Base":   "All 8 drinks (discrete, no reduction)",
            "Milk Type":    "All 8 milks (discrete, no reduction)",
            "Flavor Syrup": "All 11 syrups (discrete, no reduction)",
            "Topping":      "All 7 toppings (discrete, no reduction)",
            "Syrup Pumps":  "0, 3, 6, 7, 10, 11, 15 — one per BV zone + boundaries",
            "Temperature":  "32, 50, 100, 180, 181, 212 — iced / normal / plant-milk boundaries",
            "Shots":        "1, 2, 3, 5, 6 — min, flat-white min, mid, caffeine zones",
        }
        _breakdown_rows = []
        for _param in _raw_counts:
            _raw_n = _raw_counts[_param]
            _ec_n  = _ec_counts[_param]
            _breakdown_rows.append({
                "Parameter":          _param,
                "Raw Values":         _raw_n,
                "EC Reps":            _ec_n,
                "Reduction":          f"÷{_raw_n // _ec_n}" if _ec_n < _raw_n else "no change",
                "EC Representatives": _ec_reps_desc[_param],
            })
        st.dataframe(pd.DataFrame(_breakdown_rows), hide_index=True, use_container_width=True)

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
                return ["background-color: #f8d7da"] * len(row)
            if "WARNING" in row["Status"]:
                return ["background-color: #fff3cd"] * len(row)
            return ["background-color: #d1e7dd"] * len(row)

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

        # ── Pair coverage matrix ──────────────────────────────────────────────
        st.divider()
        st.markdown("#### 🔲 Pair Coverage Matrix")
        st.markdown(
            "Each cell shows **covered / possible** unique value-pairs for that parameter combination "
            "across the generated test suite. Pairwise guarantees every cell reaches 100%."
        )

        _param_names = ["Drink", "Milk", "Syrup", "Topping", "Pumps", "Temp °F", "Shots"]
        _param_attrs = ["drink_base", "milk_type", "syrup", "topping", "syrup_pumps", "temperature", "shots"]
        _n = len(_param_names)

        _unique_vals = [set(getattr(c, attr) for c in cases) for attr in _param_attrs]

        _matrix_rows = []
        for _i in range(_n):
            _row = {"Parameter": _param_names[_i]}
            for _j in range(_n):
                if _i == _j:
                    _row[_param_names[_j]] = "—"
                else:
                    _possible = len(_unique_vals[_i]) * len(_unique_vals[_j])
                    _covered  = len(set(
                        (getattr(c, _param_attrs[_i]), getattr(c, _param_attrs[_j]))
                        for c in cases
                    ))
                    _row[_param_names[_j]] = f"{_covered}/{_possible}"
            _matrix_rows.append(_row)

        df_matrix = pd.DataFrame(_matrix_rows).set_index("Parameter")

        def _style_matrix_row(row):
            styles = []
            for val in row:
                if val == "—":
                    styles.append("background-color: #e9ecef; color: #6c757d")
                elif "/" in str(val):
                    a, b = str(val).split("/")
                    styles.append("background-color: #d1e7dd" if a == b else "background-color: #fff3cd")
                else:
                    styles.append("")
            return styles

        st.dataframe(
            df_matrix.style.apply(_style_matrix_row, axis=1),
            use_container_width=True,
        )

        # ── Coverage accumulation chart ───────────────────────────────────────
        st.divider()
        st.markdown("#### 📈 Pair Coverage Accumulation")
        st.markdown(
            "Cumulative unique value-pairs covered as each test case is added in order. "
            "The steep early slope shows that the first few cases cover the most ground — "
            "a key property of pairwise algorithms."
        )

        _covered_set = set()
        _accum = []
        for _case in cases:
            for _i in range(_n):
                for _j in range(_i + 1, _n):
                    _covered_set.add((
                        _param_names[_i], getattr(_case, _param_attrs[_i]),
                        _param_names[_j], getattr(_case, _param_attrs[_j]),
                    ))
            _accum.append(len(_covered_set))

        _total_possible_pairs = sum(
            len(_unique_vals[_i]) * len(_unique_vals[_j])
            for _i in range(_n)
            for _j in range(_i + 1, _n)
        )

        df_accum = pd.DataFrame({
            "Test Case #":          list(range(1, len(cases) + 1)),
            "Pairs Covered":        _accum,
            "Total Possible Pairs": [_total_possible_pairs] * len(cases),
        }).set_index("Test Case #")

        st.line_chart(df_accum)

        _cases_for_100 = next(
            (i + 1 for i, v in enumerate(_accum) if v >= _total_possible_pairs),
            len(cases),
        )
        st.caption(
            f"100% pair coverage reached after **{_cases_for_100}** of {len(cases)} test cases. "
            f"The remaining {len(cases) - _cases_for_100} cases provide redundant pair coverage, "
            "ensuring robustness even if a small subset of tests is skipped."
        )

        # ── Branch coverage from pairwise suite ───────────────────────────────
        st.divider()
        st.markdown("#### 🔀 Branch Coverage from This Pairwise Suite")
        st.markdown(
            "Control flow testing asks: does your test suite hit every branch? "
            "Here's what the generated pairwise cases achieve structurally:"
        )
        _pw_rule_ids = [row["Rule"] for row in DECISION_TABLE]
        _pw_covered  = set()
        for _, _pw_res in results:
            for _pw_r in _pw_res:
                _pw_covered.add(_pw_r.rule_id)
        _pw_n   = len(set(_pw_rule_ids).intersection(_pw_covered))
        _pw_pct = int(_pw_n / len(_pw_rule_ids) * 100)
        _pw_missing = sorted(set(_pw_rule_ids) - _pw_covered)

        pw_bc1, pw_bc2, pw_bc3 = st.columns(3)
        pw_bc1.metric("Branch Coverage", f"{_pw_n}/{len(_pw_rule_ids)}")
        pw_bc2.metric("Coverage %", f"{_pw_pct}%")
        pw_bc3.metric("Uncovered Branches", len(_pw_missing))

        if _pw_missing:
            st.warning(
                f"Branches not triggered by the pairwise suite: **{', '.join(_pw_missing)}**. "
                f"Pairwise optimizes for 2-way interaction coverage, not structural branch coverage. "
                f"Targeted single-parameter boundary orders are needed to reach those branches."
            )
        else:
            st.success("The pairwise suite achieves 100% branch coverage as a side effect of thorough pair coverage.")

        with st.expander("💡 Pairwise vs. Branch Coverage"):
            st.markdown("""
            Pairwise testing targets **interaction coverage** (every pair of values appears at least once),
            not structural branch coverage. However, because it systematically exercises edge values
            across all parameter combinations, it frequently achieves high branch coverage as a side effect.

            When pairwise misses branches, it's usually for rules that require a **specific
            single-parameter extreme** the algorithm didn't happen to select. A small set of
            hand-picked boundary tests fills those gaps — and now you know exactly which ones
            to add, thanks to the coverage table above.

            **Key insight:** branch coverage and pairwise coverage are complementary.
            A robust test suite needs both structural coverage (every branch hit) and
            interaction coverage (every pair exercised).
            """)


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
                return ["background-color: #f8d7da"] * len(row)
            if s == "WARNING":
                return ["background-color: #fff3cd"] * len(row)
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
                st.session_state.cf_covered_rules = set()
                st.session_state.df_var_seen = {k: set() for k in st.session_state.df_var_seen}
                st.rerun()

        # ── Data Flow: Variable Value Coverage ────────────────────────────────
        with st.expander("📡 Data Flow: Variable Value Coverage"):
            st.markdown(
                "Data flow testing asks whether each variable has been tested with **enough variety** "
                "to reach all its downstream rule uses. The table shows which EC value classes have "
                "appeared in your logged orders — the **Missing Classes** column identifies data flow gaps."
            )

            _dv = st.session_state.df_var_seen

            _vc_config = [
                ("drink_base",  "Stn 1", [
                    ("Espresso/Americano",   bool(_dv["drink_base"] & {"Espresso", "Americano"}),                         "R6c"),
                    ("Affogato",             "Affogato" in _dv["drink_base"],                                             "R5a"),
                    ("Milk-required drinks", bool(_dv["drink_base"] & {"Latte","Cappuccino","Macchiato","Mocha","Flat White"}), "R6a"),
                    ("Flat White",           "Flat White" in _dv["drink_base"],                                           "R6b"),
                ]),
                ("milk_type",   "Stn 2", [
                    ("No Milk (None)",   "None" in _dv["milk_type"],                                                     "R6a"),
                    ("Dairy",            bool(_dv["milk_type"] & {"Whole Milk", "Skim Milk", "Half & Half"}),            "R1, R6c"),
                    ("Plant-based",      bool(_dv["milk_type"] & PLANT_MILKS),                                           "R1, R2, R6c"),
                ]),
                ("syrup",       "Stn 3", [
                    ("None",        "None" in _dv["syrup"],                                  "—"),
                    ("Acid syrup",  "Lemon/Citrus" in _dv["syrup"],                          "R1"),
                    ("Safe syrup",  bool(_dv["syrup"] - {"None", "Lemon/Citrus"}),           "R3a, R3b"),
                ]),
                ("syrup_pumps", "Stn 3", [
                    ("0 pumps",       0 in _dv["syrup_pumps"],                               "—"),
                    ("Valid 1–6",     any(1 <= p <= 6  for p in _dv["syrup_pumps"]),         "—"),
                    ("Warning 7–10",  any(7 <= p <= 10 for p in _dv["syrup_pumps"]),         "R3a"),
                    ("Overflow >10",  any(p > 10       for p in _dv["syrup_pumps"]),         "R3b"),
                ]),
                ("topping",     "Stn 4", [
                    ("None",          "None" in _dv["topping"],                              "—"),
                    ("Standard",      bool(_dv["topping"] - {"None", "Foam"}),               "—"),
                    ("Foam",          "Foam" in _dv["topping"],                              "R5b"),
                ]),
                ("temperature", "Stn 5", [
                    ("Iced (<50°F)",    any(t < 50        for t in _dv["temperature"]),      "R5b"),
                    ("Normal (50–180)", any(50 <= t <= 180 for t in _dv["temperature"]),     "—"),
                    ("Very hot (>180)", any(t > 180        for t in _dv["temperature"]),     "R2"),
                ]),
                ("shots",       "Stn 5", [
                    ("1 shot",    1 in _dv["shots"],                                         "R6b"),
                    ("2 shots",   2 in _dv["shots"],                                         "—"),
                    ("3–4 shots", bool(_dv["shots"] & {3, 4}),                               "—"),
                    ("5–6 shots", bool(_dv["shots"] & {5, 6}),                               "R4a"),
                ]),
            ]

            _vc_summary_rows = []
            for _vname, _stn, _classes in _vc_config:
                _n_total = len(_classes)
                _n_seen  = sum(1 for _, seen, _ in _classes if seen)
                _missing = [lbl for lbl, seen, _ in _classes if not seen]
                _pct     = int(_n_seen / _n_total * 100)
                _vc_summary_rows.append({
                    "Variable":       _vname,
                    "Station":        _stn,
                    "Seen / Total":   f"{_n_seen}/{_n_total}",
                    "Coverage":       f"{_pct}%",
                    "Missing Classes": ", ".join(_missing) if _missing else "—",
                })

            def _style_vc(row):
                pct = int(row["Coverage"].replace("%", ""))
                if pct == 100:
                    return ["background-color:#d1e7dd"] * len(row)
                if pct > 0:
                    return ["background-color:#fff3cd"] * len(row)
                return ["background-color:#f8d7da"] * len(row)

            st.dataframe(
                pd.DataFrame(_vc_summary_rows).style.apply(_style_vc, axis=1),
                use_container_width=True,
                hide_index=True,
            )

            _vc_total   = sum(len(c) for _, _, c in _vc_config)
            _vc_covered = sum(1 for _, _, cls in _vc_config for _, seen, _ in cls if seen)
            _vc_pct     = int(_vc_covered / _vc_total * 100)
            st.progress(
                _vc_pct / 100,
                text=f"Variable Value Class Coverage: {_vc_covered}/{_vc_total} classes tested ({_vc_pct}%)",
            )

            with st.expander("💡 How this differs from branch coverage"):
                st.markdown("""
                The **branch coverage** view (Decision Table tab) asks: *which rules have fired?*

                This **variable value coverage** view asks: *which values have you used for each variable?*

                They measure different things. You could trigger R1 (acid + milk) once using Lemon/Citrus
                syrup with Whole Milk — R1 branch covered — but never test `milk_type = "Oat Milk"` or
                `milk_type = "None"`, leaving R2 and R6a without any data flowing through them.

                Data flow testing ensures the **variety of values** is sufficient to reach all
                downstream computations, not just that a branch exists and fires once.
                """)
