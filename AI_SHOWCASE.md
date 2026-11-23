# AI-Powered Engineering Case Study: Building C9 Fearless Nexus with JetBrains PyCharm, Junie CLI & Air Gateway

> **Bonus Prize Submission — Best AI-Powered Workflow Story**  
> **Project:** C9 Fearless Nexus (Category 2: League of Legends Macro Scouting & Draft Management System)

---

## 1. Overview: Guardrail-First Agentic Development

Building an esports intelligence platform against **1.4 GB of compressed (`~160 GB` uncompressed) proprietary GRID tournament feeds** introduces two failure modes that break typical AI-assisted prototypes:

1. **License & Data-Leakage Risk:** Accidentally staging a `.zst` feed, a decompressed `.jsonl` match log, or a copy of `meta/rosters.csv` into Git history violates Section 3(a) of the hackathon data license—even if deleted in a later commit.
2. **Subtle Telemetry State Bugs:** GRID's event envelopes emit partial `seriesState` trees whenever `includesFullState` is `false`, include `58` invalid series (`session_valid: False`), and represent rolled-back in-game actions via `!` event prefixes (such as `player-!purchased-item` and `series-!started-game`).

To move fast without breaking either constraint, we anchored our entire workflow around **JetBrains tools**:
- **JetBrains AI Coding Agent Junie CLI (`26.11.2 / 4100.11`)** with repository-level guardrails in [`.junie/guidelines.md`](.junie/guidelines.md)
- **JetBrains Air Gateway CLI (`central v2.8.1`)** for agentic CLI workflow orchestration
- **JetBrains PyCharm Community Edition (`2025.2.5`, Build `252.28238.29`)** — specifically leveraging its `.idea/` run configurations and **headless PSI static analyzer (`inspect.sh`)** as an automated quality gate

---

## 2. Encoding Domain & Legal Invariants in `.junie/guidelines.md`

Before writing application code, we encoded non-negotiable engineering rules into [`.junie/guidelines.md`](.junie/guidelines.md) so every agent task and human review operated against the same contract:

- **Zero-Redistribution Boundary:** Keep `STL_DATA_DIR` strictly outside the repo (`../stl-hackathon-2026-grid-starter`), block `*.zst`, `*.jsonl`, `*.parquet`, `*.sqlite`, and `*.duckdb` in `.gitignore`, and verify `git ls-files` before every commit.
- **Streaming Telemetry Rules:** Decompress `.jsonl.zst` streams line-by-line rather than inflating gigabyte match files to disk; ignore rolled-back `!` events; filter on `session_valid == "True"`.
- **Exact 20-Step Pro Draft Sequence:** Enforce the official tournament pick/ban cadence (`BB1..RB3 → B1, R1, R2, B2, B3, R3 → RB4..BB5 → R4, B4, B5, R5`) and cumulative Bo3/Bo5 Fearless champion locks (`10 / 20 / 30 / 40` champions burned across Games 2–5).

---

## 3. Three Real Engineering Challenges Solved During the Build

### Challenge 1: Fixing Small-Sample & Baseline Bias in the Fearless "Pinch Index"
In our initial mathematical formulation of `compute_pinch_score()`, we measured comfort scarcity against a fixed constant (`4` comfort picks). When our unit test `test_pinch_score_monotonicity_under_fearless_and_bans` ran against a realistic 4-champion pro jungle pool (`Sejuani 14g`, `Skarner 10g`, `Vi 6g`, `Ivern 1g`), **Game 1 with zero bans or Fearless locks unexpectedly produced a non-zero Pinch Index (`7.5` instead of `0.0`)** because `Ivern (1g)` was below the comfort threshold.

- **Resolution:** Guided by failing unit-test feedback, we refactored `compute_pinch_score()` in `backend/fearless_engine.py` to measure **relative comfort depletion** (`(initial_comfort - remaining_comfort) / len(initial_comfort)`) paired with **Beta/Dirichlet smoothing** (`(wins + 2.5) / (games + 5.0)`).
- **Impact:** Baseline Pinch Index became strictly `0.0` at full pool availability, monotonic under every incremental Fearless lock or target ban, and immune to `1-game 100% WR` outliers.

