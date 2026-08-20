#!/usr/bin/env python3
"""SONDE DU GEL — la collision FABRIQUEE. Pre-inscription PREINSCRIPTION_SONDE_GEL.md.

Le correctif du gel a son EFFET etabli par temoin, pas son CHEMIN : `VERDICT_TU` n a jamais
ete journalise. On ne guette plus une collision fortuite — on la FABRIQUE :
prevol lance, `HMT_PV_GEN` incremente A LA MAIN en plein vol, et le temoin DOIT parler.
⚠️ Regle 16 appliquee au temoin lui-meme : un temoin qu on n a jamais fait crier ne prouve
pas qu il crierait.
"""
import sys, os, time, subprocess, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
from banc_live import SCENE, sans_commentaires
import arma_couture as C

SB = "/mnt/data/harmattan-sandbox"; EXT, PORT = 5836, 6068
LOG = SB + "/logs/serverSGEL.out"
def sh(c): subprocess.run(c, shell=True, executable="/bin/bash")
def tuer(): sh("for p in $(pgrep -f '\\-port=%d'); do kill $p; done" % PORT)

def un_bras(b, collision):
    """Un bras : lance un prevol, provoque (ou non) la collision, lit le temoin."""
    b.send('HMT_PV = nil; '
           'private _att = (missionNamespace getVariable ["HMT_PV_GEN", 0]) + 1; '
           '[_att] spawn { params ["_att"]; '
           '  private _r = [HMT_FR] call HMT_PREVOL; '
           '  if ((missionNamespace getVariable ["HMT_PV_GEN", 0]) == _att) then { HMT_PV = _r } '
           '  else { (format ["HMT|SOCLE|PREVOL|VERDICT_TU|gen|%1|courante|%2|valeur|%3", '
           '                  _att, missionNamespace getVariable ["HMT_PV_GEN", 0], _r]) call HMT_LOG }; '
           '};', wait=False)
    time.sleep(8)
    if collision:
        # ⚠️ LA COLLISION, FABRIQUEE : on perime le prevol EN VOL, sans rien tuer.
        b.send('HMT_PV_GEN = (missionNamespace getVariable ["HMT_PV_GEN", 0]) + 1;', wait=False)
        time.sleep(1)
    t0 = time.time()
    while time.time() - t0 < 220:
        time.sleep(4)
        b.send('diag_log format ["HMT|SG|pv|%1", (if (isNil "HMT_PV") then {"nil"} else {HMT_PV})];', wait=False)
        time.sleep(0.6)
        ls = [L for L in b._log_lines(400) if "HMT|SG|pv|" in L]
        if ls and "nil" not in ls[-1].split("HMT|SG|pv|")[1][:8]:
            return ("depose", ls[-1].split("HMT|SG|pv|")[1].strip()[:12])
        try: txt = open(LOG, errors="ignore").read()
        except Exception: txt = ""
        if txt.count("VERDICT_TU") > un_bras.vus:
            un_bras.vus = txt.count("VERDICT_TU")
            return ("temoin", "VERDICT_TU")
    return ("silence", "220 s")
un_bras.vus = 0

if __name__ == "__main__":
    C.CX, C.CY = 4644.0, 5652.0; C.SCALE = 200.0
    open(LOG, "w").close(); tuer(); time.sleep(3)
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverLV.cfg' -profiles='%s/profilesLV' "
       "-port=%d -world=Stratis -autoInit "
       "-mod='@CBA_A3;@rhsusaf;@rhsafrf;@LAMBS_Danger;@PinnedDown_BattleLines;@PinnedDown_CoverConcealment' "
       ">> '%s' 2>&1 < /dev/null & disown" % (SB, EXT, SB, SB, PORT, LOG))
    time.sleep(45)
    b = SocketBridge(EXT); time.sleep(3)
    b.send('call compile preprocessFileLineNumbers "socle.sqf";', wait=False); time.sleep(3)
    b.send(sans_commentaires(SCENE), wait=False); time.sleep(10)
    v = [L for L in b._log_lines(200) if "HMT|SOCLE|pret|" in L]
    print("  socle : %s" % (v[-1].split("pret|")[1].strip().strip('"') if v else "?"), flush=True)
    res = {"collision": [], "temoin": []}
    for k in range(3):
        r = un_bras(b, True);  res["collision"].append(r); print("  S1 bras %d (collision) : %s %s" % (k+1, r[0], r[1]), flush=True)
    for k in range(3):
        r = un_bras(b, False); res["temoin"].append(r);    print("  S2 bras %d (sans)      : %s %s" % (k+1, r[0], r[1]), flush=True)
    tuer()
    s1 = sum(1 for r in res["collision"] if r[0] == "temoin")
    s2 = sum(1 for r in res["temoin"] if r[0] == "temoin")
    s3 = sum(1 for r in res["collision"] if r[0] != "depose")
    print("\n  ══ LES ATTENTES, ECRITES AVANT ══", flush=True)
    print("  S1  temoin parle sous collision  : %d/3   %s" % (s1, "PASSE" if s1 == 3 else "ECHOUE"), flush=True)
    print("  S2  temoin muet sans collision   : %d/3 cris   %s" % (s2, "PASSE" if s2 == 0 else "ECHOUE"), flush=True)
    print("  S3  verdict perime NON depose    : %d/3   %s" % (s3, "PASSE" if s3 == 3 else "ECHOUE"), flush=True)
    if s1 == 3 and s2 == 0 and s3 == 3:
        print("\n  ✓ LE CHEMIN EST ETABLI : la garde agit par son test, pas par un effet de timing.", flush=True)
    else:
        print("\n  ⛔ LE TEMOIN NE PROUVE PAS SON CHEMIN — le correctif du gel reste NON ETABLI.", flush=True)
