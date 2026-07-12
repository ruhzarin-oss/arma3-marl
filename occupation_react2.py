#!/usr/bin/env python3
"""occupation_react2.py — MOTEUR D'ALERTE pilote par Python (robuste : requetes discretes via le pont).
Spawne garnison + QRF nommee + contact BLUFOR ; boucle Python : detecte (knowsAbout), monte l'alerte,
dispatche la QRF vers le contact, suit la distance. Mesure le delai de reaction. Env : SLOT(2)."""
import os, sys, time, subprocess, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge

SB = "/mnt/data/harmattan-sandbox"; SLOT = int(os.environ.get("SLOT", 2)); PORT = 2402 + SLOT * 100
MIS = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SLOT
LOG = SB + "/logs/server%d.out" % SLOT
GX, GY = 20885, 16959; HX, HY = GX + 1100, GY + 1100

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

def query_num(b, sqf, tag):
    """envoie un SQF qui logge HARMATTAN_<tag> <nombre> (send attend le RECV), puis lit le log."""
    try: b.send(sqf, timeout=12)
    except Exception: return None
    time.sleep(0.5)
    for ln in reversed(b._log_lines(300)):
        m = re.search(r"HARMATTAN_%s ([\-\d.]+)" % tag, ln)
        if m: return float(m.group(1))
    return None

def wait_ready(b, tries=18):
    """handshake : l'actuateur natif execute-t-il nos cmd ? (les 1ers envois post-boot sont perdus sinon)"""
    for i in range(tries):
        if query_num(b, 'diag_log format ["HARMATTAN_PING %1", 1];', "PING") == 1.0: return True
        time.sleep(2)
    return False
def east_count(b): return query_num(b, 'diag_log format ["HARMATTAN_EC %1", count (allUnits select {side _x==east})];', "EC")
def west_count(b): return query_num(b, 'diag_log format ["HARMATTAN_WC %1", count (allUnits select {side _x==west})];', "WC")

def main():
    print("=== MOTEUR D'ALERTE (pilote Python) | slot=%d ===" % SLOT, flush=True)
    launch_server(); print("[%s] boot..." % time.strftime("%H:%M"), flush=True)
    if not wait_boot(): print("ECHEC boot", flush=True); return
    b = ArmaBridge(mission=MIS, log=LOG)
    if not wait_ready(b): print("ECHEC handshake actuateur", flush=True); return
    print("[%s] actuateur pret (handshake ok)." % time.strftime("%H:%M"), flush=True)
    # garnison + QRF en UN seul envoi (batch = fiable), avec verification + retry
    spawn = ('HMT_GARR = createGroup east; for "_a" from 1 to 20 do { HMT_GARR createUnit ["O_Soldier_F", [%d+(random 30)-15, %d+(random 30)-15, 0], [], 0, "FORM"]; }; {_x setSkill 0.7; _x setBehaviour "AWARE"} forEach units HMT_GARR; [HMT_GARR,[%d,%d],120] call BIS_fnc_taskPatrol; '
             'HMT_QRF = createGroup east; for "_a" from 1 to 14 do { HMT_QRF createUnit ["O_Soldier_F", [%d+(random 30)-15, %d+(random 30)-15, 0], [], 0, "FORM"]; }; {_x setSkill 0.7; _x setBehaviour "AWARE"} forEach units HMT_QRF;' % (GX, GY, GX, GY, HX, HY))
    ec = 0
    for attempt in range(3):
        b.send(spawn, timeout=20); time.sleep(4)
        ec = east_count(b) or 0
        print("[%s] spawn garnison+QRF (essai %d) -> east=%d" % (time.strftime("%H:%M"), attempt + 1, ec), flush=True)
        if ec >= 30: break
    if ec < 30: print("[%s] ECHEC spawn east (%d). Abandon." % (time.strftime("%H:%M"), ec), flush=True); return
    print("[%s] garnison+QRF en place (east=%d). Repos 10s..." % (time.strftime("%H:%M"), ec), flush=True)
    time.sleep(10)
    # contact BLUFOR qui avance vers la garnison (+ verif)
    contact = 'HMT_CT = createGroup west; for "_a" from 1 to 6 do { HMT_CT createUnit ["B_Soldier_F", [%d+(random 20)-10, %d+(random 20)-10, 0], [], 0, "FORM"]; }; {_x setSkill 0.6; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setSpeedMode "FULL"} forEach units HMT_CT; HMT_CT setCombatMode "RED"; (units HMT_CT) doMove [%d,%d];' % (GX - 110, GY - 110, GX, GY)
    wc = 0
    for attempt in range(3):
        b.send(contact, timeout=20); time.sleep(3)
        wc = west_count(b) or 0
        if wc >= 5: break
    print("[%s] contact west=%d" % (time.strftime("%H:%M"), wc), flush=True)
    t0 = time.time(); print("[%s] >>> CONTACT BLUFOR injecte (avance vers la garnison)." % time.strftime("%H:%M"), flush=True)
    alert = 0.0; dispatched = None
    for k in range(20):                                                  # ~100s
        time.sleep(5)
        kk = query_num(b, 'private _k=0; { private _e=_x; { _k=_k max (_e knowsAbout _x) } forEach (allUnits select {side _x==west}) } forEach (allUnits select {side _x==east && alive _x}); diag_log format ["HARMATTAN_K %1", round(_k*10)/10];', "K")
        if kk is None: continue
        if kk > 1.0:
            alert = min(3.0, alert + 1.0)
            if dispatched is None:
                b.send('{ _x doMove (getPosATL (leader HMT_CT)) } forEach (units HMT_QRF); HMT_QRF setBehaviour "COMBAT";')
                dispatched = time.time() - t0
                print("[%s]   >>> QRF DISPATCHEE a t+%.0fs (alerte montee)" % (time.strftime("%H:%M"), dispatched), flush=True)
        else:
            alert = max(0.0, alert - 0.4)
        qd = query_num(b, 'diag_log format ["HARMATTAN_QD %1", round((leader HMT_QRF) distance (leader HMT_CT))];', "QD")
        print("[%s] knowsAbout=%.1f alerte=%.1f qrf_dist=%sm" % (time.strftime("%H:%M"), kk, alert, int(qd) if qd is not None else "?"), flush=True)
        if dispatched and qd is not None and qd < 120: print("[%s]   >>> QRF AU CONTACT (%dm)" % (time.strftime("%H:%M"), qd), flush=True); break
    print("\n=== RESULTAT REACTIVITE ===", flush=True)
    print("Detection : %s | QRF dispatchee a : %s | alerte max : %.1f/3" % (
        "oui" if dispatched else "non", ("t+%.0fs" % dispatched) if dispatched else "jamais", alert), flush=True)
    print("REACT2_DONE", flush=True)

if __name__ == "__main__":
    main()
