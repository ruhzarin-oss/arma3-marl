"""run_react — DEFENSE QUI REAGIT. BLUFOR identique a run_breach (20 petites escouades, 2 etages, percee LLM).
OPFOR : 11 secteurs RE-TASKABLES + un COMMANDANT defenseur (regle OU llm) qui detecte la breche et BASCULE la
reserve pour colmater. On mesure la course : colmatage vs percee.
  --opcmd none  : defense statique (baseline = run_breach)
  --opcmd rule  : commandant deterministe (pression max -> bascule reserve)
  --opcmd llm   : MEME qwen, 2e role (system prompt 'defenseur'), SITREP par secteur -> renforts
"""
import time, json, argparse, math
import numpy as np
import torch
import urllib.request
from op_arma import OpArma, STANCES
from train_koth_gpu import Net
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
STAFF = "/home/younes/arma3-marl/staff/state.json"; HB = "/home/younes/arma3-marl/staff/react_heartbeat.json"
OLLAMA = "http://localhost:11434/api/chat"; MODEL = "qwen2.5:14b"
COL = {"ASSAUT": "#4a9eff", "APPUI": "#38bdf8", "FIX_O": "#22c55e", "FIX_E": "#f59e0b"}
CX, CY = M.COMPLEXE; R = 135
LLM = {}; _t0 = [None]

ORDER = [("ASSAUT", 6, 8), ("APPUI", 4, 8), ("FIX_O", 5, 7), ("FIX_E", 5, 7)]   # 150 BLUFOR
SQUADS = []; SPAWNS = {}; SEC = {"ASSAUT": [], "APPUI": [], "FIX_O": [], "FIX_E": []}
_slots = [(20750 + c * 30, yy) for yy in (16640, 16686) for c in range(10)]
_i = 0
for _sn, _cnt, _sz in ORDER:
    for _k in range(_cnt):
        _nm = "%s_%d" % (_sn, _k); SQUADS.append((_nm, _sz)); SPAWNS[_nm] = _slots[_i]
        SEC[_sn].append(len(SQUADS) - 1); _i += 1
SECCOL = {s[0]: COL[sn] for sn, _, _ in ORDER for s in SQUADS if s[0].startswith(sn)}
AX = {"sud": (0, -1), "sud-ouest": (-0.7, -0.7), "sud-est": (0.7, -0.7), "ouest": (-1, 0), "est": (1, 0)}


def card(x, y):
    dx, dy = x - CX, y - CY
    if abs(dx) < 35 and abs(dy) < 35:
        return "centre"
    a = math.degrees(math.atan2(dy, dx)) % 360
    return ["E", "NE", "N", "NO", "O", "SO", "S", "SE"][int((a + 22.5) // 45) % 8]


def llm_axe(report):
    sysp = ("Tu commandes l'ASSAUT (150 h, 20 escouades) sur une ville defendue en herisson 360 deg. Doctrine : on "
            "CONCENTRE sur UN axe pour PERCER, on fixe le reste. Choisis l'axe parmi : sud, sud-ouest, sud-est, ouest, "
            "est. Reponds UNIQUEMENT en JSON : {\"axe\":\"<...>\",\"justification\":\"<1-2 phrases>\"}.")
    return _ask(sysp, report)


def llm_defend(report):
    sysp = ("Tu es le COMMANDANT DEFENSEUR de Paros. Tes hommes tiennent des secteurs autour de la ville. L'ennemi "
            "CONCENTRE son assaut sur un secteur (la breche). Tu dois COLMATER : choisir quel(s) secteur(s) RESERVE "
            "(sans pression) basculer vers le secteur menace. Ne degarnis pas un secteur deja attaque. Reponds "
            "UNIQUEMENT en JSON : {\"renforcer\":\"<id secteur menace>\",\"depuis\":[\"<id reserve>\",...],"
            "\"justification\":\"<1-2 phrases>\"}.")
    return _ask(sysp, report)


def llm_officer_adapt(report):
    sysp = ("Tu commandes l'ASSAUT. Tu as concentre ta percee sur un axe, mais le defenseur a REAGI et renforce. Tu "
            "peux MAINTENIR ton axe (si tu progresses) ou BASCULER ton effort principal vers la direction la MOINS "
            "defendue pour percer la ou c'est faible (exploiter que l'ennemi s'est degarni ailleurs). Ne bascule pas "
            "sans raison nette. Reponds UNIQUEMENT en JSON : {\"action\":\"maintenir\"|\"basculer\","
            "\"axe\":\"<si basculer: sud|sud-est|est|ouest|sud-ouest>\",\"justification\":\"<1-2 phrases>\"}.")
    return _ask(sysp, report)


def _ask(sysp, report):
    body = json.dumps({"model": MODEL, "stream": False, "format": "json", "options": {"temperature": 0.3},
                       "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": report}]}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(OLLAMA, body, {"Content-Type": "application/json"}), timeout=120))
    return json.loads(r["message"]["content"])


