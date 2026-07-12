"""avatar_brain — l'avatar incarné piloté par le SYSTÈME DE MÉMOIRES complet (les 7 types en action, en live).
Démonstration clé : la mémoire ÉPISODIQUE retient les contacts sortis du champ de vue (l'agent ne les 'oublie'
plus). Le cerveau de travail (GRU) décide ; la procédurale exécute ; la spatiale cartographie ; la prospective
suit le plan. args: server_idx seed cycles."""
import time, re, sys, math
import numpy as np, torch
import torch.nn as nn
torch.backends.cudnn.enabled = False
sys.path.insert(0, "/home/younes/arma3-marl")
from op_arma import OpArma
from memory_system import MemorySystem, ProceduralMemory
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
SRV = int(sys.argv[1]) if len(sys.argv) > 1 else 6
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 71
CYCLES = int(sys.argv[3]) if len(sys.argv) > 3 else 300
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)
SCALE, SIGHT = 140.0, 110.0
STANCE = {"STAND": 0.0, "CROUCH": 0.5, "PRONE": 1.0}
N_EN = 3


class RecurrentBrain(nn.Module):
    def __init__(self, obs_dim=14, n_act=4, hidden=128):
        super().__init__(); self.gru = nn.GRU(obs_dim, hidden, batch_first=True); self.head = nn.Linear(hidden, n_act)
    def step(self, x1, h=None):
        out, h = self.gru(x1.unsqueeze(1), h); return self.head(out.squeeze(1)), h


brain = RecurrentBrain(14, 4, 128).to(DEV)
brain.load_state_dict(torch.load("/home/younes/arma3-marl/koth_lambs_gru14.pt", map_location=DEV)); brain.eval()
env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SRV,
             log=SB + "/logs/server%d.out" % SRV, acc=1.0, seed=SEED)
start = (OBJ[0] + 10, OBJ[1] - 70)
env.spawn({"AV": start}, [(OBJ[0], OBJ[1], N_EN, 14)])
env.b.send('private _g = group (AV select 0); while {count waypoints _g > 0} do {deleteWaypoint [_g, 0]};'
           '{ _x setVariable ["lambs_danger_disableGroupAI", true]; _x allowFleeing 0; } forEach units _g;'
           '_g setBehaviour "AWARE"; _g setCombatMode "YELLOW"; _g setSpeedMode "NORMAL";'
           '{ _x enableAI "ALL"; _x enableAI "TARGET"; _x enableAI "AUTOTARGET"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setUnitPos "AUTO"; _x setSkill 0.5; _x reveal (AV select 0); } forEach HMT_EN;', wait=True)
