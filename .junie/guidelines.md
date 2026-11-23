# Junie Engineering Guidelines — C9 Fearless Nexus

## 1. Zero-Redistribution Data Guardrail (CRITICAL)
- Official GRID esports data lives **outside** this repository at `STL_DATA_DIR` (default `../stl-hackathon-2026-grid-starter`).
- **NEVER** copy, commit, cache-commit, or bundle `.zst`, `.jsonl`, `meta/*.csv`, `series.csv`, `.parquet`, `.sqlite`, or `.duckdb` files inside this repository.
- Before staging or committing, verify `git ls-files` contains zero licensed data files.

## 2. GRID Event Stream Invariants
- Stream `.jsonl.zst` line-by-line (never load full uncompressed 1GB feeds into RAM).
- Check `session_valid == "True"` in `meta/games.csv` or `seriesState.valid is True` on the final full snapshot before counting series outcomes (58 series in the corpus end with `valid: false`).
- `seriesState` is partial whenever `includesFullState` is `false`: never assume omitted fields were deleted; merge partial updates into the latest full snapshot and honor `!` reversal events (e.g., `player-!purchased-item`, `series-!started-game`).
- Summoner's Rift bounds are `x in [0, 15000]`, `y in [-300, 14700]`.

## 3. Domain Rules — Fearless Draft & Coaching Insights
- **Tournament 20-Action Sequence**:
  - Ban Phase 1 (1–6): `B1, R1, B2, R2, B3, R3`
  - Pick Phase 1 (7–12): `B1, R1, R2, B2, B3, R3`
  - Ban Phase 2 (13–16): `R4, B4, R5, B5`
  - Pick Phase 2 (17–20): `R4, B4, B5, R5`
- **Fearless Lock Rule**: Any champion picked by **either** team in Games `1..(k-1)` of a Bo3/Bo5 series is globally unavailable in Game `k` (10 locked in G2, 20 in G3, 30 in G4, 40 in G5).
- **Evidence First**: Every scouting card and recommendation must expose sample size (`n` games / series), side context (Blue vs Red), and quantified win-rate / pool-entropy delta.

## 4. Verification Standard
- Run `python3 -m unittest discover -s tests -v` after every backend change. All unit tests must pass cleanly with zero external network dependencies.
