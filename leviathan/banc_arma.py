#!/usr/bin/env python3
"""banc_arma — LA CERTIFICATION. Les MEMES doctrines, dans le vrai jeu.

Ce qu'on certifie, ce ne sont pas des chiffres : c'est un CLASSEMENT.
Le sandbox dit : crochet 75 %, frontal 19 %. Arma ne dira pas 75 et 19 — il dira
peut-etre 60 et 25. Sans importance. Ce qui compte, c'est que le crochet gagne des deux
cotes, et a peu pres dans le meme rapport. Si Arma dit que le frontal gagne, tout ce qu'on
a construit est a jeter.

MEMES DOCTRINES DES DEUX COTES. C'est le seul protocole qui teste le MONDE et non la
politique — une politique apprise dans le sandbox mesurerait son inadaptation.

GEOMETRIE COPIEE SUR LE BANC FIGE (DURETE_FIGEE.md, empreinte 0eeae9efcdd67572) :
    4 attaquants, 8 defenseurs, depart a 170 m, ligne defensive a ~37 m devant l'objectif,
    defenseurs etales sur ~20 deg et faisant FACE A L'EXTERIEUR.
Cote Arma on ne simule pas d'arc de tir : on place les defenseurs face au dehors et on
laisse le moteur faire. C'est justement ce qu'on veut verifier.

ECONOMIE DU PONT (lecons du 26-27/07) :
  - les ordres partent SANS accuse (wait=False) : un envoi bloquant coute 14 s par defaut
  - un seul releve toutes les 20 s, pas cent allers-retours
  - fermeture garantie a chaque sortie : un client mort rend le pont muet pour tous
  - quatre duels EN PARALLELE sur la carte : une seance rend quatre episodes

Usage : python banc_arma.py --doctrine frontal|flanc --seances 3
"""
import sys
import time
import json
import math
import argparse

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
P = chr(37)
LEV = "/home/younes/arma3-marl/leviathan"

ap = argparse.ArgumentParser()
ap.add_argument("--doctrine", choices=["frontal", "flanc"], required=True)
ap.add_argument("--seances", type=int, default=3)
ap.add_argument("--cellules", type=int, default=4, help="duels en parallele")
ap.add_argument("--zone", default="23000,17400")
ap.add_argument("--pas_cellule", type=int, default=900)
ap.add_argument("--duree", type=int, default=200, help="s ; 60 pas de sandbox x 3,28 s")
ap.add_argument("--nA", type=int, default=4)
ap.add_argument("--nD", type=int, default=8)
ap.add_argument("--rspawn", type=float, default=170.0)
ap.add_argument("--rline", type=float, default=37.0)
ap.add_argument("--secure", type=float, default=25.0)
ap.add_argument("--out", default=None)
theatre.add_theatre_arg(ap)
a = ap.parse_args()
TH = theatre.apply_theatre_arg(a)
ZX, ZY = [int(v) for v in a.zone.split(",")]


def _fermer(b):
    try:
        b.close()
    except Exception:
        pass