time.sleep(2)
mem = MemorySystem(14, OBJ, plan=[("rejoindre", OBJ), ("tenir", OBJ)])
proc = ProceduralMemory()
print("=== AVATAR + SYSTÈME DE MÉMOIRES (7 types en live) — server%d ===" % SRV, flush=True)
gx, gy = OBJ
px, py, dmg, sup, fat = start[0], start[1], 0.0, 0.0, 0.0
pos_stance = "STAND"; last_act = -1; t0 = time.time(); prev_vis = {}
for c in range(CYCLES):
    ls = env._query('private _u = AV select 0; private _p = getPosATL _u;'
                    ' diag_log format ["AV %1 %2 %3 %4 %5 %6", round(_p#0), round(_p#1), stance _u, round((getDammage _u)*100), round((getSuppression _u)*100), round((getFatigue _u)*100)];'
                    ' { private _e = HMT_EN select _forEachIndex; private _q = getPosATL _e; private _vis = 0;'
                    '   if (alive _e && {(_u distance _e) < 110} && {(count (lineIntersectsSurfaces [eyePos _u, eyePos _e, _u, _e])) == 0}) then { _vis = 1; };'
                    '   diag_log format ["EN %1 %2 %3 %4 %5", _forEachIndex, round(_q#0), round(_q#1), round((getDammage _e)*100), _vis]; } forEach HMT_EN;'
                    ' diag_log "SENSEND";', settle=0.08)
    contacts = []
    for l in ls:
        m = re.search(r"AV (-?\d+) (-?\d+) (\w+) (\d+) (\d+) (\d+)", l)
        if m:
            px = int(m.group(1)); py = int(m.group(2)); pos_stance = m.group(3); dmg = int(m.group(4)) / 100.0
            sup = int(m.group(5)) / 100.0; fat = int(m.group(6)) / 100.0
        me = re.search(r"EN (\d+) (-?\d+) (-?\d+) (\d+) (\d+)", l)
        if me:
            contacts.append((int(me.group(1)), int(me.group(2)), int(me.group(3)), int(me.group(4)), int(me.group(5)) == 1))
    if dmg >= 0.9:
        print("  t=%.0fs : avatar TOMBE." % (time.time() - t0), flush=True); break
    if not contacts:
        time.sleep(0.05); continue
    now = time.time() - t0
    # transitions VU -> DE MÉMOIRE (la démonstration de l'épisodique)
    for cid, x, y, d, vis in contacts:
        if d < 70:
            if prev_vis.get(cid) and not vis:
                print("    » contact #%d : VU → DE MÉMOIRE (l'œil le perd, le souvenir le garde)" % cid, flush=True)
            prev_vis[cid] = vis
    # YEUX (visible) + MÉMOIRE (system update -> rappel épisodique)
    rec = mem.update(np.zeros(14, np.float32), (px, py), contacts, now)   # obs_vec rempli juste après
    vis_contacts = [(x, y) for cid, x, y, d, vis in contacts if vis and d < 70]
    seen = min(vis_contacts, key=lambda p: (p[0] - px) ** 2 + (p[1] - py) ** 2) if vis_contacts else None
    remembered = mem.episodique.nearest(now, px, py)        # ce dont on se SOUVIENT (vu OU non)
    # obs14 : ennemi VISIBLE par les yeux ; ennemi CONNU par la mémoire épisodique (pas par le simulateur)
    o = [(px - gx) / SCALE, (py - gy) / SCALE, (gx - px) / SCALE, (gy - py) / SCALE, 1.0, 0.0, 0.0,
         (seen[0] - px) / SCALE if seen else 0.0, (seen[1] - py) / SCALE if seen else 0.0, sup, fat,
         STANCE.get(pos_stance, 0.0),
         (remembered["x"] - px) / SCALE if remembered else 0.0, (remembered["y"] - py) / SCALE if remembered else 0.0]
    mem.sensorielle.update(o)
    # MÉMOIRE DE TRAVAIL : le GRU avance son état mental h
    with torch.no_grad():
        logits, mem.travail.h = brain.step(torch.tensor([o], dtype=torch.float32, device=DEV), mem.travail.h)
        a = int(logits.argmax(1).item())
    # PROSPECTIVE : on bascule 'rejoindre' -> 'tenir' à l'objectif
    do = math.hypot(gx - px, gy - py)
    intent = mem.prospective.avancer_si(do < mem.semantique.get("rayon_tenue_objectif_m"))
    # intention de commande (sémantique) : avancer tant qu'on n'est pas réellement engagé
    engaged = (seen is not None) or sup > mem.semantique.get("seuil_engagement_sup")
    if not engaged:
        a = 1
    # PROCÉDURALE : exécuter
    cible = seen if seen else ((remembered["x"], remembered["y"]) if remembered else None)
    if a == 1 and last_act == 1 and c % 10 != 0:
        pass                                               # ne pas re-pather en boucle
    else:
        env.b.send(proc.commande("(AV select 0)", a, OBJ, cible), wait=True)
    last_act = a
    if c % 5 == 0:
        st = mem.etat(now, px, py)
        nm = ("souvenir conf=%.2f age=%.0fs" % (st["nearest"]["conf"], st["nearest"]["age"])) if st["nearest"] else "—"
        print("  t=%4.1fs|obj %3.0fm|sup %.2f| ÉPIS: %d connus (%d vus / %d de mémoire) | SPAT danger=%.2f | PROSP=%s | -> %s [%s]" % (
            now, do, sup, st["contacts_connus"], st["contacts_vus"], st["contacts_de_memoire"], st["danger_spatial"],
            intent[0] if intent else "—", proc.ACTIONS[a], nm), flush=True)
print(">>> 7 mémoires actives. contacts en mémoire fin : %d" % len(mem.episodique.recall(time.time() - t0)), flush=True)
print("BRAIN FINI", flush=True)