def opf_secteurs(total=150):
    rings = 10; per = (total - 20) // rings
    secs = [(CX, CY, 20, "hold")]
    for i in range(rings):
        ang = 2 * math.pi * i / rings; r = 120 + (i % 2) * 30
        secs.append((int(CX + r * math.cos(ang)), int(CY + r * math.sin(ang)), per, "suppress"))
    return secs


def act(env, brain, si):
    o = env.obs(si)
    with torch.no_grad():
        lg = brain.a_logits(torch.as_tensor(o, dtype=torch.float32, device=DEV)) + torch.as_tensor(STANCES[env.stances[si]], device=DEV)
    return torch.distributions.Categorical(logits=lg).sample().cpu().numpy()


def compute_obs(px, py, al, gx, gy, epx, epy, eal, S, sight):
    n = len(px)
    ox = (px - gx) / S; oy = (py - gy) / S; dgx = (gx - px) / S; dgy = (gy - py) / S
    dx = px[None, :] - px[:, None]; dy = py[None, :] - py[:, None]
    d2 = np.where(np.eye(n, dtype=bool) | (~al)[None, :], 1e18, dx * dx + dy * dy)
    jm = d2.argmin(1); adx = dx[np.arange(n), jm] / S; ady = dy[np.arange(n), jm] / S
    nm = d2.min(1) >= 1e18; adx[nm] = 0.0; ady[nm] = 0.0
    if len(epx) and eal.any():
        ex = epx[None, :] - px[:, None]; ey = epy[None, :] - py[:, None]
        ed2 = np.where(eal[None, :], ex * ex + ey * ey, 1e18); km = ed2.argmin(1)
        edx = ex[np.arange(n), km]; edy = ey[np.arange(n), km]
        nd = np.sqrt(ed2.min(1)); seen = (nd <= sight) & (ed2.min(1) < 1e18)
        edx = (edx / S) * seen; edy = (edy / S) * seen
    else:
        edx = np.zeros(n); edy = np.zeros(n)
    return np.stack([ox, oy, dgx, dgy, al.astype(np.float32), adx, ady, edx, edy, np.zeros(n)], 1).astype(np.float32)


def drive_opfor(env, brain, groups, move=22.0):
    dead = env.dmg_dead * 100
    BX = np.concatenate([env.px[si] for si in range(env.S)]); BY = np.concatenate([env.py[si] for si in range(env.S)])
    BAL = np.concatenate([env.alive(si) for si in range(env.S)])
    cmds = []
    for g in groups:
        a, b = g["a"], g["b"]; gx, gy, stance = g["gx"], g["gy"], g["stance"]
        ox = env.epx[a:b]; oy = env.epy[a:b]; al = env.edmg[a:b] < dead
        if not al.any():
            continue
        obs = compute_obs(ox, oy, al, gx, gy, BX, BY, BAL, env.scale, env.sight)
        with torch.no_grad():
            lg = brain.a_logits(torch.as_tensor(obs, dtype=torch.float32, device=DEV)) + torch.as_tensor(STANCES[stance], device=DEV)
        acts = torch.distributions.Categorical(logits=lg).sample().cpu().numpy()
        tox = gx - ox; toy = gy - oy; tn = np.sqrt(tox ** 2 + toy ** 2) + 1e-6
        for i in range(b - a):
            if not al[i]:
                continue
            gi = a + i; m = int(acts[i])
            if m == 1:                                          # AVANCER (cle de la bascule : le secteur marche vers son objectif)
                tx = int(ox[i] + tox[i] / tn[i] * move); ty = int(oy[i] + toy[i] / tn[i] * move)
                cmds.append('private _u=HMT_EN select %d; if (!isNull _u && {alive _u}) then {_u setUnitPos "MIDDLE"; _u doMove [%d,%d,0];};' % (gi, tx, ty))
            elif m == 2:
                cmds.append('private _u=HMT_EN select %d; if (!isNull _u && {alive _u}) then {doStop _u; _u setUnitPos "UP";};' % gi)
            elif m == 3:
                cmds.append('private _u=HMT_EN select %d; if (!isNull _u && {alive _u}) then {doStop _u; _u setUnitPos "DOWN";};' % gi)
            else:
                cmds.append('private _u=HMT_EN select %d; if (!isNull _u && {alive _u}) then {doStop _u; _u setUnitPos "MIDDLE";};' % gi)
    if cmds:
        env.b.send("\n".join(cmds), wait=True)


