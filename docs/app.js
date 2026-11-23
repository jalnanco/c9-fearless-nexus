/* C9 Fearless Nexus — Interactive Coaching Workstation
 * Supports:
 *  1) Live Local Python API (`http://127.0.0.1:8787/api/...` reading full `STL_DATA_DIR`)
 *  2) Zero-Server Browser Local GRID Folder Loader (`meta/*.csv` + `.jsonl.zst` via `fzstd`)
 *  3) Instant Judge Showcase Mode (aggregate team summary statistics per LICENSE.md §4b)
 */

(() => {
  "use strict";

  const DRAFT_SEQUENCE = [
    { step: 1, phase: "Ban Phase 1", side: "blue", action: "ban", slot: "BB1" },
    { step: 2, phase: "Ban Phase 1", side: "red", action: "ban", slot: "RB1" },
    { step: 3, phase: "Ban Phase 1", side: "blue", action: "ban", slot: "BB2" },
    { step: 4, phase: "Ban Phase 1", side: "red", action: "ban", slot: "RB2" },
    { step: 5, phase: "Ban Phase 1", side: "blue", action: "ban", slot: "BB3" },
    { step: 6, phase: "Ban Phase 1", side: "red", action: "ban", slot: "RB3" },
    { step: 7, phase: "Pick Phase 1", side: "blue", action: "pick", slot: "B1" },
    { step: 8, phase: "Pick Phase 1", side: "red", action: "pick", slot: "R1" },
    { step: 9, phase: "Pick Phase 1", side: "red", action: "pick", slot: "R2" },
    { step: 10, phase: "Pick Phase 1", side: "blue", action: "pick", slot: "B2" },
    { step: 11, phase: "Pick Phase 1", side: "blue", action: "pick", slot: "B3" },
    { step: 12, phase: "Pick Phase 1", side: "red", action: "pick", slot: "R3" },
    { step: 13, phase: "Ban Phase 2", side: "red", action: "ban", slot: "RB4" },
    { step: 14, phase: "Ban Phase 2", side: "blue", action: "ban", slot: "BB4" },
    { step: 15, phase: "Ban Phase 2", side: "red", action: "ban", slot: "RB5" },
    { step: 16, phase: "Ban Phase 2", side: "blue", action: "ban", slot: "BB5" },
    { step: 17, phase: "Pick Phase 2", side: "red", action: "pick", slot: "R4" },
    { step: 18, phase: "Pick Phase 2", side: "blue", action: "pick", slot: "B4" },
    { step: 19, phase: "Pick Phase 2", side: "blue", action: "pick", slot: "B5" },
    { step: 20, phase: "Pick Phase 2", side: "red", action: "pick", slot: "R5" },
  ];

  const CHAMPIONS = {
    "K'Sante": { roles: ["Top"], dmg: "AD", engage: 0.75, frontline: 0.95, early_prio: 0.55, scaling: 0.80 },
    "Rumble": { roles: ["Top"], dmg: "AP", engage: 0.65, frontline: 0.45, early_prio: 0.90, scaling: 0.70 },
    "Jax": { roles: ["Top", "Jungle"], dmg: "Mixed", engage: 0.65, frontline: 0.70, early_prio: 0.55, scaling: 0.90 },
    "Renekton": { roles: ["Top"], dmg: "AD", engage: 0.60, frontline: 0.75, early_prio: 0.92, scaling: 0.45 },
    "Gnar": { roles: ["Top"], dmg: "AD", engage: 0.80, frontline: 0.70, early_prio: 0.72, scaling: 0.72 },
    "Ambessa": { roles: ["Top"], dmg: "AD", engage: 0.82, frontline: 0.68, early_prio: 0.68, scaling: 0.84 },
    "Aurora": { roles: ["Mid", "Top"], dmg: "AP", engage: 0.70, frontline: 0.25, early_prio: 0.78, scaling: 0.80 },
    "Ornn": { roles: ["Top"], dmg: "Mixed", engage: 0.95, frontline: 0.98, early_prio: 0.45, scaling: 0.92 },
    "Aatrox": { roles: ["Top"], dmg: "AD", engage: 0.55, frontline: 0.75, early_prio: 0.68, scaling: 0.70 },
    "Jayce": { roles: ["Top", "Mid"], dmg: "AD", engage: 0.20, frontline: 0.25, early_prio: 0.90, scaling: 0.65 },
    "Gwen": { roles: ["Top"], dmg: "AP", engage: 0.25, frontline: 0.50, early_prio: 0.48, scaling: 0.94 },
    "Sion": { roles: ["Top"], dmg: "AD", engage: 0.85, frontline: 0.96, early_prio: 0.48, scaling: 0.82 },
    "Olaf": { roles: ["Top", "Jungle"], dmg: "AD", engage: 0.55, frontline: 0.72, early_prio: 0.82, scaling: 0.55 },
    "Skarner": { roles: ["Jungle", "Top"], dmg: "Mixed", engage: 0.92, frontline: 0.92, early_prio: 0.68, scaling: 0.78 },
    "Vi": { roles: ["Jungle"], dmg: "AD", engage: 0.95, frontline: 0.68, early_prio: 0.72, scaling: 0.65 },
    "Sejuani": { roles: ["Jungle"], dmg: "AP", engage: 0.90, frontline: 0.90, early_prio: 0.62, scaling: 0.75 },
    "Maokai": { roles: ["Jungle", "Support"], dmg: "AP", engage: 0.92, frontline: 0.85, early_prio: 0.55, scaling: 0.82 },
    "Xin Zhao": { roles: ["Jungle"], dmg: "AD", engage: 0.70, frontline: 0.72, early_prio: 0.88, scaling: 0.55 },
    "Wukong": { roles: ["Jungle"], dmg: "AD", engage: 0.88, frontline: 0.70, early_prio: 0.68, scaling: 0.76 },
    "Nocturne": { roles: ["Jungle"], dmg: "AD", engage: 0.88, frontline: 0.55, early_prio: 0.65, scaling: 0.68 },
    "Viego": { roles: ["Jungle"], dmg: "AD", engage: 0.45, frontline: 0.52, early_prio: 0.66, scaling: 0.82 },
    "Lee Sin": { roles: ["Jungle"], dmg: "AD", engage: 0.72, frontline: 0.55, early_prio: 0.92, scaling: 0.50 },
    "Poppy": { roles: ["Jungle", "Support", "Top"], dmg: "AD", engage: 0.68, frontline: 0.86, early_prio: 0.76, scaling: 0.72 },
    "Jarvan IV": { roles: ["Jungle"], dmg: "AD", engage: 0.90, frontline: 0.74, early_prio: 0.82, scaling: 0.62 },
    "Pantheon": { roles: ["Jungle", "Support", "Mid"], dmg: "AD", engage: 0.80, frontline: 0.52, early_prio: 0.94, scaling: 0.48 },
    "Naafiri": { roles: ["Jungle", "Mid"], dmg: "AD", engage: 0.78, frontline: 0.42, early_prio: 0.80, scaling: 0.72 },
    "Trundle": { roles: ["Jungle", "Top"], dmg: "AD", engage: 0.48, frontline: 0.80, early_prio: 0.82, scaling: 0.62 },
    "Ivern": { roles: ["Jungle"], dmg: "AP", engage: 0.35, frontline: 0.40, early_prio: 0.65, scaling: 0.84 },
    "Zyra": { roles: ["Jungle", "Support"], dmg: "AP", engage: 0.55, frontline: 0.20, early_prio: 0.84, scaling: 0.74 },
    "Azir": { roles: ["Mid"], dmg: "AP", engage: 0.78, frontline: 0.25, early_prio: 0.68, scaling: 0.95 },
    "Orianna": { roles: ["Mid"], dmg: "AP", engage: 0.65, frontline: 0.20, early_prio: 0.76, scaling: 0.90 },
    "Ahri": { roles: ["Mid"], dmg: "AP", engage: 0.72, frontline: 0.25, early_prio: 0.78, scaling: 0.76 },
    "Taliyah": { roles: ["Mid", "Jungle"], dmg: "AP", engage: 0.68, frontline: 0.22, early_prio: 0.82, scaling: 0.78 },
    "Yone": { roles: ["Mid", "Top"], dmg: "Mixed", engage: 0.82, frontline: 0.48, early_prio: 0.55, scaling: 0.92 },
    "Corki": { roles: ["Mid", "Bot"], dmg: "Mixed", engage: 0.20, frontline: 0.22, early_prio: 0.84, scaling: 0.82 },
    "Sylas": { roles: ["Mid"], dmg: "AP", engage: 0.70, frontline: 0.52, early_prio: 0.64, scaling: 0.85 },
    "Viktor": { roles: ["Mid"], dmg: "AP", engage: 0.35, frontline: 0.22, early_prio: 0.72, scaling: 0.94 },
    "Galio": { roles: ["Mid", "Support"], dmg: "AP", engage: 0.85, frontline: 0.84, early_prio: 0.68, scaling: 0.74 },
    "Ryze": { roles: ["Mid"], dmg: "AP", engage: 0.58, frontline: 0.42, early_prio: 0.66, scaling: 0.90 },
    "Cassiopeia": { roles: ["Mid"], dmg: "AP", engage: 0.45, frontline: 0.35, early_prio: 0.68, scaling: 0.90 },
    "Annie": { roles: ["Mid", "Support"], dmg: "AP", engage: 0.84, frontline: 0.25, early_prio: 0.70, scaling: 0.74 },
    "Karma": { roles: ["Mid", "Support"], dmg: "AP", engage: 0.35, frontline: 0.25, early_prio: 0.92, scaling: 0.68 },
    "Smolder": { roles: ["Mid", "Bot"], dmg: "Mixed", engage: 0.10, frontline: 0.18, early_prio: 0.42, scaling: 0.98 },
    "Kalista": { roles: ["Bot"], dmg: "AD", engage: 0.65, frontline: 0.20, early_prio: 0.96, scaling: 0.55 },
    "Varus": { roles: ["Bot"], dmg: "Mixed", engage: 0.72, frontline: 0.18, early_prio: 0.88, scaling: 0.72 },
    "Ashe": { roles: ["Bot"], dmg: "AD", engage: 0.85, frontline: 0.18, early_prio: 0.86, scaling: 0.70 },
    "Ezreal": { roles: ["Bot"], dmg: "Mixed", engage: 0.15, frontline: 0.22, early_prio: 0.74, scaling: 0.82 },
    "Kai'Sa": { roles: ["Bot"], dmg: "Mixed", engage: 0.45, frontline: 0.22, early_prio: 0.52, scaling: 0.92 },
    "Yunara": { roles: ["Bot"], dmg: "Mixed", engage: 0.35, frontline: 0.20, early_prio: 0.76, scaling: 0.92 },
    "Ziggs": { roles: ["Bot", "Mid"], dmg: "AP", engage: 0.20, frontline: 0.15, early_prio: 0.88, scaling: 0.80 },
    "Jhin": { roles: ["Bot"], dmg: "AD", engage: 0.62, frontline: 0.18, early_prio: 0.78, scaling: 0.76 },
    "Miss Fortune": { roles: ["Bot"], dmg: "AD", engage: 0.45, frontline: 0.18, early_prio: 0.82, scaling: 0.76 },
    "Xayah": { roles: ["Bot"], dmg: "AD", engage: 0.35, frontline: 0.25, early_prio: 0.66, scaling: 0.88 },
    "Sivir": { roles: ["Bot"], dmg: "AD", engage: 0.45, frontline: 0.18, early_prio: 0.74, scaling: 0.90 },
    "Lucian": { roles: ["Bot"], dmg: "AD", engage: 0.30, frontline: 0.20, early_prio: 0.92, scaling: 0.68 },
    "Rell": { roles: ["Support"], dmg: "AP", engage: 0.98, frontline: 0.85, early_prio: 0.65, scaling: 0.75 },
    "Rakan": { roles: ["Support"], dmg: "AP", engage: 0.95, frontline: 0.60, early_prio: 0.62, scaling: 0.82 },
    "Nautilus": { roles: ["Support"], dmg: "AP", engage: 0.94, frontline: 0.82, early_prio: 0.74, scaling: 0.65 },
    "Leona": { roles: ["Support"], dmg: "AP", engage: 0.95, frontline: 0.88, early_prio: 0.72, scaling: 0.68 },
    "Alistar": { roles: ["Support"], dmg: "AP", engage: 0.92, frontline: 0.92, early_prio: 0.58, scaling: 0.78 },
    "Braum": { roles: ["Support"], dmg: "AP", engage: 0.55, frontline: 0.88, early_prio: 0.60, scaling: 0.80 },
    "Renata Glasc": { roles: ["Support"], dmg: "AP", engage: 0.55, frontline: 0.30, early_prio: 0.78, scaling: 0.86 },
    "Neeko": { roles: ["Support", "Mid"], dmg: "AP", engage: 0.92, frontline: 0.40, early_prio: 0.84, scaling: 0.74 },
    "Bard": { roles: ["Support"], dmg: "AP", engage: 0.82, frontline: 0.45, early_prio: 0.74, scaling: 0.84 },
    "Nami": { roles: ["Support"], dmg: "AP", engage: 0.52, frontline: 0.20, early_prio: 0.82, scaling: 0.76 },
    "Tahm Kench": { roles: ["Support", "Top"], dmg: "AP", engage: 0.50, frontline: 0.92, early_prio: 0.62, scaling: 0.76 },
  };

  function getArch(ch) {
    return CHAMPIONS[ch] || { roles: ["Flex"], dmg: "Mixed", engage: 0.55, frontline: 0.50, early_prio: 0.60, scaling: 0.70 };
  }

  // Build realistic prior-game Fearless burn pools per opponent matchup
  function buildPriorGamesPicks(c9Prof, oppProf, gameNum) {
    if (gameNum <= 1) return [];
    const c9Champs = (c9Prof.signature_champions || []).map((c) => c.champion);
    const oppChamps = (oppProf.signature_champions || []).map((c) => c.champion);
    const fallback = Object.keys(CHAMPIONS);
    const merged = [];
    const used = new Set();
    let ci = 0;
    let oi = 0;
    let fi = 0;
    const needed = (gameNum - 1) * 10;
    while (merged.length < needed) {
      let cand = null;
      if (merged.length % 2 === 0 && ci < c9Champs.length) cand = c9Champs[ci++];
      else if (oi < oppChamps.length) cand = oppChamps[oi++];
      else if (ci < c9Champs.length) cand = c9Champs[ci++];
      else cand = fallback[fi++ % fallback.length];
      if (cand && !used.has(cand)) {
        used.add(cand);
        merged.push(cand);
      }
    }
    const games = [];
    for (let g = 0; g < gameNum - 1; g++) {
      games.push(merged.slice(g * 10, (g + 1) * 10));
    }
    return games;
  }

  // Deterministic math mirrors `backend/fearless_engine.py`
  function smoothedWR(wins, games) {
    return (wins + 2.5) / Math.max(1, games + 5.0);
  }

  function shannonEntropy(counts) {
    const total = counts.reduce((a, b) => a + b, 0);
    if (total <= 0) return 0;
    let ent = 0;
    for (const c of counts) {
      if (c > 0) {
        const p = c / total;
        ent -= p * Math.log2(p);
      }
    }
    return ent;
  }

  function computePinchScore(poolStats, lockedSet, bannedSet) {
    const valid = (poolStats || []).filter((r) => (r.games || 0) > 0);
    const totalGames = valid.reduce((acc, r) => acc + r.games, 0);
    if (totalGames === 0) {
      return { pinch_index: 0, pool_share_removed: 0, expected_wr_delta: 0, remaining_comfort_count: 0, burned_champions: [], remaining_top: [], sample_games: 0 };
    }
    const baseEnt = shannonEntropy(valid.map((r) => r.games));
    const baseWR = valid.reduce((acc, r) => acc + r.games * smoothedWR(r.wins || 0, r.games), 0) / totalGames;
    const initialComfort = valid.filter((r) => r.games >= 2);
    const remaining = valid.filter((r) => !lockedSet.has(r.champion) && !bannedSet.has(r.champion));
    const burned = valid.filter((r) => lockedSet.has(r.champion) || bannedSet.has(r.champion)).map((r) => r.champion);
    const removedGames = valid.filter((r) => lockedSet.has(r.champion) || bannedSet.has(r.champion)).reduce((a, r) => a + r.games, 0);
    const shareRemoved = removedGames / totalGames;
    const remComfort = remaining.filter((r) => r.games >= 2);

    let remWR = baseWR;
    let remEnt = 0;
    if (remaining.length > 0) {
      const remTotal = remaining.reduce((a, r) => a + r.games, 0);
      remEnt = shannonEntropy(remaining.map((r) => r.games));
      remWR = remaining.reduce((a, r) => a + r.games * smoothedWR(r.wins || 0, r.games), 0) / remTotal;
      if (initialComfort.length > 0 && remComfort.length === 0) remWR -= 0.065;
      else if (initialComfort.length >= 2 && remComfort.length === 1) remWR -= 0.030;
    } else {
      remWR = Math.max(0.35, baseWR - 0.11);
    }
    const wrDelta = remWR - baseWR;
    let pinchIndex = 0;
    if (removedGames > 0) {
      const comfortDepletion = initialComfort.length > 0 ? (initialComfort.length - remComfort.length) / initialComfort.length : shareRemoved;
      const raw = (0.50 * shareRemoved + 0.30 * comfortDepletion + 0.20 * Math.min(1, Math.max(0, -wrDelta / 0.12))) * 100;
      pinchIndex = Math.round(Math.min(100, Math.max(0, raw)) * 10) / 10;
    }
    return {
      pinch_index: pinchIndex,
      pool_share_removed: shareRemoved,
      entropy_drop_pct: baseEnt > 1e-6 ? Math.max(0, (baseEnt - remEnt) / baseEnt) : 0,
      expected_wr_delta: wrDelta,
      remaining_comfort_count: remComfort.length,
      burned_champions: burned,
      remaining_top: remaining.slice(0, 3),
      sample_games: totalGames,
    };
  }

  function evaluateCompBalance(picks) {
    if (!picks || picks.length === 0) {
      return { engage: 0.5, frontline: 0.5, early_prio: 0.5, scaling: 0.5, damage_mix: 0.5, composite: 0.5 };
    }
    const archs = picks.map(getArch);
    const maxEngage = Math.max(...archs.map((a) => a.engage));
    const avgFront = archs.reduce((s, a) => s + a.frontline, 0) / archs.length;
    const avgPrio = archs.reduce((s, a) => s + a.early_prio, 0) / archs.length;
    const avgScale = archs.reduce((s, a) => s + a.scaling, 0) / archs.length;
    const hasAD = archs.some((a) => a.dmg === "AD" || a.dmg === "Mixed");
    const hasAP = archs.some((a) => a.dmg === "AP" || a.dmg === "Mixed");
    const dmgMix = picks.length < 2 ? 0.65 : hasAD && hasAP ? 0.90 : 0.32;
    const frontScore = Math.min(1, avgFront / 0.58);
    const composite = 0.28 * maxEngage + 0.24 * frontScore + 0.20 * dmgMix + 0.14 * avgPrio + 0.14 * avgScale;
    return { engage: maxEngage, frontline: frontScore, early_prio: avgPrio, scaling: avgScale, damage_mix: dmgMix, composite };
  }

  function estimateWinProb(c9Side, c9Picks, oppPicks, c9Prof, oppProf, pinchBonus) {
    const sideLogit = c9Side === "blue" ? 0.088 : -0.088;
    const c9Map = new Map((c9Prof.signature_champions || []).map((r) => [r.champion, r.smoothed_wr]));
    const oppMap = new Map((oppProf.signature_champions || []).map((r) => [r.champion, r.smoothed_wr]));

    let c9Skill = 0;
    for (const ch of c9Picks) {
      const wr = Math.min(0.72, Math.max(0.32, c9Map.get(ch) ?? 0.515));
      c9Skill += 0.42 * Math.log(wr / (1 - wr));
    }
    let oppSkill = 0;
    for (const ch of oppPicks) {
      const wr = Math.min(0.72, Math.max(0.32, oppMap.get(ch) ?? 0.50));
      oppSkill += 0.42 * Math.log(wr / (1 - wr));
    }
    const c9Comp = evaluateCompBalance(c9Picks);
    const oppComp = evaluateCompBalance(oppPicks);
    const compLogit = c9Picks.length || oppPicks.length ? 1.15 * (c9Comp.composite - oppComp.composite) : 0;
    const pinchLogit = 2.4 * Math.min(0.20, Math.max(-0.20, pinchBonus));
    const logit = sideLogit + (c9Skill - oppSkill) + compLogit + pinchLogit;
    const prob = Math.min(0.95, Math.max(0.05, 1 / (1 + Math.exp(-logit))));
    return { c9_win_probability: prob, c9_comp: c9Comp, opp_comp: oppComp };
  }

  // Application State
  const state = {
    profiles: Object.assign({}, window.SHOWCASE_AGGREGATES || {}),
    c9Id: "47351",
    oppId: "54198", // Default: LYON (2026 LCS Playoffs rival)
    c9Side: "blue",
    gameNum: 3, // Default: Game 3 Fearless (-20 champions locked!) for immediate wow factor
    priorGamesPicks: [],
    actions: [], // Array of 0..20 chosen champion names
    winHistory: [], // Win prob at each step 0..current
    roleFilter: "All",
    searchQuery: "",
    apiConnected: false,
  };

  // Try connecting to local Python backend (`http://127.0.0.1:8787`) if running
  async function tryConnectLocalBackend() {
    if (location.protocol === "https:") return;
    try {
      const resp = await fetch("/api/health", { cache: "no-store" });
      if (!resp.ok) return;
      const health = await resp.json();
      if (health.grid_data_connected) {
        state.apiConnected = true;
        const pill = document.getElementById("data-mode-pill");
        pill.textContent = `Live GRID Stream (${health.lol_teams_loaded} Teams · ${health.event_feeds_indexed} Feeds)`;
        const teamsResp = await fetch("/api/teams");
        const teamsJson = await teamsResp.json();
        if (teamsJson.c9_team_id) state.c9Id = teamsJson.c9_team_id;
        populateOpponentDropdown(teamsJson.teams.filter((t) => t.team_id !== state.c9Id));
        await fetchScoutingFromApi(state.oppId);
      }
    } catch (_) {
      // Static mode (GitHub Pages or file://) — uses built-in showcase or local folder picker
    }
  }

  async function fetchScoutingFromApi(oppId) {
    if (!state.apiConnected) return;
    const res = await fetch(`/api/scouting?opponent_id=${encodeURIComponent(oppId)}`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.c9 && data.c9.team_id) state.profiles[data.c9.team_id] = data.c9;
    if (data.opponent && data.opponent.team_id) state.profiles[data.opponent.team_id] = data.opponent;
  }

  function populateOpponentDropdown(customList) {
    const sel = document.getElementById("opponent-select");
    sel.innerHTML = "";
    const items = customList
      ? customList
      : Object.values(state.profiles)
          .filter((p) => p.team_id !== state.c9Id)
          .map((p) => ({ team_id: p.team_id, name: p.name, games: p.sample_games, has_macro_telemetry: true }));

    for (const item of items) {
      const opt = document.createElement("option");
      opt.value = item.team_id;
      opt.textContent = `${item.name} (n=${item.games}g${item.has_macro_telemetry ? " · Telemetry" : ""})`;
      if (item.team_id === state.oppId) opt.selected = true;
      sel.appendChild(opt);
    }
    if (!items.some((i) => i.team_id === state.oppId) && items.length > 0) {
      state.oppId = items[0].team_id;
      sel.value = state.oppId;
    }
  }

  function resetDraftForCurrentSeries() {
    const c9Prof = state.profiles[state.c9Id];
    const oppProf = state.profiles[state.oppId];
    state.priorGamesPicks = buildPriorGamesPicks(c9Prof, oppProf, state.gameNum);
    state.actions = [];
    // Pre-populate 4 opening phase-1 bans on Game 3 initial load ONLY first time? No, clean step 0 or partial mid-draft?
    // Starting with 6 Phase-1 Bans + B1/R1/R2 already in progress on initial load makes the screen immediately rich & alive!
    state.winHistory = [computeCurrentEvaluation().live.c9_win_probability];
    renderAll();
  }

  function seedMidDraftDemo() {
    const c9Prof = state.profiles[state.c9Id];
    const oppProf = state.profiles[state.oppId];
    state.priorGamesPicks = buildPriorGamesPicks(c9Prof, oppProf, state.gameNum);
    state.actions = [];
    state.winHistory = [computeCurrentEvaluation().live.c9_win_probability];
    // Auto-advance 8 steps (6 Phase-1 bans + B1 + R1) so coaches/judges immediately see live trajectory, bans, & picks in action
    for (let i = 0; i < 8; i++) {
      stepAutoAction(false);
    }
    renderAll();
  }

  function getLockedSet() {
    const s = new Set();
    for (const g of state.priorGamesPicks) {
      for (const ch of g) s.add(ch);
    }
    return s;
  }

  function getDraftBuckets() {
    const blueBans = [];
    const redBans = [];
    const bluePicks = [];
    const redPicks = [];
    state.actions.forEach((champ, idx) => {
      const meta = DRAFT_SEQUENCE[idx];
      if (!meta) return;
      if (meta.side === "blue" && meta.action === "ban") blueBans.push(champ);
      else if (meta.side === "red" && meta.action === "ban") redBans.push(champ);
      else if (meta.side === "blue" && meta.action === "pick") bluePicks.push(champ);
      else if (meta.side === "red" && meta.action === "pick") redPicks.push(champ);
    });
    const c9Picks = state.c9Side === "blue" ? bluePicks : redPicks;
    const oppPicks = state.c9Side === "blue" ? redPicks : bluePicks;
    const allBans = [...blueBans, ...redBans];
    return { blueBans, redBans, bluePicks, redPicks, c9Picks, oppPicks, allBans };
  }

  function computeCurrentEvaluation() {
    const c9Prof = state.profiles[state.c9Id];
    const oppProf = state.profiles[state.oppId];
    const lockedSet = getLockedSet();
    const { c9Picks, oppPicks, allBans } = getDraftBuckets();
    const bannedSet = new Set(allBans);
    const unavailable = new Set([...lockedSet, ...allBans, ...c9Picks, ...oppPicks]);

    const pinches = (oppProf.players || []).slice(0, 5).map((p) => ({
      player: p.player,
      role: p.role,
      pool: p.pool || [],
      ...computePinchScore(p.pool || [], lockedSet, bannedSet),
    }));

    const avgPinchBonus =
      pinches.reduce((acc, p) => acc + Math.max(0, -p.expected_wr_delta), 0) / Math.max(1, pinches.length);

    const live = estimateWinProb(state.c9Side, c9Picks, oppPicks, c9Prof, oppProf, avgPinchBonus);

    // Ban recommendations
    const banRecs = [];
    const seenBan = new Set();
    for (const p of oppProf.players || []) {
      const baseP = computePinchScore(p.pool || [], lockedSet, bannedSet);
      for (const ce of (p.pool || []).slice(0, 5)) {
        if (unavailable.has(ce.champion) || seenBan.has(ce.champion)) continue;
        seenBan.add(ce.champion);
        const nextBanSet = new Set(bannedSet);
        nextBanSet.add(ce.champion);
        const simP = computePinchScore(p.pool || [], lockedSet, nextBanSet);
        const gain = Math.round((simP.pinch_index - baseP.pinch_index) * 10) / 10;
        banRecs.push({
          champion: ce.champion,
          player: p.player,
          role: p.role,
          games: ce.games,
          wins: ce.wins,
          gain,
          comfortLeft: simP.remaining_comfort_count,
        });
      }
    }
    banRecs.sort((a, b) => b.gain - a.gain || b.games - a.games);

    // Pick recommendations
    const coveredRoles = new Set();
    for (const ch of c9Picks) coveredRoles.add(getArch(ch).roles[0]);
    const c9SigMap = new Map((c9Prof.signature_champions || []).map((c) => [c.champion, c]));
    const candidates = Array.from(new Set([...c9SigMap.keys(), ...Object.keys(CHAMPIONS)]));

    const pickRecs = [];
    for (const ch of candidates) {
      if (unavailable.has(ch)) continue;
      const sim = estimateWinProb(state.c9Side, [...c9Picks, ch], oppPicks, c9Prof, oppProf, avgPinchBonus);
      const arch = getArch(ch);
      const primaryRole = arch.roles[0];
      const roleBonus = !coveredRoles.has(primaryRole) ? 0.020 : -0.014;
      const sig = c9SigMap.get(ch);
      const games = sig ? sig.games : 0;
      const wins = sig ? sig.wins : 0;
      const score = sim.c9_win_probability + roleBonus + Math.min(0.016, games * 0.0014);
      const deltaPct = Math.round((sim.c9_win_probability - live.c9_win_probability) * 1000) / 10;
      pickRecs.push({
        champion: ch,
        role: primaryRole,
        dmg: arch.dmg,
        games,
        wins,
        deltaPct,
        score,
      });
    }
    pickRecs.sort((a, b) => b.score - a.score);

    return { lockedSet, unavailable, pinches, live, banRecs: banRecs.slice(0, 4), pickRecs: pickRecs.slice(0, 4) };
  }

  function commitChampionAction(champion, shouldRender = true) {
    if (state.actions.length >= DRAFT_SEQUENCE.length) return;
    const { unavailable } = computeCurrentEvaluation();
    if (unavailable.has(champion)) return;
    state.actions.push(champion);
    const nextEval = computeCurrentEvaluation();
    state.winHistory.push(nextEval.live.c9_win_probability);
    if (shouldRender) renderAll();
  }

  function stepAutoAction(shouldRender = true) {
    const stepIdx = state.actions.length;
    if (stepIdx >= DRAFT_SEQUENCE.length) return;
    const meta = DRAFT_SEQUENCE[stepIdx];
    const ev = computeCurrentEvaluation();
    const isC9Turn = meta.side === state.c9Side;

    let chosen = null;
    if (meta.action === "ban") {
      if (isC9Turn && ev.banRecs.length > 0) {
        chosen = ev.banRecs[0].champion;
      } else {
        // Opponent bans high-presence C9 comfort pick
        const c9Sigs = state.profiles[state.c9Id].signature_champions || [];
        const found = c9Sigs.find((c) => !ev.unavailable.has(c.champion));
        chosen = found ? found.champion : Object.keys(CHAMPIONS).find((c) => !ev.unavailable.has(c));
      }
    } else {
      if (isC9Turn && ev.pickRecs.length > 0) {
        chosen = ev.pickRecs[0].champion;
      } else {
        // Opponent picks unfilled role from its signature pool
        const { c9Picks, oppPicks } = getDraftBuckets();
        const oppCovered = new Set(oppPicks.map((c) => getArch(c).roles[0]));
        const oppSigs = state.profiles[state.oppId].signature_champions || [];
        const roleFit = oppSigs.find((c) => !ev.unavailable.has(c.champion) && !oppCovered.has(getArch(c.champion).roles[0]));
        const anyFit = oppSigs.find((c) => !ev.unavailable.has(c.champion));
        chosen = roleFit
          ? roleFit.champion
          : anyFit
          ? anyFit.champion
          : Object.keys(CHAMPIONS).find((c) => !ev.unavailable.has(c) && !oppCovered.has(getArch(c).roles[0])) ||
            Object.keys(CHAMPIONS).find((c) => !ev.unavailable.has(c));
      }
    }
    if (chosen) commitChampionAction(chosen, shouldRender);
  }

  // Rendering Functions
  function renderDraftBoard(ev) {
    const c9Prof = state.profiles[state.c9Id];
    const oppProf = state.profiles[state.oppId];
    const stepIdx = state.actions.length;
    const activeMeta = DRAFT_SEQUENCE[stepIdx] || null;

    const banner = document.getElementById("active-step-banner");
    if (activeMeta) {
      const actorName = activeMeta.side === state.c9Side ? c9Prof.name : oppProf.name;
      banner.textContent = `Step ${activeMeta.step}/20 · ${activeMeta.phase} · ${actorName} (${activeMeta.slot})`;
    } else {
      banner.textContent = "Draft Complete (20/20 Locked) · Ready for Summoner's Rift";
    }

    document.getElementById("fearless-count-badge").textContent = `${ev.lockedSet.size} Fearless Locked`;
    document.getElementById("blue-team-label").textContent =
      state.c9Side === "blue" ? `${c9Prof.name} (Blue)` : `${oppProf.name} (Blue)`;
    document.getElementById("red-team-label").textContent =
      state.c9Side === "red" ? `${c9Prof.name} (Red)` : `${oppProf.name} (Red)`;

    // Map slots
    const slotValues = {};
    state.actions.forEach((ch, idx) => {
      slotValues[DRAFT_SEQUENCE[idx].slot] = ch;
    });

    const blueBanSlots = ["BB1", "BB2", "BB3", "BB4", "BB5"];
    const redBanSlots = ["RB1", "RB2", "RB3", "RB4", "RB5"];
    const bluePickSlots = ["B1", "B2", "B3", "B4", "B5"];
    const redPickSlots = ["R1", "R2", "R3", "R4", "R5"];

    const renderBans = (containerId, slots) => {
      const el = document.getElementById(containerId);
      el.innerHTML = slots
        .map((sl) => {
          const val = slotValues[sl];
          const isAct = activeMeta && activeMeta.slot === sl;
          return `<div class="ban-chip ${val ? "filled" : ""} ${isAct ? "active-slot" : ""}" title="${val || sl}">${
            val ? val.slice(0, 7) : sl
          }</div>`;
        })
        .join("");
    };
    renderBans("blue-bans", blueBanSlots);
    renderBans("red-bans", redBanSlots);

    const renderPicks = (containerId, slots, sideClass) => {
      const el = document.getElementById(containerId);
      el.innerHTML = slots
        .map((sl) => {
          const val = slotValues[sl];
          const isAct = activeMeta && activeMeta.slot === sl;
          const role = val ? getArch(val).roles[0] : "OPEN";
          return `<div class="pick-slot ${val ? sideClass : ""} ${isAct ? "active-slot" : ""}">
            <span class="slot-code">${sl}</span>
            <span class="slot-champ">${val || "Awaiting Pick..."}</span>
            <span class="slot-role">${role}</span>
          </div>`;
        })
        .join("");
    };
    renderPicks("blue-picks", bluePickSlots, "filled-blue");
    renderPicks("red-picks", redPickSlots, "filled-red");

    // Fearless Vault
    const vaultSub = document.getElementById("vault-subtitle");
    vaultSub.textContent =
      state.gameNum === 1
        ? "Game 1 Fresh Pool (0 Prior Locks)"
        : `Games 1–${state.gameNum - 1} Burned (${ev.lockedSet.size} Unavailable)`;
    const tagsEl = document.getElementById("fearless-tags");
    if (ev.lockedSet.size === 0) {
      tagsEl.innerHTML = `<span class="mono-note">No champions burned yet in Game 1. Switch to G3–G5 above to test Fearless pool pinches.</span>`;
    } else {
      tagsEl.innerHTML = Array.from(ev.lockedSet)
        .map((ch) => `<span class="burn-tag">${ch}</span>`)
        .join("");
    }

    // Champion Picker Grid
    const gridEl = document.getElementById("champ-grid");
    const q = state.searchQuery.trim().toLowerCase();
    const entries = Object.keys(CHAMPIONS).filter((ch) => {
      const arch = getArch(ch);
      if (state.roleFilter !== "All" && !arch.roles.includes(state.roleFilter)) return false;
      if (q && !ch.toLowerCase().includes(q)) return false;
      return true;
    });
    gridEl.innerHTML = entries
      .map((ch) => {
        const disabled = ev.unavailable.has(ch) || state.actions.length >= 20;
        const arch = getArch(ch);
        return `<button type="button" class="champ-tile" data-champ="${ch}" ${disabled ? "disabled" : ""}>
          <strong>${ch}</strong>
          <span>${arch.roles[0]} · ${arch.dmg}</span>
        </button>`;
      })
      .join("");

    gridEl.querySelectorAll(".champ-tile").forEach((btn) => {
      btn.addEventListener("click", () => commitChampionAction(btn.dataset.champ));
    });
  }

  function renderCenterIntel(ev) {
    const c9Prof = state.profiles[state.c9Id];
    const oppProf = state.profiles[state.oppId];
    const wrPct = (ev.live.c9_win_probability * 100).toFixed(1);
    const oppPct = (100 - parseFloat(wrPct)).toFixed(1);
    const basePct = state.c9Side === "blue" ? 52.2 : 47.8;
    const delta = (parseFloat(wrPct) - basePct).toFixed(1);

    document.getElementById("c9-wr-value").textContent = `${wrPct}%`;
    const deltaEl = document.getElementById("c9-wr-delta");
    deltaEl.textContent = `${delta >= 0 ? "+" : ""}${delta}% vs Side Baseline`;
    deltaEl.className = `wr-delta ${delta >= 0 ? "positive" : "negative"}`;

    document.getElementById("c9-wr-fill").style.width = `${wrPct}%`;
    document.getElementById("wr-label-c9").textContent = `${c9Prof.name} · ${wrPct}%`;
    document.getElementById("wr-label-opp").textContent = `${oppProf.name} · ${oppPct}%`;

    document.getElementById("matchup-sample-badges").innerHTML = `
      <span class="stat-pill">C9 G3+ WR: ${(c9Prof.fearless_g3plus_win_rate * 100).toFixed(1)}% (n=${c9Prof.fearless_g3plus_games})</span>
      <span class="stat-pill">${oppProf.name} G3+ WR: ${(oppProf.fearless_g3plus_win_rate * 100).toFixed(1)}% (n=${oppProf.fearless_g3plus_games})</span>
    `;

    // Sparkline SVG
    const svg = document.getElementById("wr-sparkline");
    const w = 380;
    const h = 86;
    const pts = state.winHistory.map((v, idx) => {
      const x = 14 + (idx / 20) * (w - 28);
      const y = h - 12 - ((v - 0.25) / 0.5) * (h - 24);
      return `${x.toFixed(1)},${Math.min(h - 8, Math.max(8, y)).toFixed(1)}`;
    });
    const midY = (h / 2).toFixed(1);
    svg.innerHTML = `
      <line x1="10" y1="${midY}" x2="${w - 10}" y2="${midY}" stroke="rgba(148,163,184,0.25)" stroke-dasharray="3,3" />
      <text x="12" y="${midY - 4}" fill="#64748b" font-size="9" font-family="JetBrains Mono">50%</text>
      ${pts.length > 1 ? `<polyline fill="none" stroke="#00aeef" stroke-width="2.4" points="${pts.join(" ")}" />` : ""}
      ${state.winHistory
        .map((v, idx) => {
          const [cx, cy] = pts[idx].split(",");
          return `<circle cx="${cx}" cy="${cy}" r="${idx === state.winHistory.length - 1 ? 4 : 2.3}" fill="${
            v >= 0.5 ? "#38bdf8" : "#fb7185"
          }" />`;
        })
        .join("")}
    `;

    // Comp Balance Bars
    const comp = ev.live.c9_comp;
    const dims = [
      ["Engage", comp.engage],
      ["Frontline", comp.frontline],
      ["Early Prio", comp.early_prio],
      ["Scaling", comp.scaling],
      ["Dmg Mix", comp.damage_mix],
    ];
    document.getElementById("comp-balance-bars").innerHTML = dims
      .map(
        ([label, val]) => `<div class="comp-row">
          <span>${label}</span>
          <div class="comp-track"><div class="comp-fill" style="width:${Math.round(val * 100)}%"></div></div>
          <span class="comp-val">${Math.round(val * 100)}</span>
        </div>`
      )
      .join("");

    // Ban & Pick Recommendation Cards
    const canAct = state.actions.length < 20;
    document.getElementById("ban-recs-list").innerHTML = ev.banRecs
      .map(
        (r) => `<div class="rec-item">
          <div class="rec-main">
            <div class="rec-title-line">
              <strong>${r.champion}</strong>
              <span class="rec-metric">+${r.gain} Pinch · ${r.player} (${r.role})</span>
            </div>
            <p class="rec-sub">Sample n=${r.games}g (${r.wins}W) · Leaves ${r.comfortLeft} comfort picks</p>
          </div>
          ${canAct ? `<button type="button" class="lock-mini-btn" data-lock="${r.champion}">Lock</button>` : ""}
        </div>`
      )
      .join("");

    document.getElementById("pick-recs-list").innerHTML = ev.pickRecs
      .map(
        (r) => `<div class="rec-item">
          <div class="rec-main">
            <div class="rec-title-line">
              <strong>${r.champion}</strong>
              <span class="rec-metric">${r.deltaPct >= 0 ? "+" : ""}${r.deltaPct}% WR · ${r.role}</span>
            </div>
            <p class="rec-sub">${r.dmg} profile · C9 mastery n=${r.games}g (${r.wins}W)</p>
          </div>
          ${canAct ? `<button type="button" class="lock-mini-btn" data-lock="${r.champion}">Lock</button>` : ""}
        </div>`
      )
      .join("");

    document.querySelectorAll(".lock-mini-btn").forEach((btn) => {
      btn.addEventListener("click", () => commitChampionAction(btn.dataset.lock));
    });

    // Opponent 5-Player Pinch Matrix
    const burnedUnion = new Set([...ev.lockedSet, ...getDraftBuckets().allBans]);
    document.getElementById("pinch-cards-grid").innerHTML = ev.pinches
      .map((p) => {
        const wrDropPct = (p.expected_wr_delta * 100).toFixed(1);
        const isHigh = p.pinch_index >= 38;
        const poolHtml = (p.pool || [])
          .slice(0, 5)
          .map((c) => {
            const isBurned = burnedUnion.has(c.champion);
            return `<span class="mini-champ ${isBurned ? "burned" : ""}" title="${c.games}g ${c.wins}W">${c.champion} (${c.games})</span>`;
          })
          .join("");
        return `<div class="pinch-card ${isHigh ? "high-pinch" : ""}">
          <div class="pinch-top">
            <span class="pinch-player">${p.player}</span>
            <span class="pinch-role">${p.role}</span>
          </div>
          <div class="pinch-score-row">
            <span class="pinch-idx">${p.pinch_index.toFixed(0)}<small style="font-size:10px;color:#94a3b8">/100</small></span>
            <span class="pinch-wr">${wrDropPct}% WR</span>
          </div>
          <div class="pinch-meter"><div style="width:${Math.min(100, p.pinch_index)}%"></div></div>
          <div class="mono-note">${p.remaining_comfort_count} comfort left (n=${p.sample_games}g)</div>
          <div class="pinch-pool-tags">${poolHtml}</div>
        </div>`;
      })
      .join("");
  }

  function renderMacroRift() {
    const c9Prof = state.profiles[state.c9Id];
    const oppProf = state.profiles[state.oppId];
    const c9M = c9Prof.macro || {};
    const oppM = oppProf.macro || {};

    document.getElementById("macro-sample-subtitle").textContent = `${oppProf.name} Telemetry (n=${
      oppM.games_analyzed || oppProf.sample_games
    }g analyzed) · GRID Coordinates`;

    // Render Summoner's Rift Tactical SVG (360x360, Y inverted from game [0..15000] to SVG [360..0])
    const rift = document.getElementById("rift-svg");
    const hotspots = (oppM.map_hotspots || []).slice(0, 12);
    const maxWeight = Math.max(1, ...hotspots.map((h) => h.weight));

    const c9TopScuttle = Math.round((c9M.top_scuttle_rate ?? 0.385) * 100);
    const oppTopScuttle = Math.round((oppM.top_scuttle_rate ?? 0.5) * 100);
    const oppBotScuttle = 100 - oppTopScuttle;

    rift.innerHTML = `
      <defs>
        <radialGradient id="heatGrad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#f59e0b" stop-opacity="0.72" />
          <stop offset="65%" stop-color="#f43f5e" stop-opacity="0.32" />
          <stop offset="100%" stop-color="#f43f5e" stop-opacity="0" />
        </radialGradient>
        <marker id="arrowC9" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8" />
        </marker>
        <marker id="arrowOpp" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 10 5 L 0 9 z" fill="#f43f5e" />
        </marker>
      </defs>

      <!-- Terrain Background & River -->
      <rect x="8" y="8" width="344" height="344" rx="14" fill="#091526" stroke="rgba(56,189,248,0.22)" />
      <path d="M 55 85 C 125 135, 225 225, 295 285" stroke="rgba(56,189,248,0.16)" stroke-width="26" stroke-linecap="round" fill="none" />

      <!-- Outer & Mid Lanes -->
      <path d="M 34 326 L 34 36 L 326 36" stroke="rgba(148,163,184,0.22)" stroke-width="8" fill="none" stroke-linejoin="round" />
      <path d="M 34 326 L 326 326 L 326 36" stroke="rgba(148,163,184,0.22)" stroke-width="8" fill="none" stroke-linejoin="round" />
      <line x1="36" y1="324" x2="324" y2="36" stroke="rgba(148,163,184,0.24)" stroke-width="8" />

      <!-- Bases -->
      <circle cx="36" cy="324" r="16" fill="rgba(0,174,239,0.28)" stroke="#00aeef" stroke-width="2" />
      <text x="36" y="328" text-anchor="middle" fill="#e0f2fe" font-size="9" font-family="JetBrains Mono" font-weight="700">BLUE</text>
      <circle cx="324" cy="36" r="16" fill="rgba(244,63,94,0.28)" stroke="#f43f5e" stroke-width="2" />
      <text x="324" y="40" text-anchor="middle" fill="#ffe4e6" font-size="9" font-family="JetBrains Mono" font-weight="700">RED</text>

      <!-- Opponent Early Kill Density Hotspots (from GRID {x,y} buckets) -->
      ${hotspots
        .map((h) => {
          const cx = 16 + ((h.gx + 0.5) / 20) * 328;
          const cy = 344 - ((h.gy + 0.5) / 20) * 328;
          const r = 12 + (h.weight / maxWeight) * 16;
          return `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${r.toFixed(1)}" fill="url(#heatGrad)" />`;
        })
        .join("")}

      <!-- Void Grub / Baron Pit & Dragon Pit -->
      <circle cx="122" cy="112" r="13" fill="rgba(168,85,247,0.24)" stroke="#c084fc" stroke-width="1.6" />
      <text x="122" y="94" text-anchor="middle" fill="#e9d5ff" font-size="9.5" font-family="JetBrains Mono" font-weight="700">GRUBS ${(
        (oppM.first_grub_rate ?? 0.5) * 100
      ).toFixed(0)}%</text>

      <circle cx="238" cy="246" r="13" fill="rgba(245,158,11,0.24)" stroke="#fbbf24" stroke-width="1.6" />
      <text x="238" y="271" text-anchor="middle" fill="#fde68a" font-size="9.5" font-family="JetBrains Mono" font-weight="700">DRAKE ${(
        (oppM.first_dragon_rate ?? 0.5) * 100
      ).toFixed(0)}%</text>

      <!-- Jungle First-Scuttle Pathing Vectors -->
      <path d="M 92 268 Q 162 258 220 228" stroke="#38bdf8" stroke-width="2.5" stroke-dasharray="5,3" fill="none" marker-end="url(#arrowC9)" />
      <text x="144" y="286" fill="#38bdf8" font-size="9" font-family="JetBrains Mono" font-weight="700">C9 Bot Scuttle ${
        100 - c9TopScuttle
      }%</text>

      ${
        oppTopScuttle >= 50
          ? `<path d="M 255 96 Q 190 92 138 118" stroke="#f43f5e" stroke-width="2.5" fill="none" marker-end="url(#arrowOpp)" />
             <text x="208" y="80" text-anchor="middle" fill="#fda4af" font-size="9" font-family="JetBrains Mono" font-weight="700">Opp Top Scuttle ${oppTopScuttle}%</text>`
          : `<path d="M 268 132 Q 262 195 236 226" stroke="#f43f5e" stroke-width="2.5" fill="none" marker-end="url(#arrowOpp)" />
             <text x="276" y="182" text-anchor="middle" fill="#fda4af" font-size="9" font-family="JetBrains Mono" font-weight="700">Opp Bot Scuttle ${oppBotScuttle}%</text>`
      }
    `;

    // Comparison Bars
    const metrics = [
      ["1st Bot Scuttle", 1 - (c9M.top_scuttle_rate ?? 0.385), 1 - (oppM.top_scuttle_rate ?? 0.5)],
      ["1st Void Grubs", c9M.first_grub_rate ?? 0.593, oppM.first_grub_rate ?? 0.5],
      ["1st Dragon", c9M.first_dragon_rate ?? 0.481, oppM.first_dragon_rate ?? 0.5],
      ["1st Rift Herald", c9M.first_herald_rate ?? 0.704, oppM.first_herald_rate ?? 0.5],
      ["1st Tower Blood", c9M.first_tower_rate ?? 0.630, oppM.first_tower_rate ?? 0.5],
    ];
    document.getElementById("macro-comparison-bars").innerHTML = metrics
      .map(([label, c9v, oppv]) => {
        const c9p = Math.round(c9v * 100);
        const oppp = Math.round(oppv * 100);
        return `<div class="macro-row">
          <div class="macro-row-head">
            <span style="color:#38bdf8">C9 ${c9p}%</span>
            <strong>${label}</strong>
            <span style="color:#fb7185">${oppProf.name.split(" ")[0]} ${oppp}%</span>
          </div>
          <div class="dual-bar">
            <div class="dual-half left"><div class="fill-c9" style="width:${c9p}%"></div></div>
            <div class="dual-half right"><div class="fill-opp" style="width:${oppp}%"></div></div>
          </div>
        </div>`;
      })
      .join("");

    // Automated "How-to-Win" Coaching Brief
    const ev = computeCurrentEvaluation();
    const topPinched = [...ev.pinches].sort((a, b) => b.pinch_index - a.pinch_index)[0];
    const oppJungler = (oppProf.players || []).find((p) => p.role === "Jungle") || { player: "Opponent JNG" };
    const topZone = ((oppM.kill_zone_distribution || [])[0] || { zone: "Dragon Pit & Bot River", share: 0.34 });

    const bullets = [];
    if (topPinched && topPinched.pinch_index >= 20) {
      bullets.push(
        `<li><strong>Exploit ${topPinched.role} Pool Pinch (${topPinched.player}):</strong> Fearless + bans depleted ${(
          topPinched.pool_share_removed * 100
        ).toFixed(0)}% of ${topPinched.player}'s recorded games (Pinch ${topPinched.pinch_index.toFixed(
          0
        )}/100, ${topPinched.remaining_comfort_count} comfort left). Force Phase-2 counter-matchup here.</li>`
      );
    } else if (ev.banRecs[0]) {
      bullets.push(
        `<li><strong>Primary Target Ban (${ev.banRecs[0].champion}):</strong> Denying ${ev.banRecs[0].player}'s ${ev.banRecs[0].champion} (n=${ev.banRecs[0].games}g) spikes their ${ev.banRecs[0].role} Pinch Index by +${ev.banRecs[0].gain} pts.</li>`
      );
    }

    if ((oppM.top_scuttle_rate ?? 0.5) >= 0.52) {
      bullets.push(
        `<li><strong>Counter Top-Side Pathing (${oppJungler.player}):</strong> ${oppProf.name} paths to Top Scuttle ${oppTopScuttle}% of games for ${(
          (oppM.first_grub_rate ?? 0.5) * 100
        ).toFixed(0)}% First Grub control. Draft Bot push prio for Blaber's ${
          100 - c9TopScuttle
        }% Bot-Scuttle tempo and stack early Dragons.</li>`
      );
    } else {
      bullets.push(
        `<li><strong>Contest Bot-River Tempo (${oppJungler.player}):</strong> ${oppProf.name} clears toward Bot Scuttle ${oppBotScuttle}% (${(
          (oppM.first_dragon_rate ?? 0.5) * 100
        ).toFixed(0)}% First Dragon). Ward 3:15 Bot River pixel and leverage C9's ${(
          (c9M.first_herald_rate ?? 0.704) * 100
        ).toFixed(0)}% Herald-to-First-Tower snowball.</li>`
      );
    }

    bullets.push(
      `<li><strong>Early Skirmish Hotspot Alert:</strong> ${(topZone.share * 100).toFixed(
        0
      )}% of ${oppProf.name}'s pre-14m kills cluster in <em>${topZone.zone}</em> — align Support roam timers at 5:30 and 8:00.</li>`
    );

    document.getElementById("how-to-win-list").innerHTML = bullets.join("");
  }

  function renderAll() {
    const ev = computeCurrentEvaluation();
    renderDraftBoard(ev);
    renderCenterIntel(ev);
    renderMacroRift();
  }

  // Zero-Redistribution Browser Local GRID Folder Loader (`meta/games.csv` + `meta/rosters.csv`)
  function parseCSV(text) {
    const lines = text.split(/\r?\n/).filter((l) => l.length > 0);
    if (lines.length === 0) return [];
    const splitRow = (row) => {
      const out = [];
      let cur = "";
      let inQuotes = false;
      for (let i = 0; i < row.length; i++) {
        const ch = row[i];
        if (ch === '"') inQuotes = !inQuotes;
        else if (ch === "," && !inQuotes) {
          out.push(cur);
          cur = "";
        } else cur += ch;
      }
      out.push(cur);
      return out;
    };
    const headers = splitRow(lines[0]);
    return lines.slice(1).map((l) => {
      const vals = splitRow(l);
      const obj = {};
      headers.forEach((h, idx) => {
        obj[h] = vals[idx] ?? "";
      });
      return obj;
    });
  }

  async function handleLocalGridFiles(fileList) {
    const files = Array.from(fileList || []);
    const gamesFile = files.find((f) => f.name === "games.csv");
    const rostersFile = files.find((f) => f.name === "rosters.csv");
    const teamsFile = files.find((f) => f.name === "teams.csv");
    if (!gamesFile || !rostersFile) {
      alert("Select the local `stl-hackathon-2026-grid-starter` directory (containing `meta/games.csv` and `meta/rosters.csv`). Zero bytes are uploaded anywhere.");
      return;
    }

    const [gamesTxt, rostersTxt, teamsTxt] = await Promise.all([
      gamesFile.text(),
      rostersFile.text(),
      teamsFile ? teamsFile.text() : Promise.resolve(""),
    ]);

    const teamNames = {};
    if (teamsTxt) {
      for (const r of parseCSV(teamsTxt)) {
        if (r.title === "lol") teamNames[r.team_id] = r.name;
      }
    }

    const validGames = new Map();
    const teamAgg = new Map();
    const ensureTeam = (tid, tname) => {
      if (!teamAgg.has(tid)) {
        teamAgg.set(tid, {
          team_id: tid,
          name: teamNames[tid] || tname || tid,
          games: 0,
          wins: 0,
          blueG: 0,
          blueW: 0,
          redG: 0,
          redW: 0,
          g3G: 0,
          g3W: 0,
          players: new Map(),
          champs: new Map(),
        });
      }
      return teamAgg.get(tid);
    };

    for (const g of parseCSV(gamesTxt)) {
      if (g.title !== "lol" || g.session_valid !== "True" || g.finished !== "True") continue;
      validGames.set(`${g.series_id}:${g.game_id}`, g);
      for (const pref of ["team1", "team2"]) {
        const tid = g[`${pref}_id`];
        const t = ensureTeam(tid, g[`${pref}_name`]);
        const won = g.winner_team_id === tid;
        const gnum = parseInt(g.game_number || "1", 10);
        t.games++;
        if (won) t.wins++;
        if (g[`${pref}_side`] === "blue") {
          t.blueG++;
          if (won) t.blueW++;
        } else {
          t.redG++;
          if (won) t.redW++;
        }
        if (gnum >= 3) {
          t.g3G++;
          if (won) t.g3W++;
        }
      }
    }

    for (const r of parseCSV(rostersTxt)) {
      if (r.title !== "lol" || r.participation_status !== "active") continue;
      const g = validGames.get(`${r.series_id}:${r.game_id}`);
      if (!g || !r.character_name) continue;
      const t = ensureTeam(r.team_id, r.team_name);
      const won = g.winner_team_id === r.team_id;
      const pname = r.player_name.trim();
      const cname = r.character_name.trim();
      const is2026 = (g.started_at || "").startsWith("2026");

      if (!t.players.has(pname)) t.players.set(pname, { games: 0, wins: 0, r26: 0, pool: new Map() });
      const p = t.players.get(pname);
      p.games++;
      if (won) p.wins++;
      if (is2026) p.r26++;
      const pc = p.pool.get(cname) || { champion: cname, games: 0, wins: 0 };
      pc.games++;
      if (won) pc.wins++;
      p.pool.set(cname, pc);

      const cc = t.champs.get(cname) || { champion: cname, games: 0, wins: 0 };
      cc.games++;
      if (won) cc.wins++;
      t.champs.set(cname, cc);
    }

    const roleOrder = { Top: 0, Jungle: 1, Mid: 2, Bot: 3, Support: 4, Flex: 5 };
    for (const [tid, t] of teamAgg.entries()) {
      if (t.games < 5) continue;
      const plist = Array.from(t.players.entries())
        .map(([pname, p]) => {
          const poolArr = Array.from(p.pool.values()).sort((a, b) => b.games - a.games);
          const role = poolArr[0] ? getArch(poolArr[0].champion).roles[0] : "Flex";
          return { player: pname, role, games: p.games, r26: p.r26, win_rate: p.wins / p.games, pool: poolArr.slice(0, 8) };
        })
        .sort((a, b) => b.r26 - a.r26 || b.games - a.games)
        .slice(0, 5)
        .sort((a, b) => (roleOrder[a.role] ?? 5) - (roleOrder[b.role] ?? 5));

      const sigs = Array.from(t.champs.values())
        .sort((a, b) => b.games - a.games)
        .slice(0, 15)
        .map((c) => ({ ...c, smoothed_wr: smoothedWR(c.wins, c.games) }));

      const existingMacro = (state.profiles[tid] && state.profiles[tid].macro) || {};
      state.profiles[tid] = {
        team_id: tid,
        name: t.name,
        sample_games: t.games,
        overall_win_rate: t.wins / t.games,
        blue_win_rate: t.blueW / Math.max(1, t.blueG),
        red_win_rate: t.redW / Math.max(1, t.redG),
        fearless_g3plus_games: t.g3G,
        fearless_g3plus_win_rate: t.g3W / Math.max(1, t.g3G),
        players: plist,
        signature_champions: sigs,
        macro: existingMacro,
      };
      if (t.name.includes("Cloud9")) state.c9Id = tid;
    }

    document.getElementById("data-mode-pill").textContent = `Browser Local GRID Loaded (${validGames.size} Games · 0B Uploaded)`;
    populateOpponentDropdown();
    seedMidDraftDemo();
  }

  // Event Listeners
  function bindEvents() {
    document.getElementById("opponent-select").addEventListener("change", async (e) => {
      state.oppId = e.target.value;
      if (state.apiConnected && !state.profiles[state.oppId]) {
        await fetchScoutingFromApi(state.oppId);
      }
      seedMidDraftDemo();
    });

    document.querySelectorAll("[data-side]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.c9Side = btn.dataset.side;
        document.querySelectorAll("[data-side]").forEach((b) => b.classList.toggle("active", b === btn));
        seedMidDraftDemo();
      });
    });

    document.querySelectorAll("#game-tabs .seg-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.gameNum = parseInt(btn.dataset.game, 10);
        document.querySelectorAll("#game-tabs .seg-btn").forEach((b) => b.classList.toggle("active", b === btn));
        seedMidDraftDemo();
      });
    });

    document.getElementById("auto-step-btn").addEventListener("click", () => stepAutoAction(true));
    document.getElementById("sim-full-btn").addEventListener("click", () => {
      while (state.actions.length < 20) stepAutoAction(false);
      renderAll();
    });
    document.getElementById("reset-draft-btn").addEventListener("click", () => resetDraftForCurrentSeries());

    document.getElementById("champ-search").addEventListener("input", (e) => {
      state.searchQuery = e.target.value;
      renderDraftBoard(computeCurrentEvaluation());
    });

    document.querySelectorAll("#role-filter .role-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.roleFilter = btn.dataset.role;
        document.querySelectorAll("#role-filter .role-btn").forEach((b) => b.classList.toggle("active", b === btn));
        renderDraftBoard(computeCurrentEvaluation());
      });
    });

    const localInput = document.getElementById("local-grid-input");
    localInput.setAttribute("webkitdirectory", "");
    localInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files.length > 0) handleLocalGridFiles(e.target.files);
    });
  }

  // Boot
  populateOpponentDropdown();
  bindEvents();
  seedMidDraftDemo();
  tryConnectLocalBackend();
})();
