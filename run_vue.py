#!/usr/bin/env python3
"""LE CONTROLE VISUEL DU GESTE — demande de Younes, 19/08.

Tout le dossier du vol repose sur une CHAINE (`afal` contre `amov`), lue au dernier
tick. Cette sonde la remplace par la HAUTEUR AU-DESSUS DU TERRAIN a chaque tick, et
releve le relief et les objets autour, pour qu on VOIE le lieu et la trace dessus.

12 lieux tires de l archive de la porte 3.1.0 (graine fixe 19) : 6 qui ont fini au SOL,
6 qui ont fini EN L AIR. Plus DEUX BRAS DE CONTROLE de l instrument (regle 18) :
  - jambes coupees (vy=0)  -> doit rendre part_sol 100 % et distance ~0
  - vol force (vz=+5 au depart) -> doit rendre part_sol 0 % et une hauteur qui monte
Une sonde incapable de separer ces deux-la ne dira rien des lieux.

⚠️ ANGLE MORT DECLARE (regle 20) : la sonde tourne dans le monde EVEILLE de la porte
(scene + reveil natif), donc a la charge serveur de la porte. Elle ne dit RIEN du
regime au repos, ni d une eventuelle dependance du vol a la cadence de tick.
"""
import sys, os, time, re, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
from banc_live import SCENE, sans_commentaires
import arma_couture as C

SB = "/mnt/data/harmattan-sandbox"; EXT, PORT = 5832, 6064
LOG = SB + ("/logs/serverVUECTRL.out" if (len(sys.argv) > 1 and sys.argv[1] == "ctrl") else "/logs/serverVUE.out")
SORTIE = "/mnt/data/preuves/2026-08-19_controle_visuel"

# graine 19, tires par /tmp/pts.py sur l archive
SOL   = [(4983,5759,14),(4207,5363,10),(4861,5771,11),(4434,5223,14),(4805,5619,15),(4499,5702,13)]
VOL   = [(4680,5414,14),(4640,5403,24),(4886,5210,25),(4600,5894,23),(5001,5571,25),(4424,5422,25)]

def sh(c): subprocess.run(c, shell=True, executable="/bin/bash")

