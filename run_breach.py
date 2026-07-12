"""run_breach — PERCEE ARTICULEE : 150 BLUFOR en 20 PETITES escouades (7-8, la taille d'entrainement du cerveau)
sous un commandement A DEUX ETAGES, contre 150 OPFOR RL defendant Paros sur 360 deg.
  Etage 1 (LLM)     : choisit l'AXE de percee (ou concentrer l'effort principal).
  Etage 2 (sections): ASSAUT concentre 6 escouades sur UN point etroit ; APPUI suppresse ce point ;
                      FIX_O / FIX_E fixent les flancs pour empecher le renfort ennemi.
  Etage 3 (RL gele) : pilote chaque escouade de 7-8.
Hypothese : la percee est un probleme d'ARTICULATION. Petites escouades + concentration -> elle perce.
"""
import time, json, argparse, math
import numpy as np
import torch
import urllib.request
from op_arma import OpArma, STANCES
from train_koth_gpu import Net
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
STAFF = "/home/younes/arma3-marl/staff/state.json"; HB = "/home/younes/arma3-marl/staff/breach_heartbeat.json"
OLLAMA = "http://localhost:11434/api/chat"; MODEL = "qwen2.5:14b"
COL = {"ASSAUT": "#4a9eff", "APPUI": "#38bdf8", "FIX_O": "#22c55e", "FIX_E": "#f59e0b"}
CX, CY = M.COMPLEXE; R = 135
LLM = {}
_t0 = [None]

# -------- ordre de bataille : 20 escouades, 4 sections, 150 hommes --------
ORDER = [("ASSAUT", 6, 8), ("APPUI", 4, 8), ("FIX_O", 5, 7), ("FIX_E", 5, 7)]   # 48+32+35+35 = 150
SQUADS = []; SPAWNS = {}; SEC = {"ASSAUT": [], "APPUI": [], "FIX_O": [], "FIX_E": []}
_slots = [(20750 + c * 30, yy) for yy in (16640, 16686) for c in range(10)]
_i = 0
for _sn, _cnt, _sz in ORDER:
    for _k in range(_cnt):
        _nm = "%s_%d" % (_sn, _k); SQUADS.append((_nm, _sz)); SPAWNS[_nm] = _slots[_i]
        SEC[_sn].append(len(SQUADS) - 1); _i += 1
SECCOL = {nm: COL[sn] for sn, _, _ in ORDER for nm in [s[0] for s in SQUADS] if nm.startswith(sn)}


def opf_secteurs(total=150):
    rings = 10; per = (total - 20) // rings
    secs = [(CX, CY, 20, "hold")]
    for i in range(rings):
        ang = 2 * math.pi * i / rings; r = 120 + (i % 2) * 30
        secs.append((int(CX + r * math.cos(ang)), int(CY + r * math.sin(ang)), per, "suppress"))
    return secs


def llm_axe(report):
    sysp = ("Tu es l'officier qui commande l'ASSAUT (150 hommes, 20 petites escouades). L'ennemi (150 hommes) defend "
            "une ville en HERISSON sur 360 deg. Doctrine : on ne disperse pas, on CONCENTRE l'effort sur UN axe pour "
            "PERCER, on fixe le reste. Choisis l'AXE de percee parmi exactement : sud, sud-ouest, sud-est, ouest, est "
            "(tu debarques par le sud). Reponds UNIQUEMENT en JSON : {\"axe\":\"<un de la liste>\",\"justification\":\"<1-2 phrases>\"}.")
    body = json.dumps({"model": MODEL, "stream": False, "format": "json", "options": {"temperature": 0.3},
                       "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": report}]}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(OLLAMA, body, {"Content-Type": "application/json"}), timeout=120))
    return json.loads(r["message"]["content"])


AX = {"sud": (0, -1), "sud-ouest": (-0.7, -0.7), "sud-est": (0.7, -0.7), "ouest": (-1, 0), "est": (1, 0)}


def act(env, brain, si):
    o = env.obs(si)
    with torch.no_grad():
        lg = brain.a_logits(torch.as_tensor(o, dtype=torch.float32, device=DEV))
    lg = lg + torch.as_tensor(STANCES[env.stances[si]], device=DEV)
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


