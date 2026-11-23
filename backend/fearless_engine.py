"""Core Fearless Draft validation, Pool Pinch entropy scoring, and live Bayesian win-rate model.

Built with zero external dependencies (Python 3.10+ standard library) for deterministic,
instant coaching workflows in Bo3 and Bo5 Fearless Draft series.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class DraftStep:
    step: int
    phase: str
    side: str  # "blue" or "red"
    action: str  # "ban" or "pick"
    slot: str


TOURNAMENT_DRAFT_SEQUENCE: Tuple[DraftStep, ...] = (
    # Ban Phase 1 (Steps 1-6)
    DraftStep(1, "Ban Phase 1", "blue", "ban", "BB1"),
    DraftStep(2, "Ban Phase 1", "red", "ban", "RB1"),
    DraftStep(3, "Ban Phase 1", "blue", "ban", "BB2"),
    DraftStep(4, "Ban Phase 1", "red", "ban", "RB2"),
    DraftStep(5, "Ban Phase 1", "blue", "ban", "BB3"),
    DraftStep(6, "Ban Phase 1", "red", "ban", "RB3"),
    # Pick Phase 1 (Steps 7-12)
    DraftStep(7, "Pick Phase 1", "blue", "pick", "B1"),
    DraftStep(8, "Pick Phase 1", "red", "pick", "R1"),
    DraftStep(9, "Pick Phase 1", "red", "pick", "R2"),
    DraftStep(10, "Pick Phase 1", "blue", "pick", "B2"),
    DraftStep(11, "Pick Phase 1", "blue", "pick", "B3"),
    DraftStep(12, "Pick Phase 1", "red", "pick", "R3"),
    # Ban Phase 2 (Steps 13-16)
    DraftStep(13, "Ban Phase 2", "red", "ban", "RB4"),
    DraftStep(14, "Ban Phase 2", "blue", "ban", "BB4"),
    DraftStep(15, "Ban Phase 2", "red", "ban", "RB5"),
    DraftStep(16, "Ban Phase 2", "blue", "ban", "BB5"),
    # Pick Phase 2 (Steps 17-20)
    DraftStep(17, "Pick Phase 2", "red", "pick", "R4"),
    DraftStep(18, "Pick Phase 2", "blue", "pick", "B4"),
    DraftStep(19, "Pick Phase 2", "blue", "pick", "B5"),
    DraftStep(20, "Pick Phase 2", "red", "pick", "R5"),
)


# Tactical archetype metadata for pro-play champions (role, damage, engage, frontline, early_prio, scaling)
CHAMPION_ARCHETYPES: Dict[str, Dict[str, Any]] = {
    # Top
    "K'Sante": {"roles": ["Top"], "dmg": "AD", "engage": 0.75, "frontline": 0.95, "early_prio": 0.55, "scaling": 0.80},
    "Rumble": {"roles": ["Top"], "dmg": "AP", "engage": 0.65, "frontline": 0.45, "early_prio": 0.90, "scaling": 0.70},
    "Jax": {"roles": ["Top", "Jungle"], "dmg": "Mixed", "engage": 0.65, "frontline": 0.70, "early_prio": 0.55, "scaling": 0.90},
    "Renekton": {"roles": ["Top"], "dmg": "AD", "engage": 0.60, "frontline": 0.75, "early_prio": 0.92, "scaling": 0.45},
    "Gnar": {"roles": ["Top"], "dmg": "AD", "engage": 0.80, "frontline": 0.70, "early_prio": 0.72, "scaling": 0.72},
    "Ambessa": {"roles": ["Top"], "dmg": "AD", "engage": 0.82, "frontline": 0.68, "early_prio": 0.68, "scaling": 0.84},
    "Aurora": {"roles": ["Mid", "Top"], "dmg": "AP", "engage": 0.70, "frontline": 0.25, "early_prio": 0.78, "scaling": 0.80},
    "Ornn": {"roles": ["Top"], "dmg": "Mixed", "engage": 0.95, "frontline": 0.98, "early_prio": 0.45, "scaling": 0.92},
    "Aatrox": {"roles": ["Top"], "dmg": "AD", "engage": 0.55, "frontline": 0.75, "early_prio": 0.68, "scaling": 0.70},
    "Jayce": {"roles": ["Top", "Mid"], "dmg": "AD", "engage": 0.20, "frontline": 0.25, "early_prio": 0.90, "scaling": 0.65},
    "Gwen": {"roles": ["Top"], "dmg": "AP", "engage": 0.25, "frontline": 0.50, "early_prio": 0.48, "scaling": 0.94},
    "Camille": {"roles": ["Top"], "dmg": "AD", "engage": 0.85, "frontline": 0.62, "early_prio": 0.58, "scaling": 0.86},
    "Olaf": {"roles": ["Top", "Jungle"], "dmg": "AD", "engage": 0.55, "frontline": 0.72, "early_prio": 0.82, "scaling": 0.55},
    "Sion": {"roles": ["Top"], "dmg": "AD", "engage": 0.85, "frontline": 0.96, "early_prio": 0.48, "scaling": 0.82},
    "Udyr": {"roles": ["Top", "Jungle"], "dmg": "AP", "engage": 0.55, "frontline": 0.85, "early_prio": 0.72, "scaling": 0.68},
    # Jungle
    "Naafiri": {"roles": ["Jungle", "Mid"], "dmg": "AD", "engage": 0.78, "frontline": 0.42, "early_prio": 0.80, "scaling": 0.72},
    "Trundle": {"roles": ["Jungle", "Top"], "dmg": "AD", "engage": 0.48, "frontline": 0.80, "early_prio": 0.82, "scaling": 0.62},
    "Rek'Sai": {"roles": ["Jungle"], "dmg": "AD", "engage": 0.76, "frontline": 0.68, "early_prio": 0.90, "scaling": 0.48},
    "Elise": {"roles": ["Jungle", "Support"], "dmg": "AP", "engage": 0.68, "frontline": 0.35, "early_prio": 0.94, "scaling": 0.45},
    "Gragas": {"roles": ["Jungle", "Top"], "dmg": "AP", "engage": 0.86, "frontline": 0.76, "early_prio": 0.68, "scaling": 0.76},
    "Skarner": {"roles": ["Jungle", "Top"], "dmg": "Mixed", "engage": 0.92, "frontline": 0.92, "early_prio": 0.68, "scaling": 0.78},
    "Vi": {"roles": ["Jungle"], "dmg": "AD", "engage": 0.95, "frontline": 0.68, "early_prio": 0.72, "scaling": 0.65},
    "Sejuani": {"roles": ["Jungle"], "dmg": "AP", "engage": 0.90, "frontline": 0.90, "early_prio": 0.62, "scaling": 0.75},
    "Maokai": {"roles": ["Jungle", "Support"], "dmg": "AP", "engage": 0.92, "frontline": 0.85, "early_prio": 0.55, "scaling": 0.82},
    "Xin Zhao": {"roles": ["Jungle"], "dmg": "AD", "engage": 0.70, "frontline": 0.72, "early_prio": 0.88, "scaling": 0.55},
    "Wukong": {"roles": ["Jungle"], "dmg": "AD", "engage": 0.88, "frontline": 0.70, "early_prio": 0.68, "scaling": 0.76},
    "Nocturne": {"roles": ["Jungle"], "dmg": "AD", "engage": 0.88, "frontline": 0.55, "early_prio": 0.65, "scaling": 0.68},
    "Viego": {"roles": ["Jungle"], "dmg": "AD", "engage": 0.45, "frontline": 0.52, "early_prio": 0.66, "scaling": 0.82},
    "Lee Sin": {"roles": ["Jungle"], "dmg": "AD", "engage": 0.72, "frontline": 0.55, "early_prio": 0.92, "scaling": 0.50},
    "Nidalee": {"roles": ["Jungle"], "dmg": "AP", "engage": 0.15, "frontline": 0.20, "early_prio": 0.95, "scaling": 0.52},
    "Ivern": {"roles": ["Jungle"], "dmg": "AP", "engage": 0.35, "frontline": 0.40, "early_prio": 0.65, "scaling": 0.84},
    "Zyra": {"roles": ["Jungle", "Support"], "dmg": "AP", "engage": 0.55, "frontline": 0.20, "early_prio": 0.84, "scaling": 0.74},
    "Poppy": {"roles": ["Jungle", "Support", "Top"], "dmg": "AD", "engage": 0.68, "frontline": 0.86, "early_prio": 0.76, "scaling": 0.72},
    "Jarvan IV": {"roles": ["Jungle"], "dmg": "AD", "engage": 0.90, "frontline": 0.74, "early_prio": 0.82, "scaling": 0.62},
    "Pantheon": {"roles": ["Jungle", "Support", "Mid"], "dmg": "AD", "engage": 0.80, "frontline": 0.52, "early_prio": 0.94, "scaling": 0.48},
    "Lillia": {"roles": ["Jungle"], "dmg": "AP", "engage": 0.75, "frontline": 0.42, "early_prio": 0.55, "scaling": 0.86},
    # Mid
    "Azir": {"roles": ["Mid"], "dmg": "AP", "engage": 0.78, "frontline": 0.25, "early_prio": 0.68, "scaling": 0.95},
    "Orianna": {"roles": ["Mid"], "dmg": "AP", "engage": 0.65, "frontline": 0.20, "early_prio": 0.76, "scaling": 0.90},
    "Ahri": {"roles": ["Mid"], "dmg": "AP", "engage": 0.72, "frontline": 0.25, "early_prio": 0.78, "scaling": 0.76},
    "Taliyah": {"roles": ["Mid", "Jungle"], "dmg": "AP", "engage": 0.68, "frontline": 0.22, "early_prio": 0.82, "scaling": 0.78},
    "Yone": {"roles": ["Mid", "Top"], "dmg": "Mixed", "engage": 0.82, "frontline": 0.48, "early_prio": 0.55, "scaling": 0.92},
    "Corki": {"roles": ["Mid", "Bot"], "dmg": "Mixed", "engage": 0.20, "frontline": 0.22, "early_prio": 0.84, "scaling": 0.82},
    "Sylas": {"roles": ["Mid"], "dmg": "AP", "engage": 0.70, "frontline": 0.52, "early_prio": 0.64, "scaling": 0.85},
    "Viktor": {"roles": ["Mid"], "dmg": "AP", "engage": 0.35, "frontline": 0.22, "early_prio": 0.72, "scaling": 0.94},
    "Galio": {"roles": ["Mid", "Support"], "dmg": "AP", "engage": 0.85, "frontline": 0.84, "early_prio": 0.68, "scaling": 0.74},
    "Syndra": {"roles": ["Mid"], "dmg": "AP", "engage": 0.55, "frontline": 0.18, "early_prio": 0.85, "scaling": 0.82},
    "LeBlanc": {"roles": ["Mid"], "dmg": "AP", "engage": 0.48, "frontline": 0.15, "early_prio": 0.90, "scaling": 0.62},
    "Cassiopeia": {"roles": ["Mid"], "dmg": "AP", "engage": 0.45, "frontline": 0.35, "early_prio": 0.68, "scaling": 0.90},
    "Smolder": {"roles": ["Mid", "Bot"], "dmg": "Mixed", "engage": 0.10, "frontline": 0.18, "early_prio": 0.42, "scaling": 0.98},
    "Tristana": {"roles": ["Mid", "Bot"], "dmg": "AD", "engage": 0.30, "frontline": 0.20, "early_prio": 0.84, "scaling": 0.86},
    "Ryze": {"roles": ["Mid"], "dmg": "AP", "engage": 0.58, "frontline": 0.42, "early_prio": 0.66, "scaling": 0.90},
    "Annie": {"roles": ["Mid", "Support"], "dmg": "AP", "engage": 0.84, "frontline": 0.25, "early_prio": 0.70, "scaling": 0.74},
    "Hwei": {"roles": ["Mid", "Bot"], "dmg": "AP", "engage": 0.52, "frontline": 0.18, "early_prio": 0.82, "scaling": 0.84},
    "Karma": {"roles": ["Mid", "Support"], "dmg": "AP", "engage": 0.35, "frontline": 0.25, "early_prio": 0.92, "scaling": 0.68},
    "Mel": {"roles": ["Mid", "Bot"], "dmg": "AP", "engage": 0.45, "frontline": 0.20, "early_prio": 0.80, "scaling": 0.86},
    # Bot (ADC)
    "Yunara": {"roles": ["Bot"], "dmg": "Mixed", "engage": 0.35, "frontline": 0.20, "early_prio": 0.76, "scaling": 0.92},
    "Sivir": {"roles": ["Bot"], "dmg": "AD", "engage": 0.45, "frontline": 0.18, "early_prio": 0.74, "scaling": 0.90},
    "Draven": {"roles": ["Bot"], "dmg": "AD", "engage": 0.25, "frontline": 0.20, "early_prio": 0.96, "scaling": 0.58},
    "Senna": {"roles": ["Bot", "Support"], "dmg": "AD", "engage": 0.45, "frontline": 0.15, "early_prio": 0.78, "scaling": 0.90},
    "Kalista": {"roles": ["Bot"], "dmg": "AD", "engage": 0.65, "frontline": 0.20, "early_prio": 0.96, "scaling": 0.55},
    "Varus": {"roles": ["Bot"], "dmg": "Mixed", "engage": 0.72, "frontline": 0.18, "early_prio": 0.88, "scaling": 0.72},
    "Ashe": {"roles": ["Bot"], "dmg": "AD", "engage": 0.85, "frontline": 0.18, "early_prio": 0.86, "scaling": 0.70},
    "Ezreal": {"roles": ["Bot"], "dmg": "Mixed", "engage": 0.15, "frontline": 0.22, "early_prio": 0.74, "scaling": 0.82},
    "Kai'Sa": {"roles": ["Bot"], "dmg": "Mixed", "engage": 0.45, "frontline": 0.22, "early_prio": 0.52, "scaling": 0.92},
    "Ziggs": {"roles": ["Bot", "Mid"], "dmg": "AP", "engage": 0.20, "frontline": 0.15, "early_prio": 0.88, "scaling": 0.80},
    "Jhin": {"roles": ["Bot"], "dmg": "AD", "engage": 0.62, "frontline": 0.18, "early_prio": 0.78, "scaling": 0.76},
    "Miss Fortune": {"roles": ["Bot"], "dmg": "AD", "engage": 0.45, "frontline": 0.18, "early_prio": 0.82, "scaling": 0.76},
    "Xayah": {"roles": ["Bot"], "dmg": "AD", "engage": 0.35, "frontline": 0.25, "early_prio": 0.66, "scaling": 0.88},
    "Jinx": {"roles": ["Bot"], "dmg": "AD", "engage": 0.25, "frontline": 0.15, "early_prio": 0.48, "scaling": 0.95},
    "Caitlyn": {"roles": ["Bot"], "dmg": "AD", "engage": 0.25, "frontline": 0.15, "early_prio": 0.94, "scaling": 0.82},
    "Zeri": {"roles": ["Bot"], "dmg": "AD", "engage": 0.25, "frontline": 0.20, "early_prio": 0.48, "scaling": 0.94},
    "Lucian": {"roles": ["Bot"], "dmg": "AD", "engage": 0.30, "frontline": 0.20, "early_prio": 0.92, "scaling": 0.68},
    # Support
    "Rell": {"roles": ["Support"], "dmg": "AP", "engage": 0.98, "frontline": 0.85, "early_prio": 0.65, "scaling": 0.75},
    "Rakan": {"roles": ["Support"], "dmg": "AP", "engage": 0.95, "frontline": 0.60, "early_prio": 0.62, "scaling": 0.82},
    "Nautilus": {"roles": ["Support"], "dmg": "AP", "engage": 0.94, "frontline": 0.82, "early_prio": 0.74, "scaling": 0.65},
    "Leona": {"roles": ["Support"], "dmg": "AP", "engage": 0.95, "frontline": 0.88, "early_prio": 0.72, "scaling": 0.68},
    "Alistar": {"roles": ["Support"], "dmg": "AP", "engage": 0.92, "frontline": 0.92, "early_prio": 0.58, "scaling": 0.78},
    "Braum": {"roles": ["Support"], "dmg": "AP", "engage": 0.55, "frontline": 0.88, "early_prio": 0.60, "scaling": 0.80},
    "Renata Glasc": {"roles": ["Support"], "dmg": "AP", "engage": 0.55, "frontline": 0.30, "early_prio": 0.78, "scaling": 0.86},
    "Lulu": {"roles": ["Support"], "dmg": "AP", "engage": 0.20, "frontline": 0.20, "early_prio": 0.72, "scaling": 0.88},
    "Nami": {"roles": ["Support"], "dmg": "AP", "engage": 0.52, "frontline": 0.20, "early_prio": 0.82, "scaling": 0.76},
    "Bard": {"roles": ["Support"], "dmg": "AP", "engage": 0.82, "frontline": 0.45, "early_prio": 0.74, "scaling": 0.84},
    "Thresh": {"roles": ["Support"], "dmg": "AP", "engage": 0.78, "frontline": 0.58, "early_prio": 0.74, "scaling": 0.75},
    "Pyke": {"roles": ["Support"], "dmg": "AD", "engage": 0.75, "frontline": 0.25, "early_prio": 0.90, "scaling": 0.45},
    "Tahm Kench": {"roles": ["Support", "Top"], "dmg": "AP", "engage": 0.50, "frontline": 0.92, "early_prio": 0.62, "scaling": 0.76},
    "Neeko": {"roles": ["Support", "Mid"], "dmg": "AP", "engage": 0.92, "frontline": 0.40, "early_prio": 0.84, "scaling": 0.74},
    "Milio": {"roles": ["Support"], "dmg": "AP", "engage": 0.15, "frontline": 0.18, "early_prio": 0.68, "scaling": 0.90},
}


def get_champion_archetype(champion: str) -> Dict[str, Any]:
    return CHAMPION_ARCHETYPES.get(
        champion,
        {"roles": ["Flex"], "dmg": "Mixed", "engage": 0.55, "frontline": 0.50, "early_prio": 0.60, "scaling": 0.70},
    )


def compute_fearless_locked(prior_games_picks: Iterable[Iterable[str]]) -> List[str]:
    """Return sorted unique champions picked by EITHER team across previous games in the series."""
    locked: Set[str] = set()
    for game_picks in prior_games_picks:
        for champ in game_picks:
            clean = champ.strip()
            if clean:
                locked.add(clean)
    return sorted(locked)


def validate_draft_action(
    champion: str,
    locked_champions: Iterable[str],
    banned_champions: Iterable[str],
    picked_champions: Iterable[str],
) -> Tuple[bool, str]:
    """Verify whether a champion can legally be banned or picked in the current Fearless game."""
    clean = champion.strip()
    if not clean:
        return False, "Champion name cannot be empty."
    if clean in set(locked_champions):
        return False, f"{clean} is Fearless-locked from an earlier game in this series."
    if clean in set(banned_champions):
        return False, f"{clean} has already been banned in this game."
    if clean in set(picked_champions):
        return False, f"{clean} has already been picked in this game."
    return True, "OK"


def _shannon_entropy(counts: Sequence[int]) -> float:
    total = sum(counts)
    if total <= 0:
        return 0.0
    ent = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            ent -= p * math.log2(p)
    return ent


def smoothed_win_rate(wins: int, games: int, prior_wins: float = 2.5, prior_games: float = 5.0) -> float:
    """Dirichlet/Beta-smoothed win rate preventing small-sample 0% or 100% distortion."""
    return (wins + prior_wins) / max(1.0, games + prior_games)


def compute_pinch_score(
    role_pool_stats: Sequence[Dict[str, Any]],
    locked_champions: Iterable[str],
    banned_champions: Iterable[str],
    comfort_min_games: int = 2,
) -> Dict[str, Any]:
    """Quantify how severely an opponent player's or role's champion pool is pinched.

    Args:
        role_pool_stats: List of dicts `{"champion": str, "games": int, "wins": int}` for an opponent player/role.
        locked_champions: Champions burned via Fearless Draft in earlier games.
        banned_champions: Champions banned in the current draft.
        comfort_min_games: Minimum games required to treat a pick as a proven comfort pick.

    Returns:
        Dict with pinch_index [0..100], pool_share_removed, entropy_drop_pct,
        expected_wr_delta, remaining_comfort_picks, and actionable coaching text.
    """
    unavailable = set(locked_champions) | set(banned_champions)
    valid_pool = [r for r in role_pool_stats if int(r.get("games", 0)) > 0]
    total_games = sum(int(r["games"]) for r in valid_pool)
    if total_games == 0:
        return {
            "pinch_index": 0.0,
            "pool_share_removed": 0.0,
            "entropy_drop_pct": 0.0,
            "baseline_wr": 0.5,
            "remaining_wr": 0.5,
            "expected_wr_delta": 0.0,
            "remaining_comfort_count": 0,
            "burned_champions": [],
            "remaining_top": [],
            "sample_games": 0,
        }

    baseline_counts = [int(r["games"]) for r in valid_pool]
    baseline_entropy = _shannon_entropy(baseline_counts)

    baseline_weighted_wr = sum(
        int(r["games"]) * smoothed_win_rate(int(r.get("wins", 0)), int(r["games"]))
        for r in valid_pool
    ) / total_games

    remaining = [r for r in valid_pool if r["champion"] not in unavailable]
    burned = [r["champion"] for r in valid_pool if r["champion"] in unavailable]
    removed_games = sum(int(r["games"]) for r in valid_pool if r["champion"] in unavailable)
    pool_share_removed = removed_games / total_games

    initial_comfort = [r for r in valid_pool if int(r["games"]) >= comfort_min_games]
    remaining_comfort = [r for r in remaining if int(r["games"]) >= comfort_min_games]

    if remaining:
        rem_total = sum(int(r["games"]) for r in remaining)
        rem_entropy = _shannon_entropy([int(r["games"]) for r in remaining])
        rem_weighted_wr = sum(
            int(r["games"]) * smoothed_win_rate(int(r.get("wins", 0)), int(r["games"]))
            for r in remaining
        ) / rem_total
        # Off-comfort penalty when player's proven comfort pool is depleted relative to baseline
        if initial_comfort and len(remaining_comfort) == 0:
            rem_weighted_wr -= 0.065
        elif len(initial_comfort) >= 2 and len(remaining_comfort) == 1:
            rem_weighted_wr -= 0.030
    else:
        rem_entropy = 0.0
        rem_weighted_wr = max(0.35, baseline_weighted_wr - 0.11)

    entropy_drop_pct = (
        max(0.0, (baseline_entropy - rem_entropy) / baseline_entropy)
        if baseline_entropy > 1e-6
        else (1.0 if not remaining else 0.0)
    )
    expected_wr_delta = rem_weighted_wr - baseline_weighted_wr  # negative when opponent is hurt

    # Composite Pinch Severity Index (0-100): strictly 0 when zero pool champions are removed
    if removed_games == 0:
        pinch_index = 0.0
    else:
        comfort_depletion = (
            (len(initial_comfort) - len(remaining_comfort)) / len(initial_comfort)
            if initial_comfort
            else pool_share_removed
        )
        raw_index = (
            0.50 * pool_share_removed
            + 0.30 * comfort_depletion
            + 0.20 * min(1.0, max(0.0, -expected_wr_delta / 0.12))
        ) * 100.0
        pinch_index = round(min(100.0, max(0.0, raw_index)), 1)

    remaining_sorted = sorted(remaining, key=lambda x: (-int(x["games"]), -int(x.get("wins", 0))))
    return {
        "pinch_index": pinch_index,
        "pool_share_removed": round(pool_share_removed, 4),
        "entropy_drop_pct": round(entropy_drop_pct, 4),
        "baseline_wr": round(baseline_weighted_wr, 4),
        "remaining_wr": round(rem_weighted_wr, 4),
        "expected_wr_delta": round(expected_wr_delta, 4),
        "remaining_comfort_count": len(remaining_comfort),
        "burned_champions": burned,
        "remaining_top": [
            {
                "champion": r["champion"],
                "games": int(r["games"]),
                "wins": int(r.get("wins", 0)),
                "wr": round(smoothed_win_rate(int(r.get("wins", 0)), int(r["games"])), 3),
            }
            for r in remaining_sorted[:3]
        ],
        "sample_games": total_games,
    }


def evaluate_comp_balance(picks: Sequence[str]) -> Dict[str, float]:
    """Score a partial or full 5-champion lineup across tactical pro-play dimensions."""
    if not picks:
        return {
            "engage": 0.5,
            "frontline": 0.5,
            "early_prio": 0.5,
            "scaling": 0.5,
            "damage_mix": 0.5,
            "composite": 0.5,
        }

    archs = [get_champion_archetype(c) for c in picks]
    max_engage = max(a["engage"] for a in archs)
    avg_frontline = sum(a["frontline"] for a in archs) / len(archs)
    avg_prio = sum(a["early_prio"] for a in archs) / len(archs)
    avg_scaling = sum(a["scaling"] for a in archs) / len(archs)

    has_ad = any(a["dmg"] in ("AD", "Mixed") for a in archs)
    has_ap = any(a["dmg"] in ("AP", "Mixed") for a in archs)
    if len(picks) < 2:
        dmg_mix = 0.65
    elif has_ad and has_ap:
        dmg_mix = 0.90
    else:
        dmg_mix = 0.32  # Easy to itemize armor/MR against mono-damage comps

    frontline_score = min(1.0, avg_frontline / 0.58)
    composite = (
        0.28 * max_engage
        + 0.24 * frontline_score
        + 0.20 * dmg_mix
        + 0.14 * avg_prio
        + 0.14 * avg_scaling
    )
    return {
        "engage": round(max_engage, 3),
        "frontline": round(frontline_score, 3),
        "early_prio": round(avg_prio, 3),
        "scaling": round(avg_scaling, 3),
        "damage_mix": round(dmg_mix, 3),
        "composite": round(composite, 3),
    }


def estimate_live_win_probability(
    c9_side: str,
    c9_picks: Sequence[str],
    opp_picks: Sequence[str],
    champ_metrics: Optional[Dict[str, Dict[str, Any]]] = None,
    pinch_bonus: float = 0.0,
) -> Dict[str, Any]:
    """Estimate Cloud9's live win probability in [0.05, 0.95] via calibrated log-odds update.

    Args:
        c9_side: "blue" or "red".
        c9_picks: Champions currently locked by Cloud9 in this game.
        opp_picks: Champions currently locked by Opponent in this game.
        champ_metrics: Optional dict mapping champion -> {"c9_wr": float, "opp_wr": float, "global_wr": float}.
        pinch_bonus: Positive advantage [0..0.15] earned by pinching opponent champion pools.
    """
    metrics = champ_metrics or {}

    # Pro LoL structural side baseline (~52.2% Blue side historical advantage in Fearless Bo3/Bo5)
    side_logit = 0.088 if c9_side.lower() == "blue" else -0.088

    c9_skill_logit = 0.0
    for ch in c9_picks:
        m = metrics.get(ch, {})
        wr = float(m.get("c9_wr", m.get("global_wr", 0.51)))
        wr = min(0.72, max(0.32, wr))
        c9_skill_logit += 0.42 * math.log(wr / (1.0 - wr))

    opp_skill_logit = 0.0
    for ch in opp_picks:
        m = metrics.get(ch, {})
        wr = float(m.get("opp_wr", m.get("global_wr", 0.50)))
        wr = min(0.72, max(0.32, wr))
        opp_skill_logit += 0.42 * math.log(wr / (1.0 - wr))

    c9_comp = evaluate_comp_balance(c9_picks)
    opp_comp = evaluate_comp_balance(opp_picks)
    comp_delta_logit = 1.15 * (c9_comp["composite"] - opp_comp["composite"]) if (c9_picks or opp_picks) else 0.0

    clamped_pinch = min(0.20, max(-0.20, float(pinch_bonus)))
    pinch_logit = 2.4 * clamped_pinch

    total_logit = side_logit + (c9_skill_logit - opp_skill_logit) + comp_delta_logit + pinch_logit
    raw_prob = 1.0 / (1.0 + math.exp(-total_logit))
    win_prob = round(min(0.95, max(0.05, raw_prob)), 4)

    return {
        "c9_win_probability": win_prob,
        "opp_win_probability": round(1.0 - win_prob, 4),
        "c9_comp": c9_comp,
        "opp_comp": opp_comp,
        "factors": {
            "side_advantage": round(side_logit, 4),
            "comfort_mastery_delta": round(c9_skill_logit - opp_skill_logit, 4),
            "composition_synergy_delta": round(comp_delta_logit, 4),
            "fearless_pinch_leverage": round(pinch_logit, 4),
        },
    }
