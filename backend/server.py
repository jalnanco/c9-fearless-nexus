"""Zero-dependency HTTP API & Static UI server for C9 Fearless Nexus.

Run locally with:
    STL_DATA_DIR=../stl-hackathon-2026-grid-starter python3 -m backend.server
"""

from __future__ import annotations

import json
import mimetypes
import os
import pathlib
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List
from urllib.parse import parse_qs, urlparse

from backend.fearless_engine import (
    CHAMPION_ARCHETYPES,
    TOURNAMENT_DRAFT_SEQUENCE,
    compute_fearless_locked,
    compute_pinch_score,
    estimate_live_win_probability,
    get_champion_archetype,
    validate_draft_action,
)
from backend.grid_stream import GridLoLRepository

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"


def recommend_next_actions(
    c9_profile: Dict[str, Any],
    opp_profile: Dict[str, Any],
    c9_side: str,
    step_index: int,
    prior_games_picks: List[List[str]],
    banned_champions: List[str],
    c9_picks: List[str],
    opp_picks: List[str],
) -> Dict[str, Any]:
    """Generate coach-grade Ban/Pick recommendations, Pinch Index cards, and Win-Rate forecast."""
    locked = compute_fearless_locked(prior_games_picks)
    unavailable = set(locked) | set(banned_champions) | set(c9_picks) | set(opp_picks)

    # Compute Pinch Scores across opponent's active 5 players
    opp_pinches = []
    for p in opp_profile.get("players", [])[:5]:
        ps = compute_pinch_score(p.get("pool", []), locked, banned_champions)
        opp_pinches.append({"player": p["player"], "role": p["role"], **ps})

    avg_pinch_bonus = sum(max(0.0, -p["expected_wr_delta"]) for p in opp_pinches) / max(1, len(opp_pinches))

    champ_metrics: Dict[str, Dict[str, float]] = {}
    for row in c9_profile.get("signature_champions", []):
        champ_metrics.setdefault(row["champion"], {})["c9_wr"] = float(row["smoothed_wr"])
    for row in opp_profile.get("signature_champions", []):
        champ_metrics.setdefault(row["champion"], {})["opp_wr"] = float(row["smoothed_wr"])

    live_eval = estimate_live_win_probability(
        c9_side=c9_side,
        c9_picks=c9_picks,
        opp_picks=opp_picks,
        champ_metrics=champ_metrics,
        pinch_bonus=avg_pinch_bonus,
    )

    step_meta = (
        TOURNAMENT_DRAFT_SEQUENCE[step_index]
        if 0 <= step_index < len(TOURNAMENT_DRAFT_SEQUENCE)
        else None
    )

    # Candidate Target Bans (maximize incremental pinch against opponent comfort picks)
    ban_recommendations = []
    for p in opp_profile.get("players", [])[:5]:
        base_pinch = compute_pinch_score(p.get("pool", []), locked, banned_champions)
        for c_entry in p.get("pool", [])[:5]:
            ch = c_entry["champion"]
            if ch in unavailable:
                continue
            sim_pinch = compute_pinch_score(p.get("pool", []), locked, list(banned_champions) + [ch])
            delta_idx = round(sim_pinch["pinch_index"] - base_pinch["pinch_index"], 1)
            wr_drop = round((sim_pinch["expected_wr_delta"] - base_pinch["expected_wr_delta"]) * 100, 1)
            ban_recommendations.append(
                {
                    "champion": ch,
                    "target_player": p["player"],
                    "role": p["role"],
                    "opp_games": c_entry["games"],
                    "opp_wins": c_entry["wins"],
                    "pinch_gain": delta_idx,
                    "opp_wr_shift_pct": wr_drop,
                    "rationale": (
                        f"{p['player']} plays {ch} in {c_entry['games']} games ({c_entry['wins']}W); "
                        f"banning raises {p['role']} Pinch Index +{delta_idx} pts ({sim_pinch['remaining_comfort_count']} comfort left)."
                    ),
                }
            )
    ban_recommendations.sort(key=lambda x: (-x["pinch_gain"], -x["opp_games"]))

    # Candidate C9 Picks (maximize Cloud9 win-probability delta + role coverage)
    covered_roles = set()
    for ch in c9_picks:
        covered_roles.update(get_champion_archetype(ch)["roles"])

    c9_sig_map = {r["champion"]: r for r in c9_profile.get("signature_champions", [])}
    candidate_pool = list(dict.fromkeys(list(c9_sig_map.keys()) + list(CHAMPION_ARCHETYPES.keys())))

    pick_recommendations = []
    for ch in candidate_pool:
        if ch in unavailable:
            continue
        sim_eval = estimate_live_win_probability(
            c9_side=c9_side,
            c9_picks=list(c9_picks) + [ch],
            opp_picks=opp_picks,
            champ_metrics=champ_metrics,
            pinch_bonus=avg_pinch_bonus,
        )
        arch = get_champion_archetype(ch)
        primary_role = arch["roles"][0]
        role_bonus = 0.018 if primary_role not in covered_roles else -0.012
        c9_row = c9_sig_map.get(ch)
        mastery_games = int(c9_row["games"]) if c9_row else 0
        mastery_wins = int(c9_row["wins"]) if c9_row else 0
        score = sim_eval["c9_win_probability"] + role_bonus + min(0.015, mastery_games * 0.0015)
        wr_gain_pct = round((sim_eval["c9_win_probability"] - live_eval["c9_win_probability"]) * 100, 1)
        pick_recommendations.append(
            {
                "champion": ch,
                "role": primary_role,
                "dmg": arch["dmg"],
                "c9_games": mastery_games,
                "c9_wins": mastery_wins,
                "projected_c9_wr": round(sim_eval["c9_win_probability"] * 100, 1),
                "wr_delta_pct": wr_gain_pct,
                "score": round(score, 4),
                "rationale": (
                    f"{primary_role} ({arch['dmg']}) · C9 sample n={mastery_games} ({mastery_wins}W) · "
                    f"Shifts live win probability { '+' if wr_gain_pct >= 0 else '' }{wr_gain_pct}%."
                ),
            }
        )
    pick_recommendations.sort(key=lambda x: -x["score"])

    return {
        "current_step": (
            {
                "step": step_meta.step,
                "phase": step_meta.phase,
                "side": step_meta.side,
                "action": step_meta.action,
                "slot": step_meta.slot,
            }
            if step_meta
            else None
        ),
        "fearless_locked": locked,
        "fearless_locked_count": len(locked),
        "opponent_pinches": opp_pinches,
        "live_prediction": live_eval,
        "ban_recommendations": ban_recommendations[:6],
        "pick_recommendations": pick_recommendations[:6],
    }


