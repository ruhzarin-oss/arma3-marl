#!/usr/bin/env python3
"""occupation_react.py — TEST DU MOTEUR D'ALERTE (cœur du realisme, §4).
Spawne 1 secteur (garnison + QRF nommee + relais), injecte le moteur d'alerte (FSM server-side),
injecte un CONTACT BLUFOR, et observe la chaine : contact -> alerte monte -> QRF dispatchee -> se rapproche.
Mesure le delai de reaction. Env : SLOT(2)."""
import os, sys, time, subprocess, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge

SB = "/mnt/data/harmattan-sandbox"; SLOT = int(os.environ.get("SLOT", 2)); PORT = 2402 + SLOT * 100
MIS = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SLOT
LOG = SB + "/logs/server%d.out" % SLOT
GX, GY = 20885, 16959                 # Paros (une garnison)
HX, HY = GX + 1200, GY + 1200         # QG/QRF a ~1.7km

def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True)
def launch_server():
    sh("pkill -9 -f 'profiles%d'" % SLOT); time.sleep(3)
    sh("rm -rf '%s'; cp -r '%s/arma3server/mpmissions/HarmattanBridge.Altis' '%s'" % (MIS, SB, MIS))
    sh("rm -f '%s/hmt_bridge/'cmd_*.sqf" % MIS)
    sh("sed 's/HarmattanBridge\\.Altis/HarmattanBridge%d.Altis/g' '%s/staging/server.cfg' > '%s/staging/server%d.cfg'" % (SLOT, SB, SB, SLOT))
    sh("mkdir -p '%s/profiles%d'; : > '%s'" % (SB, SLOT, LOG))
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid ./arma3server_x64 -config='%s/staging/server%d.cfg' -profiles='%s/profiles%d' -port=%d -world=Altis -autoInit >> '%s' 2>&1 < /dev/null & disown" % (SB, 5801 + SLOT, SB, SLOT, SB, SLOT, PORT, LOG))
def wait_boot(t=200):
    t0 = time.time()
    while time.time() - t0 < t:
        try:
            if "Starting mission" in open(LOG, encoding="utf-8", errors="ignore").read(): time.sleep(10); return True
        except FileNotFoundError: pass
        time.sleep(4)
    return False

# --- moteur d'alerte (FSM server-side) : contact -> alerte -> dispatch QRF -> log ---
ALERT_ENGINE = (
'HMT_QRF_SENT = false;\n'
'[] spawn {\n'
'  while {true} do {\n'
'    private _contact = objNull;\n'
'    private _wests = allUnits select {(side _x == west) && (alive _x)};\n'
'    {\n'
'      private _e = _x;\n'
'      { if (_e knowsAbout _x > 1.4) exitWith { _contact = _x; }; } forEach _wests;\n'
'      if (!isNull _contact) exitWith {};\n'
'    } forEach (allUnits select {(side _x == east) && (alive _x)});\n'
'    private _al = missionNamespace getVariable ["HMT_ALERT", 0];\n'
'    if (!isNull _contact) then {\n'
'      _al = (_al + 1) min 3;\n'
'      if ((!HMT_QRF_SENT) && (!isNull HMT_QRF)) then { HMT_QRF_SENT = true; { _x doMove (getPosATL _contact) } forEach (units HMT_QRF); diag_log format ["HARMATTAN_QRF DISPATCH vers %1", mapGridPosition (getPosATL _contact)]; };\n'
'    } else { _al = (_al - 0.4) max 0; };\n'
'    missionNamespace setVariable ["HMT_ALERT", _al];\n'
'    private _qd = if ((!isNull HMT_QRF) && (!isNull _contact)) then { round ((leader HMT_QRF) distance _contact) } else { -1 };\n'
'    diag_log format ["HARMATTAN_ALERT niveau=%1 contact=%2 qrf_dist=%3", round(_al*10)/10, (!isNull _contact), _qd];\n'
'    sleep 4;\n'
'  };\n'
'};\n')

