"""
pairwise.py — Pairwise (all-pairs) test case generation.

Uses EC boundary-representative values for numeric parameters so the
generator produces meaningful test cases without exploding combinatorially.
The educational point: pairwise works best *after* EC partitioning has
already reduced the value space.

Falls back to a simple greedy generator if allpairspy is not installed.
"""

from menu import DRINK_BASES, MILK_TYPES, FLAVOR_SYRUPS, TOPPINGS
from rules import Order, evaluate_order

# ── EC representative values for numeric parameters ───────────────────────────
# Each number is chosen to sit AT or just across a boundary — exactly the
# values boundary-value analysis tells us are most likely to reveal bugs.

SYRUP_PUMP_REPS = [0, 3, 6, 7, 10, 11, 15]   # boundaries: 6|7, 10|11
TEMP_REPS       = [32, 50, 100, 180, 181, 212] # boundaries: 50 (iced), 180|181, 140 (affogato)
SHOT_REPS       = [1, 2, 3, 5, 6]             # boundaries: 1 (min), 2 (flat white min), caffeine zones

PAIRWISE_PARAMETERS = {
    "drink_base":  DRINK_BASES,
    "milk_type":   MILK_TYPES,
    "syrup":       FLAVOR_SYRUPS,
    "topping":     TOPPINGS,
    "syrup_pumps": SYRUP_PUMP_REPS,
    "temperature": TEMP_REPS,
    "shots":       SHOT_REPS,
}


def brute_force_count() -> int:
    """Total full-factorial combinations across EC representatives."""
    result = 1
    for values in PAIRWISE_PARAMETERS.values():
        result *= len(values)
    return result


def generate_pairwise_cases() -> list:
    """Generate pairwise (2-way covering array) test cases as Order objects."""
    try:
        from allpairspy import AllPairs
        param_names  = list(PAIRWISE_PARAMETERS.keys())
        param_values = list(PAIRWISE_PARAMETERS.values())
        cases = []
        for combo in AllPairs(param_values):
            cases.append(Order(**dict(zip(param_names, combo))))
        return cases
    except ImportError:
        return _greedy_pairwise()


def _greedy_pairwise() -> list:
    """
    Simple greedy pairwise fallback (no external library needed).
    Iterates parameters left-to-right, cycling through uncovered pairs.
    Not optimal but sufficient for demonstration purposes.
    """
    import itertools

    param_names  = list(PAIRWISE_PARAMETERS.keys())
    param_values = list(PAIRWISE_PARAMETERS.values())
    n_params = len(param_names)

    # Build the set of all 2-way pairs that need to be covered
    uncovered = set()
    for i, j in itertools.combinations(range(n_params), 2):
        for vi in param_values[i]:
            for vj in param_values[j]:
                uncovered.add((i, vi, j, vj))

    cases = []
    max_iterations = brute_force_count()  # safety cap

    while uncovered and max_iterations > 0:
        max_iterations -= 1
        best_case = None
        best_count = -1

        # Sample candidates — try cycling through values of param 0
        for anchor_val in param_values[0]:
            candidate = [anchor_val]
            for p in range(1, n_params):
                best_v = param_values[p][0]
                best_c = 0
                for v in param_values[p]:
                    # count how many uncovered pairs this value covers with already-chosen params
                    c = sum(
                        1 for q in range(p)
                        if (q, candidate[q], p, v) in uncovered
                        or (p, v, q, candidate[q]) in uncovered
                    )
                    if c > best_c:
                        best_c = c
                        best_v = v
                candidate.append(best_v)

            covered = sum(
                1 for (i, j) in itertools.combinations(range(n_params), 2)
                if (i, candidate[i], j, candidate[j]) in uncovered
                or (j, candidate[j], i, candidate[i]) in uncovered
            )
            if covered > best_count:
                best_count = covered
                best_case = candidate

        if best_case is None or best_count == 0:
            break

        # Remove covered pairs
        for i, j in itertools.combinations(range(n_params), 2):
            uncovered.discard((i, best_case[i], j, best_case[j]))
            uncovered.discard((j, best_case[j], i, best_case[i]))

        cases.append(Order(**dict(zip(param_names, best_case))))

    return cases


def pairwise_count() -> int:
    return len(generate_pairwise_cases())


def run_all_pairwise(cases: list) -> list:
    """Evaluate each pairwise case. Returns list of (Order, results) tuples."""
    return [(case, evaluate_order(case)) for case in cases]
