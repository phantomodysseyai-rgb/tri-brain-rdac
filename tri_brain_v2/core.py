"""
================================================================================
Tri-Brain System — Core Engine
================================================================================
Copyright (c) 2026 Masanao Ishikawa (Phantom Odyssey AI)
DOI: https://doi.org/10.5281/zenodo.18859272
================================================================================

Core brain execution and analysis functions:
  compress_conflict()    — compress past conflict text for history window
  build_history_text()   — build structured history string for Diff AI
  ask_brain()            — call a single brain (V x D integration)
  tri_brain()            — run all 3 brains in parallel + Diff AI analysis
  check_convergence()    — run convergence judge after CONVERGENCE_ROUND

Language switching:
  Replace the prompts import line to switch between Japanese and English:
    from prompts_ja import ...   (default)
    from prompts_en import ...   (English session)
================================================================================
"""

from openai import AsyncOpenAI
import asyncio
import re

# Language selection — change this one line to switch languages
from prompts_ja import (
    ROLES, apply_density, build_diff_prompt,
    build_convergence_prompt, build_convergence_instruction,
)
from config import (
    WINDOW_SIZE, MAX_KEYWORD_LEN,
    CONVERGENCE_ROUND, BRAIN_MODEL, DIFF_MODEL, CONV_MODEL,
)

import os
client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))


async def ask_brain(brain_config: dict, question: str) -> dict:
    """
    V (role) and D (information density) are controlled simultaneously.
    """
    contextualized_question = apply_density(question, brain_config["density"])
    response = await client.chat.completions.create(
        model=BRAIN_MODEL,
        messages=[
            {"role": "system", "content": brain_config["system_prompt"]},
            {"role": "user",   "content": contextualized_question},
        ],
    )
    return {
        "name":    brain_config["name"],
        "density": brain_config["density"],
        "content": response.choices[0].message.content,
    }


def compress_conflict(text: str) -> str:
    """
    衝突文（1〜2行）をキーワード形式に圧縮する。
    例: "LogicはAIがアクセスを広げて人を救うと言い、EmotionはAIが人間関係を奪うと言っている。これらは両立しない。"
        → "アクセス拡大 vs 人間関係喪失"
    """
    import re
    # "LogicはXと言い、EmotionはYと言っている" パターンから X と Y を抽出
    m = re.search(r'Logicは(.+?)と言い.*?Emotionは(.+?)と言って', text)
    if m:
        lx = m.group(1).strip()[:MAX_KEYWORD_LEN]
        em = m.group(2).strip()[:MAX_KEYWORD_LEN]
        return f"{lx} vs {em}"
    # パターン不一致の場合は先頭MAX_KEYWORD_LEN文字
    return text.strip()[:MAX_KEYWORD_LEN]


def build_history_text(history: list, conflict_levels: list, round_num_current: int, next_conflict_level: str, choice_history: list = None) -> str:
    """
    スライディングウィンドウ＋圧縮全履歴で history_text を構築する。
    - 直近 WINDOW_SIZE ラウンド：フル文章で渡す（コンテキスト維持）
    - それ以前のラウンド：キーワード圧縮で渡す（トークン節約）
    - choice_history：ユーザーの選択履歴をラウンドごとに渡す
    """
    if not history:
        return ""

    lines = ["\n\n【過去のラウンドで扱った衝突点（再利用禁止）】"]

    window_start = max(0, len(history) - WINDOW_SIZE)

    for i, h in enumerate(history):
        level = conflict_levels[min(i, len(conflict_levels) - 1)]
        choice_note = ""
        if choice_history and i < len(choice_history):
            choice_note = f"　→ ユーザー選択：{choice_history[i]}"
        if i < window_start:
            # 古いラウンド：圧縮キーワードのみ
            compressed = compress_conflict(h)
            lines.append(f"Round {i+1}（{level}）[要約]：{compressed}{choice_note}")
        else:
            # 直近ラウンド：フル文章
            lines.append(f"Round {i+1}（{level}）：{h}{choice_note}")

    lines.append(f"\n今回（Round {round_num_current}）は必ず「{next_conflict_level}」の衝突を見つけること。")
    lines.append("上記の過去の衝突と1文字でも重なる表現を使った場合、その出力は失敗とみなす。")
    if choice_history:
        lines.append(f"\n【ユーザーの選択履歴】")
        for i, c in enumerate(choice_history):
            lines.append(f"Round {i+1}: {c}")
        lines.append(f"\n【ユーザーの立場分析（Reframed Question生成前に必ず行うこと）】")
        lines.append("上記の選択履歴から以下を分析せよ：")
        lines.append("1. Orientation（以下から最も近いものを1つ選べ）")
        lines.append("   ・政策志向：市場主導 / 国家主導 / 地域主導 / 倫理重視")
        lines.append("   ・認識論志向：真偽・検証・定義の問題として捉えている（例：クオリア・意識・不可知論）")
        lines.append("   ※選択テキストに「証明」「確かめ」「真偽」「言い訳」「分からない」「不可知」等が含まれる場合は認識論志向を優先せよ")
        lines.append("2. Value priority（何を最優先にしているか1行で）")
        lines.append("3. Hidden assumption（この立場が無意識に前提としている思い込みを1行で）")
        lines.append("3. Unresolved tension（この立場がまだ答えていない最大の緊張を1行で）")
        lines.append("\n【重要】認識論志向・社会プロセス志向と判断した場合のReframed Question生成ルール：")
        lines.append("・認識論志向：政策（誰が決めるか・規制するか）ではなく「知識の限界・検証の可能性」を軸に問いを作れ")
        lines.append("・社会プロセス志向：「科学/法/社会のどれが判断を先導するか」を軸に問いを作れ")
        lines.append("\n【政策志向の場合のルール】")
        lines.append("・ユーザーの立場そのものを一方の選択肢に含めること")
        lines.append("・もう一方はその立場の盲点・矛盾を突く選択肢にすること")
        lines.append("・同じ立場を繰り返せる選択肢は禁止")
    return "\n".join(lines)


