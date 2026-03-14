"""
================================================================================
Tri-Brain System — Main Session Loop
================================================================================
Copyright (c) 2026 Masanao Ishikawa (Phantom Odyssey AI)
DOI: https://doi.org/10.5281/zenodo.18859272
================================================================================

Entry point. Run with:
    python main.py

To switch to English session, edit core.py:
    from prompts_en import ...   (instead of prompts_ja)
================================================================================
"""

import asyncio

from config     import HTTP_PORT, CONVERGENCE_ROUND, MAX_ROUND
from classifier import classify_choice, classify_question_type
from core       import tri_brain, check_convergence
from renderer   import save_html, save_live_html, start_http_server
from prompts_ja import REFLECTION_L0_EPISTEMIC, REFLECTION_L0_VALUE, REFLECTION_Q1, REFLECTION_Q2


async def tri_brain_loop():

    print("=== Tri-Brain System (RDAC: V × D Complete) ===\n")
    start_http_server()
    print(f"📺 ブラウザで http://127.0.0.1:{HTTP_PORT}/tri_brain_live.html を開いてください\n"
          f"   （自動更新されます。file:// ではなく http:// で開くことが重要です）\n")

    question = input("Initial Question: ")

    # ライブHTML初期化
    state = {
        "question": question,
        "status": "① 3つの脳が処理中...",
        "thought_log": [
            {"type": "initial", "text": question}
        ]
    }
    save_live_html(state)

    # --- First Pass ---
    print("\n⏳ 処理中...\n")
    conflict_history = []  # 過去の衝突点を蓄積
    choice_history = []    # ユーザーの選択履歴を蓄積
    hook_history = []      # 過去のCognitive Hookシーンを蓄積
    round_num = 1

    raw_results, diff = await tri_brain(question, history=conflict_history, hook_history=hook_history)
    answers = [r for r in raw_results] if isinstance(raw_results, list) else []

    # 3脳の結果をライブ更新
    state["answers"] = answers
    state["status"] = "③ Diff分析中..."
    save_live_html(state)

    state["diff"] = diff
    state["status"] = "⏸ Human入力待ち — ターミナルに統合判断を入力してください"
    save_live_html(state)

    print("\n=== First Tri-Brain Answers ===")
    for r in answers:
        print(f"\n--- {r['name']} [D:{r['density']}] ---\n{r['content']}\n")
    print("\n=== Diff Analysis (First) ===\n")
    print(diff)

    # 衝突点を履歴に追加（Core Conflictの行を抽出）
    for line in diff.split("\n"):
        if "両立しない" in line:
            conflict_history.append(line.strip())
            break

    # Reframed Question抽出ユーティリティ
    def extract_reframed(diff_text):
        """
        Section 6からReframed Questionの本文を抽出。
        型ラベル行・Step1/2行・A/B行・得失行はスキップ。
        Step3（問い）行は取得対象。
        """
        import re
        in_reframe = False
        candidates = []
        skip_patterns = [
            r'^Type\s*[:：]',
            r'^\([EOVPS]\)',
            r'^Hidden Assumption',
            r'^Step[12]\s*[:：]',  # Step1:・Step2:はスキップ、問い:は通す
            r'^【',
            r'^A[=＝（：:\s]',
            r'^B[=＝（：:\s]',
            r'^###',
            r'^[EOVPS]型',
            r'^型\s*[:：]',          # 型：E（〜）形式
            r'^得る[:：]',
            r'^失う[:：]',
            r'^\s*得る[:：]',
            r'^\s*失う[:：]',
        ]
        for line in diff_text.split("\n"):
            stripped_trigger = line.strip()
            # 複数パターンでセクション開始を検出（見出し省略時も対応）
            if not in_reframe:
                import re as _re2
                if ("Reframed" in line or "🔁" in line or
                        _re2.match(r'^Step1\s*[:：]', stripped_trigger) or
                        _re2.match(r'^問い\s*[:：]', stripped_trigger)):
                    in_reframe = True
                    # 「Reframed」「🔁」見出し行はスキップ、Step1:/問い:は処理継続
                    if "Reframed" in line or "🔁" in line:
                        continue
                else:
                    continue
            stripped = line.strip()
            if not stripped:
                continue
            if any(re.match(p, stripped) for p in skip_patterns):
                continue
            # 「問い:」プレフィックスを除去（新フォーマット対応）
            stripped = re.sub(r'^(新しい問い|問い)\s*[:：]\s*', '', stripped)
            # マークダウン装飾を除去
            stripped = re.sub(r'\*\*(.+?)\*\*', r'\1', stripped)
            is_question = (
                stripped.endswith("か？") or
                stripped.endswith("か?") or
                stripped.endswith("か") or
                "べきか" in stripped or
                "するか" in stripped or
                "とみなす" in stripped or
                "とみなさない" in stripped or
                stripped.endswith("。") and len(stripped) > 15
            )
            if is_question:
                return stripped
            candidates.append(stripped)
        return candidates[0] if candidates else ""

    def _extract_reframed_fallback(diff_text):
        """extract_reframedが空の場合、A選択肢の内容を問いの代替として返す"""
        import re
        in_reframe = False
        for line in diff_text.split("\n"):
            if "Reframed" in line:
                in_reframe = True
                continue
            if not in_reframe:
                continue
            stripped = line.strip()
            if not stripped:
                continue
            # A行（A= / A＝ / A: 等）の内容を取得
            pattern_paren = r'^[\*_]*A[\*_]*（[^）]*）[\s]*[=＝：:\s][\s]*'
            pattern       = r'^[\*_]*A[\*_]*[\s]*[:：\.・、=＝\s][\s]*'
            m = re.match(pattern_paren, stripped) or re.match(pattern, stripped)
            if m:
                content = stripped[m.end():].strip()
                content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
                # 「得るもの:」「失うもの:」以降を除去（表記ゆれ対応）
                content = re.split(r'[　\s]*得る(もの)?[:：]|[　\s]*失う(もの)?[:：]|／得る|／失う|／得[:：]|／失[:：]', content)[0].strip()
                if content:
                    return content
        return ""

    def extract_hook_scene(diff_text):
        """Cognitive Hookの1行目（場所・時間・状況）を抽出"""
        in_hook = False
        for line in diff_text.split("\n"):
            if "Cognitive Hook" in line:
                in_hook = True
                continue
            if in_hook and line.strip() and not line.startswith("#"):
                return line.strip()
        return ""

    # Round 1のCognitive Hookシーンを記録
    first_hook = extract_hook_scene(diff)
    if first_hook:
        hook_history.append(first_hook)

    def extract_ab_text(diff_text, choice):
        """DiffからA/Bの文言を抽出する（表記ゆれ・複数行・括弧注釈対応）"""
        import re
        lines = diff_text.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            # 通常パターン：A: / A= / A＝ / A・ 等
            pattern = rf'^[\*_]*{choice}[\*_]*[\s]*[:：\.・、=＝\s][\s]*'
            # 括弧注釈パターン：A（〜）= / A（〜）：等
            pattern_paren = rf'^[\*_]*{choice}[\*_]*（[^）]*）[\s]*[=＝：:\s][\s]*'
            m = re.match(pattern_paren, stripped) or re.match(pattern, stripped, re.IGNORECASE)
            if m:
                content = stripped[m.end():].strip()
                content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
                # 次の行が得失の補足なら結合
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line or re.match(
                        rf'^[\*_]*[AB][\*_]*[\s]*[:：\.・、=＝\s]|^[\*_]*[AB][\*_]*（',
                        next_line
                    ) or next_line.startswith('#'):
                        break
                    content += '　' + next_line
                    j += 1
                if content:
                    return f"{choice}: {content}"
        return choice

    def extract_conflict(diff_text):
        """DiffからCore Conflictの1文を抽出"""
        import re
        in_conflict = False
        for line in diff_text.split("\n"):
            if "Core Conflict" in line:
                in_conflict = True
                continue
            if in_conflict and line.strip() and not line.startswith("#"):
                stripped = line.strip()
                # 禁止：過去の衝突... 行はスキップ
                if stripped.startswith("禁止"):
                    continue
                # 【衝突レベル：〇〇】が行頭にある場合、その注釈部分を除去して本文を取得
                # 例：「【今回の衝突レベル：価値観レベル（〜）】Logicは...」
                cleaned = re.sub(r'^【[^】]*衝突レベル[^】]*】\s*', '', stripped)
                # 注釈除去後に本文が残る場合はそれを返す
                if cleaned and cleaned != stripped:
                    text = re.sub(r'\*\*(.+?)\*\*', r'\1', cleaned)
                    return text
                # 注釈のみの行（本文なし）はスキップ
                if "衝突レベル" in stripped:
                    continue
                # 通常行
                text = re.sub(r'\*\*(.+?)\*\*', r'\1', stripped)
                return text
        return ""

    # Round 1のCore ConflictとReframed Questionをログに追加
    _conflict_levels = [
        "手段レベル", "責任レベル", "価値観レベル", "存在レベル",
    ]
    first_conflict = extract_conflict(diff)
    if first_conflict:
        state["thought_log"].append({
            "type": "conflict",
            "round": 1,
            "level": _conflict_levels[0],
            "text": first_conflict
        })
    first_reframed = extract_reframed(diff) or _extract_reframed_fallback(diff)
    _r1_ab_a = extract_ab_text(diff, "A")
    _r1_ab_b = extract_ab_text(diff, "B")
    state["thought_log"].append({
        "type": "reframed",
        "round": 1,
        "text": first_reframed if first_reframed else "Round 1 の問い直し",
        "ab_a": _r1_ab_a if _r1_ab_a != "A" else "",
        "ab_b": _r1_ab_b if _r1_ab_b != "B" else "",
    })

    # --- メインループ ---
    all_answers = [answers]
    all_diffs = [diff]
    state["all_diffs"] = all_diffs  # Round1終了時点でstateに反映
    state["all_answers"] = all_answers
    save_live_html(state)  # all_diffs反映後にHTML更新
    current_diff = diff
    choice = ""

    while True:
        # --- Human Integration ---
        print("\n" + "="*50)
        print(f"📋 Round {round_num} — 選択してください：")
        print("   A / B  → Diffで提示された選択肢")
        print("   C      → 独自のアイデア（自由入力）")
        print("   Q      → セッション終了・最終結論へ")
        print("="*50)

        choice = ""
        while choice not in ["A", "B", "C", "Q"]:
            choice = input("\n選択（A / B / C / Q）: ").strip().upper()
            if choice not in ["A", "B", "C", "Q"]:
                print("⚠️  A、B、C、またはQを入力してください。")

        if choice == "Q":
            break

        if choice == "C":
            synthesis_input = ""
            while not synthesis_input.strip():
                synthesis_input = input("あなたのアイデアを入力してください: ").strip()
            # C選択のポリシー分類（Diff AIが立場分析に使う）
            policy_hint = classify_choice(synthesis_input)
            synthesis = (
                f"元の問い：{question}\n\n"
                f"Diffの選択肢には収まらない独自の視点として以下を提案する：\n{synthesis_input}\n\n"
                f"（立場分類：{policy_hint}）\n\n"
                f"この視点から改めて分析してください。"
            )
            display_synthesis = f"C（独自）: {synthesis_input}"
            choice_label = f"{synthesis_input}（{policy_hint}）"  # 分類ラベル付きで履歴に記録
        else:
            synthesis = (
                f"元の問い：{question}\n\n"
                f"Round {round_num}のDiffで「{choice}」を選択した。\n"
                f"この選択の意味・影響・次に考えるべきことを深掘りしてください。"
            )
            display_synthesis = f"Round {round_num} 選択：{choice}"
            # DiffからA/Bの文言を抽出
            choice_label = extract_ab_text(current_diff, choice)

        # thought_log：選択を独立エントリとして追加
        state["thought_log"].append({
            "type": "choice",
            "round": round_num,
            "text": choice_label
        })
        # ユーザー選択を choice_history に蓄積（Diff AIへ渡すため）
        # 得失テキストを除去して核心だけを記録（プロンプト肥大化防止）
        import re as _re
        _label_short = _re.split(
            r'[　\s]*得る(もの)?[:：]|[　\s]*失う(もの)?[:：]|／得る|／失う|／得[:：]|／失[:：]',
            choice_label
        )[0].strip()
        # 先頭の「A: 」「B: 」も除去
        _label_short = _re.sub(r'^[A-C][:：]\s*', '', _label_short).strip()
        # 50文字以上は切り捨て
        _label_short = _label_short[:50] + ('…' if len(_label_short) > 50 else '')
        choice_history.append(_label_short if _label_short else choice_label[:50])

        state["synthesis"] = display_synthesis
        state["round_num"] = round_num + 1
        state["status"] = f"⑤ Round {round_num + 1} の3脳が処理中..."
        state["processing"] = True   # 処理中フラグ
        state["all_answers"] = all_answers  # 現時点のall_answersをstateに反映（スピナー表示のため）
        state["all_diffs"] = all_diffs
        save_live_html(state)

        # --- Next Round ---
        print(f"\n⏳ Round {round_num + 1} 処理中...\n")
        round_num += 1
        raw_results_new, diff_new = await tri_brain(synthesis, history=conflict_history, hook_history=hook_history, choice_history=choice_history)
        answers_new = [r for r in raw_results_new] if isinstance(raw_results_new, list) else []

        all_answers.append(answers_new)
        all_diffs.append(diff_new)

        # thought_log：Core ConflictとReframed Questionを追加
        next_conflict = extract_conflict(diff_new)
        if next_conflict:
            _level_idx = min(round_num - 1, len(_conflict_levels) - 1)
            state["thought_log"].append({
                "type": "conflict",
                "round": round_num,
                "level": _conflict_levels[_level_idx],
                "text": next_conflict
            })
        next_reframed = extract_reframed(diff_new) or _extract_reframed_fallback(diff_new)
        _rn_ab_a = extract_ab_text(diff_new, "A")
        _rn_ab_b = extract_ab_text(diff_new, "B")
        state["thought_log"].append({
            "type": "reframed",
            "round": round_num,
            "text": next_reframed if next_reframed else f"Round {round_num} の問い直し",
            "ab_a": _rn_ab_a if _rn_ab_a != "A" else "",
            "ab_b": _rn_ab_b if _rn_ab_b != "B" else "",
        })

        state["all_answers"] = all_answers
        state["processing"] = False
        state["status"] = f"⑥ Round {round_num} Diff分析中..."
        save_live_html(state)

        state["all_diffs"] = all_diffs
        state["all_answers"] = all_answers
        state["status"] = "⏸ Human入力待ち"
        save_live_html(state)

        print(f"\n=== Round {round_num} Tri-Brain Answers ===")
        for r in answers_new:
            print(f"\n--- {r['name']} [D:{r['density']}] ---\n{r['content']}\n")
        print(f"\n=== Diff Analysis (Round {round_num}) ===\n")
        print(diff_new)

        # 衝突点を履歴に追加
        for line in diff_new.split("\n"):
            if "両立しない" in line:
                conflict_history.append(line.strip())
                break

        # Cognitive Hookシーンを記録
        new_hook = extract_hook_scene(diff_new)
        if new_hook:
            hook_history.append(new_hook)

        current_diff = diff_new

        # ── 収束チェック（CONVERGENCE_ROUND以降）──
        if round_num >= CONVERGENCE_ROUND:
            print(f"\n🔍 収束チェック中（Round {round_num}）...")
            conv = await check_convergence(question, all_diffs)

            if conv["verdict"] == "converged":
                conv_msg = f"【収束検出】{conv['reason']}"
                state["convergence"] = conv_msg
                state["status"] = "🔁 収束を検出 — Human Final Choiceへ"
                save_live_html(state)
                print(f"\n{'='*50}")
                print(f"🔁 収束を検出しました")
                print(f"   理由：{conv['reason']}")
                print(f"{'='*50}")
                break

            # 強制終了チェック（MAX_ROUND到達）
            if round_num >= MAX_ROUND:
                state["convergence"] = f"【ラウンド上限（{MAX_ROUND}）到達】"
                state["status"] = "⛔ Round上限到達 — Human Final Choiceへ"
                save_live_html(state)
                print(f"\n{'='*50}")
                print(f"⛔ Round {MAX_ROUND} に達しました（上限）。")
                print(f"{'='*50}")
                break

    # ================================================================
    # Human Final Choice（収束後・最終立場の決定）
    # ================================================================
    print(f"\n{'='*50}")
    print(f"🎯 {round_num}ラウンドの議論を経て、最後の選択をしてください。")
    print(f"   AIの議論はここで収束しました。")
    print(f"   あなた自身の立場を決めてください。")
    print(f"{'='*50}")
    print(f"   A / B  → 最後のDiffで提示された選択肢")
    print(f"   C      → どちらでもない・独自の立場")
    print(f"   Q      → 立場を決めずに終了")
    print(f"{'='*50}")

    final_choice = ""
    while final_choice not in ["A", "B", "C", "Q"]:
        final_choice = input("\n最終選択（A / B / C / Q）: ").strip().upper()
        if final_choice not in ["A", "B", "C", "Q"]:
            print("⚠️  A、B、C、またはQを入力してください。")

    if final_choice == "C":
        final_choice_text = ""
        while not final_choice_text.strip():
            print("あなたの立場を1行で入力してください：")
            final_choice_text = input("> ").strip()
            if not final_choice_text:
                print("⚠️  入力が空です。")
        final_choice_label = f"C（独自）: {final_choice_text}"
    elif final_choice == "Q":
        final_choice_label = "立場を決めずに終了"
    else:
        final_choice_label = extract_ab_text(current_diff, final_choice)

    state["final_choice"] = final_choice_label
    state["thought_log"].append({
        "type": "final_choice",
        "text": final_choice_label
    })
    state["status"] = "✍️ Meta Reflection入力待ち"
    save_live_html(state)

    print(f"\n✅ 最終選択：{final_choice_label}")

    # ================================================================
    # Meta Reflection（Layer0 → Q1 → Q2）
    # ================================================================
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    _q_type = classify_question_type(question)
    if _q_type in ("epistemic", "value"):
        print(f"💬 最後に3つ答えてください。")
    else:
        print(f"💬 最後に2つだけ答えてください。")
    print(f"   ※ 選択肢の言葉ではなく、あなた自身の言葉で。")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Layer 0：主題への直接回答（認識論・価値観系の問いに表示）
    final_layer0 = ""
    if _q_type == "epistemic":
        while not final_layer0.strip():
            print(f"\nL0. 最初の問い「{question}」に、今のあなたの言葉で1文答えてください。")
            print(f"    （断定できなくてもOK。「〜と思う」「〜かもしれない」でよい）")
            final_layer0 = input("> ").strip()
            if not final_layer0:
                print("⚠️  入力が空です。1文だけでも書いてみてください。")
    elif _q_type == "value":
        while not final_layer0.strip():
            print(f"\nL0. 4ラウンドを経て、最初の問い「{question}」に対する")
            print(f"    今のあなたの答えを1文で。")
            print(f"    （「やっぱり〜」「どちらでもなく〜」でもOK）")
            final_layer0 = input("> ").strip()
            if not final_layer0:
                print("⚠️  入力が空です。1文だけでも書いてみてください。")

    final_q1 = ""
    while not final_q1.strip():
        print(f"\nQ1. " + REFLECTION_Q1.format(round_num=round_num))
        final_q1 = input("> ").strip()
        if not final_q1:
            print("⚠️  入力が空です。1行だけでも書いてみてください。")

    final_q2 = ""
    while not final_q2.strip():
        print(f"\nQ2. 「{final_choice_label}」を選びました。")
        print(f"    これはこれまでのあなたの考えと一致していますか？")
        print(f"    一致・不一致どちらでも、その理由を1行で。")
        final_q2 = input("> ").strip()
        if not final_q2:
            print("⚠️  入力が空です。1行だけでも書いてみてください。")

    state["final_q1"] = final_q1
    state["final_q2"] = final_q2
    state["final_layer0"] = final_layer0
    _final_parts = [f"最終選択：{final_choice_label}"]
    if final_layer0:
        _final_parts.append(f"L0: {final_layer0}")
    _final_parts += [f"Q1: {final_q1}", f"Q2: {final_q2}"]
    state["final"] = "\n".join(_final_parts)
    state["status"] = "✅ セッション完了"
    state["thought_log"].append({
        "type": "final",
        "layer0": final_layer0,
        "q1": final_q1,
        "q2": final_q2,
        "text": state["final"]
    })
    save_live_html(state)

    print("\n=== FINAL RESULT ===")
    print(f"最終選択：{final_choice_label}")
    if final_layer0:
        print(f"L0. {final_layer0}")
    print(f"Q1. {final_q1}")
    print(f"Q2. {final_q2}")

    # --- HTML保存（アーカイブ用）---
    save_html(
        question,
        all_answers[0],
        all_diffs[0],
        state.get("synthesis", ""),
        all_answers[-1] if len(all_answers) > 1 else all_answers[0],
        all_diffs[-1] if len(all_diffs) > 1 else all_diffs[0],
        state["final"]
    )


if __name__ == "__main__":
    asyncio.run(tri_brain_loop())
    # セッション終了後もHTTPサーバーを維持（ブラウザで結果を閲覧できるように）
    print(f"\n✅ セッション終了。ブラウザで結果を確認してください。")
    print(f"   http://127.0.0.1:{HTTP_PORT}/tri_brain_live.html")
    print(f"   終了するには Ctrl+C を押してください。")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n終了します。")
