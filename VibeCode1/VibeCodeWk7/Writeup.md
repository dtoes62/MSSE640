# Vibe Coding Assignment — Week 7: State Transitions, Control Flow Testing, and Data Flow Testing

## Introduction: Test Case Methodologies

This assignment covers three complementary structural and behavioral testing techniques: **State Transition Testing**, **Control Flow Testing**, and **Data Flow Testing**. Each targets a different dimension of software behavior — how a system moves between states, which branches in the code get executed, and whether variables carry the right values to every place they are used.

All three techniques were added to the existing Coffee Shop Chaos — Barista Basics Streamlit app, which was originally built in Weeks 4–5 to illustrate Equivalence Class, Boundary Value, Decision Table, and Pairwise testing. The Week 7 additions extend that foundation without replacing it, making the same coffee order domain teach three more techniques interactively.

---

### State Transition Testing

State transition testing models a system as a **finite state machine**: a collection of named states, plus the transitions (inputs) that move the system from one state to another. The goal is to verify that every valid transition works correctly and that every invalid transition is caught.

**When to use it:**
- Whenever a system's behavior depends on its history or current mode (login flows, order workflows, device states)
- When combining two individually-valid inputs can create an incompatible combined state
- When you need to map "sneak paths" — transitions that should be blocked but are not

**Limitations:**
- State explosion: the number of reachable states can grow exponentially with the number of parameters
- Identifying all meaningful states requires domain expertise; missed states mean missed tests
- State models can become stale when the codebase changes and the model is not updated

---

### Control Flow Testing

Control flow testing analyzes the logical structure of code to determine which paths through the decision points (branches, conditions, loops) have been exercised by a test suite.

**When to use it:**
- When you need to measure the structural completeness of a test suite (as distinct from its functional coverage)
- During code review and auditing to find dead code or unreachable branches
- After writing unit tests, to verify that no decision point is untested

**Coverage criteria (weakest to strongest):**
- *Statement coverage* — every line of code executed at least once
- *Branch coverage* — every decision taken both TRUE and FALSE at least once
- *Path coverage* — every unique end-to-end path executed (often exponential; rarely practical)

**Limitations:**
- 100% branch coverage does not mean 100% correctness — a branch can be exercised with the wrong assertion
- Path coverage is NP-complete in the general case; practical test suites stop at branch coverage
- Does not detect missing branches (a condition that should exist but was never written)

---

### Data Flow Testing

Data flow testing tracks each variable from its **definition** (assignment) to every **use** (where the value is read in a predicate or computation). A **def-use pair (DU-pair)** is one such path. Coverage criteria measure how many DU-pairs have been exercised across the test suite.

**When to use it:**
- When you need to verify that values computed in one part of the system are correctly propagated to every downstream rule or calculation that reads them
- When variables pass through multiple transformations before being used
- When certain rules or branches are only reachable for specific value classes of an upstream variable

**Coverage criteria:**
- *All-Defs* — every variable reaches at least one use (trivially met after any test)
- *All-Uses* — every variable reaches every downstream use it feeds
- *All-DU-Paths* — every unique path from each definition to each use (exponential; impractical)

**Limitations:**
- All-Uses coverage does not guarantee the values flowing through are *correct*, only that the paths are exercised
- Data flow analysis of dynamic languages requires care — Python's dynamic typing means a variable's type at use may differ from its type at definition
- Full DU-path coverage is generally infeasible for large programs; All-Uses is the practical target

---

## Vibe Coding Assignment: Coffee Shop Chaos — Week 7 Extensions

### Concept

The three Week 7 techniques were layered on top of the existing Barista Basics app rather than starting from scratch. This was a deliberate choice: the same coffee order domain, the same rule engine, and the same eleven rules (R1–R6c) serve as the substrate for all three new techniques. The domain did not need to change — only the *lens* through which it is analyzed.

