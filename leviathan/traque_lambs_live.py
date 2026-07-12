#!/usr/bin/env python3
"""traque_lambs_live.py — BENCHMARK : une escouade de 9 FS pilotee par LE VRAI LAMBS (IA complete, le mod gere
couvert/suppression/manoeuvre) vs notre escouade APPRISE (traque_reflex_live, bounding 4/9 coerc10). Memes noeuds,
memes 44 defenseurs. Ici Python ne PILOTE PAS : il donne les objectifs (doMove vers noeud disperse) et LAISSE LAMBS jouer,
puis surveille survie + sabote sur proximite + mesure. Reponse a la question de depart : notre soldat appris vaut-il le mod ?"""
import sys, time, re, math, ast
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from arma_bridge import ArmaBridge
from island_stratis import NODES
from traque_env import TraqueEnv

SB = "/mnt/data/harmattan-sandbox"; MIS = SB + "/arma3server/mpmissions/HarmattanBridge14.Stratis"; LOG = SB + "/logs/server14.out"
N_FS = 9; STEPS = 120; INS = (5250, 3050)
NODECLASS = {"hq": "Land_Cargo_HQ_V1_F", "radar": "Land_Radar_01_HQ_F", "comms": "Land_TTowerBig_1_F"}
DEFAULT_NODE = "Land_Cargo20_military_green_F"


def q(b, sqf, tag, settle=0.6, look=600):
    b.send(sqf); time.sleep(settle)
    for ln in reversed(b._log_lines(look)):
        m = re.search(r"HARMATTAN_%s (.+)$" % tag, ln)
        if m: return m.group(1).strip().rstrip('"')
    return None


def parr(s):
    try: return ast.literal_eval(s)
    except Exception: return None


def main():
    b = ArmaBridge(mission=MIS, log=LOG); time.sleep(2)
    for _ in range(15):
        b.send('diag_log format ["HARMATTAN_PING %1",1];'); time.sleep(0.4)
        if any("HARMATTAN_PING 1" in l for l in b._log_lines(120)): print("[pont] OK", flush=True); break
        time.sleep(1.2)
    nodes_sqf = ""
    for i, (nm, x, y, t) in enumerate(NODES):
        nodes_sqf += 'HMT_NODES set [%d, (createVehicle ["%s",[%d,%d,0],[],0,"CAN_COLLIDE"])];\n' % (i, NODECLASS.get(t, DEFAULT_NODE), x, y)
    # FS gardent leur IA COMPLETE -> LAMBS les pilote (pas de disableAI, pas de setVelocity)
    spawn = ('[] spawn {\n{deleteVehicle _x} forEach allUnits;\n'
             'if (!isNil "HMT_NODES") then {{deleteVehicle _x} forEach HMT_NODES};\nHMT_NODES = []; HMT_NODES resize %d;\n%s'
             'HMT_G = createGroup west; HMT_FS = [];\n'
             'for "_i" from 0 to %d do { private _u = HMT_G createUnit ["B_recon_F",[%d + (_i %% 3)*70 - 70, %d + (floor(_i/3))*45, 0],[],0,"FORM"]; '
             '_u setSkill 0.85; _u setBehaviour "AWARE"; _u setCombatMode "RED"; _u setUnitPos "UP"; _u setSpeedMode "FULL"; _u forceSpeed 6; HMT_FS pushBack _u; };\n'
             'HMT_DEF = createGroup east;\n'
             '{ private _n=_x; for "_k" from 0 to 1 do { private _d=HMT_DEF createUnit ["O_Soldier_F",[(getPos _n)#0+(random 60)-30,(getPos _n)#1+(random 60)-30,0],[],0,"FORM"]; _d setSkill 0.55; _d setBehaviour "AWARE"; }; } forEach HMT_NODES;\n'
             '};') % (len(NODES), nodes_sqf, N_FS - 1, INS[0], INS[1])
    b.send(spawn, timeout=30); time.sleep(8)
    print("[spawn]", q(b, 'diag_log format ["HARMATTAN_SP %1 %2 %3", count HMT_FS, count (allUnits select {side _x==east && alive _x}), count (HMT_NODES select {!isNull _x})];', "SP", 1.0), flush=True)
    npos = [(x, y) for _, x, y, _ in NODES]; dead = set(); coercion = 0.0
    e = TraqueEnv(num_envs=1, device="cpu", n_fs=N_FS, relief=True); nw = e.nw.tolist()
    print("=== BENCHMARK LAMBS (le mod pilote — regarde au spectateur) ===", flush=True)
    for step in range(STEPS):
        st = q(b, 'private _sf=HMT_FS apply {[round((getposatl _x)#0),round((getposatl _x)#1),[0,1] select (alive _x)]}; '
                  'private _nd=HMT_NODES apply {[0,1] select (!isNull _x)}; '
                  'diag_log format ["HARMATTAN_LX %1#%2", _sf, _nd];', "LX", 0.6, 600)
        if not st: time.sleep(1); continue
        p = st.split("#"); sf = parr(p[0]); nd = parr(p[1]) if len(p) > 1 else []
        if not sf or not nd or len(sf) < N_FS: time.sleep(1); continue
        for ti in dead:
            if ti < len(nd): nd[ti] = 0
        # COMMANDANT : assigne un noeud disperse a chaque FS, et (re)donne l'ordre -> LAMBS execute le combat
        alive_nodes = [j for j in range(len(npos)) if nd[j] == 1]; taken = set(); cmds = []
        for i in range(N_FS):
            if sf[i][2] == 0: continue
            cands = [j for j in alive_nodes if j not in taken] or alive_nodes
            if not cands: continue
            tj = min(cands, key=lambda j: math.hypot(sf[i][0] - npos[j][0], sf[i][1] - npos[j][1])); taken.add(tj)
            if step % 4 == 0:                                              # re-ordonne toutes les 4 etapes (laisse LAMBS jouer entre)
                cmds.append('(HMT_FS select %d) doMove [%d,%d,0];' % (i, npos[tj][0], npos[tj][1]))
        # SABOTAGE sur proximite (meme regle que notre escouade)
        sab = 0
        for i in range(N_FS):
            if sf[i][2] == 0: continue
            for ti in range(len(npos)):
                if nd[ti] == 1 and ti not in dead and math.hypot(sf[i][0] - npos[ti][0], sf[i][1] - npos[ti][1]) < 60:
                    cmds.append('deleteVehicle (HMT_NODES select %d);' % ti); coercion += nw[ti]; dead.add(ti); nd[ti] = 0; sab += 1
        if cmds: b.send("[] spawn {" + "; ".join(cmds) + ";};", timeout=20)
        nalive = sum(a[2] for a in sf)
        print("  [%02d] FS %d/9 | noeuds %d/22 | coercion %.0f" % (step, nalive, sum(nd), coercion), flush=True)
        if nalive == 0: break
        time.sleep(1.0)
    print("=== FIN LAMBS | survie %d/9 | coercion %.0f/88 ===" % (sum(a[2] for a in sf), coercion), flush=True)


if __name__ == "__main__":
    main()
