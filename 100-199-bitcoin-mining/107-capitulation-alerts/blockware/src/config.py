GRAPHQL_URL = "https://marketplace.api.blockwaresolutions.com/api/opengraphql"

DISCOUNT_THRESHOLD = 60  # percent off last trade (or 90d midpoint fallback)

MAX_EFFICIENCY_WTH = 17.5  # skip offers above this W/TH (filters junk M66S 18-19 W/T)
MIN_DEAL_SCORE = 50        # skip offers below this deal score (filters unscored/junk)

RANGE_WINDOW_DAYS = 90  # days for windowed high/low stats

POLL_LIMIT = 100  # max offers per query page

# ── TARGET MINER MODELS ──────────────────────────────────────────
# Only S21-class and equivalent new-gen. NO S19s.
# Format: model_id -> (description, ath_price_usd)
# ATH prices pulled from Blockware tradeStatsByModel on 2026-02-07.
# The bot ALSO refreshes ATH dynamically from the API each run.

TARGET_MODELS = {
    # Bitmain S21 base
    1308210: {"name": "Bitmain S21 188T",           "static_ath": 5043.10},
    1308236: {"name": "Bitmain S21 195T",           "static_ath": 6750.00},
    1189061: {"name": "Bitmain S21 200T",           "static_ath": 5900.00},
    # Bitmain S21+
    2591919: {"name": "Bitmain S21+ 225T",          "static_ath": None},     # no trade history yet
    2591920: {"name": "Bitmain S21+ 235T",          "static_ath": 5650.00},
    # Bitmain S21 Pro
    2466775: {"name": "Bitmain S21 Pro 234T",       "static_ath": 6899.00},
    # Bitmain S21 XP
    2591911: {"name": "Bitmain S21 XP 270T",        "static_ath": 8910.00},
    # Bitmain S21 Hydro
    2591922: {"name": "Bitmain S21 Hydro 335T",     "static_ath": 8877.50},
    # SealMiner A2
    2591924: {"name": "SealMiner A2 228T",          "static_ath": 4250.00},
    2591925: {"name": "SealMiner A2 230T",          "static_ath": 4200.00},
    2591926: {"name": "SealMiner A2 232T",          "static_ath": 4250.00},
    2591927: {"name": "SealMiner A2 234T",          "static_ath": 4275.00},
    # Whatsminer M66S
    2472680: {"name": "M66S 268T 18.5 W/T",        "static_ath": 7906.00},
    2473190: {"name": "M66S 266T 18.5 W/T",        "static_ath": 4495.00},
    2591402: {"name": "M66S 268T 19 W/T",          "static_ath": 8308.00},
    2473199: {"name": "M66S 270T 19 W/T",          "static_ath": 6699.00},
    2473201: {"name": "M66S 290T 18.5 W/T",        "static_ath": 4495.00},
    2473215: {"name": "M66S 296T 18.5 W/T",        "static_ath": None},
    2473228: {"name": "M66S 300T 18.5 W/T",        "static_ath": 4495.00},
    2473230: {"name": "M66S 302T 18.5 W/T",        "static_ath": 4995.00},
    2473252: {"name": "M66S 278T 19 W/T",          "static_ath": None},
    2473261: {"name": "M66S 288T 18 W/T",          "static_ath": None},
    2473262: {"name": "M66S 284T 18.5 W/T",        "static_ath": None},
}

SENT_ALERTS_PATH = "data/sent_alerts.json"
