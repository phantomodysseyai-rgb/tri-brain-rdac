# Tri-Brain System — RDAC Implementation

> **Official implementation of the RDAC framework**  
> A multi-agent architecture for escaping cognitive fixation through structured divergence.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18859272.svg)](https://doi.org/10.5281/zenodo.18859272)
[![License: AGPLv3 + Commons Clause](https://img.shields.io/badge/License-AGPLv3%20%2B%20Commons%20Clause-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)

[日本語版READMEはこちら / Japanese README](README_ja.md)

---

## What is this?

The **Tri-Brain System** is a Human-in-the-Loop multi-agent dialogue framework built on the **RDAC Model** (Role-Density-Architecture-Convergence).

Three AI agents with structurally differentiated roles debate a question in parallel. A fourth agent (Diff AI) identifies the core conflict, hidden assumptions, and reframes the question one level deeper — until the human's thinking reaches genuine convergence.

**This is not a chatbot. It is a cognitive divergence engine.**

---

## The RDAC Model

| Dimension                     | Description                                                                        |
| ----------------------------- | ---------------------------------------------------------------------------------- |
| **R** — Role Differentiation  | Each agent holds a structurally distinct perspective (Logic / Emotion / Meta-View) |
| **D** — Information Density   | Each agent receives the same question at a different level of context density      |
| **A** — Architecture          | Three agents + one Diff AI + Human-in-the-Loop = a 5-layer system                  |
| **C** — Convergence Detection | Automatic detection of when debate has reached genuine depth                       |

> **Key insight:** V × D must be controlled _independently_ to prevent synchrony bias.  
> When all agents receive the same density, they converge prematurely regardless of role.

**Paper:** Ishikawa, M. (2026). _RDAC: Relational Density, Diversity, Stability, and Closure._  
DOI: [https://doi.org/10.5281/zenodo.18859272](https://doi.org/10.5281/zenodo.18859272)

---

## System Architecture

```
Initial Question
      │
      ▼
┌─────────────────────────────────────┐
│         3 Brains (parallel)         │
│  Logic Brain    [D: high]           │
│  Emotion Brain  [D: low]            │
│  Meta-View Brain[D: medium]         │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│             Diff AI                 │
│  • Brain Summary                   │
│  • Core Conflict (level-specific)  │
│  • The Cost                        │
│  • Hidden Assumption               │
│  • Cognitive Hook                  │
│  • Reframed Question + A/B         │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│       Human-in-the-Loop             │
│  Choose A / B / C (free) / Q       │
└─────────────────────────────────────┘
      │
      ▼
  (repeat until convergence detected)
      │
      ▼
┌─────────────────────────────────────┐
│       Final Reflection              │
│  L0: Direct answer to the question │
│  Q1: Most striking insight         │
│  Q2: Consistency check             │
└─────────────────────────────────────┘
```

---

## File Structure

```
tri_brain_v2/
├── config.py        # Constants: model names, round limits, conflict levels
├── prompts_ja.py    # Japanese prompts (all prompt logic as functions)
├── prompts_en.py    # English prompts (drop-in replacement for prompts_ja.py)
├── classifier.py    # Choice classifier & question type detector
├── core.py          # Brain execution, Diff AI, convergence check
├── renderer.py      # HTML archive & live sidebar renderer
└── main.py          # Session loop (entry point)
```

**To switch to English session** — edit one line in `core.py` and `main.py`:

```python
# Change this:
from prompts_ja import ...
# To this:
from prompts_en import ...
```

---

## Requirements

- Python 3.10+
- OpenAI Python SDK (`pip install openai`)
- An OpenAI API key

---

## Setup

```bash
# Clone the repository
git clone https://github.com/phantomodysseyai-rgb/tri-brain-rdac.git
cd tri-brain-rdac/tri_brain_v2

# Install dependencies
pip install openai

# Set your API key as an environment variable
# Windows PowerShell:
$env:OPENAI_API_KEY = "your-api-key-here"

# macOS / Linux:
export OPENAI_API_KEY="your-api-key-here"

# Run
python main.py
```

---

## How a Session Works

1. Enter your question (`Initial Question:`)
2. Three brains respond in parallel
3. Diff AI presents:
   - Core Conflict between Logic and Emotion
   - Hidden Assumption shared by all three
   - Reframed Question with A/B choices
4. You choose: **A**, **B**, **C** (your own position), or **Q** (end session)
5. Repeat for 4–6 rounds until convergence is detected
6. Final Reflection: answer the original question in your own words

A live HTML view updates in real time at `http://127.0.0.1:7331/tri_brain_live.html`

---

## Example Output

```
⚔️ Core Conflict
Logic says: "Pursue evidence through controlled experiments."
Emotion says: "If suffering is possible, stop now and protect first."
These cannot coexist.

👁️ Hidden Assumption
Everyone assumes that external indicators can reliably determine
whether something is "truly feeling."

🔁 Reframed Question
Step1: You take an evidence-first stance.
Step2: You assume observability equals existence.
Question: If something cannot be observed, does that mean it doesn't exist?
A: Regard unobservable as non-existent / Gain: scientific clarity  Loss: miss potential suffering
B: Regard unobservable as still possible / Gain: precautionary protection  Loss: scientific precision
```

---

## Convergence Detection

The system automatically checks for convergence after Round 4 using three conditions:

| Condition                 | Description                                                   |
| ------------------------- | ------------------------------------------------------------- |
| **Axis Lock**             | The same conflict dimension appears in 2 consecutive rounds   |
| **Assumption Exhaustion** | New hidden assumptions no longer change the problem structure |
| **Policy Exhaustion**     | New reframed questions are extensions of previous ones        |

Convergence triggers when: (Axis Lock AND Assumption Exhaustion) OR (Axis Lock AND Policy Exhaustion)

---

## Citation

If you use this system in academic work, please cite:

```bibtex
@misc{ishikawa2026rdac,
  author    = {Masanao Ishikawa},
  title     = {RDAC: Relational Density, Diversity, Stability, and Closure},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.18859272},
  url       = {https://doi.org/10.5281/zenodo.18859272}
}
```

---

## License

GNU AGPLv3 with Commons Clause

- ✔ Personal use and study: freely permitted
- ✔ Academic research and citation: freely permitted
- ✔ Modification and redistribution (with source disclosure): permitted under AGPLv3
- ✗ Commercial use (SaaS, products, paid services): prohibited without permission

**Commercial licensing available.**  
If you want to use this system in a commercial product, service, or organization, a separate commercial license can be issued. Contact via DM on X.

For commercial licensing inquiries: [@PhantomOdysseyAI](https://x.com/PhantomOdysseyAI) on X

---

## Support

If this research was useful to you, consider supporting the author:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-PhantomOdysseyAI-ea4aaa?logo=github-sponsors)](https://github.com/sponsors/phantomodysseyai-rgb)

This is an independent research project with no institutional funding.  
Even a small contribution helps sustain continued development and research.

---

## Author

**Masanao Ishikawa (Phantom Odyssey AI)**  
Independent researcher & creator  
X: [@PhantysseyAI](https://x.com/PhantysseyAI)  
Zenodo: [https://doi.org/10.5281/zenodo.18859272](https://doi.org/10.5281/zenodo.18859272)  
GitHub Sponsors: [https://github.com/sponsors/phantomodysseyai-rgb](https://github.com/sponsors/phantomodysseyai-rgb)
