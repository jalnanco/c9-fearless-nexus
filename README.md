# C9 Fearless Nexus

[![License: MIT](https://img.shields.io/badge/License-MIT-00AEEF.svg)](LICENSE)
[![Built with JetBrains](https://img.shields.io/badge/Built%20with-JetBrains%20PyCharm%20%2B%20Junie%20%2B%20Air-38BDF8)](AI_SHOWCASE.md)
[![Category 2](https://img.shields.io/badge/Cloud9%20x%20JetBrains%202026-Category%202%20(LoL)-F59E0B)](https://cloud9.devpost.com/)

**Series-Aware Fearless Draft Simulator, Champion Pool Pinch Analyzer & Early-Macro Scouting Workstation for Cloud9 Kia League of Legends.**

- **Live Web Workstation (Zero-Install):** `https://jalnanco.github.io/c9-fearless-nexus/`
- **Bonus Prize Case Study (`AI_SHOWCASE.md`):** [`AI_SHOWCASE.md`](AI_SHOWCASE.md)

---

## 1. Problem Statement: Why Spreadsheets Break in Fearless Draft

In modern competitive *League of Legends* Bo3 and Bo5 **Fearless Draft** series, every champion picked in earlier games is permanently locked for **both** teams for the remainder of the series (**10 locked in Game 2, 20 in Game 3, 30 in Game 4, and 40 in Game 5**).

Across the 2025–2026 GRID dataset (`n = 142` valid Cloud9 Kia games), Cloud9 holds an impressive **63.4% overall win rate** (72.5% Blue / 54.8% Red), yet in **Game 3+ deep Fearless states (`n = 44`), win rate shifts to 56.8% (-6.6%p)**. Static spreadsheets fail coaching staffs in two critical ways:

1. **Non-Linear Pool Collapse ("Pinch Points"):** Coaches cannot instantly see how burning two meta junglers in Games 1–2 plus a single Phase-1 target ban in Game 3 collapses an opponent player's remaining comfort pool and expected win rate.
2. **Draft-to-Macro Disconnect:** Pick/ban tables ignore *how* an opponent executes the first 14 minutes on Summoner's Rift—such as first Scuttle Crab pathing direction (`Top` vs `Bot`), Void Grubs vs. First Dragon trade preferences, and early skirmish `{x, y}` spatial hotspots.

---

## 2. Core Capabilities

### A. 20-Step Tournament Fearless Draft Engine (`Game 1 → Game 5`)
- Exact pro tournament 20-action sequence: **Ban Phase 1 (`1–6`) → Pick Phase 1 (`7–12: B1, R1, R2, B2, B3, R3`) → Ban Phase 2 (`13–16: R4, B4, R5, B5`) → Pick Phase 2 (`17–20: R4, B4, B5, R5`)**.
- **Prior-Series Fearless Burn Vault:** Automatically locks champions played in earlier games of the series and provides instant **G1 / G2 (-10) / G3 (-20) / G4 (-30) / G5 (-40)** state tabs so coaches can rehearse deep-series pinch scenarios in one click.

### B. Opponent 5-Player Pool Pinch Matrix & Target Ban Engine
- Quantifies pool pressure per opposing starter (`Top / Jungle / Mid / Bot / Support`) using **Pool Share Depletion**, **Normalized Shannon Entropy Drop**, and **Dirichlet-Smoothed Expected Win-Rate Delta** (`Pinch Index 0–100`).
- Surfaces data-backed target ban recommendations with explicit sample sizes (`n` games) and incremental Pinch Index gains.

### C. Summoner's Rift Early-Macro Tactical Canvas (`GRID Telemetry`)
- Streams compressed `lol/events_*_grid.jsonl.zst` match feeds (`[0..15000, -300..14700]` Summoner's Rift coordinate bounds) to overlay:
  - **Jungle Pathing Direction:** `slayRiftScuttlerTop` vs. `slayRiftScuttlerBot` opening clear vectors (e.g., *Team Liquid Alienware* paths Top Scuttle **58.8%** for **66.7%** First Void Grub control, whereas *Shopify Rebellion* paths Bot Scuttle **83.3%** for **66.7%** First Dragon).
  - **Early Objective Trade Profile:** First Void Grub, First Dragon, First Rift Herald (**70.4%** for Cloud9 Kia), and First Tower Blood (**63.0%** for Cloud9 Kia).
  - **Pre-14m Kill Density Heatmap:** Spatial clustering of early kills across Baron/Grub Pit, Mid-Raptor crossing, and Dragon/Bot River, paired with an automated **3-point "How-to-Win" Coaching Brief**.

### D. Live Bayesian Win-Probability & Composition Balance
- Updates Cloud9's projected win probability after every pick/ban (`[5%, 95%]`) by combining side baseline log-odds, Dirichlet-smoothed champion mastery, 5-axis team composition synergy (`Engage`, `Frontline`, `Early Prio`, `Scaling`, `AD/AP Damage Mix`), and Fearless Pinch leverage.

---

## 3. Zero-Redistribution GRID Data Architecture (`LICENSE.md` Compliant)

Per the official `stl-hackathon-2026-grid-starter` license, **zero raw `.zst` feeds, `.jsonl` logs, `meta/*.csv` copies, or reconstructible extracts are committed to this repository.** Instead, C9 Fearless Nexus operates in three seamless modes:

1. **Local Full-Corpus Streaming Backend (`Python 3.10+`, zero pip dependencies required):**
   Reads `../stl-hackathon-2026-grid-starter` directly from disk via streaming Zstandard decompression (`compression.zstd` / `zstandard` / `zstd -dc`) while honoring `session_valid == True` and `!` rollback event invariants.
2. **Zero-Server Browser Local Folder Loader:**
   On the hosted web app, clicking **`Load Local GRID`** parses a judge's local `stl-hackathon-2026-grid-starter/meta/*.csv` directly inside browser memory (**0 bytes uploaded over the network**).
3. **Instant Judge Showcase Mode (`LICENSE.md` §4b):**
   Opens immediately in any browser with high-level aggregate team summary percentages so judges can test all 20 draft steps, Game 1–5 Fearless locks, and macro visualizations with zero setup.

---

## 4. Quick Start (Local Backend + Tests)

```bash
# 1. Place official GRID starter repository alongside this project (never inside it)
git clone --filter=blob:none --sparse https://github.com/cloud9esports/stl-hackathon-2026-grid-starter.git
cd stl-hackathon-2026-grid-starter
git sparse-checkout set meta lol
cd ..

# 2. Clone and run C9 Fearless Nexus (Python 3.10+ standard library — no pip install needed)
git clone https://github.com/jalnanco/c9-fearless-nexus.git
cd c9-fearless-nexus

# 3. Run unit tests
python3 -m unittest discover -s tests -v

# 4. Launch local telemetry server & open workstation at http://127.0.0.1:8787
STL_DATA_DIR=../stl-hackathon-2026-grid-starter python3 -m backend.server
```

---

## 5. JetBrains Tools Used

- **JetBrains PyCharm (`2025.2.5`, Build `252.28238.29`):** Project model (`.idea/`), shared run configurations (`Start Nexus Server`, `Run Unit Tests`), and headless PSI static code analysis (`inspect.sh` with `.idea/inspectionProfiles/Project_Default.xml`) to audit type safety, PEP 8 naming, unused locals, and broad exception clauses across `backend/` and `tests/`.
- **JetBrains AI Coding Agent Junie CLI (`26.11.2 / 4100.11`):** Configured via [`.junie/guidelines.md`](.junie/guidelines.md) to enforce strict GRID data non-redistribution guardrails, streaming parser invariants (`includesFullState` & `!` rollback events), and tournament Fearless Draft validation rules.
- **JetBrains Air Gateway CLI (`central v2.8.1`):** Agentic CLI workspace setup for terminal-to-JetBrains workflow orchestration.

See [`AI_SHOWCASE.md`](AI_SHOWCASE.md) for the complete engineering case study.

---

## 6. License

Code and original assets in this repository are licensed under the [MIT License](LICENSE). Official esports telemetry accessed via `STL_DATA_DIR` remains subject to the proprietary license in `cloud9esports/stl-hackathon-2026-grid-starter`.