def grp_stat(env, g, BX, BY, BAL):
    dead = env.dmg_dead * 100
    ox = env.epx[g["a"]:g["b"]]; oy = env.epy[g["a"]:g["b"]]; al = env.edmg[g["a"]:g["b"]] < dead
    g["alive"] = int(al.sum())
    if al.any():
        mx, my = float(ox[al].mean()), float(oy[al].mean())
        g["mx"], g["my"] = mx, my
        g["press"] = int((((BX - mx) ** 2 + (BY - my) ** 2 < 130 ** 2) & BAL).sum())
    else:
        g["press"] = 0


def commander_rule(env, groups, logf):
    BX = np.concatenate([env.px[si] for si in range(env.S)]); BY = np.concatenate([env.py[si] for si in range(env.S)])
    BAL = np.concatenate([env.alive(si) for si in range(env.S)])
    for g in groups:
        grp_stat(env, g, BX, BY, BAL)
    threat = max(groups, key=lambda g: g.get("press", 0))
    if threat.get("press", 0) < 12:
        return
    bx = int(threat["home"][0] * 0.6 + CX * 0.4); by = int(threat["home"][1] * 0.6 + CY * 0.4)
    res = [g for g in groups if g.get("press", 0) < 4 and g is not threat and g["alive"] > 0 and not g.get("reinf")]
    res.sort(key=lambda g: (g.get("mx", CX) - threat["home"][0]) ** 2 + (g.get("my", CY) - threat["home"][1]) ** 2)
    for g in res[:2]:
        g["gx"], g["gy"], g["stance"], g["reinf"] = bx, by, "move", threat["id"]
        logf("[REGLE] renfort %s (%s) -> breche %s (%s)" % (g["id"], g["card"], threat["id"], threat["card"]))


def commander_llm(env, groups, logf):
    BX = np.concatenate([env.px[si] for si in range(env.S)]); BY = np.concatenate([env.py[si] for si in range(env.S)])
    BAL = np.concatenate([env.alive(si) for si in range(env.S)])
    for g in groups:
        grp_stat(env, g, BX, BY, BAL)
    rep = "SITUATION DEFENSE Paros. Tes secteurs (id, position, hommes, pression ennemie) :\n"
    for g in groups:
        rep += "  %s (%s) : %d hommes, pression=%d\n" % (g["id"], g["card"], g["alive"], g.get("press", 0))
    try:
        d = llm_defend(rep)
    except Exception as e:
        logf("[LLM] erreur %s" % str(e)[:40]); return
    tid = str(d.get("renforcer", "")).strip()
    threat = next((g for g in groups if g["id"] == tid), max(groups, key=lambda g: g.get("press", 0)))
    bx = int(threat["home"][0] * 0.6 + CX * 0.4); by = int(threat["home"][1] * 0.6 + CY * 0.4)
    moved = []
    for sid in (d.get("depuis") or [])[:3]:
        g = next((x for x in groups if x["id"] == str(sid).strip()), None)
        if g and g["alive"] > 0 and g is not threat and not g.get("reinf"):
            g["gx"], g["gy"], g["stance"], g["reinf"] = bx, by, "move", threat["id"]; moved.append(g["id"])
    LLM["defense"] = {"renforcer": threat["id"], "depuis": moved, "justification": d.get("justification")}
    logf("[LLM] colmate %s depuis %s : %s" % (threat["id"], moved, str(d.get("justification"))[:80]))