async def tri_brain(question: str, history: list = None, hook_history: list = None, choice_history: list = None) -> tuple[str, str]:

    # 3脳を並列実行（V × D がそれぞれ異なる）
    tasks = [ask_brain(role, question) for role in ROLES]
    results = await asyncio.gather(*tasks)

    # 回答整形
    answers_text = ""
    for res in results:
        answers_text += (
            f"\n=== {res['name']} [D:{res['density']}] ===\n"
            f"{res['content']}\n"
        )

    # 衝突の深化レベルをラウンドごとに定義（手段→責任→価値観→存在）
    conflict_levels = [
        "手段レベル（何をするか・しないか）",
        "責任レベル（誰がコントロールするか）",
        "価値観レベル（何を最優先にするか）",
        "存在レベル（そもそも何が人間にとって必要か）",
    ]
    round_num_current = len(history) + 1 if history else 1
    next_conflict_level = conflict_levels[min(round_num_current - 1, len(conflict_levels) - 1)]

    # 過去の衝突点を履歴から構造化（スライディングウィンドウ＋圧縮）
    history_text = build_history_text(history or [], conflict_levels, round_num_current, next_conflict_level, choice_history or [])

    # 収束ラウンド特別指示（prompts_ja / prompts_en から取得）
    is_convergence_round = round_num_current >= CONVERGENCE_ROUND and bool(choice_history)
    convergence_instruction = build_convergence_instruction(is_convergence_round)

    # Diff分析プロンプト（prompts_ja / prompts_en から生成）
    diff_prompt = build_diff_prompt(
        question=question,
        answers_text=answers_text,
        history_text=history_text,
        next_conflict_level=next_conflict_level,
        history=history or [],
        hook_history=hook_history or [],
        convergence_instruction=convergence_instruction,
    )


    # Diff統合は推論負荷が最も高いため上位モデルを使用
    diff = await client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": diff_prompt}],
    )

    return results, diff.choices[0].message.content


# ============================================================
# 収束チェック（Round 4以降）
# ============================================================
async def check_convergence(question: str, all_diffs: list) -> dict:
    """
    過去のDiff全体を見て収束しているか判定する。
    収束条件（3つのうち①②、または①③で収束）：
      ① 衝突軸の固定：同じ次元の衝突が2ラウンド連続している
      ② Hidden Assumptionの枯渇：新しい前提が出てこない
      ③ 政策空間の枯渇：新しい解決策が前ラウンドの拡張に留まっている
    判定はDiff AIとは独立した専用プロンプトで実行。
    """
    diffs_text = ""
    for i, d in enumerate(all_diffs, 1):
        diffs_text += f"\n=== Round {i} Diff ===\n{d}\n"

    convergence_prompt = build_convergence_prompt(question, diffs_text)

    result = await client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": convergence_prompt}],
    )
    text = result.choices[0].message.content.strip()

    # パース
    import re
    axis_fixed       = bool(re.search(r'AXIS_FIXED:\s*yes', text, re.IGNORECASE))
    exhausted        = bool(re.search(r'EXHAUSTED:\s*yes', text, re.IGNORECASE))
    policy_exhausted = bool(re.search(r'POLICY_EXHAUSTED:\s*yes', text, re.IGNORECASE))
    reason_m         = re.search(r'REASON:\s*(.+)', text)
    verdict_m        = re.search(r'VERDICT:\s*(converged|continue)', text, re.IGNORECASE)

    reason  = reason_m.group(1).strip() if reason_m else ""
    verdict = verdict_m.group(1).lower() if verdict_m else "continue"

    # 収束ルールをPython側でも保証（LLMの出力ミスを防ぐ）
    if axis_fixed and (exhausted or policy_exhausted):
        verdict = "converged"

    return {
        "axis_fixed": axis_fixed,
        "exhausted": exhausted,
        "policy_exhausted": policy_exhausted,
        "reason": reason,
        "verdict": verdict,
        "raw": text,
    }


# ============================================================
# HTML出力
# ============================================================
