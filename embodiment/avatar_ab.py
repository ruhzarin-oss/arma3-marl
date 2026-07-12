"""avatar_ab — TEST CONTRÔLÉ mémoire→comportement. Même scénario, deux agents :
  mode 'mem'   : utilise la mémoire épisodique -> se souvient d'un contact hors de vue et ne fonce pas dessus.
  mode 'nomem' : aucune mémoire -> dès que le contact sort du champ, il l'oublie et avance en aveugle.
Métrique : AVANCES AVEUGLES (avancer alors qu'un ennemi RÉEL est devant, à portée, mais non vu) + dégâts encaissés.
args: mode server_idx seed cycles."""
import time, re, sys, math
import numpy as np, torch
import torch.nn as nn
torch.backends.cudnn.enabled = False
sys.path.insert(0, "/home/younes/arma3-marl")
from op_arma import OpArma
from memory_system import MemorySystem, ProceduralMemory
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
MODE = sys.argv[1] if len(sys.argv) > 1 else "mem"
SRV = int(sys.argv[2]) if len(sys.argv) > 2 else 7
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 77
CYCLES = int(sys.argv[4]) if len(sys.argv) > 4 else 260
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)
SCALE = 140.0; N_EN = 3; THREAT_R = 90.0


class RecurrentBrain(nn.Module):
    def __init__(self, o=14, a=4, h=128):
        super().__init__(); self.gru = nn.GRU(o, h, batch_first=True); self.head = nn.Linear(h, a)
    def step(self, x, h=None):
        out, h = self.gru(x.unsqueeze(1), h); return self.head(out.squeeze(1)), h


brain = RecurrentBrain().to(DEV)
brain.load_state_dict(torch.load("/home/younes/arma3-marl/koth_lambs_gru14.pt", map_location=DEV)); brain.eval()
env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SRV,
             log=SB + "/logs/server%d.out" % SRV, acc=1.0, seed=SEED)
start = (OBJ[0] + 8, OBJ[1] - 60)
env.spawn({"AV": start}, [(OBJ[0], OBJ[1], N_EN, 13)])
env.b.send('private _g = group (AV select 0); while {count waypoints _g > 0} do {deleteWaypoint [_g, 0]};'
           '{ _x setVariable ["lambs_danger_disableGroupAI", true]; _x allowFleeing 0; } forEach units _g;'
           '_g setBehaviour "AWARE"; _g setCombatMode "YELLOW"; _g setSpeedMode "NORMAL";'
           '{ _x enableAI "ALL"; _x enableAI "TARGET"; _x enableAI "AUTOTARGET"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setUnitPos "AUTO"; _x setSkill 0.6; _x reveal (AV select 0); } forEach HMT_EN;', wait=True)
time.sleep(2)
mem = MemorySystem(14, OBJ, plan=[("rejoindre", OBJ), ("tenir", OBJ)]); proc = ProceduralMemory()
gx, gy = OBJ
px, py, dmg, sup, fat, pos_stance, last_act = start[0], start[1], 0.0, 0.0, 0.0, "STAND", -1
t0 = time.time(); blind = 0; engaged_from_mem = 0; dmg0 = 0.0


def ahead(ex, ey):
    return (ex - px) * (gx - px) + (ey - py) * (gy - py) > 0     # l'ennemi est du côté de l'objectif