def arrive_check(env, groups, logf):
    """un renfort arrive pres de la breche -> il se met a suppresser (il defend)."""
    for g in groups:
        if g.get("reinf") and g.get("alive", 0) > 0 and "mx" in g:
            if math.hypot(g["mx"] - g["gx"], g["my"] - g["gy"]) < 45 and g["stance"] != "suppress":
                g["stance"] = "suppress"; logf("[ARRIVEE] %s en position sur la breche" % g["id"])


def opf_near(env, pt, r):
    eal = env.en_alive(); d = np.hypot(env.epx - pt[0], env.epy - pt[1])
    return int((eal & (d < r)).sum())


def losses(env):
    tot = sum(env.sizes); al = sum(int(env.alive(si).sum()) for si in range(env.S))
    return 1.0 - al / tot


def dump(env, op, step, phase, breach):
    sq = {}
    for si, nm in enumerate(env.squads):
        units = [[int(env.px[si][u]), int(env.py[si][u]), int(env.dmg[si][u] < env.dmg_dead * 100)] for u in range(env.sizes[si])]
        sq[nm] = {"color": SECCOL.get(nm, "#ddd"), "units": units, "goal": [int(env.goals[si][0]), int(env.goals[si][1])], "stance": env.stances[si]}
    en = [[int(env.epx[k]), int(env.epy[k]), int(env.edmg[k] < env.dmg_dead * 100)] for k in range(env.en_n)]
    st = {"op": op, "step": step, "losses": round(losses(env), 3), "squads": sq, "enemies": en,
          "pts": {"COMPLEXE": list(M.COMPLEXE), "CRETE": [int(breach[0]), int(breach[1])], "FLANC_O": list(M.FLANC_O), "FLANC_E": list(M.FLANC_E), "QRF": list(M.QRF_PT)},
          "llm": LLM, "phase": phase}
    try:
        json.dump(st, open(STAFF, "w"))
    except Exception:
        pass
    now = time.time(); dt = None if _t0[0] is None else round(now - _t0[0], 2); _t0[0] = now
    blu = sum(int(env.alive(si).sum()) for si in range(env.S))
    try:
        json.dump({"step": step, "phase": phase, "dt_par_pas_s": dt, "BLUFOR_vivants": blu, "OPFOR_vivants": int(env.en_alive().sum()),
                   "opf_sur_breche": opf_near(env, breach, 55), "pertes_BLU_pct": round(100 * losses(env), 1)}, open(HB, "w"))
    except Exception:
        pass


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--srv", type=int, default=2); p.add_argument("--seed", type=int, default=5)
    p.add_argument("--max_steps", type=int, default=340); p.add_argument("--acc", type=float, default=1.0)
    p.add_argument("--opcmd", choices=["none", "rule", "llm"], default="rule"); p.add_argument("--every", type=int, default=12)
    p.add_argument("--bofficer", choices=["fixed", "adaptive", "disc-rule", "disc-llm"], default="fixed"); p.add_argument("--bevery", type=int, default=20)
    a = p.parse_args()
    LOG = open("/tmp/react_cmd.log", "a")

    def logf(s):
        print(s, flush=True); LOG.write(s + "\n"); LOG.flush()
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    print("=== PERCEE vs DEFENSE REACTIVE [opcmd=%s] — server%d ===" % (a.opcmd, a.srv), flush=True)
    rep = ("L'ennemi tient Paros en herisson 360 deg, 150 hommes. Tu as 150 hommes en 20 petites escouades. "
           "Crete dominante au nord-ouest. Tu abordes par le sud.")
    try:
        d = llm_axe(rep)
    except Exception as e:
        d = {"axe": "sud", "justification": "(repli %s)" % str(e)[:30]}
    axe = d.get("axe", "sud").lower().strip()
    if axe not in AX:
        axe = "sud"
    LLM.update({"axe": axe, "justification": d.get("justification")})
    logf("[LLM etage1 BLUFOR] axe percee = %s | %s" % (axe, d.get("justification")))
    geo = {}

    def set_axe(ax):
        dxx, dyy = AX[ax]; pxx, pyy = -dyy, dxx
        geo.update({"axe": ax, "breach": (CX + dxx * R, CY + dyy * R), "form": (CX + dxx * (R + 80), CY + dyy * (R + 80)),
                    "support": (CX + dxx * (R + 55) + pxx * 45, CY + dyy * (R + 55) + pyy * 45),
                    "fixO": (int(CX - R * 0.92), int(CY + 15)), "fixE": (int(CX + R * 0.92), int(CY + 15))})
    set_axe(axe); breach = geo["breach"]
    env = OpArma(squads=tuple(SQUADS), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % a.srv,
                 log=SB + "/logs/server%d.out" % a.srv, move=34, acc=a.acc, seed=a.seed)
    secs = opf_secteurs(150); GARR = [(x, y, n, 22) for (x, y, n, st) in secs]
    print("[spawn] 150 BLUFOR + 150 OPFOR (11 secteurs)...", flush=True)
    t = time.time(); env.spawn(SPAWNS, GARR)
    env._query('{ private _g=_x; while {count waypoints _g > 0} do {deleteWaypoint [_g,0]}; } forEach (allGroups select {side _x == east}); diag_log "HARMATTAN_NOWP";', settle=1.0)
    groups = []; idx = 0
    for k, (x, y, n, st) in enumerate(secs):
        groups.append({"id": "S%d" % k, "a": idx, "b": idx + n, "home": (x, y), "gx": x, "gy": y,
                       "stance": st, "card": card(x, y), "reinf": None, "alive": n}); idx += n
    for _ in range(8):
        env.read()
        if float(np.abs(env.epx).sum()) > 100:
            break
        time.sleep(1.0)
    logf("[spawn] 300 IA en %.1fs | breche=%d,%d | secteurs: %s" % (time.time() - t, breach[0], breach[1], ", ".join("%s=%s" % (g["id"], g["card"]) for g in groups)))

    def orders(phase):
        tgt = ({"ASSAUT": (geo["breach"], "assault"), "APPUI": (geo["support"], "suppress"), "FIX_O": (geo["fixO"], "suppress"), "FIX_E": (geo["fixE"], "suppress")} if phase == "PERCEE"
               else {"ASSAUT": (M.COMPLEXE, "assault"), "APPUI": (M.COMPLEXE, "suppress"), "FIX_O": (geo["fixO"], "hold"), "FIX_E": (geo["fixE"], "hold")})
        for sn, (pt, stn) in tgt.items():
            for si in SEC[sn]:
                env.goals[si] = np.array(pt, dtype=float); env.stances[si] = stn

    phase = "PERCEE"; step = 0; sig = None; t_fige = time.time(); succes = False; t_renfort = None; last_sw = -99; nb_sw = 0
    cur_best = 99; stall = 0; abandoned = []
    op = "DUEL[bof=%s vs opf=%s] / axe %s" % (a.bofficer, a.opcmd, axe)
    dump(env, op, 0, phase, breach)
    while step < a.max_steps:
        orders(phase); breach = geo["breach"]
        # --- officier BLUFOR : re-arbitre l'axe (naif OU discipline a garde-fous) ---
        if a.bofficer != "fixed" and step > 12 and step % a.bevery == 0:
            eal = env.en_alive()
            DIRS = {"sud": (0, -1), "sud-est": (0.7, -0.7), "est": (1, 0), "ouest": (-1, 0), "sud-ouest": (-0.7, -0.7)}
            strg = {k: int((eal & (np.hypot(env.epx - (CX + dx2 * R), env.epy - (CY + dy2 * R)) < 95)).sum()) for k, (dx2, dy2) in DIRS.items()}
            onb0 = opf_near(env, geo["breach"], 55); cur_best = min(cur_best, onb0)
            switch_to = None; reason = ""
            if a.bofficer == "adaptive":                                     # naif : on demande, on suit
                if step - last_sw > 24:
                    try:
                        dd = llm_officer_adapt("Axe=%s, def sur breche=%d.\nDef/dir:\n%sMaintenir ou basculer vers le plus faible ?" % (geo["axe"], onb0, "".join("  %s: %d\n" % (k, v) for k, v in strg.items())))
                    except Exception:
                        dd = {}
                    if str(dd.get("action", "")).startswith("bascul") and str(dd.get("axe", "")).strip().lower() in AX and str(dd.get("axe", "")).strip().lower() != geo["axe"]:
                        switch_to = str(dd.get("axe", "")).strip().lower(); reason = dd.get("justification")
            else:                                                            # DISCIPLINE (garde-fous en dur)
                RUPT = 6
                if onb0 < RUPT:                                              # verrou de rupture : on NE LACHE PAS un axe quasi-ouvert
                    stall = 0
                elif onb0 > cur_best + 1:                                    # l'axe ne progresse plus
                    stall += 1
                else:
                    stall = 0
                if onb0 >= RUPT and stall >= 2 and step - last_sw > 30:      # bloque, cooldown ok
                    cands = sorted([k for k in DIRS if k != geo["axe"] and k not in abandoned[-2:]], key=lambda k: strg[k])
                    if cands:
                        if a.bofficer == "disc-rule":
                            switch_to = cands[0]; reason = "(regle) axe bloque -> plus faible"
                        else:                                               # disc-llm : LLM juge, mais SEULEMENT si bloque et parmi les axes permis
                            try:
                                dd = llm_officer_adapt("Tu es BLOQUE sur l'axe %s (breche stagne a %d, l'ennemi y a masse). Deja %d bascules — NE REVIENS PAS sur un axe abandonne. Defense/dir:\n%sBascule UNE fois vers un secteur faible PERMIS (%s), ou maintiens si rien de clairement mieux." % (geo["axe"], onb0, nb_sw, "".join("  %s: %d\n" % (k, v) for k, v in strg.items()), ", ".join(cands)))
                            except Exception:
                                dd = {}
                            if str(dd.get("action", "")).startswith("bascul") and str(dd.get("axe", "")).strip().lower() in cands:
                                switch_to = str(dd.get("axe", "")).strip().lower(); reason = dd.get("justification")
            if switch_to:
                abandoned.append(geo["axe"])
                logf("[OFFICIER %s] BASCULE %s -> %s (breche=%d, def/dir=%s) : %s" % (a.bofficer, geo["axe"], switch_to, onb0, strg, str(reason)[:70]))
                set_axe(switch_to); breach = geo["breach"]; phase = "PERCEE"; last_sw = step; nb_sw += 1; cur_best = 99; stall = 0
                LLM["axe"] = switch_to; LLM["bascules"] = nb_sw
        acts = [act(env, brain, si) for si in range(env.S)]
        env.step(acts); step += 1
        # --- commandant defenseur ---
        if a.opcmd != "none" and step % a.every == 0:
            (commander_rule if a.opcmd == "rule" else commander_llm)(env, groups, logf)
            if t_renfort is None and any(g.get("reinf") for g in groups):
                t_renfort = step; logf("[COURSE] 1er renfort lance au pas %d (breche=%d def)" % (step, opf_near(env, breach, 55)))
        arrive_check(env, groups, logf)
        drive_opfor(env, brain, groups)
        dump(env, op, step, phase, breach)
        onb = opf_near(env, breach, 55)
        if step % 5 == 0:
            logf("[%4d] %-12s BLU=%d OPF=%d breche=%d pertes=%.0f%% renf=%d"
                 % (step, phase, sum(int(env.alive(si).sum()) for si in range(env.S)), int(env.en_alive().sum()), onb, 100 * losses(env), sum(1 for g in groups if g.get("reinf"))))
        if phase == "PERCEE" and step > 6 and onb == 0:
            phase = "EXPLOITATION"; logf("[PHASE] -> EXPLOITATION (breche ouverte au pas %d)" % step); t_fige = time.time()
        elif phase == "EXPLOITATION" and step > 15 and opf_near(env, M.COMPLEXE, 60) == 0:
            succes = True; logf("[PHASE] OBJECTIF PRIS au pas %d" % step); break
        s2 = (int(env.en_alive().sum()), sum(int(env.alive(si).sum()) for si in range(env.S)), phase)
        if s2 != sig:
            sig = s2; t_fige = time.time()
        elif time.time() - t_fige > 440:
            logf("[ABORT] enlisement"); break
        if losses(env) > 0.8:
            logf("[ABORT] pertes > 80%"); break
    dump(env, op, step, phase, breach)
    blu = sum(int(env.alive(si).sum()) for si in range(env.S)); opf = int(env.en_alive().sum())
    logf(">>> [bof=%s vs opf=%s] percee %s | axe final %s (%d bascules) | objectif %s | BLUFOR %d/150 (pertes %.0f%%) | OPFOR %d/150 | pas %d"
         % (a.bofficer, a.opcmd, "REUSSIE" if succes else "ECHEC", geo["axe"], nb_sw, "PRIS" if succes else "non pris", blu, 100 * losses(env), opf, step))
    print("REACT FINI", flush=True)