### Challenge 2: Aligning Historical 2025–2026 GRID Rosters with Active 2026 Starters
When streaming `meta/rosters.csv` (`38,305` player-game rows) alongside `35` 2026 LCS `.jsonl.zst` series feeds, naive sorting by total career games surfaced split-era 6-man roster overlaps and trailing whitespace in player handles (e.g., `"Loki "` vs. `"APA"` on Cloud9 Kia).

- **Resolution:** We updated `GridLoLRepository` in `backend/grid_stream.py` to normalize player identifiers (`.strip()`), weight active `2026` season appearances (`recent_2026_games`) ahead of legacy `2025` splits, and deterministically order the active 5-man lineup (`Top → Jungle → Mid → Bot → Support`).
- **Verified Output:** All five 2026 LCS benchmark teams resolved cleanly to their exact 5-role starting lineups (e.g., Cloud9 Kia: `Thanatos / Blaber / APA / Zven / Vulcan`; LYON: `Dhokla / Inspired / Saint / Berserker / Isles`; Team Liquid Alienware: `Morgan / Josedeodo / Quid / Yeon / CoreJJ`).

### Challenge 3: Catching Code Smells with Headless PyCharm PSI Inspection (`inspect.sh`)
Rather than relying on LLM generation alone, we ran **PyCharm's headless PSI inspection engine** against `.idea/inspectionProfiles/Project_Default.xml`:

```bash
"/Applications/PyCharm CE.app/Contents/bin/inspect.sh" \
  . .idea/inspectionProfiles/Project_Default.xml ../src/pycharm_inspect -v2
```

PyCharm's PSI analyzer emitted structured XML inspection reports across `backend/`, `tests/`, and `docs/`, catching four concrete issues that we immediately remediated:
1. **`PyUnusedImportsInspection` (`backend/grid_stream.py:21`):** Removed unused `CHAMPION_ARCHETYPES` symbol import.
2. **`PyMethodMayBeStaticInspection` (`backend/grid_stream.py:258`):** Promoted `_parse_single_feed` to `@staticmethod` to decouple stream parsing from mutable instance state.
3. **`HtmlUnknownAttribute` (`docs/index.html:61`):** Moved non-standard `webkitdirectory` folder-picker initialization from static HTML markup to progressive JS enhancement (`localInput.setAttribute("webkitdirectory", "")`) in `docs/app.js` for clean W3C HTML5 validation.
4. **`PyPep8NamingInspection` (`backend/server.py:182, 189, 251`):** Annotated stdlib `BaseHTTPRequestHandler` overrides (`do_OPTIONS`, `do_GET`, `do_POST`) with `# noinspection PyPep8Naming` directives for zero-noise IDE inspections.

---

## 4. Measurable Results

| Engineering Metric | Result |
|---|---|
| **GRID Corpus Coverage** | `745` LoL series metadata + streaming `.jsonl.zst` coordinate/objective parser |
| **External Runtime Dependencies** | **Zero** (`Python 3.10+` standard library backend + vanilla ES6/SVG frontend) |
| **Unit Test Execution Time** | `< 2 ms` (`5/5` deterministic unit tests passing) |
| **Licensed Data Leaked to Git** | **`0 bytes`** (verified via `git ls-files` & `.gitignore` guardrails) |
| **Judge Onboarding Friction** | **`0 seconds`** (instant browser showcase + zero-upload client-side local CSV loader) |

By combining **agentic speed (`.junie/guidelines.md` + Junie/Air CLI)** with **deterministic IDE verification (PyCharm PSI inspections + unit tests)**, we turned raw esports event streams into a coach-ready tactical workstation without sacrificing mathematical rigor or data-license compliance.
