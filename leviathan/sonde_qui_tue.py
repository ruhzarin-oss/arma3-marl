#!/usr/bin/env python3
"""sonde_qui_tue — QUI TUE LE PONT : MES ORDRES, OU LE COMBAT ?

Ce qu'on sait maintenant, mesure du 28/07 : le pont est muet des le PREMIER releve
pendant le tir (+12 s) et ne revient jamais. Il ne meurt donc pas a la transition — il
meurt pendant la phase de tir. Trois causes sont deja mortes : le timeout (45 s, meme
echec), la charge (4 tireurs meurent comme 12), la transition (refutee a l'instant).

Il reste deux suspects, et un seul essai les separe :

  PHASE A   les memes unites sont posees, AUCUN ordre n'est envoye. On lit toutes les 10 s.
            Si le pont meurt -> c'est le COMBAT (ou la simple presence des unites).
            S'il tient       -> ce sont MES ORDRES.

  PHASE B   on envoie l'ordre de tir, et on continue a lire.
            Le pont meurt ici -> l'ordre est le coupable, et on saura en combien d'envois.

On ne conclut sur une absence que si le canari a prouve le capteur : phase 0.
"""
import sys
import time
import json

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
P = chr(37)
LEV = "/home/younes/arma3-marl/leviathan"


def _fermer(b):
    try:
        b.close()
    except Exception:
        pass


def lire(b, etiquette, t):
    r = b.query("(format [" + Q + "VIF " + P + "1" + Q + ", HMT_SHOTS select 0]) call HMT_EMIT;",
                r"VIF (\d+)", want=1, timeout=15)
    ok = bool(r)
    print("    %-8s +%2d s : %s" % (etiquette, t, ("VIF (%s balles)" % r[-1].group(1)) if ok else "MUET"),
          flush=True)
    return ok


