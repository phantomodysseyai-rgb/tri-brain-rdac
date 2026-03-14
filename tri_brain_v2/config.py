"""
================================================================================
Tri-Brain System — Configuration
================================================================================
Copyright (c) 2026 Masanao Ishikawa (Phantom Odyssey AI)
DOI: https://doi.org/10.5281/zenodo.18859272
================================================================================
"""

# ============================================================
# System constants
# ============================================================
WINDOW_SIZE       = 3   # Number of recent rounds passed in full to Diff AI
MAX_KEYWORD_LEN   = 20  # Max characters for compressed conflict keywords
CONVERGENCE_ROUND = 4   # Round from which convergence check is activated
MAX_ROUND         = 6   # Hard upper limit for rounds
HTTP_PORT         = 7331

# ============================================================
# Model settings
# ============================================================
BRAIN_MODEL = "gpt-5-mini"   # Model used for Logic / Emotion / Meta brains
DIFF_MODEL  = "gpt-5-mini"   # Model used for Diff AI (higher reasoning load)
CONV_MODEL  = "gpt-5-mini"   # Model used for convergence judge

# ============================================================
# Conflict depth levels (used for round-by-round deepening)
# ============================================================
CONFLICT_LEVELS = [
    "手段レベル（何をするか・しないか）",
    "責任レベル（誰がコントロールするか）",
    "価値観レベル（何を最優先にするか）",
    "存在レベル（そもそも何が人間にとって必要か）",
]