def poser(b, seance):
    """Une cellule = un objectif, 8 defenseurs en ligne devant, 4 attaquants a 170 m.

    L'azimut d'approche change a chaque seance : on ne certifie pas une geometrie unique.
    """
    c = ["if (!isNil " + Q + "HMT_C" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_C }; "
         "HMT_C = []; HMT_ATT = []; HMT_DEF = []; HMT_OBJ = []; HMT_PRIS = []; "
         "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "]
    for k in range(a.cellules):
        K = str(k)
        ox = ZX + k * a.pas_cellule
        oy = ZY
        # azimut d'approche : reparti sur les seances et les cellules
        th = (seance * 67.0 + k * 90.0) * math.pi / 180.0
        c.append("HMT_PRIS pushBack 0; "
                 "HMT_OBJ pushBack [" + str(ox) + "," + str(oy) + "]; "
                 "private _gd" + K + " = createGroup east; "
                 "private _ga" + K + " = createGroup west; ")
        # --- la LIGNE defensive : etalee sur ~20 deg autour de l'axe de menace, FACE au dehors
        for i in range(a.nD):
            frac = (i / max(a.nD - 1, 1) - 0.5) * 2.0          # -1..1
            az = th + frac * (20.0 * math.pi / 180.0)
            dx = ox + a.rline * math.sin(az)
            dy = oy + a.rline * math.cos(az)
            U = "_d" + K + "_" + str(i)
            c.append("private " + U + " = _gd" + K + " createUnit ["
                     + Q + "O_Soldier_F" + Q + ", [" + ("%.1f" % dx) + "," + ("%.1f" % dy) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
                     + U + " setPosATL [" + ("%.1f" % dx) + "," + ("%.1f" % dy) + ",0]; "
                     + U + " setDir " + ("%.1f" % (math.degrees(az))) + "; "
                     + U + " setSkill 0.5; " + U + " setUnitPos " + Q + "MIDDLE" + Q + "; "
                     + U + " setBehaviour " + Q + "COMBAT" + Q + "; " + U + " setCombatMode " + Q + "RED" + Q + "; "
                     + U + " disableAI " + Q + "PATH" + Q + "; "                    # la ligne TIENT, elle ne charge pas
                     "HMT_C pushBack " + U + "; HMT_DEF pushBack " + U + "; ")
        # --- les attaquants, a rspawn sur l'axe de menace
        for i in range(a.nA):
            lat = (i - (a.nA - 1) / 2.0) * 8.0
            ax = ox + a.rspawn * math.sin(th) + lat * math.cos(th)
            ay = oy + a.rspawn * math.cos(th) - lat * math.sin(th)
            U = "_a" + K + "_" + str(i)
            c.append("private " + U + " = _ga" + K + " createUnit ["
                     + Q + "B_Soldier_F" + Q + ", [" + ("%.1f" % ax) + "," + ("%.1f" % ay) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
                     + U + " setPosATL [" + ("%.1f" % ax) + "," + ("%.1f" % ay) + ",0]; "
                     + U + " setSkill 0.5; " + U + " setBehaviour " + Q + "COMBAT" + Q + "; "
                     + U + " setCombatMode " + Q + "RED" + Q + "; "
                     "HMT_C pushBack " + U + "; HMT_ATT pushBack " + U + "; ")
    c.append("HMT_TH = " + str(0) + "; (format [" + Q + "POSE " + P + "1 " + P + "2" + Q
             + ", count HMT_ATT, count HMT_DEF]) call HMT_EMIT;")
    return b.query("".join(c), r"POSE (\d+) (\d+)", want=1, timeout=120)


def ordonner(b, seance):
    """La doctrine, envoyee SANS accuse. Un ordre suffit : l'IA d'Arma poursuit son deplacement."""
    ordres = []
    for k in range(a.cellules):
        ox = ZX + k * a.pas_cellule
        oy = ZY
        th = (seance * 67.0 + k * 90.0) * math.pi / 180.0
        base = k * a.nA
        for i in range(a.nA):
            idx = base + i
            U = "(HMT_ATT select " + str(idx) + ")"
            if a.doctrine == "frontal" or i < 2:
                # FRONTAL : droit sur l'objectif. Et dans le crochet, les 2 premiers FIXENT :
                # ils s'arretent a portee et tiennent le feu.
                if a.doctrine == "flanc" and i < 2:
                    fx = ox + 110.0 * math.sin(th)
                    fy = oy + 110.0 * math.cos(th)
                    ordres.append(U + " doMove [" + ("%.1f" % fx) + "," + ("%.1f" % fy) + ",0];")
                else:
                    ordres.append(U + " doMove [" + str(ox) + "," + str(oy) + ",0];")
            else:
                # CROCHET : point de passage lateral a ~190 m, puis l'objectif.
                # 14 pas de sandbox x 14 m = 196 m de tangente : on copie la doctrine.
                sgn = 1.0 if (i % 2 == 0) else 1.0
                lx = ox + a.rspawn * math.sin(th) + sgn * 190.0 * math.cos(th)
                ly = oy + a.rspawn * math.cos(th) - sgn * 190.0 * math.sin(th)
                ordres.append(U + " doMove [" + ("%.1f" % lx) + "," + ("%.1f" % ly) + ",0];")
    b.send(" ".join(ordres), wait=False)


def relancer_crochet(b, seance):
    """Une fois le point lateral atteint, les crocheteurs rentrent sur l'objectif."""
    ordres = []
    for k in range(a.cellules):
        ox = ZX + k * a.pas_cellule
        oy = ZY
        base = k * a.nA
        for i in range(2, a.nA):
            U = "(HMT_ATT select " + str(base + i) + ")"
            ordres.append(U + " doMove [" + str(ox) + "," + str(oy) + ",0];")
    if ordres:
        b.send(" ".join(ordres), wait=False)


