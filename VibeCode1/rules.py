"""
rules.py — Rule engine for Coffee Shop Chaos.
Every validation result carries a TestType label so the UI can teach
*which testing technique* caught each problem.
No Streamlit imports — fully testable with plain pytest.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from menu import PLANT_MILKS, ACID_SYRUPS, DRINK_RECIPES, CAFFEINE_PER_SHOT


# ── Core enums ────────────────────────────────────────────────────────────────

class TestType(Enum):
    EQUIVALENCE_CLASS = "Equivalence Class"
    BOUNDARY_VALUE    = "Boundary Value Analysis"
    DECISION_TABLE    = "Decision Table"
    PAIRWISE          = "Pairwise Testing"


class Severity(Enum):
    PASS    = "pass"
    WARNING = "warning"
    INVALID = "invalid"


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RuleResult:
    rule_id:     str        # short identifier, e.g. "R1"
    title:       str        # short headline shown in UI
    description: str        # full explanation
    test_type:   TestType   # which technique caught this
    severity:    Severity   # PASS / WARNING / INVALID
    parameter:   str        # which input(s) are involved
    detail:      str        # specific numeric/value context


@dataclass
class Order:
    drink_base:  str
    milk_type:   str
    syrup:       str
    syrup_pumps: int
    topping:     str
    temperature: int
    shots:       int

    @property
    def caffeine_mg(self) -> int:
        return self.shots * CAFFEINE_PER_SHOT


# ── Individual rule checks ─────────────────────────────────────────────────────

def check_acid_milk_curdling(order: Order) -> Optional[RuleResult]:
    """R1 — Acid syrup + any milk = curdling. Decision Table catch."""
    if order.syrup in ACID_SYRUPS and order.milk_type != "None":
        return RuleResult(
            rule_id="R1",
            title="Acid + Milk = Curdling",
            description=(
                f"{order.syrup} syrup is acidic. Milk proteins react to acidity "
                f"and clump on contact. This drink will look like cottage cheese."
            ),
            test_type=TestType.DECISION_TABLE,
            severity=Severity.INVALID,
            parameter="syrup + milk_type",
            detail=(
                f"Rule: Acid syrup={order.syrup!r}, Milk={order.milk_type!r} → INVALID. "
                f"Decision Table Row R1 fires when (acid_syrup=YES ∧ milk_present=YES)."
            ),
        )
    return None


def check_plant_milk_heat(order: Order) -> Optional[RuleResult]:
    """R2 — Plant milk above 180°F. Boundary Value catch."""
    if order.milk_type in PLANT_MILKS:
        if order.temperature > 180:
            return RuleResult(
                rule_id="R2",
                title="Plant Milk Heat Shock",
                description=(
                    f"{order.milk_type} destabilizes above 180°F. "
                    f"The proteins separate and the drink looks curdled."
                ),
                test_type=TestType.BOUNDARY_VALUE,
                severity=Severity.WARNING,
                parameter="temperature",
                detail=(
                    f"Boundary: ≤180°F = PASS, 181°F = WARNING. "
                    f"Current: {order.temperature}°F — {order.temperature - 180}°F above the boundary."
                ),
            )
    return None


def check_syrup_pump_boundary(order: Order) -> Optional[RuleResult]:
    """R3 — Syrup pump count boundary zones. Boundary Value catch."""
    if order.syrup == "None" or order.syrup_pumps == 0:
        return None
    if order.syrup_pumps > 10:
        return RuleResult(
            rule_id="R3",
            title="Syrup Overflow — Too Many Pumps",
            description=(
                f"{order.syrup_pumps} pumps is past the invalid boundary. "
                f"This is technically syrup with a coffee accent, not a coffee drink."
            ),
            test_type=TestType.BOUNDARY_VALUE,
            severity=Severity.INVALID,
            parameter="syrup_pumps",
            detail=(
                f"Zones: 0–6 pumps = VALID | 7–10 = WARNING | >10 = INVALID. "
                f"Boundary at 10→11: {order.syrup_pumps} pumps lands in INVALID zone."
            ),
        )
    if order.syrup_pumps > 6:
        return RuleResult(
            rule_id="R3",
            title="Syrup Warning — Sweet Zone",
            description=(
                f"{order.syrup_pumps} pumps of {order.syrup} is in the warning zone. "
                f"The drink is technically legal but the dentist will disagree."
            ),
            test_type=TestType.BOUNDARY_VALUE,
            severity=Severity.WARNING,
            parameter="syrup_pumps",
            detail=(
                f"Zones: 0–6 pumps = VALID | 7–10 = WARNING | >10 = INVALID. "
                f"Boundary at 6→7: {order.syrup_pumps} pumps just crossed into the warning zone."
            ),
        )
    return None


def check_caffeine_boundary(order: Order) -> Optional[RuleResult]:
    """R4 — Caffeine limits from shot count. Boundary Value catch."""
    mg = order.caffeine_mg
    if mg > 600:
        return RuleResult(
            rule_id="R4",
            title="Caffeine Critical — Danger Zone",
            description=(
                f"{mg}mg caffeine exceeds the 600mg invalid boundary. "
                f"This is past FDA safe-intake guidance. The customer may vibrate."
            ),
            test_type=TestType.BOUNDARY_VALUE,
            severity=Severity.INVALID,
            parameter="shots",
            detail=(
                f"Zones: 0–400mg = VALID | 401–600mg = WARNING | >600mg = INVALID. "
                f"Boundary at 600→601mg: {mg}mg = {order.shots} shots × {CAFFEINE_PER_SHOT}mg."
            ),
        )
    if mg > 400:
        return RuleResult(
            rule_id="R4",
            title="Caffeine Warning — High Intake",
            description=(
                f"{mg}mg caffeine is in the warning zone. "
                f"Technically safe but the customer will feel every single one of those milligrams."
            ),
            test_type=TestType.BOUNDARY_VALUE,
            severity=Severity.WARNING,
            parameter="shots",
            detail=(
                f"Zones: 0–400mg = VALID | 401–600mg = WARNING | >600mg = INVALID. "
                f"Boundary at 400→401mg: {mg}mg from {order.shots} shots."
            ),
        )
    return None


def check_texture_conflicts(order: Order) -> list:
    """R5 — Incompatible texture combinations. Decision Table catch."""
    results = []

    # R5a: Affogato served too hot — ice cream melts instantly
    if order.drink_base == "Affogato" and order.temperature > 140:
        results.append(RuleResult(
            rule_id="R5a",
            title="Ice Cream Meltdown",
            description=(
                f"Affogato at {order.temperature}°F: the espresso will incinerate the ice cream "
                f"before it reaches the table. Affogato works when the pour is controlled — "
                f"above 140°F there's no rescue."
            ),
            test_type=TestType.DECISION_TABLE,
            severity=Severity.WARNING,
            parameter="drink_base + temperature",
            detail=(
                f"Rule: drink=Affogato ∧ temperature>{140}°F → WARNING. "
                f"Current temp: {order.temperature}°F."
            ),
        ))

    # R5b: Foam topping on a very cold (iced) drink — collapses immediately
    if order.topping == "Foam" and order.temperature < 50:
        results.append(RuleResult(
            rule_id="R5b",
            title="Foam Collapse",
            description=(
                f"Foam cannot survive {order.temperature}°F. "
                f"It will collapse within seconds of hitting the cold drink. "
                f"You're just adding a brief moment of hope."
            ),
            test_type=TestType.DECISION_TABLE,
            severity=Severity.WARNING,
            parameter="topping + temperature",
            detail=(
                f"Rule: topping=Foam ∧ temperature<50°F → WARNING. "
                f"Current temp: {order.temperature}°F."
            ),
        ))

    return results


def check_recipe_violations(order: Order) -> list:
    """R6 — Canonical recipe conformance. Equivalence Class catch."""
    results = []
    recipe = DRINK_RECIPES.get(order.drink_base, {})

    # R6a: Milk-requiring drinks ordered without milk
    if recipe.get("requires_milk") and order.milk_type == "None":
        results.append(RuleResult(
            rule_id="R6a",
            title="Missing Required Ingredient",
            description=(
                f"{order.drink_base} requires milk as a core ingredient. "
                f"'None' is not a valid milk selection for this drink — it places the order "
                f"in the INVALID equivalence class for the milk parameter."
            ),
            test_type=TestType.EQUIVALENCE_CLASS,
            severity=Severity.INVALID,
            parameter="milk_type",
            detail=(
                f"EC for milk_type on {order.drink_base}: "
                f"Valid = {{any milk}} | Invalid = {{None}}. "
                f"Canonical milks: {recipe.get('canonical_milk', [])}."
            ),
        ))

    # R6b: Flat White requires 2+ shots (recipe minimum)
    if order.drink_base == "Flat White" and order.shots < recipe.get("min_shots", 1):
        results.append(RuleResult(
            rule_id="R6b",
            title="Flat White — Shot Count Too Low",
            description=(
                f"Flat White is built on a double ristretto — minimum {recipe['min_shots']} shots. "
                f"{order.shots} shot(s) produces a latte, not a Flat White."
            ),
            test_type=TestType.EQUIVALENCE_CLASS,
            severity=Severity.WARNING,
            parameter="shots",
            detail=(
                f"EC for shots on Flat White: Valid = {{≥{recipe['min_shots']}}} | "
                f"Invalid = {{<{recipe['min_shots']}}}. Current: {order.shots} shot(s)."
            ),
        ))

    # R6c: Espresso/Americano shouldn't have milk (non-canonical, style warning)
    if order.drink_base in ("Espresso", "Americano") and order.milk_type != "None":
        results.append(RuleResult(
            rule_id="R6c",
            title="Unusual Ingredient Combination",
            description=(
                f"{order.drink_base} is traditionally served without milk. "
                f"Adding {order.milk_type} changes the drink family — "
                f"this falls in an unusual equivalence class."
            ),
            test_type=TestType.EQUIVALENCE_CLASS,
            severity=Severity.WARNING,
            parameter="milk_type",
            detail=(
                f"EC for milk_type on {order.drink_base}: "
                f"Canonical = {{None}} | Non-canonical (warning) = {{any milk}}. "
                f"Not invalid, but outside the expected partition."
            ),
        ))

    return results


# ── Static Decision Table rows (for the Decision Table tab) ───────────────────
# Each row describes one rule. The 'fires' callable checks if a rule fires
# for a given order — used to highlight the matching row in the UI.

DECISION_TABLE = [
    {
        "Rule": "R1",
        "Condition A": "Acid syrup (e.g. Lemon)",
        "Condition B": "Milk present",
        "Condition C": "—",
        "Action": "❌ INVALID — Curdling",
        "Test Technique": "Decision Table",
        "fires": lambda o: o.syrup in ACID_SYRUPS and o.milk_type != "None",
    },
    {
        "Rule": "R2",
        "Condition A": "Plant-based milk",
        "Condition B": "Temperature > 180°F",
        "Condition C": "—",
        "Action": "⚠ WARNING — Heat Shock",
        "Test Technique": "Boundary Value Analysis",
        "fires": lambda o: o.milk_type in PLANT_MILKS and o.temperature > 180,
    },
    {
        "Rule": "R3a",
        "Condition A": "Syrup selected",
        "Condition B": "Pumps 7–10",
        "Condition C": "—",
        "Action": "⚠ WARNING — Sweet Zone",
        "Test Technique": "Boundary Value Analysis",
        "fires": lambda o: o.syrup != "None" and 6 < o.syrup_pumps <= 10,
    },
    {
        "Rule": "R3b",
        "Condition A": "Syrup selected",
        "Condition B": "Pumps > 10",
        "Condition C": "—",
        "Action": "❌ INVALID — Pump Overflow",
        "Test Technique": "Boundary Value Analysis",
        "fires": lambda o: o.syrup != "None" and o.syrup_pumps > 10,
    },
    {
        "Rule": "R4a",
        "Condition A": "Shots × 75mg",
        "Condition B": "Caffeine 401–600mg",
        "Condition C": "—",
        "Action": "⚠ WARNING — High Caffeine",
        "Test Technique": "Boundary Value Analysis",
        "fires": lambda o: 400 < o.caffeine_mg <= 600,
    },
    {
        "Rule": "R4b",
        "Condition A": "Shots × 75mg",
        "Condition B": "Caffeine > 600mg",
        "Condition C": "—",
        "Action": "❌ INVALID — Caffeine Critical",
        "Test Technique": "Boundary Value Analysis",
        "fires": lambda o: o.caffeine_mg > 600,
    },
    {
        "Rule": "R5a",
        "Condition A": "Drink = Affogato",
        "Condition B": "Temperature > 140°F",
        "Condition C": "—",
        "Action": "⚠ WARNING — Ice Cream Meltdown",
        "Test Technique": "Decision Table",
        "fires": lambda o: o.drink_base == "Affogato" and o.temperature > 140,
    },
    {
        "Rule": "R5b",
        "Condition A": "Topping = Foam",
        "Condition B": "Temperature < 50°F",
        "Condition C": "—",
        "Action": "⚠ WARNING — Foam Collapses",
        "Test Technique": "Decision Table",
        "fires": lambda o: o.topping == "Foam" and o.temperature < 50,
    },
    {
        "Rule": "R6a",
        "Condition A": "Drink requires milk",
        "Condition B": "Milk = None",
        "Condition C": "—",
        "Action": "❌ INVALID — Missing Required Milk",
        "Test Technique": "Equivalence Class",
        "fires": lambda o: DRINK_RECIPES.get(o.drink_base, {}).get("requires_milk") and o.milk_type == "None",
    },
    {
        "Rule": "R6b",
        "Condition A": "Drink = Flat White",
        "Condition B": "Shots < 2",
        "Condition C": "—",
        "Action": "⚠ WARNING — Insufficient Shots",
        "Test Technique": "Equivalence Class",
        "fires": lambda o: o.drink_base == "Flat White" and o.shots < 2,
    },
    {
        "Rule": "R6c",
        "Condition A": "Drink = Espresso or Americano",
        "Condition B": "Milk ≠ None",
        "Condition C": "—",
        "Action": "⚠ WARNING — Unusual Combination",
        "Test Technique": "Equivalence Class",
        "fires": lambda o: o.drink_base in ("Espresso", "Americano") and o.milk_type != "None",
    },
]


# ── Public API ─────────────────────────────────────────────────────────────────

def evaluate_order(order: Order) -> list:
    """Run all rule checks. Returns list of RuleResult sorted by severity."""
    results = []

    for check_fn in [
        check_acid_milk_curdling,
        check_plant_milk_heat,
        check_syrup_pump_boundary,
        check_caffeine_boundary,
    ]:
        r = check_fn(order)
        if r:
            results.append(r)

    results.extend(check_texture_conflicts(order))
    results.extend(check_recipe_violations(order))

    # Sort: INVALID first, then WARNING
    _order = {Severity.INVALID: 0, Severity.WARNING: 1, Severity.PASS: 2}
    results.sort(key=lambda r: _order[r.severity])
    return results


def overall_severity(results: list) -> Severity:
    if any(r.severity == Severity.INVALID for r in results):
        return Severity.INVALID
    if any(r.severity == Severity.WARNING for r in results):
        return Severity.WARNING
    return Severity.PASS


def fired_rule_ids(order: Order) -> set:
    """Return set of rule IDs that fire for the given order (for DT highlighting)."""
    return {row["Rule"] for row in DECISION_TABLE if row["fires"](order)}
