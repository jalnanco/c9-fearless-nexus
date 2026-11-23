"""Zero-Redistribution Streaming GRID Telemetry & Metadata Analyzer.

Reads official GRID League of Legends files directly from `STL_DATA_DIR`
(default `../stl-hackathon-2026-grid-starter`) without copying or persisting
licensed data inside the project repository.
"""

from __future__ import annotations

import csv
import io
import json
import os
import pathlib
import shutil
import subprocess
from collections import Counter, defaultdict
from typing import Any, Dict, Iterator, List, Optional, Tuple

from backend.fearless_engine import (
    compute_pinch_score,
    get_champion_archetype,
    smoothed_win_rate,
)

SR_MIN_X, SR_MAX_X = 0.0, 15000.0
SR_MIN_Y, SR_MAX_Y = -300.0, 14700.0


def open_zst_lines(path: pathlib.Path) -> Iterator[str]:
    """Stream UTF-8 lines from a `.jsonl.zst` file using stdlib (3.14+), zstandard, or `zstd -dc` CLI."""
    try:
        from compression import zstd as std_zstd  # type: ignore

        with std_zstd.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                yield line
        return
    except ImportError:
        pass

    try:
        import zstandard  # type: ignore

        with open(path, "rb") as raw:
            dctx = zstandard.ZstdDecompressor()
            with dctx.stream_reader(raw) as reader:
                text_stream = io.TextIOWrapper(reader, encoding="utf-8")
                for line in text_stream:
                    yield line
        return
    except ImportError:
        pass

    zstd_bin = shutil.which("zstd") or "/opt/homebrew/bin/zstd"
    if not os.path.exists(zstd_bin):
        raise RuntimeError("No Zstandard decoder available (install Python 3.14+, `pip install zstandard`, or `zstd` CLI).")

    proc = subprocess.Popen([zstd_bin, "-dc", str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    assert proc.stdout is not None
    try:
        for line in proc.stdout:
            yield line
    finally:
        proc.stdout.close()
        proc.wait()


def classify_rift_zone(x: float, y: float) -> str:
    """Classify Summoner's Rift coordinates into tactical coaching zones."""
    nx = (x - SR_MIN_X) / (SR_MAX_X - SR_MIN_X)
    ny = (y - SR_MIN_Y) / (SR_MAX_Y - SR_MIN_Y)
    if 0.24 <= nx <= 0.44 and 0.56 <= ny <= 0.76:
        return "Baron / Void Grub Pit"
    if 0.56 <= nx <= 0.76 and 0.22 <= ny <= 0.42:
        return "Dragon Pit & Bot River"
    if 0.38 <= nx <= 0.62 and 0.38 <= ny <= 0.62:
        return "Mid Lane & Raptor Crossing"
    if ny - nx > 0.25:
        return "Top Side / Dive Zone"
    if nx - ny > 0.25:
        return "Bot Side / Tri-Bush"
    return "Jungle Invasion Corridor"


class GridLoLRepository:
    """In-memory tactical intelligence repository backed by `STL_DATA_DIR`."""

    def __init__(self, data_dir: Optional[pathlib.Path] = None, max_event_feeds: int = 40) -> None:
        env_dir = os.environ.get("STL_DATA_DIR", "../stl-hackathon-2026-grid-starter")
        self.data_dir = pathlib.Path(data_dir) if data_dir else pathlib.Path(env_dir)
        self.max_event_feeds = max_event_feeds
        self.available = (self.data_dir / "meta" / "games.csv").exists()

        self.teams: Dict[str, Dict[str, Any]] = {}
        self.team_games: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.team_rosters: Dict[str, Dict[str, Dict[str, Dict[str, int]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(lambda: {"games": 0, "wins": 0, "recent_2026": 0}))
        )
        self.team_champ_stats: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: {"games": 0, "wins": 0, "g1_games": 0, "g3plus_games": 0, "g3plus_wins": 0, "blue_games": 0, "red_games": 0})
        )
        self.global_champ_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"games": 0, "wins": 0})
        self.team_macro: Dict[str, Dict[str, Any]] = {}
        self.series_index: Dict[str, Dict[str, str]] = {}

        if self.available:
            self._load_metadata()
            self._scan_available_event_feeds()

    def _load_metadata(self) -> None:
        series_csv = self.data_dir / "lol" / "series.csv"
        if series_csv.exists():
            with open(series_csv, encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    self.series_index[row["series_id"]] = row

        teams_csv = self.data_dir / "meta" / "teams.csv"
        with open(teams_csv, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("title") == "lol":
                    self.teams[row["team_id"]] = row

        valid_games: Dict[Tuple[str, str], Dict[str, Any]] = {}
        games_csv = self.data_dir / "meta" / "games.csv"
        with open(games_csv, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("title") != "lol":
                    continue
                if row.get("session_valid") != "True" or row.get("finished") != "True":
                    continue
                key = (row["series_id"], row["game_id"])
                valid_games[key] = row
                for prefix in ("team1", "team2"):
                    tid = row[f"{prefix}_id"]
                    self.team_games[tid].append(
                        {
                            "series_id": row["series_id"],
                            "game_id": row["game_id"],
                            "game_number": int(row["game_number"] or 1),
                            "patch": row.get("patch", ""),
                            "started_at": row.get("started_at", ""),
                            "side": row.get(f"{prefix}_side", ""),
                            "won": row.get("winner_team_id") == tid,
                            "opponent_id": row["team2_id"] if prefix == "team1" else row["team1_id"],
                            "opponent_name": row["team2_name"] if prefix == "team1" else row["team1_name"],
                        }
                    )

        rosters_csv = self.data_dir / "meta" / "rosters.csv"
        with open(rosters_csv, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("title") != "lol" or row.get("participation_status") != "active":
                    continue
                ginfo = valid_games.get((row["series_id"], row["game_id"]))
                if not ginfo:
                    continue
                tid = row["team_id"]
                pname = row["player_name"].strip()
                cname = row["character_name"].strip()
                if not cname:
                    continue
                won = ginfo["winner_team_id"] == tid
                gnum = int(ginfo["game_number"] or 1)
                side = row.get("side", "")
                is_2026 = str(ginfo.get("started_at", "")).startswith("2026")

                pstat = self.team_rosters[tid][pname][cname]
                pstat["games"] += 1
                if won:
                    pstat["wins"] += 1
                if is_2026:
                    pstat["recent_2026"] += 1

                cstat = self.team_champ_stats[tid][cname]
                cstat["games"] += 1
                if won:
                    cstat["wins"] += 1
                if gnum == 1:
                    cstat["g1_games"] += 1
                if gnum >= 3:
                    cstat["g3plus_games"] += 1
                    if won:
                        cstat["g3plus_wins"] += 1
                if side == "blue":
                    cstat["blue_games"] += 1
                elif side == "red":
                    cstat["red_games"] += 1

                gstat = self.global_champ_stats[cname]
                gstat["games"] += 1
                if won:
                    gstat["wins"] += 1

    def _scan_available_event_feeds(self) -> None:
        lol_dir = self.data_dir / "lol"
        if not lol_dir.exists():
            return
        zst_files = sorted(lol_dir.glob("events_*_grid.jsonl.zst"), reverse=True)[: self.max_event_feeds]
        if not zst_files:
            return

        macro_acc: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "feeds_analyzed": 0,
                "games_analyzed": 0,
                "top_scuttle_first": 0,
                "bot_scuttle_first": 0,
                "first_void_grub": 0,
                "first_dragon": 0,
                "first_herald": 0,
                "first_tower": 0,
                "first_blood": 0,
                "phase1_bans": Counter(),
                "phase1_picks": Counter(),
                "phase2_bans": Counter(),
                "bans_against": Counter(),
                "early_kill_zones": Counter(),
                "hotspot_Buckets": Counter(),
            }
        )

        for zpath in zst_files:
            try:
                self._parse_single_feed(zpath, macro_acc)
            except Exception:
                continue

        for tid, acc in macro_acc.items():
            games_n = max(1, acc["games_analyzed"])
            scuttles = max(1, acc["top_scuttle_first"] + acc["bot_scuttle_first"])
            total_zones = max(1, sum(acc["early_kill_zones"].values()))
            self.team_macro[tid] = {
                "feeds_analyzed": acc["feeds_analyzed"],
                "games_analyzed": acc["games_analyzed"],
                "top_scuttle_rate": round(acc["top_scuttle_first"] / scuttles, 3),
                "bot_scuttle_rate": round(acc["bot_scuttle_first"] / scuttles, 3),
                "first_grub_rate": round(min(1.0, acc["first_void_grub"] / games_n), 3),
                "first_dragon_rate": round(min(1.0, acc["first_dragon"] / games_n), 3),
                "first_herald_rate": round(min(1.0, acc["first_herald"] / games_n), 3),
                "first_tower_rate": round(min(1.0, acc["first_tower"] / games_n), 3),
                "first_blood_rate": round(min(1.0, acc["first_blood"] / games_n), 3),
                "phase1_bans": [{"champion": ch, "count": cnt} for ch, cnt in acc["phase1_bans"].most_common(6)],
                "phase1_picks": [{"champion": ch, "count": cnt} for ch, cnt in acc["phase1_picks"].most_common(6)],
                "phase2_bans": [{"champion": ch, "count": cnt} for ch, cnt in acc["phase2_bans"].most_common(5)],
                "bans_against": [{"champion": ch, "count": cnt} for ch, cnt in acc["bans_against"].most_common(6)],
                "kill_zone_distribution": [
                    {"zone": z, "share": round(cnt / total_zones, 3), "events": cnt}
                    for z, cnt in acc["early_kill_zones"].most_common(6)
                ],
                "map_hotspots": [
                    {"gx": gx, "gy": gy, "weight": cnt}
                    for (gx, gy), cnt in acc["hotspot_Buckets"].most_common(14)
                ],
            }

    @staticmethod
    def _parse_single_feed(zpath: pathlib.Path, macro_acc: Dict[str, Dict[str, Any]]) -> None:
        last_full_state: Optional[Dict[str, Any]] = None
        game_first_flags: Dict[str, set] = defaultdict(set)
        kill_counts_per_game: Counter = Counter()
        seen_teams: set = set()

        for line in open_zst_lines(zpath):
            env = json.loads(line)
            for ev in env.get("events", []):
                if ev.get("includesFullState") and ev.get("seriesState"):
                    last_full_state = ev["seriesState"]

                et = ev.get("type", "")
                if "!" in et:
                    continue  # Ignore rolled-back actions per AGENTS.md invariant

                actor_state = ev.get("actor", {}).get("state", {})
                tid = str(actor_state.get("teamId") or "")
                if not tid:
                    continue
                seen_teams.add(tid)

                # Determine current game ID from partial seriesState if present
                s_games = (ev.get("seriesState") or {}).get("games") or []
                gid = str(s_games[-1].get("id")) if s_games else "g"
                flags = game_first_flags[gid]

                if et == "player-completed-slayRiftScuttlerTop" and "scuttle" not in flags:
                    flags.add("scuttle")
                    macro_acc[tid]["top_scuttle_first"] += 1
                elif et == "player-completed-slayRiftScuttlerBot" and "scuttle" not in flags:
                    flags.add("scuttle")
                    macro_acc[tid]["bot_scuttle_first"] += 1
                elif et == "player-completed-slayVoidGrub" and "grub" not in flags:
                    flags.add("grub")
                    macro_acc[tid]["first_void_grub"] += 1
                elif et == "player-completed-slayDragon" and "dragon" not in flags:
                    flags.add("dragon")
                    macro_acc[tid]["first_dragon"] += 1
                elif et == "player-completed-slayRiftHerald" and "herald" not in flags:
                    flags.add("herald")
                    macro_acc[tid]["first_herald"] += 1
                elif et in ("player-destroyed-tower", "team-destroyed-tower") and "tower" not in flags:
                    flags.add("tower")
                    macro_acc[tid]["first_tower"] += 1
                elif et == "player-killed-player":
                    kill_counts_per_game[gid] += 1
                    if "fb" not in flags:
                        flags.add("fb")
                        macro_acc[tid]["first_blood"] += 1
                    # Early skirmish spatial bucket (first 8 kills of each game ~ first 14 minutes)
                    if kill_counts_per_game[gid] <= 8:
                        pos = (actor_state.get("game") or {}).get("position") or {}
                        if "x" in pos and "y" in pos:
                            fx, fy = float(pos["x"]), float(pos["y"])
                            zone = classify_rift_zone(fx, fy)
                            macro_acc[tid]["early_kill_zones"][zone] += 1
                            gx = min(19, max(0, int((fx - SR_MIN_X) / (SR_MAX_X - SR_MIN_X) * 20)))
                            gy = min(19, max(0, int((fy - SR_MIN_Y) / (SR_MAX_Y - SR_MIN_Y) * 20)))
                            macro_acc[tid]["hotspot_Buckets"][(gx, gy)] += 1

        if not last_full_state or not last_full_state.get("valid", True):
            return

        series_teams = [str(t.get("id")) for t in last_full_state.get("teams", []) if t.get("id")]
        for tid in series_teams:
            macro_acc[tid]["feeds_analyzed"] += 1

        for game in last_full_state.get("games", []):
            if not game.get("finished"):
                continue
            g_teams = [str(t.get("id")) for t in game.get("teams", []) if t.get("id")]
            for tid in g_teams:
                macro_acc[tid]["games_analyzed"] += 1

            for dact in game.get("draftActions", []):
                seq = int(dact.get("sequenceNumber") or 0)
                dtype = dact.get("type", "")
                drafter_id = str((dact.get("drafter") or {}).get("id") or "")
                champ = (dact.get("draftable") or {}).get("name") or ""
                if not drafter_id or not champ:
                    continue
                other_ids = [t for t in g_teams if t != drafter_id]
                if dtype == "ban":
                    if 1 <= seq <= 6:
                        macro_acc[drafter_id]["phase1_bans"][champ] += 1
                    elif 13 <= seq <= 16:
                        macro_acc[drafter_id]["phase2_bans"][champ] += 1
                    for oid in other_ids:
                        macro_acc[oid]["bans_against"][champ] += 1
                elif dtype == "pick" and 7 <= seq <= 12:
                    macro_acc[drafter_id]["phase1_picks"][champ] += 1

    def find_c9_team_id(self) -> Optional[str]:
        for tid, info in self.teams.items():
            if "Cloud9" in info.get("name", ""):
                return tid
        return None

    def build_team_scouting_profile(self, team_id: str) -> Dict[str, Any]:
        info = self.teams.get(team_id, {"team_id": team_id, "name": "Unknown Team"})
        games = self.team_games.get(team_id, [])
        total_games = len(games)
        wins = sum(1 for g in games if g["won"])
        blue_games = [g for g in games if g["side"] == "blue"]
        red_games = [g for g in games if g["side"] == "red"]
        g3plus = [g for g in games if g["game_number"] >= 3]

        # Active 5-player roster (most recent / highest sample players)
        player_entries = []
        for pname, cdict in self.team_rosters.get(team_id, {}).items():
            pgames = sum(v["games"] for v in cdict.values())
            pwins = sum(v["wins"] for v in cdict.values())
            precent = sum(v["recent_2026"] for v in cdict.values())
            pool_list = sorted(
                [{"champion": ch, "games": v["games"], "wins": v["wins"]} for ch, v in cdict.items()],
                key=lambda x: (-x["games"], -x["wins"]),
            )
            # Infer primary role from top 4 champions
            role_votes: Counter = Counter()
            for item in pool_list[:4]:
                for r in get_champion_archetype(item["champion"])["roles"]:
                    if r != "Flex":
                        role_votes[r] += item["games"]
            inferred_role = role_votes.most_common(1)[0][0] if role_votes else "Flex"
            player_entries.append(
                {
                    "player": pname,
                    "role": inferred_role,
                    "games": pgames,
                    "recent_2026_games": precent,
                    "win_rate": round(pwins / max(1, pgames), 3),
                    "pool": pool_list[:10],
                }
            )
        player_entries.sort(key=lambda x: (-x["recent_2026_games"], -x["games"]))
        top5 = player_entries[:5]
        role_order = {"Top": 0, "Jungle": 1, "Mid": 2, "Bot": 3, "Support": 4, "Flex": 5}
        top5.sort(key=lambda x: (role_order.get(x["role"], 5), -x["games"]))

        champ_rows = []
        for ch, st in self.team_champ_stats.get(team_id, {}).items():
            champ_rows.append(
                {
                    "champion": ch,
                    "games": st["games"],
                    "wins": st["wins"],
                    "win_rate": round(st["wins"] / max(1, st["games"]), 3),
                    "smoothed_wr": round(smoothed_win_rate(st["wins"], st["games"]), 3),
                    "g1_games": st["g1_games"],
                    "g3plus_games": st["g3plus_games"],
                    "g3plus_wins": st["g3plus_wins"],
                    "blue_games": st["blue_games"],
                    "red_games": st["red_games"],
                    "archetype": get_champion_archetype(ch),
                }
            )
        champ_rows.sort(key=lambda x: (-x["games"], -x["wins"]))

        return {
            "team_id": team_id,
            "name": info.get("name", ""),
            "events": info.get("events", ""),
            "sample_games": total_games,
            "overall_win_rate": round(wins / max(1, total_games), 3),
            "blue_win_rate": round(sum(1 for g in blue_games if g["won"]) / max(1, len(blue_games)), 3),
            "red_win_rate": round(sum(1 for g in red_games if g["won"]) / max(1, len(red_games)), 3),
            "fearless_g3plus_games": len(g3plus),
            "fearless_g3plus_win_rate": round(sum(1 for g in g3plus if g["won"]) / max(1, len(g3plus)), 3),
            "players": top5,
            "signature_champions": champ_rows[:18],
            "macro": self.team_macro.get(team_id, {}),
            "pinch_preview_empty": [
                {
                    "player": p["player"],
                    "role": p["role"],
                    **compute_pinch_score(p["pool"], [], []),
                }
                for p in top5
            ],
        }