def tuer_le_mien():
    """⚠️ NE TUE QUE LE SERVEUR DE CE LANCEUR. `pkill -f arma3server_x64` tuait aussi
    les serveurs des autres sessions (6072 A3C, 6082 DR, ...). On cible par le PORT."""
    sh("for p in $(pgrep -f '\\-port=%d'); do kill $p; done" % PORT)


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    C.CX, C.CY = 4644.0, 5652.0; C.SCALE = 200.0
    open(LOG, "w").close()
    tuer_le_mien(); time.sleep(4)
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverLV.cfg' -profiles='%s/profilesLV' "
       "-port=%d -world=Stratis -autoInit "
       "-mod='@CBA_A3;@rhsusaf;@rhsafrf;@LAMBS_Danger;@PinnedDown_BattleLines;@PinnedDown_CoverConcealment' "
       ">> '%s' 2>&1 < /dev/null & disown" % (SB, EXT, SB, SB, PORT, LOG))
    time.sleep(45)
    b = SocketBridge(EXT); time.sleep(3)
    b.send('call compile preprocessFileLineNumbers "socle.sqf";', wait=False); time.sleep(3)
    # ⚠️ LA SCENE EST SAUTEE, ET LA RAISON EST MESUREE, PAS COMMODE. Au premier essai
    # (19:25, meme monde, meme socle 3.1.0) le bloc C a juge 37 positions : 32 « encombre »,
    # 5 « muet », ZERO recue, sur SIX essais d azimut a 0/4. Avec le seuil a 23 m le
    # certificateur ne construit plus de scene : attendre 480 s ne produit rien a mesurer.
    # ⚠️ ANGLE MORT DECLARE (regle 20) : sans scene, le serveur est AU REPOS — pas de huit
    # hommes en IA complete, donc FPS hauts et cadence d impulsions maximale. Si le vol
    # depend de la cadence, cette sonde le voit dans son regime le PLUS favorable. C est
    # pourquoi `diag_fps` est desormais releve a chaque geste : la comparaison avec les FPS
    # de la porte (journalises par T5) dira si la charge deplace le phenomene.
    print("  scene SAUTEE — serveur au repos, angle mort declare", flush=True)
    b.send('call compile preprocessFileLineNumbers "sonde_vue.sqf";', wait=False); time.sleep(3)
    b.send('diag_log format ["HMT|VER|%1|VUE|%2", HMT_SOCLE_VERSION, !isNil "HMT_VUE_PRETE"];', wait=False)
    time.sleep(1.5)
    v = [L for L in b._log_lines(120) if "HMT|VER|" in L]
    print("  socle + sonde : %s" % (v[-1].split("HMT|VER|")[1].strip().strip('"')[:40] if v else "?"), flush=True)

    pts = [(x, y, "sol%d_%dm" % (i, d)) for i, (x, y, d) in enumerate(SOL)] + \
          [(x, y, "vol%d_%dm" % (i, d)) for i, (x, y, d) in enumerate(VOL)]
    liste = "[" + ",".join('[%d,%d,"%s"]' % p for p in pts) + "]"
    # les lieux, puis les deux bras de controle sur le PREMIER lieu de chaque famille
    # ⚠️ DEUX PROGRAMMES. Sans argument : les 12 lieux + 4 controles (le passage du
    # 19/08 19h36). Avec `ctrl` : les CONTROLES SEULS, repliques x3 par condition —
    # `volforce` etait a n=1 par condition, et c est le fait le plus surprenant du banc.
    # ⚠️ ON AJOUTE LE BRAS `sud` : la marche du socle est cablee vers le NORD (`[0,_vy,0]`),
    # et la pente nord separe les deux familles a 100 % (+15..+51 % contre -6..-34 %).
    # Marcher vers le SUD sur un lieu « sol » doit donc le faire « voler » — et sur un lieu
    # « vol » le clouer. C est le controle qui juge la THESE, pas seulement l instrument.
    if len(sys.argv) > 1 and sys.argv[1] == "ctrl":
        S, V = SOL[0], VOL[1]
        b_ = []
        for k in range(3):
            b_ += ['[%d, %d, "Fsol%d", "jambes"] call HMT_VUE_TRACE;' % (S[0], S[1], k),
                   '[%d, %d, "Fvol%d", "volforce"] call HMT_VUE_TRACE;' % (V[0], V[1], k),
                   '[%d, %d, "FvolSURsol%d", "volforce"] call HMT_VUE_TRACE;' % (S[0], S[1], k),
                   '[%d, %d, "SUDsurSol%d", "sud"] call HMT_VUE_TRACE;' % (S[0], S[1], k),
                   '[%d, %d, "SUDsurVol%d", "sud"] call HMT_VUE_TRACE;' % (V[0], V[1], k)]
        prog = ('HMT_VUE_FINI = false; [] spawn { ' + " ".join(b_) +
                ' HMT_VUE_FINI = true; diag_log "HMT|VUE|FINI"; };')
        print("  programme CONTROLES — 5 bras x 3", flush=True)
    else:
        prog = ('HMT_VUE_FINI = false; [] spawn { '
                '{ [_x select 0, _x select 1, _x select 2] call HMT_VUE_LIEU; '
                '  [_x select 0, _x select 1, _x select 2, "normal"] call HMT_VUE_TRACE; } forEach %s; '
                '[%d, %d, "CTRL_sol", "jambes"] call HMT_VUE_TRACE; '
                '[%d, %d, "CTRL_vol", "volforce"] call HMT_VUE_TRACE; '
                '[%d, %d, "CTRL_vol2", "volforce"] call HMT_VUE_TRACE; '
                '[%d, %d, "CTRL_sol2", "jambes"] call HMT_VUE_TRACE; '
                'HMT_VUE_FINI = true; diag_log "HMT|VUE|FINI"; };'
                % (liste, SOL[0][0], SOL[0][1], SOL[0][0], SOL[0][1],
                   VOL[1][0], VOL[1][1], VOL[1][0], VOL[1][1]))
        print("  programme COMPLET — %d lieux + 4 controles" % len(pts), flush=True)
    b.send(prog, wait=False)
    t0 = time.time(); vu = -1
    while time.time() - t0 < 900:
        time.sleep(10)
        try: txt = open(LOG, errors="ignore").read()
        except Exception: txt = ""
        n = txt.count("HMT|VUE|GESTE")
        if n != vu: print("    %d gestes releves" % n, flush=True); vu = n
        if "HMT|VUE|FINI" in txt: break
    tuer_le_mien(); time.sleep(2)
    sh("cp -p '%s' '%s/'" % (LOG, SORTIE))
    print("\n  journal archive dans %s/serverVUE.out" % SORTIE, flush=True)
