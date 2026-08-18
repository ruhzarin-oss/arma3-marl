#!/usr/bin/env python3
"""Les deux sondes prescrites par Fable : le point maudit, et l homme ne coince."""
import sys, os, time, subprocess, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
from banc_live import SCENE, sans_commentaires
import arma_couture as C
SB = "/mnt/data/harmattan-sandbox"; EXT, PORT = 5830, 6062
LOG = SB + "/logs/serverSONDES.out"
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
    # ⚠️ LE SOCLE AVANT LA SCENE. La scene appelle `HMT_CERTIFIER_POSITIONS`, definie
    # dans le socle : envoyee avant, elle plantait a chaque appel — 38 erreurs par lot,
    # certification a vide, hommes nes NON certifies. Le bloc C n avait jamais tourne.
    b.send('call compile preprocessFileLineNumbers "socle.sqf";', wait=False); time.sleep(3)
    b.send(sans_commentaires(SCENE), wait=False); time.sleep(6)
    # ⚠️ ET LE REVEIL NATIF : le lot 5, ou le point maudit a echoue cinq fois, tournait sous
    # `prevol.py natif`. Une sonde qui ne reveille pas l IA ne reproduit pas ce regime — la
    # porte certifie dans son monde, la sonde doit mesurer dans le meme.
    WAKE_NATIF = ('{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED" } forEach HMT_ENNEMI;\n'
                  '{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED" } forEach HMT_FR;\n')
    b.send(sans_commentaires(WAKE_NATIF), wait=False); time.sleep(2)
    _sc = [L for L in b._log_lines(400) if "HARMATTAN_SCENE" in L]
    print("  scene : %s" % (_sc[-1][-42:] if _sc else "AUCUNE — la sonde ne mesurerait rien"), flush=True)
    if not _sc: sh("for p in $(pgrep -f arma3server_x64); do kill $p; done"); sys.exit(3)
    b.send('call compile preprocessFileLineNumbers "sondes.sqf";', wait=False); time.sleep(3)
    b.send('diag_log format ["HMT|VER|%1", HMT_SOCLE_VERSION];', wait=False); time.sleep(1.2)
    _v = [L for L in b._log_lines(120) if "HMT|VER|" in L]
    print("  socle du monde : %s" % (_v[-1].split("HMT|VER|")[1].strip().strip('"')[:22] if _v else "?"), flush=True)
    b.send('HMT_S = nil; [] spawn { [10] call HMT_SONDE1; HMT_S = [4779, 5922, 10] call HMT_SONDE2; };', wait=False)
    print("  sondes lancees — 3 bras x 10, puis 10 poses", flush=True)
    t0 = time.time(); vu = 0
    while time.time() - t0 < 1800:
        time.sleep(15)
        try: txt = open(LOG, errors="ignore").read()
        except Exception: txt = ""
        n = txt.count("HMT|S1|bras") + txt.count("HMT|S2|k")
        if n != vu: print("    %d releves" % n, flush=True); vu = n
        if "HMT|S2|FINI" in txt: break
    sh("for p in $(pgrep -f arma3server_x64); do kill $p; done")
    T = open(LOG, errors="ignore").read()
    print("\n  ══ SONDE 1 · LE POINT MAUDIT (4629, 5856) ══")
    D = {}
    for m in re.finditer(r"S1\|bras\|(\w)\|k\|\d+\|coups\|(\d+)\|vue\|([\d.]+)\|path_mann\|(\w+)", T):
        D.setdefault(m.group(1), []).append((int(m.group(2)), float(m.group(3)), m.group(4)))
    for k in sorted(D):
        v = D[k]; c = [x[0] for x in v]; vu_ = [x[1] for x in v]
        nom = {"A": "acte 3 (mannequin PATH)", "B": "T7 (PATH coupe, POSER_HOMME)", "C": "acte 3 + PATH coupe"}[k]
        print("  %-28s n=%2d  coups med %2d  zeros %d/%d  vue med %.2f  path=%s"
              % (nom, len(v), sorted(c)[len(c)//2], sum(1 for x in c if x == 0), len(c),
                 sorted(vu_)[len(vu_)//2], v[0][2]))
    if len(D) == 3:
        z = lambda k: sum(1 for x, _, _ in D[k] if x == 0)
        print("\n  ── LE VERDICT, SUR LA PREDICTION ECRITE AVANT ──")
        if z("A") <= 2 and z("B") >= 8 and z("C") >= 8:
            print("  ➤ `PATH` DU MANNEQUIN EST LE COUPABLE — A tire, B et C se taisent.")
        elif z("A") <= 2 and z("B") >= 8 and z("C") <= 2:
            print("  ➤ `PATH` EST INNOCENT — C tire comme A. Le suspect est la NAISSANCE du tireur.")
        else:
            print("  ⚠️ figure non prevue — on ne conclut pas : A=%d B=%d C=%d zeros" % (z("A"), z("B"), z("C")))
    print("\n  ══ SONDE 2 · L HOMME NE COINCE ══")
    S2 = [(float(m.group(1)), int(m.group(2)), float(m.group(3)))
          for m in re.finditer(r"S2\|k\|\d+\|m\|([\d.]+)\|nt\|(\d+)\|derive_pose\|([\d.]+)", T)]
    if S2:
        ms = sorted(x[0] for x in S2)
        print("  n=%d  metres : %s" % (len(S2), " ".join("%.0f" % x for x in ms)))
        print("  coinces (< 10 m) : %d/%d   derive a la pose : %s"
              % (sum(1 for x in ms if x < 10), len(ms), " ".join("%.1f" % x[2] for x in S2)))
