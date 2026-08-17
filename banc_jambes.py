#!/usr/bin/env python3
"""banc_jambes.py — QUELLE PRIMITIVE DEPLACE UN FANTASSIN POSE ?

Ne du VERDICT_JAMBES du 16/08. Six bras qui croisent la primitive et le mode de pilotage,
alternes dans chaque repetition, positions tirees a neuf.

CRITERES ECRITS AVANT DE REGARDER

  · CONTROLE POSITIF ⟨regle 16⟩ — le bras 4 (natif + doMove) doit rendre PLUS DE 5 m
    medians. C est une marche lente, et 48 m ont deja ete mesures jambes actives. S il
    echoue, le banc est MUET : on ne lit AUCUN autre bras, on repare le banc.

  · TEMOIN — le bras 1 (le bras EN SERVICE) est attendu SOUS 3 m. S il depasse 10 m, il
    contredit les 4 tirages du prevol : c est alors le banc qui est suspect, et rien n est
    lu. Une mesure doit savoir contredire celle qui l a fait naitre.

  · RETENU — un bras est retenu s il rend AU MOINS 8 m medians ET AU MOINS 90 % de temps
    au sol median. Les deux, pas l un des deux : 8 m en l air est un vol, pas une marche.

  · DEPARTAGE — parmi les retenus, le plus rapide. La reference haute est 19,7 m
    (6 m/s x 3,28 s), la vitesse que le gymnase suppose.
"""
import sys, os, time, re, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SB   = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5830, 6062
LOG  = SB + "/logs/serverJB.out"
NREP = int(sys.argv[1]) if len(sys.argv) > 1 else 10

def sh(c): subprocess.run(c, shell=True, executable="/bin/bash")

if __name__ == "__main__":
    os.makedirs(SB + "/logs", exist_ok=True)
    open(LOG, "w").close()
    print("  lancement du serveur...", flush=True)
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverLV.cfg' -profiles='%s/profilesLV' "
       "-port=%d -world=Stratis -autoInit "
       "-mod='@CBA_A3;@rhsusaf;@rhsafrf;@LAMBS_Danger;@PinnedDown_BattleLines;@PinnedDown_CoverConcealment' "
       ">> '%s' 2>&1 < /dev/null & disown" % (SB, EXT, SB, SB, PORT, LOG))
    time.sleep(45)
    b = SocketBridge(EXT)
    print("  pont ouvert", flush=True)
    time.sleep(3)
    # ⚠️ PAR FICHIER, PAS PAR LA SOCKET — « gros inline -> fichier », piege deja paye.
    b.send('call compile preprocessFileLineNumbers "socle.sqf";', wait=False); time.sleep(2.5)
    b.send('call compile preprocessFileLineNumbers "jambes.sqf";', wait=False); time.sleep(2.5)
    b.send('HMT_JB = nil; [] spawn { HMT_JB = [%d] call HMT_JAMBES; };' % NREP, wait=False)
    print("  banc lance : %d repetitions x 6 bras" % NREP, flush=True)

    # Le journal du banc est ECRIT PAR LE JEU (fichier compile par le jeu, pas texte envoye
    # par le pont) : il va dans le .out, jamais dans la socket. On lit donc le fichier.
    # ⚠️ CLIQUET DU 16/08 — LE LANCEUR VERIFIE SON BUDGET AVANT DE PARTIR.
    # Le minuteur de la v2 est reste cale sur un banc plus court : il a coupe a 51 essais
    # sur 64, et le bras tronque est justement le SEUL qui decidait du verdict, parce qu il
    # etait dernier. Il a fini a n = 4. On calcule desormais bras x essais x duree, et on
    # refuse de partir plutot que de tronquer en silence.
    DUREE_BRAS = 17 + 6 * 5.3 + 12          # controle 15 s + six bras + la reproduction de T5
    BUDGET = 60 + NREP * DUREE_BRAS * 1.25  # 25 % de marge pour le serveur
    print("  budget : %d bras-secondes par repetition, %d s au total" % (DUREE_BRAS, BUDGET), flush=True)
    t0 = time.time(); vu = 0
    while time.time() - t0 < BUDGET:
        time.sleep(10)
        try: txt = open(LOG, errors="ignore").read()
        except Exception: txt = ""
        n = txt.count("HMT|JAMBES|bras")
        if n != vu: print("    %d essais" % n, flush=True); vu = n
        if "HMT|JAMBES|FINI" in txt: break
    sh("pkill -f arma3server_x64")
    time.sleep(2)

    if "HMT|JAMBES|FINI" not in open(LOG, errors="ignore").read():
        print("\n  ⛔ LE BANC N A PAS FINI dans son budget — les essais sont TRONQUES,")
        print("     et un banc tronque ne se lit pas : le dernier bras est sous-echantillonne.")
        sys.exit(5)
    L = [l for l in open(LOG, errors="ignore") if "HMT|JAMBES|bras" in l]
    print("\n  essais releves : %d\n" % len(L), flush=True)
    par = {}
    for l in L:
        # REVUE 17/08 : le motif consommait les DEUX barres qui delimitent la cle, donc
        # les paires etaient decalees d un cran : sur `HMT|JAMBES|bras|...` il rendait
        # {JAMBES: bras, ...} sans cle `bras` ni `m` -> KeyError des la 1re ligne relue,
        # et le controle positif `4_natif_domove` n etait JAMAIS atteint.
        _t = l[l.index("HMT|JAMBES|"):].strip().split("|")
        d = dict(zip(_t[2::2], _t[3::2]))
        par.setdefault(d["bras"], []).append((float(d["m"]), float(d["sol"])))
    med = lambda v: sorted(v)[len(v)//2] if v else float("nan")

    print("  %-28s %4s %8s %8s" % ("bras", "n", "metres", "au sol"))
    R = {}
    for k in sorted(par):
        v = par[k]; m = med([x[0] for x in v]); s = med([x[1] for x in v]); R[k] = (m, s, len(v))
        print("  %-28s %4d %7.1f m %6.0f %%" % (k, len(v), m, s))

    print("\n  ── LES CRITERES, DANS L ORDRE OU ILS ONT ETE ECRITS ──")
    cp = R.get("4_natif_domove", (0, 0, 0))
    if cp[0] <= 5:
        print("  ⛔ CONTROLE POSITIF ECHOUE : %.1f m <= 5. LE BANC EST MUET, rien n est lu." % cp[0]); sys.exit(2)
    print("  ✓ controle positif : natif+doMove rend %.1f m (> 5)" % cp[0])
    tm = R.get("1_pilote_vel_plat", (0, 0, 0))
    if tm[0] >= 10:
        print("  ⛔ TEMOIN A %.1f m (>= 10) : le banc CONTREDIT le prevol. Rien n est lu." % tm[0]); sys.exit(3)
    print("  ✓ temoin : le bras en service rend %.1f m (< 10, attendu < 3)" % tm[0])
    ret = [(k, v) for k, v in R.items() if v[0] >= 8 and v[1] >= 90]
    if not ret:
        print("\n  ⛔ AUCUN BRAS RETENU — aucune primitive ne marche AU SOL a 8 m par ordre.")
    else:
        ret.sort(key=lambda x: -x[1][0])
        print("\n  BRAS RETENUS (>= 8 m ET >= 90 %% au sol) :")
        for k, v in ret: print("     %-28s %5.1f m  %3.0f %% au sol" % (k, v[0], v[1]))
        print("\n  ➤ RETENU : %s — %.1f m par ordre (reference haute 19,7 m)" % (ret[0][0], ret[0][1][0]))