Each technique needed its own UI surface:
- **State Transition Testing** → a live state machine diagram in the Barista Counter tab
- **Control Flow Testing** → a branch coverage tracker in the Decision Table tab
- **Data Flow Testing** → a def-use path table in the Equivalence Classes tab, and a variable value coverage view in the Test Case Log tab

The implementation was done collaboratively with Claude Code across multiple sessions, with targeted prompts for each feature rather than one large specification.

---

### State Machine Model

The order workflow was modeled as five **stations**, each assigning the order to a named sub-state:

| Station | Sub-states |
|---|---|
| Espresso Machine | `no_milk_drink`, `affogato`, `milk_required` |
| Milk Station | `no_milk`, `plant`, `dairy` |
| Syrup Rack | `no_syrup`, `acid`, `overflow`, `sweet`, `safe` |
| Topping Bar | `foam`, `none`, `safe` |
| Controls | `iced`, `very_hot`, `normal` |

The key insight is that each sub-state can be **individually valid** while being **incompatible** with another station's sub-state. For example, `acid` (Lemon/Citrus syrup) is a valid selection at the Syrup Rack, and `dairy` is a valid selection at the Milk Station — but the transition `MILK_ADDED → ACID_SYRUP_ADDED` is invalid because the two states together cause curdling (Rule R1).

The classification logic is in `_sm_substates()` in [app.py](../app.py):

```python
def _sm_substates(drink_base, milk_type, syrup, syrup_pumps, topping, temperature, shots):
    # Drink substate
    if drink_base in ("Espresso", "Americano"):
        d_sub = "no_milk_drink"
    elif drink_base == "Affogato":
        d_sub = "affogato"
    else:
        d_sub = "milk_required"

    # Milk substate
    if milk_type == "None":
        m_sub = "no_milk"
    elif milk_type in PLANT_MILKS:
        m_sub = "plant"
    else:
        m_sub = "dairy"

    # Syrup substate
    if syrup == "None" or syrup_pumps == 0:
        s_sub = "no_syrup"
    elif syrup in ACID_SYRUPS:
        s_sub = "acid"
    elif syrup_pumps > 10:
        s_sub = "overflow"
    elif syrup_pumps > 6:
        s_sub = "sweet"
    else:
        s_sub = "safe"
    ...
```

Transition conflicts are then detected by checking pairs of sub-states against the rules:

```python
    if s_sub == "acid" and m_sub != "no_milk":
        invalids.append({
            "rule": "R1",
            "transition": "MILK_ADDED → ACID_SYRUP_ADDED",
            "stations":   "Milk Station → Syrup Rack",
            "st_case":    "Test: acid syrup + any milk → INVALID transition",
        })
    if m_sub == "plant" and p_sub == "very_hot":
        sm_warnings.append({
            "rule": "R2",
            "transition": "PLANT_MILK_SET → TEMP_ABOVE_180",
            "stations":   "Milk Station → Controls",
            "st_case":    "Test: plant milk + temp > 180°F → WARNING transition",
        })
```

The resulting UI shows each station as a colored node (green = compatible, amber = WARNING conflict, red = INVALID conflict), with detected transition issues listed below:

**State Machine View — INVALID transition (Acid syrup + Milk)**

![State Machine View showing INVALID transition R1](BaristaCounterStateMachineAcidSyrup%202026-05-03%20213053.png)

**State Machine View — WARNING transition (Plant milk + high temperature)**

![State Machine View showing WARNING transition R2](BaristaCounterStateMachinePlantBaseHighTemp%202026-05-03%20213053.png)

**State Machine View — all compatible (valid order)**

![State Machine View showing all green stations](BaristaCounterStateMachineHappyPath%202026-05-03%20213053.png)

---

### Control Flow: Branch Coverage Tracker

The Decision Table tab was extended with a **branch coverage tracker** that accumulates across the entire session. Every order placed on any tab is inspected for which of the 11 rules fired; those rule IDs are added to the `cf_covered_rules` set in session state.

