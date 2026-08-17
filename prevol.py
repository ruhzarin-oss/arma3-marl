#!/usr/bin/env python3
"""prevol.py — LA PORTE DU PREVOL.

⟨Fable, 16/08⟩ La porte n est pas 50 EPISODES, c est 50 TIRAGES DU PREVOL. Un tirage dure
une vingtaine de secondes et le prevol cree puis detruit ses propres hommes : on les
enchaine donc sur UN serveur, ce qui ramene la porte de deux heures a une vingtaine de
minutes. Le serveur n est relance a aucun moment — si sa duree de vie devenait le sujet,
ce serait un autre banc.

  prevol.py <nb_tirages> [normal|sabotage]

CRITERES ⟨poses avant, et separement de tout resultat⟩
  · CONTROLE POSITIF, EN PREMIER — en mode `sabotage`, les munitions du temoin sont
    retirees et T4 DOIT rougir. Si le sabotage ne fait rien rougir, la porte ne mesure
    rien et TOUT S ARRETE : on ne lit aucun tirage normal.
  · LA PORTE — 50 tirages, 2 echecs tolerables (5 %), coupure au 3e.
"""
import sys, os, time, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
import arma_couture as C
# ⚠️ LA SCENE VIT DANS `banc_live.py`, pas dans la couture. On l IMPORTE au lieu de la
# recopier : deux scenes qui derivent l une de l autre, c est deux mondes qu on croit pareils.
from banc_live import SCENE, sans_commentaires

N    = int(sys.argv[1]) if len(sys.argv) > 1 else 50
MODE = sys.argv[2] if len(sys.argv) > 2 else "normal"
# ⚠️ LE DELAI D ECHAUFFEMENT EST UN PARAMETRE, PAS UNE CONSTANTE. Mesure du 16/08 : les
# echecs de T5 se concentrent aux tirages 1-3 d une session (4 m, 10 m, puis 18-24 m sur
# les quatorze suivants), et la nuit tirait son prevol 48 s apres un serveur NEUF a chaque
# episode — toujours dans la zone froide, d ou 70 % de rouges contre 4 % a la porte.
CHAUD = int(sys.argv[3]) if len(sys.argv) > 3 else 45
SB   = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5830, 6062
LOG  = SB + "/logs/serverPV%s.out" % (os.environ.get("HMT_SESSION", ""))
OBJ, NDEF, NATT, DIST = (4644.0, 5652.0), 4, 4, 170.0
MAX_ECHECS = 2

def sh(c): subprocess.run(c, shell=True, executable="/bin/bash")

