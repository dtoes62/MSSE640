# Coffee Shop Chaos — Barista Basics

An interactive Streamlit app that teaches four software testing techniques simultaneously through the chaos of a coffee shop ordering counter. Build orders, fire them at the rule engine, and watch it tell you exactly *which testing technique* caught the problem — and why.

---

![Barista Counter](Video/BaristaCounterSelections.png)

---

## What It Demonstrates

| Testing Technique | How it appears in the app |
|---|---|
| **Equivalence Class Testing** | Milk types, syrup categories, and shot counts are grouped into named partitions; the EC tab highlights which class the current order falls into |
| **Boundary Value Analysis** | Syrup pumps (0–6 / 7–10 / >10), temperature (≤180°F / >180°F for plant milks), and caffeine (0–400 / 401–600 / >600 mg) are visualized as color-zone gauges with boundary markers |
| **Decision Table Testing** | 11 business rules rendered as a full decision table; matched rows highlight gold when an order fires them |
| **Pairwise Testing** | 7 parameters with EC representative values yield 1,034,880 full-factorial combinations — reduced to ~89 pairwise test cases covering all 2-way interactions |

---

## Features

- **Barista Counter** — five-station coffee shop counter (Espresso Machine → Milk Station → Syrup Rack → Topping Bar → Controls); results pop out in a modal dialog with an order ticket and rule explanations
- **Break the Barista** — game mode: a random order is generated and you predict PASS / WARNING / INVALID before the answer is revealed; score is tracked
- **Hall of Shame** — 7 pre-built legendary disaster orders, each illustrating a different rule type, with a load-to-counter button
- **Equivalence Classes tab** — visual partition grid per parameter with the current order's class highlighted
- **Boundary Values tab** — color-zone gauges for pumps, temperature, and caffeine with explicit boundary tick marks
- **Decision Table tab** — full rule table, matched rows highlighted in gold
- **Pairwise Testing tab** — coverage comparison, generated test suite, and CSV export
- **Test Case Log tab** — running log of every order placed across all tabs, exportable to CSV
- **QA Mode toggle** — reveals rule IDs, `TestType` labels (Equivalence Class / Boundary Value Analysis / Decision Table), and EC class names throughout the UI

---

## Architecture

```
VibeCode1/
├── app.py            # Streamlit UI — 8 tabs, counter layout, game modes, CSS
├── menu.py           # Static data — drinks, ingredients, recipes, Hall of Shame
├── rules.py          # Rule engine — 11 rules, each tagged with TestType enum
├── pairwise.py       # Pairwise generator — allpairspy wrapper + greedy fallback
├── requirements.txt
└── Video/
    ├── Writeup.md    # Assignment writeup
    ├── BreaktheBarista.mp4
    └── *.png         # UI screenshots
```

The core educational structure is the `RuleResult` dataclass in `rules.py`. Every validation result carries a `TestType` label so the UI can explain *which technique* caught each issue:

```python
@dataclass(frozen=True)
class RuleResult:
    rule_id:     str        # e.g. "R1", "R3"
    title:       str        # short headline shown in the UI
    description: str        # full explanation
    test_type:   TestType   # EQUIVALENCE_CLASS | BOUNDARY_VALUE | DECISION_TABLE
    severity:    Severity   # PASS | WARNING | INVALID
    parameter:   str        # which input(s) are involved
    detail:      str        # specific numeric/value context
```

---

## Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.9+ | `python --version` |
| pip | any | `pip --version` |

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/dtoes62/MSSE640.git
cd MSSE640/VibeCode1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

This installs:

| Package | Purpose |
|---|---|
| `streamlit>=1.35` | Web UI framework |
| `pandas>=2.0` | DataFrame rendering for tables and CSV export |
| `allpairspy>=2.0` | IPOG pairwise (all-pairs) covering array generation |

---

## Running the App

```bash
streamlit run app.py
```

The app opens automatically at **http://localhost:8501**

To stop the server press **Ctrl+C**.

---

## Business Rules

| Rule | Condition | Result | Technique |
|---|---|---|---|
| R1 | Acid syrup (Lemon/Citrus) + any milk | ❌ INVALID — curdling | Decision Table |
| R2 | Plant milk (Oat/Almond/Soy/Coconut) + temp > 180°F | ⚠️ WARNING — heat shock | Boundary Value |
| R3 | Syrup pumps 7–10 | ⚠️ WARNING — sweet zone | Boundary Value |
| R3 | Syrup pumps > 10 | ❌ INVALID — overflow | Boundary Value |
| R4 | Caffeine 401–600 mg | ⚠️ WARNING — high intake | Boundary Value |
| R4 | Caffeine > 600 mg | ❌ INVALID — danger zone | Boundary Value |
| R5a | Affogato + temp > 140°F | ⚠️ WARNING — ice cream melts | Decision Table |
| R5b | Foam topping + temp < 50°F | ⚠️ WARNING — foam collapses | Decision Table |
| R6a | Milk-requiring drink + milk = None | ❌ INVALID — missing required ingredient | Equivalence Class |
| R6b | Flat White + shots < 2 | ⚠️ WARNING — insufficient shots | Equivalence Class |
| R6c | Espresso or Americano + milk ≠ None | ⚠️ WARNING — unusual combination | Equivalence Class |

---

## Demo

[▶ Watch App Demo — Break the Barista Game Mode](https://regis365-my.sharepoint.com/:v:/g/personal/edick_regis_edu/IQBySalczQAZSq5fohN3_HcYARFp7PwMOxWSaBgfr4FVel8?e=9danYm)
