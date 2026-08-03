#!/usr/bin/env python3
"""COMBIEN D'HOMMES UN SOLDAT ENGAGE-T-IL EN 3,28 s ? — MESURE SUR LE CAMP QUI SE BAT.

Le sandbox appliquait les 1,15 balles/pas mesurees sur Arma a CHAQUE adversaire separement.
Avec quatre adversaires, un defenseur tirait 4,6 balles par pas. Corriger ca fait passer la
prise frontale de 22 % a 81 % et fait disparaitre l'avantage du flanc. Rien d'interne ne
peut arbitrer : il faut le chiffre d'Arma.

QUATRE RUNS ONT ECHOUE avant celui-ci, et l'echec est instructif :
  - les DEFENSEURS ne tirent JAMAIS dans ce dispositif — zero coup en 60 s, meme avec un
    `doFire` explicite — alors que les ATTAQUANTS tirent 300 a 424 coups ;
  - la difference tenait a `AUTOTARGET`. Tous les bancs du projet qui fonctionnent le
    DESACTIVENT ; je l'avais laisse actif, justement pour observer la selection libre.

D'ou ce banc : on mesure sur les ATTAQUANTS, qui se battent avec `AUTOTARGET` actif. La
question est symetrique — « combien d'hommes un soldat prend-il a partie » ne depend pas du
camp. Une seule impulsion au depart, chacun sur un adversaire DIFFERENT, puis plus aucun
ordre. La premiere fenetre, marquee par l'impulsion, est ecartee.
"""
import sys
import time
import json
import argparse

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
P = chr(37)
LEV = "/home/younes/arma3-marl/leviathan"
PAS = 3.28

ap = argparse.ArgumentParser()
ap.add_argument("--tireurs", type=int, default=4, help="ceux qu'on observe")
ap.add_argument("--cibles", type=int, default=8, help="adversaires disponibles")
ap.add_argument("--dist", type=int, default=100)
ap.add_argument("--fenetres", type=int, default=16)
ap.add_argument("--skill", type=float, default=0.5)
ap.add_argument("--theatre", default="altis")
ap.add_argument("--out", default="repartition_feu.json")
a = ap.parse_args()


def fermer(b):
    try:
        b.close()
    except Exception:
        pass