def grp_east(x, y, n, name=None, patrol=True):
    g = ("%s = createGroup east;\n" % name) if name else "private _g = createGroup east;\n"
    ref = name if name else "_g"
    s = g + 'for "_a" from 1 to %d do { %s createUnit ["O_Soldier_F", [%d+(random 30)-15, %d+(random 30)-15, 0], [], 0, "FORM"]; };\n' % (n, ref, x, y)
    s += '{_x setSkill 0.6; _x setBehaviour "AWARE"; _x allowFleeing 0} forEach units %s;\n' % ref
    if patrol: s += '[%s, [%d,%d], 120] call BIS_fnc_taskPatrol;\n' % (ref, x, y)
    return s

def grp_west(x, y, n):
    s = 'HMT_CONTACT = createGroup west;\n'
    s += 'for "_a" from 1 to %d do { HMT_CONTACT createUnit ["B_Soldier_F", [%d+(random 20)-10, %d+(random 20)-10, 0], [], 0, "FORM"]; };\n' % (n, x, y)
    s += '{_x setSkill 0.6; _x setBehaviour "COMBAT"} forEach units HMT_CONTACT;\n'
    s += '(units HMT_CONTACT) doMove [%d,%d];\n' % (GX, GY)   # avance vers la garnison
    return s

def main():
    print("=== TEST MOTEUR D'ALERTE | slot=%d ===" % SLOT, flush=True)
    launch_server(); print("[%s] boot..." % time.strftime("%H:%M"), flush=True)
    if not wait_boot(): print("ECHEC boot", flush=True); return
    b = ArmaBridge(mission=MIS, log=LOG); time.sleep(3)
    b.send(grp_east(GX, GY, 20, name=None, patrol=True))                 # garnison Paros
    b.send(grp_east(HX, HY, 14, name="HMT_QRF", patrol=False))           # QRF (idle au QG)
    b.send(ALERT_ENGINE)                                                 # moteur d'alerte
    print("[%s] garnison + QRF + moteur d'alerte en place. Etat de repos 12s..." % time.strftime("%H:%M"), flush=True)
    time.sleep(12)
    t_inject = time.time()
    b.send(grp_west(GX - 250, GY - 250, 6))                              # CONTACT BLUFOR a ~350m, avance
    print("[%s] >>> CONTACT BLUFOR injecte. Observation de la chaine..." % time.strftime("%H:%M"), flush=True)
    seen_dispatch = None; alerts = []
    for k in range(22):                                                  # ~90s d'observation
        time.sleep(4)
        lines = b._log_lines(400)
        for ln in lines[-12:]:
            m = re.search(r"HARMATTAN_ALERT niveau=([\d.]+) contact=(\w+) qrf_dist=(-?\d+)", ln)
            if m: alerts.append((float(m.group(1)), m.group(2), int(m.group(3))))
            if "HARMATTAN_QRF DISPATCH" in ln and seen_dispatch is None:
                seen_dispatch = time.time() - t_inject
        if alerts:
            a = alerts[-1]
            print("[%s] alerte=%.1f contact=%s qrf_dist=%sm%s" % (time.strftime("%H:%M"), a[0], a[1], a[2], (" | QRF DISPATCHEE a t+%.0fs" % seen_dispatch) if seen_dispatch else ""), flush=True)
        if seen_dispatch and alerts and alerts[-1][2] != -1 and alerts[-1][2] < 120: break   # QRF arrivee
    print("\n=== RESULTAT REACTIVITE ===", flush=True)
    if seen_dispatch: print("Delai contact -> QRF dispatchee : %.0f s" % seen_dispatch, flush=True)
    else: print("QRF non dispatchee (pas de contact detecte ?)", flush=True)
    if alerts:
        amax = max(a[0] for a in alerts); dmin = min((a[2] for a in alerts if a[2] >= 0), default=-1)
        print("Alerte max atteinte : %.1f / 3 | distance QRF-contact min : %sm" % (amax, dmin), flush=True)
    print("REACT_DONE", flush=True)

if __name__ == "__main__":
    main()