```python
def log_order(order: Order, results, tag: str = ""):
    ...
    for r in results:
        st.session_state.cf_covered_rules.add(r.rule_id)
```

The tracker then computes and displays:
- A progress bar showing `n / 11` branches triggered
- A per-rule table with hit status, conditions, and a hint for how to trigger each untriggered branch
- A "🚫 Unreachable" flag for branches the UI can never reach

The unreachable branch analysis discovered a genuine structural gap. Rule R4b (Caffeine > 600mg = INVALID) requires more than 8 espresso shots (8 × 75mg = 600mg), but the UI slider caps at 6 shots (450mg). The `>600mg` threshold is therefore unreachable from the counter:

```python
_MAX_SHOTS_CAFFEINE = 6 * CAFFEINE_PER_SHOT   # 450mg — slider max
if _MAX_SHOTS_CAFFEINE <= 600:
    _unreachable.add("R4b")
```

This is a real structural testing finding: the specification contains a rule that the implementation cannot exercise. A code reviewer reading only the rule engine would not notice — it takes structural analysis of the full system (UI + engine together) to catch it.

**Branch Coverage Table — session in progress**

![Branch Coverage table showing covered and uncovered branches](DecisionTablePartial%202026-05-03%20214635.png)

**Branch Coverage — 100% achieved (minus unreachable R4b)**

![Branch Coverage progress bar at 90%](DecisionTableFull%202026-05-03%20214635.png)

---

### Data Flow: Def-Use Path Table

The data flow section maps each of the seven order variables through their def-use paths:

| Variable | DEF — Station | USE → Rules | Use Type |
|---|---|---|---|
| `drink_base` | Stn 1 (Espresso Machine) | R5a, R6a, R6b, R6c | p-use |
| `milk_type` | Stn 2 (Milk Station) | R1, R2, R6a, R6c | p-use |
| `syrup` | Stn 3 (Syrup Rack) | R1, R3a, R3b | p-use |
| `syrup_pumps` | Stn 3 (Pump Slider) | R3a, R3b | p-use |
| `topping` | Stn 4 (Topping Bar) | R5b | p-use |
| `temperature` | Stn 5 (Temp Slider) | R2, R5a, R5b | p-use |
| `shots` | Stn 5 (Shots → caffeine) | R4a, R4b, R6b | c-use + p-use |

A **p-use** is a predicate use — the variable appears in a condition (`if milk_type in PLANT_MILKS`). A **c-use** is a computation use — the variable feeds a calculation (`caffeine_mg = shots × 75`). `shots` is both: it feeds the caffeine calculation (c-use) and the result is used in conditions (p-use).

The DU-pair table colors each row by coverage — green = 100%, amber = partial, red = 0% — and a progress bar tracks All-Uses coverage across the session:

```python
_DF_VARS = [
    ("drink_base",  "1", "Espresso Machine", "p-use",         ["R5a", "R6a", "R6b", "R6c"]),
    ("milk_type",   "2", "Milk Station",     "p-use",         ["R1",  "R2",  "R6a", "R6c"]),
    ("syrup",       "3", "Syrup Rack",       "p-use",         ["R1",  "R3a", "R3b"]),
    ...
]
```

The variable value coverage view (Test Case Log tab) adds a second dimension: not just which rules fired, but which value *classes* of each variable have been tested. This makes the gap explicit — you can trigger R1 (acid + milk) once and count the branch as covered, but if you never order with `milk_type = "None"` or `milk_type = "Oat Milk"`, the DU-pairs for R6a and R2 are still uncovered.

**Data Flow Def-Use Paths table — partial coverage**

![Data Flow DU-pair table with color-coded coverage and variable value coverage view showing which EC classes have been seen](DefUsePathTable%202026-05-03.png)

---

### Sunny Day Scenarios

These orders have no state transition conflicts, trigger no untested branches beyond what we intend, and result in a VALID outcome.