def drive_opfor(env, brain, opf_groups, move=24.0):
    dead = env.dmg_dead * 100
    BX = np.concatenate([env.px[si] for si in range(env.S)]); BY = np.concatenate([env.py[si] for si in range(env.S)])
    BAL = np.concatenate([env.alive(si) for si in range(env.S)])
    cmds = []
    for (a, b, (gx, gy), stance) in opf_groups:
        ox = env.epx[a:b]; oy = env.epy[a:b]; al = env.edmg[a:b] < dead
        if not al.any():
            continue
        obs = compute_obs(ox, oy, al, gx, gy, BX, BY, BAL, env.scale, env.sight)
        with torch.no_grad():
            lg = brain.a_logits(torch.as_tensor(obs, dtype=torch.float32, device=DEV)) + torch.as_tensor(STANCES[stance], device=DEV)
        acts = torch.distributions.Categorical(logits=lg).sample().cpu().numpy()
        for i in range(b - a):
            if not al[i]:
                continue
            gi = a + i; m = int(acts[i])
            if m == 2:
                cmds.append('private _u=HMT_EN select %d; if (!isNull _u && {alive _u}) then {doStop _u; _u setUnitPos "UP";};' % gi)
            elif m == 3:
                cmds.append('private _u=HMT_EN select %d; if (!isNull _u && {alive _u}) then {doStop _u; _u setUnitPos "DOWN";};' % gi)
            else:
                cmds.append('private _u=HMT_EN select %d; if (!isNull _u && {alive _u}) then {doStop _u; _u setUnitPos "MIDDLE";};' % gi)
    if cmds:
        env.b.send("\n".join(cmds), wait=True)