def main(nom="altis"):
    T = theatre.use(nom)
    b = NativeBridge(port=T.PORT)
    res = {"phase_A_sans_ordre": [], "phase_B_avec_ordre": []}
    print("=== QUI TUE LE PONT : MES ORDRES, OU LE COMBAT ? ===", flush=True)

    if not b.query("(format [" + Q + "P " + P + "1" + Q + ", round diag_tickTime]) call HMT_EMIT;",
                   r"P (\d+)", want=1, timeout=20):
        print("  pont deja MUET au depart — relancer le serveur d'abord")
        _fermer(b)
        return
    print("  pont OK", flush=True)

    # --- cellules certifiees terre ferme (lecon du 27/07 : deux bancs mesuraient des noyes)
    try:
        cel = json.load(open(LEV + "/cellules_altis.json"))["serie"]
    except Exception:
        print("  !! cellules certifiees introuvables — ARRET (on ne pose plus a l'aveugle)")
        _fermer(b)
        return

    # --- le MEME dispositif que le banc de suppression : 4 defenseurs, 4 cibles, 8 arroseurs
    c = ["if (!isNil " + Q + "HMT_X" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_X }; "
         "HMT_X = []; HMT_DEF = []; HMT_CIB = []; HMT_NSUP = []; HMT_SHOTS = [0,0,0,0]; "
         "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "]
    for k in range(4):
        K = str(k)
        x, y = cel[k % len(cel)][0], cel[k % len(cel)][1]
        D = "[" + str(x) + "," + str(y) + ",0]"
        C = "[" + str(x) + "," + str(y + 100) + ",0]"
        c.append(
            "private _g" + K + " = createGroup east; "
            "private _d" + K + " = _g" + K + " createUnit [" + Q + "O_Soldier_F" + Q + ", " + D + ", [], 0, " + Q + "NONE" + Q + "]; "
            "_d" + K + " setPosATL " + D + "; _d" + K + " setSkill 0.5; _d" + K + " allowDamage false; "
            "_d" + K + " setBehaviour " + Q + "COMBAT" + Q + "; _d" + K + " setCombatMode " + Q + "RED" + Q + "; "
            "_d" + K + " disableAI " + Q + "PATH" + Q + "; _d" + K + " disableAI " + Q + "AUTOTARGET" + Q + "; "
            "_d" + K + " addEventHandler [" + Q + "Fired" + Q + ", { HMT_SHOTS set [" + K + ", (HMT_SHOTS select " + K + ") + 1] }]; "
            "private _h" + K + " = createGroup west; "
            "private _c" + K + " = _h" + K + " createUnit [" + Q + "B_Soldier_F" + Q + ", " + C + ", [], 0, " + Q + "NONE" + Q + "]; "
            "_c" + K + " setPosATL " + C + "; _c" + K + " allowDamage false; "
            "_c" + K + " disableAI " + Q + "PATH" + Q + "; _c" + K + " disableAI " + Q + "AUTOTARGET" + Q + "; "
            "_c" + K + " disableAI " + Q + "TARGET" + Q + "; _c" + K + " setBehaviour " + Q + "CARELESS" + Q + "; "
            "HMT_X pushBack _d" + K + "; HMT_X pushBack _c" + K + "; "
            "HMT_DEF pushBack _d" + K + "; HMT_CIB pushBack _c" + K + "; ")
        if k >= 2:                                  # deux cellules ont des arroseurs
            for j in (0, 1):
                J = K + "_" + str(j)
                S = "[" + str(x + (j * 2 - 1) * 25) + "," + str(y - 120) + ",0]"
                c.append(
                    "private _sg" + J + " = createGroup west; "
                    "private _s" + J + " = _sg" + J + " createUnit [" + Q + "B_Soldier_F" + Q + ", " + S + ", [], 0, " + Q + "NONE" + Q + "]; "
                    "_s" + J + " setPosATL " + S + "; _s" + J + " allowDamage false; "
                    "_s" + J + " setBehaviour " + Q + "COMBAT" + Q + "; _s" + J + " setCombatMode " + Q + "RED" + Q + "; "
                    "_s" + J + " disableAI " + Q + "PATH" + Q + "; _s" + J + " disableAI " + Q + "AUTOTARGET" + Q + "; "
                    "HMT_X pushBack _s" + J + "; HMT_NSUP pushBack _s" + J + "; ")
    c.append("(format [" + Q + "PRET " + P + "1 " + P + "2" + Q + ", count HMT_DEF, count HMT_NSUP]) call HMT_EMIT;")
    r = b.query("".join(c), r"PRET (\d+) (\d+)", want=1, timeout=120)
    if not r:
        print("  mise en place sans reponse — le pont meurt DES LA POSE")
        _fermer(b)
        return
    print("  %s defenseurs, %s arroseurs poses" % (r[-1].group(1), r[-1].group(2)), flush=True)

    # --- canari : prouver le capteur avant de conclure a une absence
    b.send("(HMT_DEF select 0) setVehicleAmmo 1; "
           "(HMT_DEF select 0) forceWeaponFire [currentMuzzle (HMT_DEF select 0), "
           "currentWeaponMode (HMT_DEF select 0)];", wait=False)
    time.sleep(4)
    can = b.query("(format [" + Q + "CAN " + P + "1" + Q + ", HMT_SHOTS select 0]) call HMT_EMIT;",
                  r"CAN (\d+)", want=1, timeout=20)
    n_can = int(can[-1].group(1)) if can else 0
    print("  canari : %d tir(s) enregistre(s) -> capteur %s"
          % (n_can, "PROUVE" if n_can > 0 else "MUET, on ne conclura rien"), flush=True)
    if n_can == 0:
        _fermer(b)
        return

    print("", flush=True)
    print("  --- PHASE A : les unites sont la, AUCUN ordre n'est envoye ---", flush=True)
    for t in range(10, 51, 10):
        time.sleep(10)
        res["phase_A_sans_ordre"].append({"t": t, "vif": lire(b, "A", t)})
    a_ok = all(x["vif"] for x in res["phase_A_sans_ordre"])

    if not a_ok:
        print("", flush=True)
        print("  >>> LE PONT MEURT SANS QUE J'ENVOIE QUOI QUE CE SOIT.", flush=True)
        print("      Ce ne sont pas mes ordres : c'est la presence des unites, ou le combat", flush=True)
        print("      qu'elles engagent d'elles-memes (COMBAT + RED).", flush=True)
    else:
        print("", flush=True)
        print("  --- PHASE B : on envoie l'ordre de tir, on continue a lire ---", flush=True)
        ordre = ("{ private _c = HMT_CIB select _forEachIndex; _x reveal [_c, 4]; "
                 "_x doTarget _c; _x doFire _c; } forEach HMT_DEF;")
        for t in range(10, 51, 10):
            b.send(ordre, wait=False)
            time.sleep(10)
            res["phase_B_avec_ordre"].append({"t": t, "vif": lire(b, "B", t)})
        b_ok = all(x["vif"] for x in res["phase_B_avec_ordre"])
        print("", flush=True)
        if b_ok:
            print("  >>> LE PONT TIENT DANS LES DEUX PHASES. Le coupable est ailleurs :", flush=True)
            print("      la difference avec le banc est le NOMBRE d'unites ou la duree.", flush=True)
        else:
            mort = next(x["t"] for x in res["phase_B_avec_ordre"] if not x["vif"])
            print("  >>> CE SONT MES ORDRES. Le pont tient a vide et meurt a +%d s apres" % mort, flush=True)
            print("      le premier ordre de tir. Suspect : reveal/doTarget/doFire repetes.", flush=True)

    b.send("{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_X; HMT_X = []; "
           "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;", wait=False)
    time.sleep(2)
    _fermer(b)
    json.dump(res, open(LEV + "/sonde_qui_tue.json", "w"), indent=1)
    print("-> %s/sonde_qui_tue.json" % LEV, flush=True)
    print("QUITUE_DONE", flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "altis")
