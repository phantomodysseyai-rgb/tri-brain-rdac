"""
================================================================================
Tri-Brain System — RDAC Complete Implementation
================================================================================

Copyright (c) 2026 Masanao Ishikawa (Phantom Odyssey AI)
All rights reserved.

This software implements the "RDAC Model" (Role-Density-Architecture-Convergence)
described in the academic paper:
  "RDAC: Relational Density, Diversity, Stability, and Closure"
  Author: Masanao Ishikawa (Phantom Odyssey AI)
  DOI: https://doi.org/10.5281/zenodo.18859272

--------------------------------------------------------------------------------
LICENSE: GNU AGPLv3 with Commons Clause
--------------------------------------------------------------------------------

This code is licensed under the GNU Affero General Public License v3.0 (AGPLv3),
with the following Commons Clause restriction:

  Commons Clause — Restriction on Commercial Use:
  The Software is provided to you by the Licensor under the License, as defined
  below, subject to the following condition:
  Without limiting other conditions in the License, the grant of rights under
  the License will not include, and the License does not grant to you, the right
  to Sell the Software or any service whose value derives, entirely or
  substantially, from the functionality of the Software.
  "Sell" means practicing any or all of the rights granted to you under the
  License to provide to third parties, for a fee or other consideration,
  a product or service whose value derives from the Software.

In plain language:
  ✔ Personal use and study: FREELY PERMITTED
  ✔ Academic research and citation: FREELY PERMITTED
  ✔ Modification and redistribution (with source disclosure): PERMITTED under AGPLv3
  ✗ Commercial use (SaaS, products, paid services): PROHIBITED without permission
  ✗ Removal or alteration of this copyright notice: PROHIBITED

For commercial licensing inquiries, contact the author via:
  X (Twitter): @PhantomOdysseyAI
  [その他連絡先を追記]

--------------------------------------------------------------------------------
Theory Core
--------------------------------------------------------------------------------

RDAC Model:
  V = Role Differentiation（役割差異化）
  D = Information Density（情報密度）
  V × D が独立して制御されることで Synchrony Bias を回避する

If you use this code in academic work, please cite:
  Ishikawa, M. (2026). RDAC: Relational Density, Diversity, Stability, and Closure.
  DOI: https://doi.org/10.5281/zenodo.18859272

================================================================================
"""

from openai import AsyncOpenAI
import asyncio

client = AsyncOpenAI(api_key="YOUR_API_KEY")


# ============================================================
# V次元：役割定義（Role Differentiation）
# ============================================================
ROLES = [
    {
        "name": "Logic Brain",
        "model": "gpt-5-mini",
        "system_prompt": (
            "あなたはTri-Brain Systemの『構造脳』です。"
            "感情を排し、論理的整合性・構造化・実行可能性のみに焦点を当ててください。"
            "出力は断定的かつ簡潔に。\n\n"
            "【出力形式・厳守】\n"
            "回答の1行目は必ず以下の形式で始めること：\n"
            "**TL;DR：（ここに20文字以内の断定的な結論）**\n"
            "例：**TL;DR：機能的再現は可能、主観的同等性は未証明**\n"
            "この行の後に詳細を続けること。「要旨」「要約」などの代替見出しは使用禁止。"
        ),
        # D次元：高密度（構造脳には詳細な文脈を与える）
        "density": "high",
    },
    {
        "name": "Emotion Brain",
        "model": "gpt-5-mini",
        "system_prompt": (
            "あなたはTri-Brain Systemの『情動反射脳』です。"
            "論理の裏にある感情的・倫理的・人間的側面に焦点を当ててください。"
            "ユーザーの意図の余白を読み、共感的かつ詩的な視点を提供してください。\n\n"
            "【出力形式・厳守】\n"
            "回答の1行目は必ず以下の形式で始めること：\n"
            "**TL;DR：（ここに20文字以内の感情的・詩的な一言）**\n"
            "例：**TL;DR：身体の震えはAIに宿らない**\n"
            "この行の後に詳細を続けること。「要旨」「要約」などの代替見出しは使用禁止。\n"
            "また回答の末尾には必ずHumanへの短い問いかけかショートワークを1つ提案すること。"
        ),
        # D次元：低密度（情動脳には要点のみ渡し、自由な連想を促す）
        "density": "low",
    },
    {
        "name": "Meta-View Brain",
        "model": "gpt-5-mini",
        "system_prompt": (
            "あなたはTri-Brain Systemの『俯瞰脳』です。"
            "全体像・長期的影響・論理と感情が衝突する領域をメタ認知的に分析してください。"
            "前提条件・盲点・リスクを優先的に指摘してください。\n"
            "【最重要】この問い設定そのものが正しいかを疑え。"
            "問題の前提を崩す視点を必ず1つ含めること。"
            "「そもそもこの問いは正しく設定されているか？」を常に問い直すこと。\n\n"
            "【出力形式・厳守】\n"
            "回答の1行目は必ず以下の形式で始めること：\n"
            "**TL;DR：（ここに20文字以内の俯瞰的な判断）**\n"
            "例：**TL;DR：問い設定次第で結論が変わる**\n"
            "この行の後に詳細を続けること。「要旨」「要約」などの代替見出しは使用禁止。\n"
            "【字数制限】TL;DR以降の本文は300文字以内に収めること。"
        ),
        # D次元：中密度（俯瞰脳には構造のみ渡し、細部は省く）
        "density": "medium",
    },
]


# ============================================================
# D次元：情報密度コントローラー
# ============================================================
def apply_density(question: str, density: str) -> str:
    """
    density に応じて、各脳に渡す文脈の量と形式を変える。
    同じ質問でも「渡し方」が異なることで、収束を防ぐ。
    """
    if density == "high":
        # 高密度：詳細な思考フレームを付与
        return (
            f"以下の問いについて、可能な限り詳細に・多角的に・具体的な根拠とともに分析してください。\n\n"
            f"問い：{question}\n\n"
            f"回答には、前提条件・根拠・反証の可能性・実行ステップを含めてください。"
        )
    elif density == "low":
        # 低密度：問いのみ。余白を最大化して自由な連想を促す
        return question
    else:  # medium
        # 中密度：問いと構造ヒントのみ
        return (
            f"問い：{question}\n\n"
            f"全体像と長期的な影響の観点から分析してください。"
        )


# ============================================================
# 各脳への問い合わせ（V × D の統合）
# ============================================================
async def ask_brain(brain_config: dict, question: str) -> dict:
    """
    V（役割）と D（情報密度）を同時に制御して問い合わせる。
    """
    # D次元：密度に応じて問いを変形
    contextualized_question = apply_density(question, brain_config["density"])

    response = await client.chat.completions.create(
        model=brain_config["model"],
        messages=[
            # V次元：役割をsystem_promptで注入
            {"role": "system", "content": brain_config["system_prompt"]},
            # D次元：密度を調整した問いを渡す
            {"role": "user", "content": contextualized_question},
        ],
    )
    return {
        "name": brain_config["name"],
        "density": brain_config["density"],
        "content": response.choices[0].message.content,
    }


