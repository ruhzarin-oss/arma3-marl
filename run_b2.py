#!/usr/bin/env python3
import sys, os, time, subprocess, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
from banc_live import SCENE, sans_commentaires
import arma_couture as C
SB = "/mnt/data/harmattan-sandbox"; EXT, PORT = 5830, 6062
LOG = SB + "/logs/serverB2.out"
def sh(c): subprocess.run(c, shell=True, executable="/bin/bash")
if __name__ == "__main__":
    C.CX, C.CY = 4644.0, 5652.0; C.SCALE = 200.0
    open(LOG, "w").close()
    sh("for p in $(pgrep -f arma3server_x64); do kill $p; done"); time.sleep(4)
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverLV.cfg' -profiles='%s/profilesLV' "
       "-port=%d -world=Stratis -autoInit "
       "-mod='@CBA_A3;@rhsusaf;@rhsafrf;@LAMBS_Danger;@PinnedDown_BattleLines;@PinnedDown_CoverConcealment' "
       ">> '%s' 2>&1 < /dev/null & disown" % (SB, EXT, SB, SB, PORT, LOG))
    time.sleep(45)
    b = SocketBridge(EXT); time.sleep(3)
    b.send(sans_commentaires(SCENE), wait=False); time.sleep(6)
    b.send('call compile preprocessFileLineNumbers "socle.sqf";', wait=False); time.sleep(3)
    b.send('call compile preprocessFileLineNumbers "b2.sqf";', wait=False); time.sleep(3)
    b.send('HMT_B2R = nil; [] spawn { HMT_B2R = [8] call HMT_B2; };', wait=False)
    print("  B2 lance — 2x2 reveal x comportement, 8 par condition", flush=True)
    t0 = time.time(); vu = 0
    while time.time() - t0 < 1500:
        time.sleep(15)
        try: txt = open(LOG, errors="ignore").read()
        except Exception: txt = ""
        n = txt.count("HMT|B2|reveal|")
        if n != vu: print("    %d essais" % n, flush=True); vu = n
        if "HMT|B2|FINI" in txt or "HMT|B2|ECHEC" in txt: break
    sh("for p in $(pgrep -f arma3server_x64); do kill $p; done")
    L = [l for l in open(LOG, errors="ignore") if "HMT|B2|reveal|" in l]
    D = {}
    for l in L:
        p = [x.strip().strip('"') for x in l[l.index("HMT|B2|"):].split("|")]
        d = dict(zip(p[2::2], p[3::2]))
        D.setdefault((d["reveal"], d["comp"]), []).append(int(d["coups"]))
    med = lambda v: sorted(v)[len(v)//2]
    print("\n  reveal  comportement   n   coups (mediane)   min-max   zeros")
    for k in sorted(D):
        v = D[k]
        print("  %-7s %-12s %2d   %8d        %d-%d      %d/%d"
              % (k[0], k[1], len(v), med(v), min(v), max(v), sum(1 for x in v if x == 0), len(v)))
    if len(D) == 4 and min(len(v) for v in D.values()) >= 8:
        g = lambda r, c: med(D[(r, c)])
        av = g("true","COMBAT") >= 1 and g("true","AWARE") >= 1
        sa = g("false","COMBAT") == 0 and g("false","AWARE") == 0
        print("\n  ── LE VERDICT, SUR LES CRITERES ECRITS AVANT ──")
        if av and sa:
            print("  ⛔ LE `reveal` EST NECESSAIRE — sans lui, ZERO coup dans les deux comportements.")
            print("     T7 CERTIFIE UN CANAL QUE LA POLITIQUE N EMPRUNTE PAS : la couture ne reveal jamais.")
        elif g("false","COMBAT") >= 1 or g("false","AWARE") >= 1:
            print("  ✓ LE `reveal` EST INUTILE — l homme tire sans qu on lui donne la cible.")
        else:
            print("  ⚠️ resultat mixte — on ne conclut pas.")
        ec = abs(g("true","AWARE") - g("true","COMBAT"))
        print("  ecart AWARE/COMBAT a reveal actif : %d coups" % ec)
    else:
        print("\n  ⛔ n insuffisant — le critere ne se lit pas.")
