"""
menu.py — Static data: drinks, ingredients, recipes, Hall of Shame.
No Streamlit imports — fully testable standalone.
"""

DRINK_BASES = [
    "Espresso", "Americano", "Latte", "Cappuccino",
    "Macchiato", "Mocha", "Flat White", "Affogato",
]

DRINK_EMOJIS = {
    "Espresso":   "☕",
    "Americano":  "🫖",
    "Latte":      "🥛",
    "Cappuccino": "☕",
    "Macchiato":  "🍮",
    "Mocha":      "🍫",
    "Flat White": "🥛",
    "Affogato":   "🍨",
}

MILK_TYPES = [
    "Whole Milk", "Skim Milk", "Oat Milk", "Almond Milk",
    "Soy Milk", "Coconut Milk", "Half & Half", "None",
]

MILK_EMOJIS = {
    "Whole Milk":   "🐄",
    "Skim Milk":    "🐄",
    "Oat Milk":     "🌾",
    "Almond Milk":  "🌰",
    "Soy Milk":     "🫘",
    "Coconut Milk": "🥥",
    "Half & Half":  "🥛",
    "None":         "🚫",
}

# Plant-based milks are sensitive to high heat (curdling / separation)
PLANT_MILKS = frozenset(["Oat Milk", "Almond Milk", "Soy Milk", "Coconut Milk"])

FLAVOR_SYRUPS = [
    "None",
    "Vanilla",
    "Caramel",
    "Hazelnut",
    "Mocha Sauce",
    "Pumpkin Spice",
    "Irish Cream",
    "Chocolate",
    "Honey",
    "Sugar-Free Vanilla",
    "Lemon/Citrus",   # ← triggers acid+milk curdling rule
]

SYRUP_EMOJIS = {
    "None":               "🚫",
    "Vanilla":            "🍦",
    "Caramel":            "🍯",
    "Hazelnut":           "🌰",
    "Mocha Sauce":        "🍫",
    "Pumpkin Spice":      "🎃",
    "Irish Cream":        "🍀",
    "Chocolate":          "🍫",
    "Honey":              "🍯",
    "Sugar-Free Vanilla": "🍦",
    "Lemon/Citrus":       "🍋",
}

# Syrups that are acidic enough to curdle milk
ACID_SYRUPS = frozenset(["Lemon/Citrus"])

TOPPINGS = [
    "None",
    "Whipped Cream",
    "Cinnamon",
    "Nutmeg",
    "Chocolate Drizzle",
    "Caramel Drizzle",
    "Foam",
]

TOPPING_EMOJIS = {
    "None":              "🚫",
    "Whipped Cream":     "🍦",
    "Cinnamon":          "🟤",
    "Nutmeg":            "🌰",
    "Chocolate Drizzle": "🍫",
    "Caramel Drizzle":   "🍯",
    "Foam":              "🫧",
}

# Per-shot caffeine estimate (mg)
CAFFEINE_PER_SHOT = 75

# Canonical recipes — drives recipe-violation checks
DRINK_RECIPES = {
    "Espresso": {
        "requires_milk": False,
        "min_shots": 1,
        "max_temp": 212,
        "description": "Pure concentrated espresso shot(s) — no milk, no frills.",
        "canonical_milk": ["None"],
        "canonical_toppings": [],
    },
    "Americano": {
        "requires_milk": False,
        "min_shots": 1,
        "max_temp": 200,
        "description": "Espresso + hot water. Thin-bodied, big on flavor.",
        "canonical_milk": ["None"],
        "canonical_toppings": [],
    },
    "Latte": {
        "requires_milk": True,
        "min_shots": 1,
        "max_temp": 170,
        "description": "Espresso + steamed milk with a thin foam cap.",
        "canonical_milk": ["Whole Milk", "Oat Milk", "Almond Milk"],
        "canonical_toppings": ["None", "Foam"],
    },
    "Cappuccino": {
        "requires_milk": True,
        "min_shots": 1,
        "max_temp": 160,
        "description": "Equal thirds: espresso, steamed milk, thick foam. No liquid milk visible.",
        "canonical_milk": ["Whole Milk", "Skim Milk"],
        "canonical_toppings": ["Foam", "Cinnamon"],
    },
    "Macchiato": {
        "requires_milk": True,
        "min_shots": 1,
        "max_temp": 175,
        "description": "Espresso 'stained' with a small amount of milk or foam.",
        "canonical_milk": ["Whole Milk", "Oat Milk"],
        "canonical_toppings": ["None", "Caramel Drizzle"],
    },
    "Mocha": {
        "requires_milk": True,
        "min_shots": 1,
        "max_temp": 170,
        "description": "Espresso + chocolate sauce + steamed milk. A dessert in disguise.",
        "canonical_milk": ["Whole Milk", "Oat Milk"],
        "canonical_toppings": ["Whipped Cream", "Chocolate Drizzle"],
    },
    "Flat White": {
        "requires_milk": True,
        "min_shots": 2,   # ← boundary condition: 1 shot is a recipe violation
        "max_temp": 160,
        "description": "Double ristretto + microfoamed whole milk. Stronger than a latte.",
        "canonical_milk": ["Whole Milk"],
        "canonical_toppings": ["None"],
    },
    "Affogato": {
        "requires_milk": False,
        "min_shots": 1,
        "max_temp": 100,  # should be served at near-room-temp so ice cream survives
        "description": "Hot espresso poured over ice cream. The espresso must be hot; the ice cream must not melt instantly.",
        "canonical_milk": ["None"],
        "canonical_toppings": ["None"],
    },
}