def sec_at(env, idxs, pt, r):
    ds = []
    for si in idxs:
        al = env.alive(si)
        if al.any():
            ds.append(float(np.median(np.hypot(env.px[si][al] - pt[0], env.py[si][al] - pt[1]))))
    return bool(ds) and float(np.median(ds)) < r


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
    p.add_argument("--max_steps", type=int, default=320); p.add_argument("--acc", type=float, default=1.0)
    a = p.parse_args()
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    print("=== PERCEE ARTICULEE : 150 BLUFOR (20 escouades, 2 etages) vs 150 OPFOR RL — server%d ===" % a.srv, flush=True)
    rep = ("L'ennemi tient Paros en herisson : 150 hommes, noyau urbain + ceinture defensive 360 deg, densite egale "
           "partout. Tu as 150 hommes en 20 petites escouades. Crete dominante au nord-ouest. Tu abordes par le sud.")
    try:
        d = llm_axe(rep)
    except Exception as e:
        d = {"axe": "sud", "justification": "(repli: %s)" % str(e)[:40]}
    axe = d.get("axe", "sud").lower().strip()
    if axe not in AX:
        axe = "sud"
    dx, dy = AX[axe]
    LLM.update({"axe": axe, "justification": d.get("justification")})
    print("[LLM etage1] axe de percee = %s | %s" % (axe, d.get("justification")), flush=True)
    breach = (CX + dx * R, CY + dy * R)
    form = (CX + dx * (R + 80), CY + dy * (R + 80))
    px_, py_ = -dy, dx                                                   # perpendiculaire a l'axe
    support = (CX + dx * (R + 55) + px_ * 45, CY + dy * (R + 55) + py_ * 45)
    fixO = (int(CX - R * 0.92), int(CY + 15)); fixE = (int(CX + R * 0.92), int(CY + 15))
    env = OpArma(squads=tuple(SQUADS), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % a.srv,
                 log=SB + "/logs/server%d.out" % a.srv, move=34, acc=a.acc, seed=a.seed)
    secs = opf_secteurs(150); GARR = [(x, y, n, 22) for (x, y, n, st) in secs]
    print("[spawn] 150 BLUFOR (20 esc.) + 150 OPFOR...", flush=True)
    t = time.time(); env.spawn(SPAWNS, GARR)
    env._query('{ private _g=_x; while {count waypoints _g > 0} do {deleteWaypoint [_g,0]}; } forEach (allGroups select {side _x == east}); diag_log "HARMATTAN_NOWP";', settle=1.0)
    opf_groups = []; idx = 0
    for (x, y, n, st) in secs:
        opf_groups.append((idx, idx + n, (x, y), st)); idx += n
    print("[spawn] 300 IA en %.1fs (OPFOR=%d) | breche=%d,%d" % (time.time() - t, env.en_n, breach[0], breach[1]), flush=True)
    for _ in range(8):                                # lire les positions OPFOR AVANT la boucle (sinon faux 'objectif clair')
        env.read()
        if float(np.abs(env.epx).sum()) > 100:
            break
        time.sleep(1.0)
    print("[spawn] OPFOR lus (epx_sum=%d) | OPFOR pres objectif=%d" % (int(np.abs(env.epx).sum()), opf_near(env, M.COMPLEXE, 60)), flush=True)

    def orders(phase):
        if phase == "APPROCHE":
            tgt = {"ASSAUT": (form, "move"), "APPUI": (support, "move"), "FIX_O": (fixO, "move"), "FIX_E": (fixE, "move")}
        elif phase == "PERCEE":
            tgt = {"ASSAUT": (breach, "assault"), "APPUI": (support, "suppress"), "FIX_O": (fixO, "suppress"), "FIX_E": (fixE, "suppress")}
        else:
            tgt = {"ASSAUT": (M.COMPLEXE, "assault"), "APPUI": (M.COMPLEXE, "suppress"), "FIX_O": (fixO, "hold"), "FIX_E": (fixE, "hold")}
        for sn, (pt, stn) in tgt.items():
            for si in SEC[sn]:
                env.goals[si] = np.array(pt, dtype=float); env.stances[si] = stn

    phase = "PERCEE"; step = 0; t_mur = time.time(); sig = None; t_fige = time.time(); succes = False
    op = "PERCEE / axe %s / 20 esc. 2 etages" % axe
    print("[OP] axe=%s breche=%s form=%s" % (axe, tuple(map(int, breach)), tuple(map(int, form))), flush=True)
    dump(env, op, 0, phase, breach)
    while step < a.max_steps:
        orders(phase)
        acts = [act(env, brain, si) for si in range(env.S)]
        env.step(acts); step += 1
        drive_opfor(env, brain, opf_groups)
        dump(env, op, step, phase, breach)
        onb = opf_near(env, breach, 55)
        if step % 5 == 0:
            print("[%4d] %-12s BLU=%d OPF=%d breche=%d pertes=%.0f%%"
                  % (step, phase, sum(int(env.alive(si).sum()) for si in range(env.S)), int(env.en_alive().sum()), onb, 100 * losses(env)), flush=True)
        # transitions
        if phase == "APPROCHE" and sec_at(env, SEC["ASSAUT"], form, 75):
            phase = "PERCEE"; print("[PHASE] -> PERCEE (assaut en place, on suppresse la breche)", flush=True); t_fige = time.time()
        elif phase == "PERCEE" and step > 6 and onb == 0:
            phase = "EXPLOITATION"; print("[PHASE] -> EXPLOITATION (breche ouverte !)", flush=True); t_fige = time.time()
        elif phase == "EXPLOITATION" and step > 15 and opf_near(env, M.COMPLEXE, 60) == 0:
            succes = True; print("[PHASE] OBJECTIF PRIS", flush=True); break
        # bornes
        s2 = (int(env.en_alive().sum()), sum(int(env.alive(si).sum()) for si in range(env.S)), phase)
        if s2 != sig:
            sig = s2; t_fige = time.time()
        elif time.time() - t_fige > 420:
            print("[ABORT] enlisement", flush=True); break
        if losses(env) > 0.75:
            print("[ABORT] pertes > 75%", flush=True); break
    dump(env, op, step, phase, breach)
    blu = sum(int(env.alive(si).sum()) for si in range(env.S)); opf = int(env.en_alive().sum())
    print("\n>>> PERCEE %s | axe %s | objectif %s | BLUFOR %d/150 (pertes %.0f%%) | OPFOR %d/150 | pas %d"
          % ("REUSSIE" if succes else "ECHEC", axe, "PRIS" if succes else "non pris", blu, 100 * losses(env), opf, step), flush=True)
    print("BREACH FINI", flush=True)