def main():
    b = NativeBridge(port=theatre.use(a.theatre).PORT)
    print("=== COMBIEN D'HOMMES UN SOLDAT ENGAGE-T-IL EN %.2f s ? ===" % PAS, flush=True)
    print("    %d tireurs observes vs %d cibles a %d m | AUTOTARGET actif, UNE seule impulsion"
          % (a.tireurs, a.cibles, a.dist), flush=True)
    ok = False
    for e in range(12):
        if b.query("(format [" + Q + "P " + P + "1" + Q + ", round diag_tickTime]) call HMT_EMIT;",
                   r"P (\d+)", want=1, timeout=20):
            ok = True
            break
        time.sleep(10)
    if not ok:
        print("  mission muette apres 12 essais"); fermer(b); sys.exit(2)

    cel = json.load(open(LEV + "/cellules_altis.json"))["serie"]
    x, y = cel[0][0], cel[0][1]

    env = []
    env.append("if (!isNil " + Q + "HMT_X" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_X }; "
               "HMT_X = []; HMT_T = []; HMT_C = []; HMT_S = []; HMT_G = []; "
               "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; ")
    env.append("HMT_GT = createGroup west; ")
    for k in range(a.tireurs):
        px = x + (k - (a.tireurs - 1) / 2.0) * 20
        env.append("HMT_S pushBack 0; HMT_G pushBack []; "
                   "HMT_U = HMT_GT createUnit [" + Q + "B_Soldier_F" + Q + ", ["
                   + ("%.0f" % px) + "," + str(y) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
                   "HMT_U setPosATL [" + ("%.0f" % px) + "," + str(y) + ",0]; "
                   "HMT_U setSkill " + ("%.2f" % a.skill) + "; HMT_U setUnitPos " + Q + "UP" + Q + "; "
                   "HMT_U allowDamage false; HMT_U setVehicleAmmo 1; "
                   "HMT_U setBehaviour " + Q + "COMBAT" + Q + "; HMT_U setCombatMode " + Q + "RED" + Q + "; "
                   "HMT_U disableAI " + Q + "PATH" + Q + "; "
                   "HMT_X pushBack HMT_U; HMT_T pushBack HMT_U; ")
    env.append("HMT_GC = createGroup east; ")
    for k in range(a.cibles):
        cx = x + (k - (a.cibles - 1) / 2.0) * 12
        env.append("HMT_U = HMT_GC createUnit [" + Q + "O_Soldier_F" + Q + ", ["
                   + ("%.0f" % cx) + "," + str(y + a.dist) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
                   "HMT_U setPosATL [" + ("%.0f" % cx) + "," + str(y + a.dist) + ",0]; "
                   "HMT_U setSkill " + ("%.2f" % a.skill) + "; HMT_U setUnitPos " + Q + "UP" + Q + "; "
                   "HMT_U allowDamage false; HMT_U setVehicleAmmo 1; "
                   "HMT_U setBehaviour " + Q + "COMBAT" + Q + "; HMT_U setCombatMode " + Q + "RED" + Q + "; "
                   "HMT_U disableAI " + Q + "PATH" + Q + "; "
                   "HMT_X pushBack HMT_U; HMT_C pushBack HMT_U; ")
    # le capteur : a chaque tir, on note le tireur ET la cible QU'IL a choisie
    env.append("{ _x addEventHandler [" + Q + "Fired" + Q + ", { "
               "  private _u = _this select 0; private _k = HMT_T find _u; "
               "  if (_k >= 0) then { HMT_S set [_k, (HMT_S select _k) + 1]; "
               "    private _i = HMT_C find (currentTarget _u); "
               "    if (_i >= 0 && !(_i in (HMT_G select _k))) then { (HMT_G select _k) pushBack _i }; "
               "  }; }]; } forEach HMT_T; ")

    for m in env:                      # un message par unite : HMT_U ne traverse pas un envoi
        b.send(m, wait=False)
        time.sleep(0.5)
    time.sleep(2)
    r = b.query("(format [" + Q + "PRET " + P + "1 " + P + "2" + Q + ", count HMT_T, count HMT_C]) call HMT_EMIT;",
                r"PRET (\d+) (\d+)", want=1, timeout=60)
    if not r:
        print("  MORT DES LA POSE"); fermer(b); sys.exit(1)
    print("  poses : %s tireurs, %s cibles" % (r[-1].group(1), r[-1].group(2)), flush=True)

    b.send("{ private _u = _x; { _u reveal [_x, 4] } forEach HMT_C; } forEach HMT_T; "
           "{ private _u = _x; { _u reveal [_x, 4] } forEach HMT_T; } forEach HMT_C;", wait=False)
    time.sleep(3)
    # IMPULSION UNIQUE, chacun sur une cible DIFFERENTE. Ensuite : plus aucun ordre.
    amorce = ("{ private _c = HMT_C select (_forEachIndex % count HMT_C); "
              "  _x doTarget _c; _x doFire _c; } forEach HMT_T;")
    b.send(amorce, wait=False)
    time.sleep(6)

    n = 0
    for e in range(5):
        t = b.query("private _o = 0; { _o = _o + _x } forEach HMT_S; "
                    "(format [" + Q + "TOT " + P + "1" + Q + ", _o]) call HMT_EMIT;",
                    r"TOT (\d+)", want=1, timeout=20)
        n = int(t[-1].group(1)) if t else 0
        if n > 0:
            break
        print("  canari : 0 tir (essai %d), on relance l'impulsion" % (e + 1), flush=True)
        b.send(amorce, wait=False)
        time.sleep(6)
    if n == 0:
        print("  >>> PERSONNE NE TIRE. Capteur non prouve : ON NE CONCLUT RIEN.", flush=True)
        fermer(b); sys.exit(2)
    print("  canari : %d tir(s) -> capteur PROUVE" % n, flush=True)

    lire = ("private _s = " + Q + Q + "; { _s = _s + format [" + Q + P + "1," + Q + ", _x] } forEach HMT_S; "
            "private _g = " + Q + Q + "; { _g = _g + format [" + Q + P + "1," + Q + ", count _x] } forEach HMT_G; "
            "(format [" + Q + "W " + P + "1 " + P + "2" + Q + ", _s, _g]) call HMT_EMIT; "
            "{ HMT_S set [_forEachIndex, 0] } forEach HMT_S; "
            "{ HMT_G set [_forEachIndex, []] } forEach HMT_G;")

    print("", flush=True)
    print("  fenetre   balles/tireur   hommes differents/tireur   tireurs actifs", flush=True)
    fen = []
    muet = 0
    for w in range(a.fenetres):
        time.sleep(PAS)
        rr = b.query(lire, r"W ([\d,]+) ([\d,]+)", want=1, timeout=20)
        if not rr:
            muet += 1
            print("    %2d      pont MUET" % (w + 1), flush=True)
            if muet >= 3:
                break
            continue
        muet = 0
        sh = [int(v) for v in rr[-1].group(1).rstrip(",").split(",") if v.strip().isdigit()]
        tg = [int(v) for v in rr[-1].group(2).rstrip(",").split(",") if v.strip().isdigit()]
        act = [i for i in range(len(sh)) if sh[i] > 0]
        if not act:
            print("    %2d          aucun tireur actif" % (w + 1), flush=True)
            continue
        bal = sum(sh) / float(len(act))
        hom = sum(tg[i] for i in act) / float(len(act))
        print("    %2d          %6.2f                 %6.2f                %d/%d"
              % (w + 1, bal, hom, len(act), len(sh)), flush=True)
        if w > 0:                       # la 1re fenetre porte la marque de l'impulsion
            fen.append({"balles": sh, "cibles": tg, "actifs": len(act)})

    b.send("{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_X; HMT_X = []; "
           "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;", wait=False)
    time.sleep(2)
    fermer(b)

    if not fen:
        print("  aucune fenetre exploitable — ON NE CONCLUT RIEN", flush=True)
        sys.exit(1)
    tot_act = sum(f["actifs"] for f in fen)
    bal_moy = sum(sum(f["balles"]) for f in fen) / float(tot_act)
    hom_moy = sum(sum(f["cibles"][i] for i in range(len(f["cibles"])) if f["balles"][i] > 0)
                  for f in fen) / float(tot_act)
    print("", flush=True)
    print("=== RESULTAT (%d fenetres de %.2f s, impulsion exclue) ===" % (len(fen), PAS), flush=True)
    print("  balles par tireur actif et par pas : %.2f   (sandbox : tir_par_pas = 1,15)" % bal_moy, flush=True)
    print("  hommes DIFFERENTS par tireur       : %.2f   (sandbox actuel : %d = tous)"
          % (hom_moy, a.cibles), flush=True)
    print("", flush=True)
    if hom_moy <= 0:
        print("  denominateur nul : aucune conclusion.", flush=True); sys.exit(2)
    if hom_moy < 1.5:
        print("  >>> UN SOLDAT ENGAGE UN SEUL HOMME A LA FOIS (%.2f)." % hom_moy, flush=True)
        print("      Le sandbox lui en faisait viser tous : `cible_unique=True` est fidele.", flush=True)
    elif hom_moy > 3:
        print("  >>> il en arrose plusieurs (%.2f) : l'ancien monde n'etait pas absurde." % hom_moy, flush=True)
    else:
        print("  >>> regime INTERMEDIAIRE (%.2f) : ni un ni tous. Il faudra un facteur," % hom_moy, flush=True)
        print("      pas un interrupteur.", flush=True)
    json.dump({"balles_par_tireur_par_pas": bal_moy, "hommes_par_tireur_par_pas": hom_moy,
               "tireurs": a.tireurs, "cibles": a.cibles, "dist": a.dist, "pas_s": PAS,
               "fenetres": fen}, open(LEV + "/" + a.out, "w"), indent=1)
    print("-> " + LEV + "/" + a.out, flush=True)
    print("REPART_DONE", flush=True)


if __name__ == "__main__":
    main()