# ── Hall of Shame ─────────────────────────────────────────────────────────────
# Each entry is a pre-built "disaster order" students can load and analyze.

HALL_OF_SHAME = [
    {
        "name": "🍋 The Lemon Latte Catastrophe",
        "subtitle": "Acid + Milk = Chemistry Lesson",
        "story": (
            "A customer asked for 'something refreshing and milky.' "
            "The new barista, eager to please, reached for the lemon syrup. "
            "The milk curdled on contact. The customer was not refreshed. "
            "The drain was clogged for a week."
        ),
        "order": {
            "drink_base": "Latte",
            "milk_type": "Whole Milk",
            "syrup": "Lemon/Citrus",
            "syrup_pumps": 4,
            "topping": "Foam",
            "temperature": 165,
            "shots": 2,
        },
    },
    {
        "name": "🎃 The 15-Pump Pumpkin Bomb",
        "subtitle": "Boundary Values Gone Wrong",
        "story": (
            "It was October. The customer said 'I LOVE pumpkin spice — give me EXTRA.' "
            "Fifteen pumps later, the drink was technically syrup with a faint memory of coffee. "
            "The cup vibrated on the counter. No one knows why."
        ),
        "order": {
            "drink_base": "Latte",
            "milk_type": "Oat Milk",
            "syrup": "Pumpkin Spice",
            "syrup_pumps": 15,
            "topping": "Whipped Cream",
            "temperature": 160,
            "shots": 1,
        },
    },
    {
        "name": "🧊 The Frozen Affogato",
        "subtitle": "Texture Conflict + Recipe Violation",
        "story": (
            "The customer wanted their affogato 'really, really cold.' "
            "At 32°F, the espresso never melted the ice cream. "
            "It sat there. Two separate things in a cup. "
            "The barista stared into the void."
        ),
        "order": {
            "drink_base": "Affogato",
            "milk_type": "None",
            "syrup": "Vanilla",
            "syrup_pumps": 2,
            "topping": "Whipped Cream",
            "temperature": 32,
            "shots": 1,
        },
    },
    {
        "name": "🌋 The Oat Milk Volcano",
        "subtitle": "Plant Milk Heat Shock",
        "story": (
            "Health-conscious customer, very specific: 'Oat milk, as hot as you can make it.' "
            "At 210°F, the oat proteins destabilized spectacularly. "
            "The foam was more of a geological event. "
            "The MSDS sheet would describe it as 'beige lava.'"
        ),
        "order": {
            "drink_base": "Latte",
            "milk_type": "Oat Milk",
            "syrup": "None",
            "syrup_pumps": 0,
            "topping": "Foam",
            "temperature": 210,
            "shots": 3,
        },
    },
    {
        "name": "💀 The Deadline Destroyer",
        "subtitle": "Caffeine Boundary Violation",
        "story": (
            "A grad student, 72-hour deadline, bloodshot eyes: '6 shots. No milk. No syrup. Just pain.' "
            "450mg of caffeine in a single cup. "
            "Technically past the FDA warning threshold. "
            "The student finished their thesis. We don't talk about the shaking."
        ),
        "order": {
            "drink_base": "Espresso",
            "milk_type": "None",
            "syrup": "None",
            "syrup_pumps": 0,
            "topping": "None",
            "temperature": 185,
            "shots": 6,
        },
    },
    {
        "name": "🫧 The Iced Foam Disaster",
        "subtitle": "Decision Table Rule: Foam + Iced",
        "story": (
            "A customer ordered an iced cappuccino 'with extra foam.' "
            "The barista dutifully piled foam on a 35°F drink. "
            "The foam collapsed within seconds. "
            "The customer blinked. 'Where did my foam go?' "
            "Foam does not survive the cold, friend."
        ),
        "order": {
            "drink_base": "Cappuccino",
            "milk_type": "Whole Milk",
            "syrup": "Vanilla",
            "syrup_pumps": 3,
            "topping": "Foam",
            "temperature": 35,
            "shots": 2,
        },
    },
    {
        "name": "🥛 The Milkless Latte",
        "subtitle": "Equivalence Class: Required Ingredient Missing",
        "story": (
            "New barista, first day. Customer: 'Latte with no milk please.' "
            "Barista: '...okay.' "
            "What arrived was an espresso in a large cup with extra air. "
            "A latte with no milk is just espresso with an identity crisis."
        ),
        "order": {
            "drink_base": "Latte",
            "milk_type": "None",
            "syrup": "Vanilla",
            "syrup_pumps": 2,
            "topping": "None",
            "temperature": 160,
            "shots": 2,
        },
    },
]
