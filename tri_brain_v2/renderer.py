"""
================================================================================
Tri-Brain System — HTML Renderer
================================================================================
Copyright (c) 2026 Masanao Ishikawa (Phantom Odyssey AI)
DOI: https://doi.org/10.5281/zenodo.18859272
================================================================================

Provides two rendering functions:
  save_html()      — saves a static archive HTML after session completion
  save_live_html() — writes the real-time sidebar HTML (polled by browser)
  start_http_server() — starts the local HTTP server for live view

Both functions are language-agnostic: they render whatever text is passed in.
================================================================================
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import os

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