print("=== A/B mémoire→comportement : MODE=%s (server%d) ===" % (MODE, SRV), flush=True)
for c in range(CYCLES):
    ls = env._query('private _u = AV select 0; private _p = getPosATL _u;'
                    ' diag_log format ["AV %1 %2 %3 %4 %5", round(_p#0), round(_p#1), stance _u, round((getDammage _u)*100), round((getSuppression _u)*100)];'
                    ' { private _e = HMT_EN select _forEachIndex; private _q = getPosATL _e; private _vis = 0;'
                    '   if (alive _e && {(_u distance _e) < 110} && {(count (lineIntersectsSurfaces [eyePos _u, eyePos _e, _u, _e])) == 0}) then { _vis = 1; };'
                    '   diag_log format ["EN %1 %2 %3 %4 %5", _forEachIndex, round(_q#0), round(_q#1), round((getDammage _e)*100), _vis]; } forEach HMT_EN;'
                    ' diag_log "SENSEND";', settle=0.08)
    contacts = []
    for l in ls:
        m = re.search(r"AV (-?\d+) (-?\d+) (\w+) (\d+) (\d+)", l)
        if m:
            px = int(m.group(1)); py = int(m.group(2)); pos_stance = m.group(3); dmg = int(m.group(4)) / 100.0; sup = int(m.group(5)) / 100.0
        me = re.search(r"EN (\d+) (-?\d+) (-?\d+) (\d+) (\d+)", l)
        if me:
            contacts.append((int(me.group(1)), int(me.group(2)), int(me.group(3)), int(me.group(4)), int(me.group(5)) == 1))
    if not contacts:
        time.sleep(0.05); continue
    now = time.time() - t0
    mem.update(np.zeros(14, np.float32), (px, py), contacts, now)
    # VÉRITÉ TERRAIN : une menace réelle est-elle devant, à portée, NON vue ? (juge commun aux 2 modes)
    gt_threat = None
    for cid, x, y, d, vis in contacts:
        if d < 70 and not vis and ahead(x, y) and math.hypot(x - px, y - py) < THREAT_R:
            gt_threat = (x, y); break
    seen_list = [(x, y) for cid, x, y, d, vis in contacts if vis and d < 70]
    seen = min(seen_list, key=lambda p: (p[0] - px) ** 2 + (p[1] - py) ** 2) if seen_list else None
    remembered = mem.episodique.nearest(now, px, py) if MODE == "mem" else None   # ← la mémoire n'existe QU'en mode mem
    o = [(px - gx) / SCALE, (py - gy) / SCALE, (gx - px) / SCALE, (gy - py) / SCALE, 1.0, 0.0, 0.0,
         (seen[0] - px) / SCALE if seen else 0.0, (seen[1] - py) / SCALE if seen else 0.0, sup, fat,
         {"STAND": 0, "CROUCH": .5, "PRONE": 1}.get(pos_stance, 0),
         (remembered["x"] - px) / SCALE if remembered else 0.0, (remembered["y"] - py) / SCALE if remembered else 0.0]
    with torch.no_grad():
        logits, mem.travail.h = brain.step(torch.tensor([o], dtype=torch.float32, device=DEV), mem.travail.h)
        a = int(logits.argmax(1).item())
    engaged = (seen is not None) or sup > 0.3
    if not engaged:
        a = 1
    # COUPLAGE MÉMOIRE→COMPORTEMENT : si on se souvient d'une menace devant (hors vue), ne pas foncer -> la suppresser
    cible = seen
    if MODE == "mem" and a == 1 and seen is None and remembered is not None:
        rx, ry = remembered["x"], remembered["y"]
        if remembered["conf"] > 0.3 and ahead(rx, ry) and math.hypot(rx - px, ry - py) < THREAT_R:
            a = 2; cible = (rx, ry); engaged_from_mem += 1
    # MÉTRIQUE commune : avancer alors qu'une menace réelle est devant et non vue = AVANCE AVEUGLE
    if a == 1 and gt_threat is not None:
        blind += 1
    if a == 1 and last_act == 1 and c % 10 != 0:
        pass
    else:
        env.b.send(proc.commande("(AV select 0)", a, OBJ, cible), wait=True)
    last_act = a
    if c % 8 == 0:
        do = math.hypot(gx - px, gy - py)
        print("  t=%4.1fs|obj %3.0fm|vie %3.0f%%|menace_devant=%s|avances_aveugles=%d|prudence_mémoire=%d|->%s" % (
            now, do, dmg * 100, "OUI" if gt_threat else "non", blind, engaged_from_mem, proc.ACTIONS[a]), flush=True)
print(">>> MODE=%s | avances_aveugles=%d | prudence_par_mémoire=%d | vie_finale=%.0f%% | dégâts_pris=%.0f%%" % (
    MODE, blind, engaged_from_mem, dmg * 100, dmg * 100), flush=True)
print("AB FINI", flush=True)