if __name__ == "__main__":
    C.CX, C.CY = OBJ; C.SCALE = 200.0; C.FIRE_RANGE = 110.0; C.MOVE_SPD = 6.0
    open(LOG, "w").close()
    sh("for p in $(pgrep -f arma3server_x64); do kill $p; done"); time.sleep(4)
    print("  serveur...", flush=True)
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverLV.cfg' -profiles='%s/profilesLV' "
       "-port=%d -world=Stratis -autoInit "
       "-mod='@CBA_A3;@rhsusaf;@rhsafrf;@LAMBS_Danger;@PinnedDown_BattleLines;@PinnedDown_CoverConcealment' "
       ">> '%s' 2>&1 < /dev/null & disown" % (SB, EXT, SB, SB, PORT, LOG))
    print('  echauffement : %d s' % CHAUD, flush=True)
    time.sleep(CHAUD)
    b = SocketBridge(EXT); time.sleep(3)
    b.send(sans_commentaires(SCENE), wait=False)
    time.sleep(6)
    lg = [L for L in b._log_lines(400) if "HARMATTAN_SCENE" in L]
    print("  scene : %s" % (lg[-1][-40:] if lg else "AUCUNE — on n ira pas plus loin"), flush=True)
    if not lg: sys.exit(1)
    b.send('call compile preprocessFileLineNumbers "socle.sqf";', wait=False); time.sleep(3)
    b.send('HMT_SABOTER = "%s";' % ("munitions" if MODE == "sabotage" else ""), wait=False)
    time.sleep(1)
    # Le reveil fait partie du monde. `banc_live.py natif` l envoie ENTRE la scene et le
    # prevol ; la porte du 16/08 n en envoyait aucun, et c est pour ca qu elle a certifie
    # un monde que la nuit ne jouait pas.
    WAKE_NATIF = ('{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED" } forEach HMT_ENNEMI;\n'
                  '{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED" } forEach HMT_FR;\n'
                  'HMT_POST = []; { HMT_POST pushBack 0 } forEach HMT_FR;\n')
    if MODE == "natif":
        b.send(sans_commentaires(WAKE_NATIF), wait=False); time.sleep(2)
        print("  reveil NATIF envoye — regime de la nuit", flush=True)
    print("  socle charge — mode %s, %d tirages" % (MODE, N), flush=True)

    # `callExtension "version"` rend « hmt_native 1.2 | <etat> | jetes ring=N send=N ligne=N ».
    # Le bind est hors de cause : s il avait echoue, le pont ne se serait pas connecte et la
    # session aurait AVORTE — or les mortes creaient bien leur scene. On mesure les JETES.
    def pont(quand):
        b.send('diag_log format ["HMT|PONT|%s|%%1", ("hmt_native" callExtension "version")];' % quand, wait=False)
        time.sleep(1.2)
        ls = [L for L in b._log_lines(150) if "HMT|PONT|" + quand in L]
        e = ls[-1].split("HMT|PONT|")[1][:120].rstrip('"') if ls else quand + "|AUCUNE REPONSE"
        print("  pont %s" % e, flush=True)
        return e
    pont("debut")

    verts, ech, det = 0, 0, []
    sansrep = 0                      # REVUE 17/08 : les pannes de pont, comptees A PART
    # ⚠️ LES CINQ LIEUX SONT ALTERNES DANS LA MEME SESSION. C est le point du protocole :
    # si les lieux morts echouent et les vivants passent COTE A COTE sous le meme serveur,
    # l effet de session est elimine comme explication concurrente.
    LIEUX = [("mort_4989_5877", 4989, 5877), ("vif_4776_5196", 4776, 5196),
             ("mort_4716_5207", 4716, 5207), ("vif_4445_6138", 4445, 6138),
             ("mort_4210_5369", 4210, 5369)]
    for i in range(1, N + 1):
        if MODE == "lieux":
            nom, lx, ly = LIEUX[(i - 1) % len(LIEUX)]
            b.send('HMT_LIEU_FORCE = [%d, %d];' % (lx, ly), wait=False); time.sleep(0.6)
            print("  lieu force : %s" % nom, flush=True)
        if MODE == "compare":
            b.send(sans_commentaires(WAKE_NATIF if i % 2 else C.WAKE), wait=False); time.sleep(2)
        b.send('HMT_PV = nil; [] spawn { HMT_PV = [HMT_FR] call HMT_PREVOL; };', wait=False)
        r = None
        # REVUE 17/08 : on lisait la DERNIERE ligne `HMT|PV|` du tampon, sans borne de
        # fraicheur. Sur serveur charge, une ligne du tirage PRECEDENT (true/false, jamais
        # « attente ») validait le tirage courant en 2 s pendant que son propre prevol
        # tournait encore — les deux se superposaient sur les globales HMT_PV_COUPS.
        # La reponse porte desormais le NUMERO du tirage.
        _tag = "HMT|PV|%d|" % i
        for _ in range(40):
            time.sleep(1.5)
            if not getattr(b, "alive", True):
                break
            b.send('diag_log format ["HMT|PV|%d|%%1|%%2", (if (isNil "HMT_PV") then {"attente"} else {HMT_PV}), HMT_SOCLE_VERSION];' % i, wait=False)
            time.sleep(0.4)
            ls = [L for L in b._log_lines(200) if _tag in L]
            if ls and "attente" not in ls[-1]:
                r = "true" in ls[-1].split(_tag)[1][:6]; break
        if r is None:
            # REVUE 17/08 : « SANS REPONSE » entrait dans le MEME compteur que les vrais
            # rouges, puis « PORTE TOMBEE » (exit 4) : une panne du pont etait rendue
            # comme un verdict sur la tactique. Elle est comptee a part.
            sansrep += 1; det.append((i, "SANS REPONSE"))
        elif r:
            verts += 1
        else:
            ech += 1
            b.send('diag_log format ["HMT|PVE|%1", (if (isNil "HMT_PV_ECARTS") then {"?"} else {HMT_PV_ECARTS})];', wait=False)
            time.sleep(0.6)
            e = [L for L in b._log_lines(200) if "HMT|PVE|" in L]
            det.append((i, e[-1].split("HMT|PVE|")[1][:110] if e else "?"))
        print("    %2d/%d  vert=%d  echec=%d%s" % (i, N, verts, ech,
              ("   ← " + det[-1][1][:70]) if det and det[-1][0] == i else ""), flush=True)
        if sansrep >= 3:
            print("\n  ⛔ TROIS TIRAGES SANS REPONSE : c'est le PONT qui est muet, pas la\n     porte. AUCUN verdict n'est rendu sur la tactique.", flush=True)
            sys.exit(5)
        if MODE == "normal" and ech > MAX_ECHECS:
            print("\n  ⛔ COUPURE AU %dE ECHEC — la porte tombe, la nuit reste vide." % ech, flush=True); break
    pont("fin")
    sh("for p in $(pgrep -f arma3server_x64); do kill $p; done")

    print("\n  ── %d tirages : %d verts, %d echecs, %d sans reponse ──"
          % (verts + ech + sansrep, verts, ech, sansrep), flush=True)
    if MODE == "sabotage":
        if ech == 0:
            print("  ⛔ LE SABOTAGE N A RIEN FAIT ROUGIR. La porte ne mesure rien. ARRET TOTAL."); sys.exit(2)
        rouges_t4 = sum(1 for _, d in det if "T4" in d)
        print("  ✓ le sabotage fait rougir : %d echecs, dont %d sur T4" % (ech, rouges_t4))
        if rouges_t4 == 0:
            print("  ⛔ mais AUCUN sur T4 — ce n est pas la panne qu on a fabriquee. ARRET."); sys.exit(3)
    else:
        if ech > MAX_ECHECS: print("  ⛔ PORTE TOMBEE (%d echecs > %d)" % (ech, MAX_ECHECS)); sys.exit(4)
        print("  ✓ PORTE TENUE : %d echecs sur %d, seuil %d" % (ech, verts + ech, MAX_ECHECS))
    for i, d in det: print("     tirage %2d : %s" % (i, d))
