"""
================================================================================
Tri-Brain System — Text Classifiers
================================================================================
Copyright (c) 2026 Masanao Ishikawa (Phantom Odyssey AI)
DOI: https://doi.org/10.5281/zenodo.18859272
================================================================================

Two classifiers used in the session loop:

1. classify_choice(text) — classifies a free-text C-choice into a stance category.
   Used to annotate choice_history entries for the Diff AI's User Position Analysis.

2. classify_question_type(question) — classifies the Initial Question into one of
   three types, determining whether Layer 0 (direct answer) is shown at the end.
================================================================================
"""


def classify_choice(text: str) -> str:
    """
    Classify a free-text C-choice into a stance category.

    Priority order: Social-Process > Epistemic/Philosophical > Policy categories
    Tie-breaking: policy wins over epistemic on equal score.

    Returns one of:
        "社会プロセス" / "認識論・哲学" /
        "市場主導" / "国家主導" / "地域主導" / "倫理重視" / "その他"
    """
    t = text

    # --- Epistemic / Philosophical (checked before policy) ---
    epistemic_words = [
        "クオリア", "意識", "主観", "真偽", "証明", "検証", "定義",
        "存在", "認識", "哲学", "本質", "判定できない", "分からない",
        "言い訳", "不可知", "観測", "確かめ", "真実", "知識",
    ]

    # --- Policy categories ---
    market_words = [
        "市場", "企業", "競争", "民間", "自由", "自律",
        "黎明期", "様子見", "任せ", "普及", "拡大", "先に", "まず",
    ]
    state_words  = ["国", "政府", "規制", "法", "中央", "管理", "監視", "行政"]
    local_words  = ["地域", "地元", "コミュニティ", "町内", "住民", "地方"]
    ethics_words = ["尊厳", "倫理", "人権", "責任", "搾取", "被害", "詐欺", "弱者"]

    # --- Social process ---
    social_words = [
        "裁判", "人権", "法的", "承認", "合意", "社会が", "段階", "ステージ",
        "プロセス", "認める", "受け入れ", "議論される", "制度化", "市民権",
    ]

    epistemic_score = sum(1 for w in epistemic_words if w in t)
    social_score    = sum(1 for w in social_words    if w in t)
    policy_scores = {
        "市場主導": sum(1 for w in market_words if w in t),
        "国家主導": sum(1 for w in state_words  if w in t),
        "地域主導": sum(1 for w in local_words  if w in t),
        "倫理重視": sum(1 for w in ethics_words if w in t),
    }
    policy_top   = max(policy_scores, key=policy_scores.get)
    policy_score = policy_scores[policy_top]

    # Priority: Social-Process > Epistemic > Policy (tie → policy wins)
    if social_score > 0 and social_score >= epistemic_score and social_score > policy_score:
        return "社会プロセス"
    if epistemic_score > 0 and epistemic_score > policy_score:
        return "認識論・哲学"
    if policy_score > 0:
        return policy_top
    if epistemic_score > 0:
        return "認識論・哲学"
    return "その他"


def classify_question_type(question: str) -> str:
    """
    Classify the Initial Question into one of three types.

    Returns:
        "epistemic" — ontological / epistemological question → Layer 0 shown
        "value"     — life-choice / values question          → Layer 0 shown
        "policy"    — policy / action question               → Layer 0 not shown

    Layer 0 asks the user to answer the original question directly after
    all rounds of debate, providing the "direct answer" layer.
    """
    q = question

    epistemic_words = [
        "とは何か", "とは何", "できるか", "存在するか", "生成される",
        "生じる", "クオリア", "意識とは", "主観とは", "定義できる",
        "証明できる", "判定できる", "本質とは", "可能か", "ありうるか",
        "なのか否か", "かどうかを",
    ]
    value_words = [
        "生きる", "生き方", "幸せ", "幸福", "後悔", "意味", "価値観",
        "自分らしく", "自己実現", "人生", "創作", "夢", "やりたい",
        "やりがい", "本当に", "本音", "魂", "信念", "働き方",
        "精神的", "心の", "感情", "愛", "孤独", "つながり",
        "良いことなのか", "良いのか", "幸いなのか",
    ]
    policy_words = [
        "すべきか", "べきか", "どうすれば", "どうする", "どう対応",
        "どう運用", "規制", "法律", "制度", "政策",
    ]

    ep_score  = sum(1 for w in epistemic_words if w in q)
    val_score = sum(1 for w in value_words     if w in q)
    pol_score = sum(1 for w in policy_words    if w in q)

    if ep_score > pol_score:
        return "epistemic"
    if val_score > 0:
        return "value"
    return "policy"