def releve(b):
    """UN seul aller-retour : qui a pris, qui est mort."""
    q = ("{ private _k = _forEachIndex; private _o = HMT_OBJ select _k; "
         "  private _n = 0; "
         "  for [{private _i = 0}, {_i < " + str(a.nA) + "}, {_i = _i + 1}] do { "
         "    private _u = HMT_ATT select (_k * " + str(a.nA) + " + _i); "
         "    if (alive _u && ((_u distance2D [_o select 0, _o select 1]) < " + str(a.secure) + ")) then { _n = _n + 1 }; "
         "  }; "
         "  if (_n > 0) then { HMT_PRIS set [_k, 1] }; "
         "} forEach HMT_OBJ; "
         "private _va = ({ alive _x } count HMT_ATT); private _vd = ({ alive _x } count HMT_DEF); "
         "private _pr = 0; { _pr = _pr + _x } forEach HMT_PRIS; "
         "(format [" + Q + "R " + P + "1 " + P + "2 " + P + "3" + Q + ", _pr, _va, _vd]) call HMT_EMIT;")
    r = b.query(q, r"R (\d+) (\d+) (\d+)", want=1, timeout=30)
    return (int(r[-1].group(1)), int(r[-1].group(2)), int(r[-1].group(3))) if r else None


def main():
    b = NativeBridge(port=TH.PORT)
    b.send("setDate [2035, 7, 6, 12, 0]; 0 setOvercast 0; 0 setFog 0; forceWeatherChange; "
           "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;", wait=False)
    time.sleep(2)
    print("=== BANC ARMA — CERTIFICATION | doctrine %s ===" % a.doctrine, flush=True)
    print("    %d cellules x %d seances = %d episodes | %d attaquants vs %d defenseurs | depart %.0f m"
          % (a.cellules, a.seances, a.cellules * a.seances, a.nA, a.nD, a.rspawn), flush=True)
    print("    geometrie copiee du banc fige (0eeae9efcdd67572)", flush=True)

    tot_ep = 0
    tot_pris = 0
    tot_pertes = 0
    for s in range(a.seances):
        r = poser(b, s)
        if not r:
            print("  !! mise en place sans reponse — ARRET", flush=True)
            _fermer(b)
            sys.exit(2)
        print("", flush=True)
        print("  seance %d/%d : %s attaquants, %s defenseurs"
              % (s + 1, a.seances, r[-1].group(1), r[-1].group(2)), flush=True)
        time.sleep(4)
        ordonner(b, s)
        t = 0
        bascule = False
        while t < a.duree:
            time.sleep(20)
            t += 20
            if a.doctrine == "flanc" and not bascule and t >= 80:
                relancer_crochet(b, s)      # le crochet rentre apres sa tangente
                bascule = True
            v = releve(b)
            if v:
                print("      +%3d s : %d/%d objectifs pris | %d attaquants vivants | %d defenseurs vivants"
                      % (t, v[0], a.cellules, v[1], v[2]), flush=True)
        v = releve(b)
        b.send("{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_C; HMT_C = []; "
               "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;", wait=False)
        if v:
            tot_ep += a.cellules
            tot_pris += v[0]
            tot_pertes += (a.cellules * a.nA - v[1])
        time.sleep(3)
    _fermer(b)

    prise = tot_pris / float(max(tot_ep, 1))
    pertes_par_ep = tot_pertes / float(max(tot_ep, 1))
    pertes_par_prise = tot_pertes / float(max(tot_pris, 1)) if tot_pris else float("nan")
    print("", flush=True)
    print("=== RESULTAT ARMA — doctrine %s ===" % a.doctrine, flush=True)
    print("  episodes            : %d" % tot_ep, flush=True)
    print("  objectifs pris      : %d  (%.1f %%)" % (tot_pris, 100 * prise), flush=True)
    print("  pertes par episode  : %.2f sur %d" % (pertes_par_ep, a.nA), flush=True)
    print("  pertes par prise    : %.2f" % pertes_par_prise, flush=True)
    if tot_pris:
        print("  PRISE-A-PERTES      : %.1f" % (prise / max(pertes_par_prise, 1e-6)), flush=True)
    out = a.out or ("banc_arma_%s.json" % a.doctrine)
    json.dump({"doctrine": a.doctrine, "episodes": tot_ep, "prise": prise,
               "pertes_par_episode": pertes_par_ep, "pertes_par_prise": pertes_par_prise,
               "nA": a.nA, "nD": a.nD, "rspawn": a.rspawn, "duree_s": a.duree},
              open(LEV + "/" + out, "w"), indent=1)
    print("-> %s/%s" % (LEV, out), flush=True)
    print("BANCARMA_DONE", flush=True)


if __name__ == "__main__":
    main()