| Order | State Transition Notes | Branch Coverage Notes |
|---|---|---|
| Latte + Whole Milk + Vanilla ×3 + Foam + 155°F + 2 shots | All stations: compatible substates. No conflicts. | No rules fire; tests the "no-conflict" path through every check function. |
| Cappuccino + Skim Milk + None + Cinnamon + 158°F + 2 shots | `milk_required` + `dairy` + `no_syrup` + `safe` topping + `normal` temp. All transitions valid. | Covers the FALSE branch of every rule simultaneously. |
| Espresso + None + None + None + 185°F + 1 shot | `no_milk_drink` + `no_milk` — compatible (espresso doesn't need milk). | Covers FALSE branch of R6a and R6c without triggering either. |
| Americano + None + Caramel ×4 + None + 160°F + 2 shots | `safe` syrup substate; `no_milk_drink` + `no_milk` — compatible. | Tests the safe syrup path without triggering R1 or R3a/R3b. |

---

### Rainy Day Scenarios

These orders deliberately trigger state transition conflicts or specific branches.

#### State Transition Testing — INVALID transitions

| Order | Transition Triggered | Rule | State Path |
|---|---|---|---|
| Latte + Whole Milk + Lemon/Citrus ×3 + 155°F | `MILK_ADDED → ACID_SYRUP_ADDED` | R1 | `dairy` + `acid` → conflict at Milk Station ↔ Syrup Rack |
| Cappuccino + Whole Milk + None + None + 35°F + 6 shots | `MILK_ADDED` is fine, but `CAFFEINE_SAFE → CAFFEINE_WARNING` fires | R4a | `dairy` + `normal` syrup + `iced` temp; caffeine 450mg |
| Latte + None + None + None + 155°F | `MILK_REQUIRED_DRINK → NO_MILK_SELECTED` | R6a | `milk_required` + `no_milk` → conflict at Espresso Machine ↔ Milk Station |

#### State Transition Testing — WARNING transitions

| Order | Transition Triggered | Rule | State Path |
|---|---|---|---|
| Latte + Oat Milk + None + None + 210°F + 2 shots | `PLANT_MILK_SET → TEMP_ABOVE_180` | R2 | `plant` + `very_hot` → amber at Milk Station + Controls |
| Cappuccino + Whole Milk + Foam + 35°F | `FOAM_TOPPING → ICED_TEMP` | R5b | `foam` + `iced` → amber at Topping Bar + Controls |
| Affogato + None + None + None + 185°F | `AFFOGATO_DRINK → TEMP_ABOVE_140` | R5a | `affogato` + `very_hot` → amber at Espresso Machine + Controls |
| Espresso + Oat Milk + None + None + 155°F | `NO_MILK_DRINK → MILK_ADDED` | R6c | `no_milk_drink` + `plant` → non-canonical combination |

#### Control Flow — targeting specific branches

| Order | Branch Targeted | Why This Case |
|---|---|---|
| Any drink + Lemon/Citrus + Oat Milk + 181°F | R1 + R2 simultaneously | Multi-branch: tests that both checks fire and accumulate to the worst severity |
| Latte + Oat Milk + Pumpkin Spice ×11 | R3b (pump overflow) | Crosses the 10→11 boundary — the INVALID threshold, not just the warning zone |
| Flat White + Whole Milk + None + 160°F + 1 shot | R6b (Flat White shot minimum) | Tests the shot-count branch specifically for Flat White |
| Any drink + Lemon/Citrus + None + 160°F | R1 FALSE path | Acid syrup with milk=None does NOT fire R1 — covers the FALSE branch of the acid check |

#### Data Flow — exercising all DU-pairs for `milk_type`

`milk_type` feeds four downstream rules: R1, R2, R6a, R6c. Full All-Uses coverage requires at least four orders:

| Order | DU-pair exercised |
|---|---|
| Latte + Oat Milk + Lemon/Citrus ×3 | `milk_type → R1` (plant milk with acid syrup) |
| Cappuccino + Oat Milk + None + 210°F | `milk_type → R2` (plant milk + high temp) |
| Latte + **None** + Vanilla | `milk_type → R6a` (no milk on milk-required drink) |
| Espresso + Oat Milk + None | `milk_type → R6c` (milk on no-milk drink) |

After placing all four orders, the DU-pair table shows `milk_type` at 100% coverage. Each of the remaining six variables requires a similar analysis to achieve full All-Uses coverage.

---

## Conclusions

### Problems Encountered

**Representing state machines in a stateless UI** was the core design challenge. Streamlit re-renders the entire app on every widget interaction, so there is no persistent state machine object to query. The solution was to compute the sub-state classification and transition conflicts on every render from the current widget values — essentially running the state machine forward from scratch each time. This is computationally cheap for eleven rules, but the approach would not scale to a system with hundreds of states.

**Deciding what "state" means** required several iterations. The initial design modeled the five stations as states in a linear sequence (Idle → DrinkSelected → MilkSelected → ...). This turned out to be less useful than modeling the sub-state of each station independently — because the conflicts in this domain are all *cross-station* (drink type vs. milk type, milk type vs. temperature), not sequential. Switching to the parallel sub-state model made the conflicts much easier to express and detect.

**The unreachable branch finding (R4b)** was discovered during the control flow work and was not anticipated at the start. The rule `caffeine > 600mg → INVALID` exists in the rule engine and is valid, but the UI slider cap at 6 shots means 450mg is the maximum reachable caffeine value. This is a real gap between specification and implementation that would never be caught by functional testing alone — it requires structural analysis that asks "can this branch ever be reached?" Rather than removing the rule, the decision was to flag it as unreachable and explain why, because it teaches the structural testing concept more effectively than silently deleting it.

**Session state accumulation for DU-pair coverage** required careful bookkeeping. The `df_var_seen` dict tracks which value classes have been observed for each variable across all orders in the session, while `cf_covered_rules` tracks which rule IDs have fired. These two tracking structures answer different questions (what values have you used vs. what branches have fired) and it was important to keep them separate in the UI, even though they are updated together in `log_order()`.

### What I Learned About AI Coding Tools

**Incremental extension of an existing codebase is where agentic tools shine.** Adding three new features to an already-working 1,600-line app required careful context management — the AI needed to see the existing session state structure, the rule engine, and the UI layout before proposing changes. Providing the relevant sections of `app.py` as context, rather than the full file, produced more focused and accurate edits.

**Naming precision matters more than natural language fluency.** Describing "a state machine view" to the AI produced a generic flow-chart concept. Specifying "five column nodes, one per station, each colored by conflict status, with detected transition pairs listed below as error/warning boxes" produced the intended layout immediately. The more precisely the output format is specified, the less revision is required.

**The AI caught a real testing insight I hadn't formulated.** When asked to implement the control flow branch tracker, Claude surfaced the R4b unreachable-branch finding without being prompted for it — it noticed the slider cap in the existing code and inferred that the >600mg threshold was structurally dead. This is the kind of cross-file analysis that benefits from an AI that can hold the full module context in its working memory simultaneously. I chose to leave the slider as is for demonstration purposes. 

**Iterative refinement is necessary for data flow work.** The initial DU-pair table was accurate but not immediately useful — it showed raw rule IDs without explaining what value of each variable would exercise each use. Multiple rounds of refinement were needed to surface the "Missing Classes" column in the variable value coverage view, which is the practical output a tester actually needs: not "which rules are uncovered" but "what do I need to order next to cover them."

Overall, the Week 7 extension reinforced that the most productive use of an agentic coding assistant is not one-shot generation but iterative co-authoring — describe the concept, review the structure, refine the specifics, and verify the output against the existing codebase.