def create_app_handler(repo: GridLoLRepository):
    class NexusHandler(BaseHTTPRequestHandler):
        def _send_json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()
            self.wfile.write(body)

        # noinspection PyPep8Naming
        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()

        # noinspection PyPep8Naming
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path

            if path == "/api/health":
                c9_id = repo.find_c9_team_id()
                self._send_json(
                    {
                        "status": "ok",
                        "grid_data_connected": repo.available,
                        "data_dir": str(repo.data_dir),
                        "lol_teams_loaded": len(repo.teams),
                        "event_feeds_indexed": sum(m.get("feeds_analyzed", 0) for m in repo.team_macro.values()) // 2,
                        "c9_team_id": c9_id,
                    }
                )
                return

            if path == "/api/teams":
                teams_out = []
                for tid, info in repo.teams.items():
                    gcount = len(repo.team_games.get(tid, []))
                    if gcount >= 5:
                        teams_out.append(
                            {
                                "team_id": tid,
                                "name": info.get("name", ""),
                                "games": gcount,
                                "has_macro_telemetry": tid in repo.team_macro,
                                "events": info.get("events", ""),
                            }
                        )
                teams_out.sort(key=lambda x: (-int(x["has_macro_telemetry"]), -x["games"], x["name"]))
                self._send_json({"teams": teams_out, "c9_team_id": repo.find_c9_team_id()})
                return

            if path == "/api/scouting":
                qs = parse_qs(parsed.query)
                opp_id = (qs.get("opponent_id") or [""])[0]
                c9_id = repo.find_c9_team_id() or (qs.get("c9_id") or [""])[0]
                if not opp_id or opp_id not in repo.teams:
                    self._send_json({"error": "Valid opponent_id query parameter required."}, HTTPStatus.BAD_REQUEST)
                    return
                c9_prof = repo.build_team_scouting_profile(c9_id) if c9_id else {}
                opp_prof = repo.build_team_scouting_profile(opp_id)
                self._send_json({"c9": c9_prof, "opponent": opp_prof})
                return

            # Serve static frontend from docs/
            rel = "index.html" if path in ("/", "") else path.lstrip("/")
            target = (DOCS_DIR / rel).resolve()
            if not str(target).startswith(str(DOCS_DIR.resolve())) or not target.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "File not found")
                return
            ctype, _ = mimetypes.guess_type(str(target))
            data = target.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", ctype or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        # noinspection PyPep8Naming
        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != "/api/draft/evaluate":
                self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
                return

            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            c9_id = repo.find_c9_team_id() or str(payload.get("c9_id") or "")
            opp_id = str(payload.get("opponent_id") or "")

            c9_prof = payload.get("c9_profile") or (repo.build_team_scouting_profile(c9_id) if c9_id in repo.teams else {})
            opp_prof = payload.get("opp_profile") or (repo.build_team_scouting_profile(opp_id) if opp_id in repo.teams else {})

            if "validate_champion" in payload:
                ok, reason = validate_draft_action(
                    payload["validate_champion"],
                    compute_fearless_locked(payload.get("prior_games_picks", [])),
                    payload.get("banned_champions", []),
                    list(payload.get("c9_picks", [])) + list(payload.get("opp_picks", [])),
                )
                self._send_json({"valid": ok, "reason": reason})
                return

            result = recommend_next_actions(
                c9_profile=c9_prof,
                opp_profile=opp_prof,
                c9_side=str(payload.get("c9_side", "blue")),
                step_index=int(payload.get("step_index", 0)),
                prior_games_picks=payload.get("prior_games_picks", []),
                banned_champions=payload.get("banned_champions", []),
                c9_picks=payload.get("c9_picks", []),
                opp_picks=payload.get("opp_picks", []),
            )
            self._send_json(result)

        def log_message(self, fmt: str, *args: Any) -> None:
            return  # Quiet clean server output

    return NexusHandler


def main() -> None:
    port = int(os.environ.get("PORT", "8787"))
    repo = GridLoLRepository()
    server = ThreadingHTTPServer(("127.0.0.1", port), create_app_handler(repo))
    print(f"C9 Fearless Nexus running on http://127.0.0.1:{port} (GRID connected={repo.available}, teams={len(repo.teams)})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
