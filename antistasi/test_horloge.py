#!/usr/bin/env python3
"""test_horloge.py — l'acceleration du temps accelere-t-elle la CAMPAGNE Antistasi ?

Le battement economique d'Antistasi est `time + 600` (fn_resourcecheck.sqf), donc du
temps MISSION. setTimeMultiplier, lui, accelere l'horloge du MONDE (date). La question
est de savoir si les deux sont lies.

MESURE   : d(time)/d(mur) — la vitesse du temps mission.
CONTROLE : d(date)/d(mur) — doit etre multiplie par MULT en phase B, sinon la commande
           n a pas pris et un resultat nul ne prouverait rien.

VERDICT NEGATIF si time avance a ~1 s/s dans les deux phases pendant que date accelere.
VERDICT POSITIF si time accelere lui aussi.
"""
import sys, os, re, time as clock
sys.path.insert(0, os.path.expanduser("~/arma3-marl"))
from arma_socket_bridge import SocketBridge

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5886
FENETRE = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
MULT = 16

RE_ETAT = re.compile(r"A3A_ETAT\|t=(\d+)\|date=\[(\d+),(\d+),(\d+),(\d+),(\d+)\]")


def collecte(b, depuis, duree, etiquette):
    """Renvoie [(mur, time_mission, minutes_de_jeu), ...] sur la fenetre."""
    pts = []
    t0 = clock.time()
    vus = depuis
    while clock.time() - t0 < duree:
        lignes = list(b.lines)
        for ln in lignes[vus:]:
            m = RE_ETAT.search(ln)
            if m:
                t = int(m.group(1))
                jour, h, mn = int(m.group(4)), int(m.group(5)), int(m.group(6))
                pts.append((clock.time(), t, jour * 1440 + h * 60 + mn))
        vus = len(lignes)
        clock.sleep(1.0)
    print("  %s : %d releves" % (etiquette, len(pts)))
    return pts, vus


def pente(pts, i):
    if len(pts) < 2:
        return float("nan")
    d_mur = pts[-1][0] - pts[0][0]
    return (pts[-1][i] - pts[0][i]) / d_mur if d_mur > 0 else float("nan")


b = SocketBridge(PORT)
try:
    print("PHASE A — multiplicateur d origine")
    a, vus = collecte(b, len(b.lines), FENETRE, "A")

    print("PHASE B — setTimeMultiplier %d" % MULT)
    b.send("setTimeMultiplier %d;" % MULT, wait=True, timeout=20)
    clock.sleep(12)                       # on jette la transition
    vus = len(b.lines)
    bb, _ = collecte(b, vus, FENETRE, "B")

    ta, tb = pente(a, 1), pente(bb, 1)          # secondes mission par seconde reelle
    da, db = pente(a, 2), pente(bb, 2)          # minutes de jeu par seconde reelle

    print("")
    print("temps MISSION : A = %.2f s/s   B = %.2f s/s   -> x%.2f" % (ta, tb, tb / ta if ta else 0))
    print("horloge MONDE : A = %.2f min/s B = %.2f min/s -> x%.2f" % (da, db, db / da if da else 0))
    print("")
    controle_ok = da > 0 and (db / da) > MULT * 0.5
    if not controle_ok:
        print("CONTROLE ECHOUE : l horloge du monde n a pas accelere. Test NON CONCLUANT.")
    elif ta > 0 and (tb / ta) > 1.5:
        print("VERDICT POSITIF : le temps mission accelere aussi -> le debit monte d autant.")
    else:
        print("VERDICT NEGATIF : le temps mission reste a ~1 s/s. Le battement de campagne")
        print("                  (time + 600) est INSENSIBLE a setTimeMultiplier.")
finally:
    b.sock.close()