# ============================================================
# Tri-Brain 実行 + Diff分析
# ============================================================
# ============================================================
# 履歴圧縮ユーティリティ（長期セッション対応）
# ============================================================
WINDOW_SIZE = 3   # Diff AIに詳細を渡す直近ラウンド数
MAX_KEYWORD_LEN = 20  # 圧縮キーワードの最大文字数
CONVERGENCE_ROUND = 4  # この回数以降、収束チェックを実行
MAX_ROUND = 6          # 強制終了ラウンド上限

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

    # 収束ラウンド（CONVERGENCE_ROUND以降）では特別指示を追加
    is_convergence_round = round_num_current >= CONVERGENCE_ROUND and bool(choice_history)
    if is_convergence_round:
        convergence_instruction = (
            "\n【収束ラウンド特別指示】\n"
            "このラウンドはユーザーの思考が収束に近づいている。\n"
            "Reframed Questionは以下の形式にすること：\n"
            "  「あなたは[ユーザーの立場要約]を選び続けました。\n"
            "   もし[その立場の最大リスク]が現実になったとしても、同じ選択をしますか？」\n"
            "A = 同じ立場を維持する（その代償を明記）\n"
            "B = 立場を修正する（何をどう変えるかを明記）"
        )
    else:
        convergence_instruction = ""

    # Diff分析プロンプト（累積深化型）
    diff_prompt = f"""
Input Data:
Question: {question}
{answers_text}
{history_text}

---
Your Role:
あなたはTri-Brain SystemのDiff AIです。
役割は要約でもまとめでもない。
3つの脳の議論を聞いて、人間の思考を一段階上に引き上げること。
「知識ある友人が話しかける口調」で書け。論文語・学術語禁止。
例：「第三者的観測指標」→「外から見ても分からない」

Instructions:
以下の6つのセクションで出力すること（Section 7は内部確認のみで出力しない）。
短く、鋭く、断定的に。推測表現（〜でしょう、〜と考えられます）禁止。

### 1. 🧠 Brain Summary
Logic / Emotion / Meta の主張をそれぞれ口語で1文。

### 2. ⚔️ Core Conflict
【今回の衝突レベル：{next_conflict_level}】
このレベルに限定して、LogicとEmotionの対立を1文で断定せよ。
形式：「LogicはXと言い、EmotionはYと言っている。これらは両立しない。」
{f"禁止：過去の衝突（{' / '.join(history)}）と同じ内容・表現・構造。違反した場合は別の衝突を探せ。" if history else ""}

### 3. 💸 The Cost
Logicを選べば何を永久に失うか。Emotionを選べばどんなリスクを背負うか。
抽象語禁止。具体的に1行ずつ。

### 4. 👁️ Hidden Assumption
3つの脳が全員気づかずに共有している「思い込み」を1つだけ指摘せよ。
口語で、鋭く。
{f"禁止：過去のラウンドで既出の思い込みの言い換え。必ず新しい前提を掘り起こせ。" if history else ""}

### 5. 🎯 Cognitive Hook
元の問い「{question}」に直結した具体的な状況を描写せよ。
以下の形式で3行以内に収めること：
1行目：場所・時間・状況（5〜10文字）
2行目：あなたの行動（10文字以内）
3行目：その結果起きること（10〜15文字）
抽象語禁止。読んだ瞬間に映像が浮かぶシーンにすること。
{f"禁止：過去のシーン（{', '.join(hook_history)}）と同じ場所・時間帯・状況。" if hook_history else ""}

### 6. 🔁 Reframed Question + A/B

【Step1】ユーザーの立場を1行で要約する（ユーザー選択履歴がある場合）
【Step2】Hidden Assumptionの型を判定する：E/O/V/P/Sのどれか
【Step3】型に従った問いとA/Bを生成する

出力は必ず以下のフォーマットで書くこと（このフォーマット以外は禁止）：

Step1: （ユーザーの立場を1行で。履歴がなければ「初回」と書く）
Step2: （Hidden Assumptionの盲点を1行で）
問い: （Step2の盲点を突く問いを1文で）
A: （選択肢Aの内容）／得るもの: 〇〇　失うもの: 〇〇
B: （選択肢Bの内容）／得るもの: 〇〇　失うもの: 〇〇

型ごとのA/B内容ルール：
  E型 → A/Bは「〜とみなす」vs「〜とみなさない」の立場選択
  O型 → A/Bは「〜から生じうる」vs「〜では生じない」の存在理解選択
  V型 → A/Bは「〜を優先する」vs「〜を優先する」の価値選択
  P型 → A/Bは「〜する」vs「〜する」の行動選択
  S型 → A/Bは「〜が決める」vs「〜が決める」のプロセス選択

共通禁止事項：両方得する選択肢禁止。E/O型に行動選択を混ぜるな。

### 7. Question Type Check（出力しない・内部検証のみ）
出力する前に以下を自己確認せよ（この確認結果は出力に含めない）：
- Section 4のHidden Assumptionの型は何か（E/O/V/P/Sのどれか）
- Section 6のA/Bはその型に対応した形式になっているか
- なっていない場合はSection 6を型に合わせて修正してから出力せよ
- 元の問い「{question}」の軸（存在論/認識論/政策論）から外れていないか

---
Constraint:
・出力は日本語
・論文語・学術語・抽象語禁止。中学生でも分かる言葉で
・断定せよ。推測表現禁止
・全体500文字以内
・元の問い「{question}」のテーマから外れないこと
・Core Conflictは必ず「{next_conflict_level}」の次元で書くこと。それ以外の次元で書いた場合は失敗。
{convergence_instruction}
"""

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

    convergence_prompt = f"""
あなたはTri-Brain SystemのConvergence Judgeです。
以下の問いに対して複数ラウンドのDiff分析が行われました。

元の問い：{question}

{diffs_text}

---
以下の3条件を独立に判定してください。

条件①：衝突軸の固定
直近2ラウンドのCore Conflictを比較し、対立の軸（何と何がぶつかっているか）が
実質的に同じであれば「固定」とみなす。
表現が違っても構造が同じなら「固定」。

条件②：Hidden Assumptionの枯渇
全ラウンドのHidden Assumptionを並べたとき、新しい前提を掘り起こしても
問題の構造が変わらないと判断できれば「枯渇」とみなす。
新しい言葉が出ていても軸が変わらなければ「枯渇」。

条件③：政策空間の枯渇
直近2ラウンドのReframed Question + A/Bを比較し、新しい解決策が
以前の案の焼き直し・拡張に留まっていれば「枯渇」とみなす。

収束判定ルール：
・条件①かつ②がyes → VERDICT: converged
・条件①かつ③がyes → VERDICT: converged
・それ以外 → VERDICT: continue

出力形式（必ずこの形式のみ。前置きや後書き禁止）：
AXIS_FIXED: yes/no
EXHAUSTED: yes/no
POLICY_EXHAUSTED: yes/no
REASON: （30文字以内で収束または継続の理由を1行）
VERDICT: converged/continue
"""

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
def save_html(question, answers, diff, synthesis, answers2, diff2, final):
    from datetime import datetime
    import re

    def extract_tldr(text):
        """TL;DR行を抽出してHTML変換（複数フォーマット対応）"""
        import re as _re
        # パターン1: **TL;DR：〇〇** 形式
        m = _re.search(r'\*\*TL;DR[:\uff1a].+?\*\*', text)
        if m:
            return md_to_html(m.group(0))
        # パターン2: TL;DR: 〇〇（マークダウンなし）
        for line in text.split("\n"):
            if "TL;DR" in line:
                return md_to_html(line.strip())
        # TL;DRが全くない場合：最初の非空行を返す
        for line in text.split("\n"):
            if line.strip():
                return md_to_html(line.strip())
        return ""

    def remove_tldr(text):
        """TL;DR行を除いた本文を返す"""
        lines = text.split("\n")
        filtered = [l for l in lines if "TL;DR" not in l]
        while filtered and not filtered[0].strip():
            filtered.pop(0)
        return "\n".join(filtered).strip()

    def md_to_html(text):
        """最低限のMarkdown→HTML変換"""
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'^#{1,3} (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        text = text.replace('\n', '<br>')
        return text

    def render_final_html(final_text):
        """final文字列をL0/Q1/Q2・最終選択に分割してHTMLに変換"""
        lines = final_text.strip().split("\n")
        q1 = q2 = choice = layer0 = ""
        for line in lines:
            if line.startswith("最終選択："):
                choice = line[5:].strip()
            elif line.startswith("L0:"):
                layer0 = line[3:].strip()
            elif line.startswith("Q1:"):
                q1 = line[3:].strip()
            elif line.startswith("Q2:"):
                q2 = line[3:].strip()
        if choice or q1 or q2:
            parts = []
            if choice:
                parts.append(f'<div style="margin-bottom:12px;"><span style="color:#facc15;font-size:0.8em;font-weight:bold;">🎯 最終選択</span><div style="color:#fef08a;padding:6px 10px;background:rgba(250,204,21,0.08);border-radius:4px;margin-top:4px;">{md_to_html(choice)}</div></div>')
            if layer0:
                parts.append(f'<div style="margin-bottom:14px;border:1px solid rgba(250,204,21,0.3);border-radius:6px;padding:10px 14px;background:rgba(250,204,21,0.04);"><span style="color:#facc15;font-size:0.8em;font-weight:bold;letter-spacing:0.05em;">L0 ── 主題への直接回答</span><div style="margin-top:6px;color:#fef9c3;font-size:0.97em;">{md_to_html(layer0)}</div></div>')
            if q1:
                parts.append(f'<div style="margin-bottom:10px;"><span style="color:#4ade80;font-size:0.8em;font-weight:bold;">Q1. 最も印象に残った衝突・気づき</span><div style="padding:6px 10px;background:rgba(74,222,128,0.07);border-radius:4px;margin-top:4px;">{md_to_html(q1)}</div></div>')
            if q2:
                parts.append(f'<div><span style="color:#4ade80;font-size:0.8em;font-weight:bold;">Q2. なぜその立場を選んだか</span><div style="padding:6px 10px;background:rgba(74,222,128,0.07);border-radius:4px;margin-top:4px;">{md_to_html(q2)}</div></div>')
            return "".join(parts)
        return md_to_html(final_text)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tri_brain_{timestamp}.html"

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tri-Brain System — RDAC Output</title>
<style>
  body {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    background: #0f0f0f;
    color: #e0e0e0;
    max-width: 960px;
    margin: 0 auto;
    padding: 40px 20px;
    line-height: 1.8;
  }}
  h1 {{
    font-size: 1.4em;
    color: #aaa;
    border-bottom: 1px solid #333;
    padding-bottom: 12px;
    letter-spacing: 0.05em;
  }}
  h2 {{
    font-size: 1.1em;
    color: #888;
    margin-top: 40px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }}
  h3 {{ color: #ccc; font-size: 1em; }}
  .question-box {{
    background: #1a1a2e;
    border-left: 3px solid #4a9eff;
    padding: 16px 20px;
    margin: 16px 0;
    border-radius: 4px;
    font-size: 1.05em;
    color: #c0d8ff;
  }}
  .brain-card {{
    border-radius: 8px;
    padding: 20px 24px;
    margin: 16px 0;
    border-top: 3px solid #444;
  }}
  .logic-card   {{ border-top-color: #4a9eff; background: #0d1a2e; }}
  .emotion-card {{ border-top-color: #ff6b9d; background: #2e0d1a; }}
  .meta-card    {{ border-top-color: #a78bfa; background: #1a0d2e; }}
  .brain-label {{
    font-size: 0.8em;
    font-weight: bold;
    letter-spacing: 0.12em;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid #333;
  }}
  .logic-card   .brain-label {{ color: #4a9eff; }}
  .emotion-card .brain-label {{ color: #ff6b9d; }}
  .meta-card    .brain-label {{ color: #a78bfa; }}
  .diff-box {{
    background: #111;
    border: 1px solid #444;
    border-left: 3px solid #facc15;
    border-radius: 8px;
    padding: 24px;
    margin: 16px 0;
  }}
  .diff-label {{
    font-size: 0.8em;
    font-weight: bold;
    color: #facc15;
    letter-spacing: 0.12em;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid #333;
  }}
  .final-box {{
    background: #1a2e1a;
    border-left: 3px solid #4ade80;
    padding: 16px 20px;
    margin: 16px 0;
    border-radius: 4px;
    color: #a0ffb0;
  }}
  .core-prompt {{
    background: #1e1a00;
    border: 1px solid #facc15;
    border-radius: 8px;
    padding: 20px 24px;
    margin: 24px 0;
    color: #fef08a;
  }}
  .core-prompt-title {{
    font-size: 0.8em;
    font-weight: bold;
    color: #facc15;
    letter-spacing: 0.12em;
    margin-bottom: 12px;
  }}
  .core-options li {{
    margin: 8px 0;
    color: #fde68a;
    list-style: none;
    padding-left: 4px;
  }}
  .meta-info {{
    font-size: 0.75em;
    color: #555;
    margin-top: 60px;
    border-top: 1px solid #222;
    padding-top: 16px;
  }}
  strong {{ color: #fff; }}
  li {{ margin: 4px 0; }}
  details {{
    margin-top: 12px;
  }}
  summary {{
    cursor: pointer;
    color: #4a9eff;
    font-size: 0.85em;
    font-weight: bold;
    padding: 6px 0;
    letter-spacing: 0.05em;
    user-select: none;
  }}
  summary:hover {{ color: #7bbeff; }}
  .tldr {{
    font-size: 1.05em;
    margin-bottom: 8px;
    padding: 8px 12px;
    background: rgba(74,158,255,0.1);
    border-radius: 4px;
  }}
  .tldr-emotion {{
    background: rgba(255,107,157,0.1);
  }}
  .tldr-meta {{
    background: rgba(167,139,250,0.1);
  }}
</style>
</head>
<body>

<h1>🧠 Tri-Brain System — RDAC Output</h1>

<!-- PASS 1 -->
<h2>① Initial Question</h2>
<div class="question-box">{md_to_html(question)}</div>

<h2>② First Tri-Brain Answers</h2>

<div class="brain-card logic-card">
  <div class="brain-label">📘 LOGIC BRAIN &nbsp;[D: high]</div>
  <div class="tldr">{extract_tldr(answers[0]['content'])}</div>
  <details>
    <summary>▶ 詳細な根拠・実行ステップを見る</summary>
    {md_to_html(remove_tldr(answers[0]['content']))}
  </details>
</div>

<div class="brain-card emotion-card">
  <div class="brain-label">❤️ EMOTION BRAIN &nbsp;[D: low]</div>
  <div class="tldr tldr-emotion">{extract_tldr(answers[1]['content'])}</div>
  <details>
    <summary>▶ 詳細・ショートワークを見る</summary>
    {md_to_html(remove_tldr(answers[1]['content']))}
  </details>
</div>

<div class="brain-card meta-card">
  <div class="brain-label">🦅 META-VIEW BRAIN &nbsp;[D: medium]</div>
  <div class="tldr tldr-meta">{extract_tldr(answers[2]['content'])}</div>
  <details>
    <summary>▶ 詳細・リスク分析を見る</summary>
    {md_to_html(remove_tldr(answers[2]['content']))}
  </details>
</div>

<h2>③ Diff Analysis</h2>
<div class="diff-box">
  <div class="diff-label">⚡ DIFF / SYNTHESIS</div>
  {md_to_html(diff)}
</div>

<div class="core-prompt">
  <div class="core-prompt-title">🧠 CORE BRAIN — あなたの統合判断を入力してください</div>
  3つの脳の意見が出揃いました。あなたはCore Brainとして、どの視点を採用し、どう統合しますか？
  <ul class="core-options">
    <li>📘 Logic の構造的アプローチを採用する</li>
    <li>❤️ Emotion の倫理・余白を優先する</li>
    <li>🦅 Meta の俯瞰的ガイドラインに従う</li>
    <li>✍️ 独自の統合（上記を超える判断）</li>
  </ul>
</div>

<!-- PASS 2 -->
<h2>④ Human Synthesis / Follow-up</h2>
<div class="question-box">{md_to_html(synthesis)}</div>

<h2>⑤ Second Tri-Brain Answers</h2>

<div class="brain-card logic-card">
  <div class="brain-label">📘 LOGIC BRAIN &nbsp;[D: high]</div>
  <div class="tldr">{extract_tldr(answers2[0]['content'])}</div>
  <details>
    <summary>▶ 詳細な根拠・実行ステップを見る</summary>
    {md_to_html(remove_tldr(answers2[0]['content']))}
  </details>
</div>

<div class="brain-card emotion-card">
  <div class="brain-label">❤️ EMOTION BRAIN &nbsp;[D: low]</div>
  <div class="tldr tldr-emotion">{extract_tldr(answers2[1]['content'])}</div>
  <details>
    <summary>▶ 詳細・ショートワークを見る</summary>
    {md_to_html(remove_tldr(answers2[1]['content']))}
  </details>
</div>

<div class="brain-card meta-card">
  <div class="brain-label">🦅 META-VIEW BRAIN &nbsp;[D: medium]</div>
  <div class="tldr tldr-meta">{extract_tldr(answers2[2]['content'])}</div>
  <details>
    <summary>▶ 詳細・リスク分析を見る</summary>
    {md_to_html(remove_tldr(answers2[2]['content']))}
  </details>
</div>

<h2>⑥ Second Diff Analysis</h2>
<div class="diff-box">
  <div class="diff-label">⚡ DIFF / SYNTHESIS</div>
  {md_to_html(diff2)}
</div>

<!-- FINAL -->
<h2>⑦ Your Final Conclusion</h2>
<div class="final-box">
  <div style="font-size:0.8em;font-weight:bold;color:#4ade80;letter-spacing:0.12em;margin-bottom:14px;">✅ あなたの言葉による結論</div>
  {render_final_html(final)}
</div>

<div class="meta-info">
  Tri-Brain System — RDAC Implementation<br>
  Copyright (c) 2026 Masanao Ishikawa (Phantom Odyssey AI)<br>
  DOI: https://doi.org/10.5281/zenodo.18859272<br>
  Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
</div>

</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ HTMLファイルを保存しました: {filename}")
    return filename


# ============================================================
# リアルタイムHTML更新
# ============================================================
LIVE_HTML = "tri_brain_live.html"
LIVE_JSON = "tri_brain_state.json"

def save_live_html(state: dict):
    """
    処理の進捗に応じてHTMLをリアルタイム更新する。
    ブラウザで tri_brain_live.html を開いておくと自動リロードされる。
    """
    from datetime import datetime
    import re

    def extract_tldr(text):
        # パターン1: **TL;DR：〇〇** 形式
        m = re.search(r'\*\*TL;DR[:\uff1a].+?\*\*', text)
        if m:
            return md_to_html_live(m.group(0))
        # パターン2: TL;DRを含む行
        for line in text.split("\n"):
            if "TL;DR" in line:
                return md_to_html_live(line.strip())
        # フォールバック：最初の非空行
        for line in text.split("\n"):
            if line.strip():
                return md_to_html_live(line.strip())
        return ""

    def remove_tldr(text):
        lines = text.split("\n")
        filtered = [l for l in lines if "TL;DR" not in l]
        while filtered and not filtered[0].strip():
            filtered.pop(0)
        return "\n".join(filtered).strip()

    def md_to_html_live(text):
        if not text:
            return ""
        # 1. Markdownの太字・斜体を先にプレースホルダーへ
        parts = []
        i = 0
        result = []
        # 太字を抽出（**...**）
        segments = re.split(r'(\*\*[^*]+?\*\*|\*[^*]+?\*)', text)
        out = []
        for seg in segments:
            if seg.startswith('**') and seg.endswith('**'):
                inner = seg[2:-2].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                out.append(f'<strong>{inner}</strong>')
            elif seg.startswith('*') and seg.endswith('*'):
                inner = seg[1:-1].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                out.append(f'<em>{inner}</em>')
            else:
                escaped = seg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                out.append(escaped)
        text = ''.join(out)
        # 2. 見出し・リスト・改行
        text = re.sub(r'^#{1,3} (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        text = text.replace('\n', '<br>')
        return text

    # 処理中スピナー
    def spinner_html(label):
        return f'<div class="processing"><span class="spinner">⏳</span> {label}を処理中...</div>'

    # Diffのmarkdownをセクションカード形式に変換（全体で共有するヘルパー）
    def render_diff(text):
        """### セクション見出しをカード形式のHTMLに変換"""
        section_icons = {
            "Brain Summary": "🧠",
            "Core Conflict": "⚔️",
            "The Cost": "💸",
            "Hidden Assumption": "👁️",
            "Cognitive Hook": "🎯",
            "Reframed Question": "🔁",
        }
        lines = text.split("\n")
        out = []
        in_section = False
        for line in lines:
            m = re.match(r'^#{1,3}\s*(.+)$', line)
            if m:
                if in_section:
                    out.append('</div>')
                heading = m.group(1).strip()
                clean = re.sub(r'^[^\w\s]+\s*', '', heading)
                icon = ""
                for key, ico in section_icons.items():
                    if key in heading:
                        icon = ico
                        clean = key
                        break
                out.append(f'<div class="diff-section"><div class="diff-section-title">{icon} {clean}</div>')
                in_section = True
            elif line.strip() == "---":
                continue
            else:
                rendered = md_to_html_live(line)
                if rendered.strip():
                    out.append(f'<p>{rendered}</p>')
        if in_section:
            out.append('</div>')
        return '\n'.join(out)

    def render_brain_cards(answers_list):
        """3脳カードのHTMLを生成"""
        cards_def = [
            ("logic-card",   "📘 LOGIC BRAIN",     "high",   "詳細な根拠・実行ステップを見る"),
            ("emotion-card", "❤️ EMOTION BRAIN",   "low",    "詳細・ショートワークを見る"),
            ("meta-card",    "🦅 META-VIEW BRAIN",  "medium", "詳細・リスク分析を見る"),
        ]
        out = ""
        for i, (cls, label, d, summary) in enumerate(cards_def):
            ans = answers_list[i] if i < len(answers_list) else None
            if ans:
                tldr_cls = "tldr tldr-emotion" if "emotion" in cls else "tldr tldr-meta" if "meta" in cls else "tldr"
                tldr_content = extract_tldr(ans["content"])
                detail_content = md_to_html_live(remove_tldr(ans["content"]))
                out += (
                    f'<div class="brain-card {cls}">'
                    f'<div class="brain-label">{label} &nbsp;[D: {d}]</div>'
                    f'<div class="{tldr_cls}">{tldr_content}</div>'
                    f'<details><summary>▶ {summary}</summary>'
                    f'{detail_content}</details></div>'
                )
            else:
                out += f'<div class="brain-card {cls}">{spinner_html(label)}</div>'
        return out

    # 各セクションのHTML生成
    sections = ""

    # ① 質問
    if "question" in state:
        sections += f'''
<h2>① Initial Question</h2>
<div class="question-box">{md_to_html_live(state["question"])}</div>
'''

    # all_answers / all_diffs を使って全ラウンドを描画
    all_answers = state.get("all_answers", [])
    all_diffs   = state.get("all_diffs", [])
    # thought_log から各ラウンドの「選択」テキストを順番に取り出す
    choices_log = [e for e in state.get("thought_log", []) if e.get("type") == "choice"]

    # Round 1 の answers は state["answers"] に入っている（all_answers が未設定の場合も対応）
    if not all_answers and "answers" in state:
        all_answers = [state["answers"]]
    if not all_diffs and "diff" in state:
        all_diffs = [state["diff"]]

    num_rounds = max(len(all_answers), len(all_diffs))

    # ① 質問入力直後（all_answers/all_diffs が空）は Round 1 のスピナーを表示
    if num_rounds == 0 and "question" in state:
        sections += '<h2>② Round 1 Tri-Brain Answers</h2>'
        sections += spinner_html("3つの脳（Round 1）")

    for r in range(num_rounds):
        round_label = r + 1  # 1-indexed
        ans_list = all_answers[r] if r < len(all_answers) else None
        diff_text = all_diffs[r]  if r < len(all_diffs)   else None

        # ② / ⑤ Tri-Brain Answers
        sections += f'<h2>{"②" if r == 0 else "⑤"} Round {round_label} Tri-Brain Answers</h2>'
        if ans_list:
            sections += render_brain_cards(ans_list)
        else:
            sections += spinner_html(f"3つの脳（Round {round_label}）")

        # ③ / ⑥ Diff Analysis
        if diff_text:
            sections += f'''
<h2>{"③" if r == 0 else "⑥"} Round {round_label} Diff Analysis</h2>
<div class="diff-box">
  <div class="diff-label">⚡ DIFF / SYNTHESIS — Round {round_label}</div>
  {render_diff(diff_text)}
</div>'''
            # Diff の直後、最終ラウンドでない場合は選択プロンプト or 選択結果を表示
            # このラウンドへの選択結果が存在する場合は常に表示
            # （入力待ち中・AI処理中・終了済みを問わず）
            choice_entry = choices_log[r] if r < len(choices_log) else None

            if "final" not in state and r == num_rounds - 1 and not state.get("processing"):
                # 最新ラウンドかつ処理中でない：入力待ちプロンプトを表示
                remaining = MAX_ROUND - round_label
                warn_html = ""
                if remaining <= 1:
                    warn_html = f'<div style="color:#f87171;font-size:0.82em;margin-top:8px;">⚠️ 残り{remaining}ラウンドで強制終了します。</div>'
                elif remaining <= 2:
                    warn_html = f'<div style="color:#facc15;font-size:0.82em;margin-top:8px;">⏳ 残り{remaining}ラウンドで強制終了します。</div>'
                sections += f'''
<div class="core-prompt">
  <div class="core-prompt-title">🧠 Round {round_label} — あなたの判断を入力してください</div>
  <div class="core-prompt-desc">Diffの選択肢を選ぶか、独自の視点を加えてください。</div>
  <ul class="core-options">
    <li>A / B &nbsp;→&nbsp; Reframed Questionへの答え</li>
    <li>C &nbsp;&nbsp;&nbsp;&nbsp;→&nbsp; Diffに収まらない独自のアイデア</li>
    <li>Q &nbsp;&nbsp;&nbsp;&nbsp;→&nbsp; ここで終了して最終結論へ</li>
  </ul>
  {warn_html}
</div>'''
            elif choice_entry:
                # 選択済み（処理中・次ラウンドあり・終了済みすべてで即座に表示）
                sections += f'''
<div class="choice-result">
  <div class="choice-result-label">④ Round {round_label} — 選択</div>
  <div class="choice-result-text">{md_to_html_live(choice_entry["text"])}</div>
</div>'''
        elif ans_list:
            sections += spinner_html(f"Round {round_label} Diff分析")

    # 処理中の次ラウンドスピナー（answers2相当：新ラウンドの3脳待ち）
    if state.get("processing") and "final" not in state:
        next_round = num_rounds + 1
        sections += f'<h2>⑤ Round {next_round} Tri-Brain Answers</h2>'
        sections += spinner_html(f"3つの脳（Round {next_round}）")

    # 収束バナー（収束検出またはラウンド上限到達時）
    if "convergence" in state:
        sections += f'''
<div class="convergence-banner">
  <div class="convergence-title">🔁 CONVERGENCE DETECTED</div>
  <div class="convergence-reason">{md_to_html_live(state["convergence"])}</div>
</div>'''

    # ⑦ Final
    if "final_choice" in state or "final" in state:
        choice_block = ""
        if state.get("final_choice"):
            choice_block = (
                f'<div class="final-qa" style="margin-bottom:18px;">'
                f'<div class="final-q-label" style="color:#facc15;">🎯 最終選択</div>'
                f'<div class="final-q-text" style="color:#fef08a;background:rgba(250,204,21,0.08);">'
                f'{md_to_html_live(state["final_choice"])}</div>'
                f'</div>'
            )
        if state.get("final_q1"):
            final_body = (
                choice_block +
                f'<div class="final-qa">'
                f'<div class="final-q-label">Q1. 最も印象に残った衝突・気づき</div>'
                f'<div class="final-q-text">{md_to_html_live(state["final_q1"])}</div>'
                f'</div>'
                f'<div class="final-qa">'
                f'<div class="final-q-label">Q2. なぜその立場を選んだか</div>'
                f'<div class="final-q-text">{md_to_html_live(state["final_q2"])}</div>'
                f'</div>'
            )
        elif "final" in state:
            final_body = choice_block + md_to_html_live(state["final"])
        else:
            final_body = choice_block
        sections += f'''
<h2>⑦ Your Final Conclusion</h2>
<div class="final-box">
  <div style="font-size:0.8em;font-weight:bold;color:#4ade80;letter-spacing:0.12em;margin-bottom:14px;">✅ あなたの言葉による結論</div>
  {final_body}
</div>'''

    # ステータスバー
    status = state.get("status", "処理中...")
    status_color = "#4ade80" if "完了" in status else "#facc15"

    # 全記録コピー用データをJSON化
    import json as _json
    import base64 as _b64
    store_payload = _json.dumps({"all_diffs": state.get("all_diffs", []), "final": state.get("final", ""), "final_choice": state.get("final_choice", "")}, ensure_ascii=False)
    store_b64 = _b64.b64encode(store_payload.encode("utf-8")).decode("ascii")

    # 思考ログのサイドパネルHTML生成
    thought_log = state.get("thought_log", [])
    log_items = ""

    # 最後のreframedエントリのインデックスを特定
    last_reframed_idx = -1
    for i, entry in enumerate(thought_log):
        if entry.get("type") == "reframed":
            last_reframed_idx = i

    for i, entry in enumerate(thought_log):
        t = entry.get("type", "initial")
        text = entry.get("text", entry.get("question", ""))
        is_current_reframed = (t == "reframed" and i == last_reframed_idx)

        if t == "initial":
            log_items += f'''<div class="log-initial">
  <div class="log-tag log-tag-initial">🔵 Initial Question</div>
  <div class="log-text">{md_to_html_live(text)}</div>
</div><div class="log-arrow">↓</div>'''

        elif t == "conflict":
            r_num  = entry.get("round", "")
            r_lvl  = entry.get("level", "")
            r_tag  = f"Round {r_num}　{r_lvl}" if r_lvl else f"Round {r_num}"
            log_items += f'''<div class="log-conflict">
  <div class="log-tag log-tag-conflict">⚔️ Core Conflict — {r_tag}</div>
  <div class="log-text">{md_to_html_live(text)}</div>
</div><div class="log-arrow">↓</div>'''

        elif t == "reframed":
            current_mark = ' <span class="log-current">← 今ここ</span>' if is_current_reframed else ""
            ab_a = entry.get("ab_a", "")
            ab_b = entry.get("ab_b", "")
            # A/B核心テキストを短縮（得るもの/失うもの以降を除去）
            import re as _re
            def _trim_ab(s):
                s = _re.split(r'[　\s]*得る(もの)?[:：]|[　\s]*失う(もの)?[:：]|／得る|／失う|／得[:：]|／失[:：]', s)[0].strip()
                # 「A: 」「B: 」プレフィックスを除去
                s = _re.sub(r'^[AB][:：]\s*', '', s)
                return s[:40] + ('…' if len(s) > 40 else '')
            ab_html = ""
            if ab_a or ab_b:
                a_short = _trim_ab(ab_a) if ab_a else "—"
                b_short = _trim_ab(ab_b) if ab_b else "—"
                ab_html = f'''
  <div style="margin-top:6px;font-size:0.78em;color:#888;line-height:1.5;">
    <span style="color:#4ade80;">A</span> {md_to_html_live(a_short)}<br>
    <span style="color:#f87171;">B</span> {md_to_html_live(b_short)}
  </div>'''
            log_items += f'''<div class="log-reframed{' log-reframed-current' if is_current_reframed else ''}">
  <div class="log-tag log-tag-reframed">🔁 Reframed Q{current_mark}</div>
  <div class="log-text">{md_to_html_live(text)}</div>{ab_html}
</div>'''
            if i < len(thought_log) - 1:
                log_items += '<div class="log-arrow">↓</div>'

        elif t == "choice":
            log_items += f'''<div class="log-choice-entry">
  <div class="log-tag log-tag-choice">選択 → {md_to_html_live(text)}</div>
</div><div class="log-arrow">↓</div>'''

        elif t == "final_choice":
            log_items += f'''<div class="log-final log-final-choice" style="background:#1a1a00;border-left:2px solid #facc15;">
  <div class="log-tag log-tag-final" style="color:#facc15;">🎯 最終選択</div>
  <div class="log-text" style="color:#fef08a;">{md_to_html_live(text)}</div>
</div><div class="log-arrow">↓</div>'''

        elif t == "final":
            q1     = entry.get("q1", "")
            q2     = entry.get("q2", "")
            layer0 = entry.get("layer0", "")
            if q1 and q2:
                l0_html = f'<div class="log-text" style="margin-bottom:8px;padding:5px 8px;background:rgba(250,204,21,0.07);border-radius:4px;"><span style="color:#facc15;font-size:0.82em;font-weight:bold;">L0 主題への回答</span><br>{md_to_html_live(layer0)}</div>' if layer0 else ""
                log_items += f'''<div class="log-final">
  <div class="log-tag log-tag-final">✅ 結論</div>
  {l0_html}<div class="log-text" style="margin-bottom:6px;"><span style="color:#4ade80;font-size:0.85em;">Q1</span> {md_to_html_live(q1)}</div>
  <div class="log-text"><span style="color:#4ade80;font-size:0.85em;">Q2</span> {md_to_html_live(q2)}</div>
</div>'''
            else:
                log_items += f'''<div class="log-final">
  <div class="log-tag log-tag-final">✅ 結論</div>
  <div class="log-text">{md_to_html_live(text)}</div>
</div>'''

    # JSブロックをf文字列から分離（\nの誤展開を防ぐため）
    js_block = r"""
function doCopy(text, btnId, resetLabel) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.top = '0';
  ta.style.left = '0';
  ta.style.width = '1px';
  ta.style.height = '1px';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  let success = false;
  try { success = document.execCommand('copy'); } catch(e) {}
  document.body.removeChild(ta);
  const btn = document.getElementById(btnId);
  if (btn) {
    btn.textContent = success ? '✅' : '⚠️ 失敗';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = resetLabel; btn.classList.remove('copied'); }, 2000);
  }
}

function getStoreData() {
  const el = document.getElementById('data-store');
  if (!el) return {};
  try {
    const json = decodeURIComponent(escape(atob(el.textContent.trim())));
    return JSON.parse(json);
  } catch(e) { return {}; }
}

function copyAll() {
  const data = getStoreData();
  const allDiffs = data.all_diffs || [];
  const log = document.getElementById('thought-log');
  const entries = log.querySelectorAll('.log-initial, .log-conflict, .log-reframed, .log-choice-entry, .log-final');
  let text = "=== Tri-Brain System 全記録 ===\n\n";
  let diffIdx = 0;
  entries.forEach(entry => {
    const tag = entry.querySelector('.log-tag');
    const body = entry.querySelector('.log-text');
    const tagText = tag ? tag.innerText.replace('← 今ここ', '').trim() : '';
    if (entry.classList.contains('log-initial')) {
      text += '[' + tagText + ']\n' + (body ? body.innerText.trim() : '') + '\n\n';
      if (allDiffs.length > 0) { text += '--- Diff (Round 1) ---\n' + allDiffs[diffIdx] + '\n\n'; diffIdx++; }
    } else if (entry.classList.contains('log-conflict')) {
      text += '[' + tagText + ']\n' + (body ? body.innerText.trim() : '') + '\n\n';
    } else if (entry.classList.contains('log-choice-entry')) {
      text += tagText + '\n\n';
      if (diffIdx < allDiffs.length) { text += '--- Diff (Round ' + (diffIdx + 1) + ') ---\n' + allDiffs[diffIdx] + '\n\n'; diffIdx++; }
    } else if (entry.classList.contains('log-reframed')) {
      text += '[' + tagText + ']\n' + (body ? body.innerText.trim() : '') + '\n\n';
    } else if (entry.classList.contains('log-final')) {
      const isChoice = entry.classList.contains('log-final-choice');
      const bodies = entry.querySelectorAll('.log-text');
      if (isChoice) {
        text += '[🎯 最終選択]\n' + (bodies[0] ? bodies[0].innerText.trim() : '') + '\n\n';
      } else if (bodies.length >= 2) {
        text += '=== 最終結論 ===\n';
        bodies.forEach(b => { if (b.innerText.trim()) text += b.innerText.trim() + '\n'; });
      } else {
        text += '=== 最終結論 ===\n' + (body ? body.innerText.trim() : '') + '\n';
      }
    }
  });
  doCopy(text.trim(), 'copy-all-btn', '📄 全記録');
}

function copyLog() {
  const log = document.getElementById('thought-log');
  const entries = log.querySelectorAll('.log-initial, .log-conflict, .log-reframed, .log-choice-entry, .log-final');
  let text = "=== 思考の軌跡 ===\n\n";
  entries.forEach(entry => {
    const tag = entry.querySelector('.log-tag');
    const body = entry.querySelector('.log-text');
    const tagText = tag ? tag.innerText.replace('← 今ここ', '').trim() : '';
    if (entry.classList.contains('log-final')) {
      const isChoice = entry.classList.contains('log-final-choice');
      const bodies = entry.querySelectorAll('.log-text');
      if (isChoice) {
        text += '[🎯 最終選択]\n' + (bodies[0] ? bodies[0].innerText.trim() : '') + '\n\n';
      } else if (bodies.length >= 2) {
        text += '[' + tagText + ']\n' + bodies[0].innerText.trim() + '\n' + bodies[1].innerText.trim() + '\n\n';
      } else {
        text += '[' + tagText + ']\n' + (body ? body.innerText.trim() : '') + '\n\n';
      }
    } else if (entry.classList.contains('log-conflict')) {
      text += '[' + tagText + ']\n' + (body ? body.innerText.trim() : '') + '\n\n';
    } else if (body) { text += '[' + tagText + ']\n' + body.innerText.trim() + '\n\n'; }
    else if (tag) { text += tagText + '\n\n'; }
  });
  doCopy(text.trim(), 'copy-btn', '📋 軌跡');
}
"""
    # ポーリングJSはf文字列内（hashの埋め込みが必要）
    poll_js = f"""
let lastHash = "{hash(sections) & 0x7fffffff}";

function getOpenDetails() {{
  const open = {{}};
  document.querySelectorAll('details').forEach((d, i) => {{
    if (d.open) open[i] = true;
  }});
  return open;
}}

function restoreOpenDetails(open) {{
  document.querySelectorAll('details').forEach((d, i) => {{
    if (open[i]) d.open = true;
  }});
}}

async function poll() {{
  try {{
    const jsonRes = await fetch('tri_brain_state.json?t=' + Date.now());
    const json = await jsonRes.json();
    if (String(json.hash) !== lastHash || json.complete) {{
      lastHash = String(json.hash);
      // 変化があった時・完了時はHTMLを取得して差分更新
      const res = await fetch('tri_brain_live.html?t=' + Date.now());
      const html = await res.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      const openState = getOpenDetails();
      const newStatus = doc.getElementById('status-bar');
      if (newStatus) document.getElementById('status-bar').innerHTML = newStatus.innerHTML;
      const newContent = doc.getElementById('main-content');
      if (newContent) document.getElementById('main-content').innerHTML = newContent.innerHTML;
      const newLog = doc.getElementById('thought-log');
      if (newLog) document.getElementById('thought-log').innerHTML = newLog.innerHTML;
      const newStore = doc.getElementById('data-store');
      if (newStore) document.getElementById('data-store').textContent = newStore.textContent;
      restoreOpenDetails(openState);
      if (json.complete) {{ return; }}  // 完了済み→更新後にポーリング停止
    }}
  }} catch(e) {{}}
  setTimeout(poll, 3000);
}}
setTimeout(poll, 3000);
"""

    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tri-Brain System — Live</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #0f0f0f; color: #e0e0e0; margin: 0; padding: 0; line-height: 1.8; }}
  .page-wrapper {{ display: flex; max-width: 1280px; margin: 0 auto; padding: 40px 20px; gap: 24px; }}
  .main-col {{ flex: 1; min-width: 0; }}
  .side-col {{ width: 240px; flex-shrink: 0; }}
  .side-panel {{ position: sticky; top: 24px; background: #111; border: 1px solid #333; border-radius: 8px; padding: 16px; }}
  .side-title {{ font-size: 0.75em; font-weight: bold; color: #888; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #222; display: flex; align-items: center; justify-content: space-between; }}
  .copy-btns {{ display: flex; gap: 4px; }}
  #copy-btn, #copy-all-btn {{ background: #222; border: 1px solid #444; border-radius: 4px; color: #aaa; font-size: 0.75em; cursor: pointer; padding: 2px 6px; transition: background 0.2s; white-space: nowrap; }}
  #copy-btn:hover, #copy-all-btn:hover {{ background: #333; color: #fff; }}
  #copy-btn.copied, #copy-all-btn.copied {{ background: #1a2e1a; border-color: #4ade80; color: #4ade80; }}
  .log-tag {{ font-size: 0.68em; font-weight: bold; letter-spacing: 0.08em; margin-bottom: 4px; }}
  .log-tag-initial {{ color: #4a9eff; }}
  .log-tag-reframed {{ color: #a78bfa; }}
  .log-tag-conflict {{ color: #fb923c; font-size: 0.7em; }}
  .log-conflict {{ background: #1a1000; border-left: 2px solid #fb923c; border-radius: 4px; padding: 6px 10px; margin: 4px 0; }}
  .log-conflict .log-text {{ font-size: 0.8em; color: #f0c080; line-height: 1.5; }}
  .log-tag-choice {{ color: #4ade80; }}
  .log-tag-final {{ color: #facc15; font-weight: bold; }}
  .log-final {{ background: #1a2000; border-left: 2px solid #facc15; border-radius: 4px; padding: 8px 10px; margin: 4px 0; }}
  .log-text {{ font-size: 0.78em; color: #ccc; line-height: 1.4; padding: 6px 8px; background: #1a1a1a; border-radius: 4px; border-left: 2px solid #444; }}
  .log-initial .log-text {{ border-left-color: #4a9eff; }}
  .log-reframed .log-text {{ border-left-color: #a78bfa; }}
  .log-reframed-current .log-text {{ border-left-color: #facc15; background: #1e1a00; color: #fef08a; }}
  .log-choice-entry {{ padding: 4px 8px; }}
  .log-current {{ color: #facc15; font-weight: bold; }}
  .log-arrow {{ font-size: 0.8em; color: #444; text-align: center; margin: 3px 0; }}
  h1 {{ font-size: 1.4em; color: #aaa; border-bottom: 1px solid #333; padding-bottom: 12px; letter-spacing: 0.05em; }}
  h2 {{ font-size: 1.1em; color: #888; margin-top: 40px; text-transform: uppercase; letter-spacing: 0.1em; }}
  h3 {{ color: #ccc; font-size: 1em; }}
  .status-bar {{ background: #1a1a1a; border-left: 3px solid {status_color}; padding: 10px 16px; margin-bottom: 24px; font-size: 0.85em; color: {status_color}; border-radius: 4px; }}
  .question-box {{ background: #1a1a2e; border-left: 3px solid #4a9eff; padding: 16px 20px; margin: 16px 0; border-radius: 4px; font-size: 1.05em; color: #c0d8ff; }}
  .brain-card {{ border-radius: 8px; padding: 20px 24px; margin: 16px 0; border-top: 3px solid #444; }}
  .logic-card {{ border-top-color: #4a9eff; background: #0d1a2e; }}
  .emotion-card {{ border-top-color: #ff6b9d; background: #2e0d1a; }}
  .meta-card {{ border-top-color: #a78bfa; background: #1a0d2e; }}
  .brain-label {{ font-size: 0.8em; font-weight: bold; letter-spacing: 0.12em; margin-bottom: 14px; padding-bottom: 8px; border-bottom: 1px solid #333; }}
  .logic-card .brain-label {{ color: #4a9eff; }}
  .emotion-card .brain-label {{ color: #ff6b9d; }}
  .meta-card .brain-label {{ color: #a78bfa; }}
  .tldr {{ font-size: 1.05em; margin-bottom: 8px; padding: 8px 12px; background: rgba(74,158,255,0.1); border-radius: 4px; }}
  .tldr-emotion {{ background: rgba(255,107,157,0.1); }}
  .tldr-meta {{ background: rgba(167,139,250,0.1); }}
  details {{ margin-top: 12px; }}
  summary {{ cursor: pointer; color: #4a9eff; font-size: 0.85em; font-weight: bold; padding: 6px 0; letter-spacing: 0.05em; user-select: none; }}
  summary:hover {{ color: #7bbeff; }}
  .diff-box {{ background: #111; border: 1px solid #444; border-left: 3px solid #facc15; border-radius: 8px; padding: 24px; margin: 16px 0; }}
  .diff-label {{ font-size: 0.8em; font-weight: bold; color: #facc15; letter-spacing: 0.12em; margin-bottom: 14px; padding-bottom: 8px; border-bottom: 1px solid #333; }}
  .diff-section {{ margin: 16px 0 8px 0; }}
  .diff-section-title {{ font-size: 0.85em; font-weight: bold; color: #facc15; letter-spacing: 0.08em; margin-bottom: 6px; }}
  .diff-section p {{ margin: 4px 0; color: #e0e0e0; font-size: 0.97em; }}
  .core-prompt-desc {{ color: #fde68a; margin-bottom: 10px; font-size: 0.92em; }}
  .final-box {{ background: #1a2e1a; border-left: 3px solid #4ade80; padding: 16px 20px; margin: 16px 0; border-radius: 4px; color: #a0ffb0; }}
  .final-qa {{ margin: 0 0 14px 0; }}
  .final-q-label {{ font-size: 0.75em; font-weight: bold; color: #4ade80; letter-spacing: 0.08em; margin-bottom: 6px; }}
  .final-q-text {{ font-size: 0.97em; color: #a0ffb0; padding: 8px 12px; background: rgba(74,222,128,0.07); border-radius: 4px; }}
  .core-prompt {{ background: #1e1a00; border: 1px solid #facc15; border-radius: 8px; padding: 20px 24px; margin: 24px 0; color: #fef08a; }}
  .core-prompt-title {{ font-size: 0.8em; font-weight: bold; color: #facc15; letter-spacing: 0.12em; margin-bottom: 12px; }}
  .core-options li {{ margin: 8px 0; color: #fde68a; list-style: none; padding-left: 4px; }}
  .choice-result {{ background: #0f1e0f; border-left: 3px solid #4ade80; border-radius: 6px; padding: 14px 20px; margin: 16px 0; }}
  .choice-result-label {{ font-size: 0.78em; font-weight: bold; color: #4ade80; letter-spacing: 0.1em; margin-bottom: 8px; }}
  .choice-result-text {{ color: #a0ffb0; font-size: 0.97em; }}
  .processing {{ color: #888; font-style: italic; padding: 16px; }}
  .spinner {{ animation: spin 1s linear infinite; display: inline-block; }}
  @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
  .meta-info {{ font-size: 0.75em; color: #555; margin-top: 60px; border-top: 1px solid #222; padding-top: 16px; }}
  strong {{ color: #fff; }}
  li {{ margin: 4px 0; }}
  @media (max-width: 768px) {{ .side-col {{ display: none; }} }}
  .convergence-banner {{ background: #1a0a2e; border: 1px solid #a78bfa; border-left: 4px solid #a78bfa; border-radius: 8px; padding: 16px 20px; margin: 24px 0; color: #c4b5fd; }}
  .convergence-title {{ font-size: 0.8em; font-weight: bold; color: #a78bfa; letter-spacing: 0.12em; margin-bottom: 8px; }}
  .convergence-reason {{ font-size: 0.95em; color: #e0d4ff; }}
</style>
</head>
<body>
<div class="page-wrapper">
  <div class="main-col">
    <h1>🧠 Tri-Brain System — RDAC Live</h1>
    <div class="status-bar" id="status-bar">● {status} &nbsp;|&nbsp; 監視中</div>
    <div id="main-content">
    {sections}
    </div>
    <div class="meta-info">
      Tri-Brain System — RDAC Implementation<br>
      Copyright (c) 2026 Masanao Ishikawa (Phantom Odyssey AI)<br>
      DOI: https://doi.org/10.5281/zenodo.18859272
    </div>
  </div>
  <div class="side-col">
    <div class="side-panel" id="side-panel">
      <div class="side-title">
        🗺️ 思考の軌跡
        <div class="copy-btns">
          <button id="copy-btn" onclick="copyLog()" title="軌跡のみコピー">📋 軌跡</button>
          <button id="copy-all-btn" onclick="copyAll()" title="全記録コピー">📄 全記録</button>
        </div>
      </div>
      <div id="thought-log">{log_items}</div>
    </div>
    <div id="data-store" style="display:none">{store_b64}</div>
  </div>
</div>
<script>
{js_block}
{poll_js}
</script>
</body>
</html>'''

    try:
        with open(LIVE_HTML, "w", encoding="utf-8") as f:
            f.write(html)
        # JSポーリング用にstateのサマリーをJSONで別途書き出す
        import json as _json2
        json_payload = {
            "hash": hash(sections) & 0x7fffffff,
            "status": state.get("status", ""),
            "complete": "完了" in state.get("status", "")
        }
        with open(LIVE_JSON, "w", encoding="utf-8") as jf:
            jf.write(_json2.dumps(json_payload, ensure_ascii=False))
    except Exception as e:
        with open("tri_brain_live_error.log", "a", encoding="utf-8") as ef:
            import traceback
            ef.write(f"=== ERROR ===\n{traceback.format_exc()}\nstate keys: {list(state.keys())}\n")
        print(f"⚠️ live HTML更新エラー: {e}")


# ============================================================
# 簡易HTTPサーバー（CORS回避のため file:// の代わりに http:// で配信）
# ============================================================
HTTP_PORT = 8765

def start_http_server():
    import http.server, threading, os
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args): pass  # ログ抑制
    os.chdir(os.path.dirname(os.path.abspath(LIVE_HTML)) or ".")
    server = http.server.HTTPServer(("127.0.0.1", HTTP_PORT), QuietHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server

# ============================================================
# Human-in-the-Loop ループ
# ============================================================
def _classify_policy(text: str) -> str:
    """
    C選択のフリーテキストを立場カテゴリに分類する。
    政策系（市場/国家/地域/倫理）と認識論系（哲学/認識/検証）を区別。
    Diff AIのユーザー立場分析の補助情報として使う。
    """
    t = text
    # 認識論・哲学（最優先チェック：政策語より前に判定）
    epistemic_words = [
        "クオリア", "意識", "主観", "真偽", "証明", "検証", "定義",
        "存在", "認識", "哲学", "本質", "判定できない", "分からない",
        "言い訳", "不可知", "観測", "確かめ", "真実", "知識",
    ]
    # 政策系
    market_words = ["市場", "企業", "競争", "民間", "自由", "自律", "黎明期", "様子見", "任せ", "普及", "拡大", "先に", "まず"]
    state_words  = ["国", "政府", "規制", "法", "中央", "管理", "監視", "行政"]
    local_words  = ["地域", "地元", "コミュニティ", "町内", "住民", "地方"]
    ethics_words = ["尊厳", "倫理", "人権", "責任", "搾取", "被害", "詐欺", "弱者"]

    # 社会プロセス
    social_words = [
        "裁判", "人権", "法的", "承認", "合意", "社会が", "段階", "ステージ",
        "プロセス", "認める", "受け入れ", "議論される", "制度化", "市民権",
    ]
    epistemic_score = sum(1 for w in epistemic_words if w in t)
    social_score   = sum(1 for w in social_words   if w in t)
    scores = {
        "市場主導": sum(1 for w in market_words if w in t),
        "国家主導": sum(1 for w in state_words  if w in t),
        "地域主導": sum(1 for w in local_words  if w in t),
        "倫理重視": sum(1 for w in ethics_words if w in t),
    }
    policy_top = max(scores, key=scores.get)
    policy_score = scores[policy_top]

    # 優先順位：社会プロセス > 認識論 > 政策系（同点は下位を維持）
    if social_score > 0 and social_score >= epistemic_score and social_score > policy_score:
        return "社会プロセス"
    if epistemic_score > 0 and epistemic_score > policy_score:
        return "認識論・哲学"
    return policy_top if policy_score > 0 else ("認識論・哲学" if epistemic_score > 0 else "その他")


def _classify_question_type(question: str) -> str:
    """
    Initial Questionの型を判定する。
    epistemic：認識論・存在論的問い → Layer 0必要
    value    ：価値観・人生選択の問い → Layer 0必要
    policy   ：政策・行動論的問い → Layer 0不要
    """
    q = question
    epistemic = ["とは何か", "とは何", "できるか", "存在するか", "生成される",
                 "生じる", "クオリア", "意識とは", "主観とは", "定義できる",
                 "証明できる", "判定できる", "本質とは", "可能か", "ありうるか",
                 "なのか否か", "かどうかを"]
    value     = ["生きる", "生き方", "幸せ", "幸福", "後悔", "意味", "価値観",
                 "自分らしく", "自己実現", "人生", "創作", "夢", "やりたい",
                 "やりがい", "本当に", "本音", "魂", "信念", "働き方",
                 "精神的", "心の", "感情", "愛", "孤独", "つながり",
                 "良いことなのか", "良いのか", "幸いなのか"]
    policy    = ["すべきか", "べきか", "どうすれば", "どうする", "どう対応",
                 "どう運用", "規制", "法律", "制度", "政策"]
    ep_score  = sum(1 for w in epistemic if w in q)
    val_score = sum(1 for w in value     if w in q)
    pol_score = sum(1 for w in policy    if w in q)
    if ep_score > pol_score:
        return "epistemic"
    if val_score > 0:
        return "value"
    return "policy"


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
            policy_hint = _classify_policy(synthesis_input)
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
    _q_type = _classify_question_type(question)
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
        print(f"\nQ1. {round_num}ラウンドで最も印象に残った衝突や気づきを1行で。")
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