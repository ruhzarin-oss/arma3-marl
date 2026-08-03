#!/usr/bin/env python3
"""sonde_pieces — ON REPART DE CE QUI SURVIT, ET ON AJOUTE UNE PIECE A LA FOIS.

J'ai devine cinq fois aujourd'hui et je me suis trompe cinq fois. Cinq suspects sont morts
par la mesure : le timeout, la charge, la transition, le combat lui-meme, mes ordres de tir.
La sonde de bissection tient 100 s et 205 balles avec douze unites ; le banc meurt a 12 s
avec seize.

Donc on arrete de deviner. On part de la sonde QUI SURVIT et on ajoute les pieces du banc
une par une, CUMULATIVEMENT. La premiere qui tue le pont est le coupable.

  piece 0  la sonde nue (connue bonne)                      -> temoin
  piece 1  + gestionnaire de degats sur les cibles          (se declenche a chaque balle)
  piece 2  + les marqueurs de carte envoyes avant le tir
  piece 3  + huit arroseurs au lieu de quatre
  piece 4  + ordres toutes les 4 s au lieu de 10
  piece 5  + la cible redevient VULNERABLE (le banc ne la protege que par HandleDamage->0)
  piece 6  + setVehicleAmmo / setUnitPos UP / setSkill, comme le banc
  piece 7  + le VRAI marqueurs() du banc, celui qui balaie allUnits

Chaque piece tourne sur un SERVEUR NEUF — sinon un pont deja mort fausserait la suivante.
Canari obligatoire avant chaque bras : sans capteur prouve, une absence ne veut rien dire.
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

NOMS = {0: "sonde nue (temoin)", 1: "+ gestionnaire de degats", 2: "+ marqueurs",
        3: "+ huit arroseurs", 4: "+ ordres toutes les 4 s",
        5: "+ cible VULNERABLE", 6: "+ setVehicleAmmo / UnitPos / skill",
        7: "+ le VRAI marqueurs() du banc"}

ap = argparse.ArgumentParser()
ap.add_argument("--piece", type=int, required=True, choices=[0, 1, 2, 3, 4, 5, 6, 7])
ap.add_argument("--duree", type=int, default=60)
ap.add_argument("--theatre", default="altis")
a = ap.parse_args()


def _fermer(b):
    try:
        b.close()
    except Exception:
        pass


def main():
    T = theatre.use(a.theatre)
    b = NativeBridge(port=T.PORT)
    piece = a.piece
    n_arroseurs = 2 if piece < 3 else 4          # par cellule supprimee
    periode = 4 if piece >= 4 else 10

    print("=== PIECE %d : %s ===" % (piece, NOMS[piece]), flush=True)
    print("    cumulatif | %d arroseurs par cellule | ordres toutes les %d s"
          % (n_arroseurs, periode), flush=True)
    if not b.query("(format [" + Q + "P " + P + "1" + Q + ", round diag_tickTime]) call HMT_EMIT;",
                   r"P (\d+)", want=1, timeout=20):
        print("  pont MUET au depart — le serveur n'est pas pret")
        _fermer(b)
        sys.exit(2)

    try:
        cel = json.load(open(LEV + "/cellules_altis.json"))["serie"]
    except Exception:
        print("  !! cellules certifiees introuvables — ARRET")
        _fermer(b)
        sys.exit(2)

    c = ["if (!isNil " + Q + "HMT_X" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_X }; "
         "HMT_X = []; HMT_DEF = []; HMT_CIB = []; HMT_NSUP = []; "
         "HMT_SHOTS = [0,0,0,0]; HMT_HITS = [0,0,0,0]; HMT_TQ = [-9,-9,-9,-9]; "
         "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "]
    cible_de = []
    for k in range(4):
        K = str(k)
        x, y = cel[k % len(cel)][0], cel[k % len(cel)][1]
        D = "[" + str(x) + "," + str(y) + ",0]"
        C = "[" + str(x) + "," + str(y + 100) + ",0]"
        c.append(
            "private _g" + K + " = createGroup east; "
            "private _d" + K + " = _g" + K + " createUnit [" + Q + "O_Soldier_F" + Q + ", " + D + ", [], 0, " + Q + "NONE" + Q + "]; "
            "_d" + K + " setPosATL " + D + "; _d" + K + " setSkill 0.5; _d" + K + " allowDamage false; "
            + ("_d" + K + " setVehicleAmmo 1; _d" + K + " setUnitPos " + Q + "UP" + Q + "; " if piece >= 6 else "")
            + 
            "_d" + K + " setBehaviour " + Q + "COMBAT" + Q + "; _d" + K + " setCombatMode " + Q + "RED" + Q + "; "
            "_d" + K + " disableAI " + Q + "PATH" + Q + "; _d" + K + " disableAI " + Q + "AUTOTARGET" + Q + "; "
            "_d" + K + " addEventHandler [" + Q + "Fired" + Q + ", { HMT_SHOTS set [" + K + ", (HMT_SHOTS select " + K + ") + 1] }]; "
            "private _h" + K + " = createGroup west; "
            "private _c" + K + " = _h" + K + " createUnit [" + Q + "B_Soldier_F" + Q + ", " + C + ", [], 0, " + Q + "NONE" + Q + "]; "
            "_c" + K + " setPosATL " + C + "; "
            + ("" if piece >= 5 else "_c" + K + " allowDamage false; ")
            + 
            "_c" + K + " disableAI " + Q + "PATH" + Q + "; _c" + K + " disableAI " + Q + "AUTOTARGET" + Q + "; "
            "_c" + K + " disableAI " + Q + "TARGET" + Q + "; _c" + K + " setBehaviour " + Q + "CARELESS" + Q + "; ")
        if piece >= 1:
            # PIECE 1 : le gestionnaire de degats du banc, tel quel — il se declenche
            # a CHAQUE balle qui touche, donc des centaines de fois par seance.
            c.append(
                "_c" + K + " addEventHandler [" + Q + "HandleDamage" + Q + ", { "
                "  if (diag_tickTime - (HMT_TQ select " + K + ") > 0.05) then { "
                "    HMT_TQ set [" + K + ", diag_tickTime]; "
                "    if ((_this select 3) == (HMT_DEF select " + K + ")) then { "
                "      HMT_HITS set [" + K + ", (HMT_HITS select " + K + ") + 1] } "
                "  }; 0 }]; ")
        c.append("HMT_X pushBack _d" + K + "; HMT_X pushBack _c" + K + "; "
                 "HMT_DEF pushBack _d" + K + "; HMT_CIB pushBack _c" + K + "; ")
        if k >= 2:
            for j in range(n_arroseurs):
                J = K + "_" + str(j)
                sx = x + (j - (n_arroseurs - 1) / 2.0) * 25
                S = "[" + ("%.0f" % sx) + "," + str(y - 120) + ",0]"
                cible_de.append(k)
                c.append(
                    "private _sg" + J + " = createGroup west; "
                    "private _s" + J + " = _sg" + J + " createUnit [" + Q + "B_Soldier_F" + Q + ", " + S + ", [], 0, " + Q + "NONE" + Q + "]; "
                    "_s" + J + " setPosATL " + S + "; _s" + J + " allowDamage false; "
                    + ("_s" + J + " setVehicleAmmo 1; _s" + J + " setUnitPos " + Q + "UP" + Q + "; " if piece >= 6 else "")
                    + 
                    "_s" + J + " setBehaviour " + Q + "COMBAT" + Q + "; _s" + J + " setCombatMode " + Q + "RED" + Q + "; "
                    "_s" + J + " disableAI " + Q + "PATH" + Q + "; _s" + J + " disableAI " + Q + "AUTOTARGET" + Q + "; "
                    "HMT_X pushBack _s" + J + "; HMT_NSUP pushBack _s" + J + "; ")
    c.append("(format [" + Q + "PRET " + P + "1 " + P + "2" + Q + ", count HMT_DEF, count HMT_NSUP]) call HMT_EMIT;")
    r = b.query("".join(c), r"PRET (\d+) (\d+)", want=1, timeout=120)
    if not r:
        print("  MORT DES LA POSE")
        _fermer(b)
        print("VERDICT piece %d : MORT (pose)" % piece, flush=True)
        sys.exit(1)
    nd, ns = int(r[-1].group(1)), int(r[-1].group(2))
    print("  poses : %d defenseurs, %d arroseurs (Python en attendait %d)"
          % (nd, ns, len(cible_de)), flush=True)
    if ns != len(cible_de):
        print("  !! DESACCORD entre le SQF et Python sur le nombre d arroseurs", flush=True)

    b.send("(HMT_DEF select 0) setVehicleAmmo 1; (HMT_DEF select 0) forceWeaponFire "
           "[currentMuzzle (HMT_DEF select 0), currentWeaponMode (HMT_DEF select 0)];", wait=False)
    time.sleep(4)
    can = b.query("(format [" + Q + "CAN " + P + "1" + Q + ", HMT_SHOTS select 0]) call HMT_EMIT;",
                  r"CAN (\d+)", want=1, timeout=20)
    # AUCUN n est PAS PAS-DE-REPONSE. Les deux cas ci-dessous disent des choses opposees
    # et je viens de les confondre une fois de plus.
    if not can:
        print("  canari SANS REPONSE — le pont est DEJA MORT a +4 s apres la pose", flush=True)
        _fermer(b)
        print("VERDICT piece %d : MORT a +4 s  <-- COUPABLE : %s" % (piece, NOMS[piece]), flush=True)
        sys.exit(1)
    if int(can[-1].group(1)) == 0:
        print("  canari REPOND 0 tir — le pont est VIF mais le coup force n a pas pris", flush=True)
        print("  on retente une fois", flush=True)
        b.send("(HMT_DEF select 0) setVehicleAmmo 1; (HMT_DEF select 0) forceWeaponFire "
               "[currentMuzzle (HMT_DEF select 0), currentWeaponMode (HMT_DEF select 0)];", wait=False)
        time.sleep(5)
        can = b.query("(format [" + Q + "CAN " + P + "1" + Q + ", HMT_SHOTS select 0]) call HMT_EMIT;",
                      r"CAN (\d+)", want=1, timeout=20)
        if not can or int(can[-1].group(1)) == 0:
            print("  canari toujours a zero — capteur NON PROUVE, on ne conclut rien", flush=True)
            _fermer(b)
            sys.exit(2)
    print("  canari : %s tir(s) -> capteur prouve" % can[-1].group(1), flush=True)

    if piece >= 7:
        # LE VRAI marqueurs() DU BANC, pas mon approximation. Il balaie allUnits pour
        # trouver le joueur — un balayage que ma version n avait pas.
        import importlib.util as _il
        _sp = _il.spec_from_file_location("_ms", LEV + "/mesurer_suppression.py")
        print("  marqueurs : version EXACTE du banc", flush=True)
        _g = chr(34)
        _vrai = ("{ deleteMarker _x } forEach (allMapMarkers select { (_x find " + _g + "hmtsup" + _g + ") == 0 }); "
                 "{ private _i = _forEachIndex; "
                 "  private _m = createMarker [format [" + _g + "hmtsup_d" + P + "1" + _g + ", _i], getPos _x]; "
                 "  _m setMarkerType " + _g + "mil_dot" + _g + "; _m setMarkerSize [1.2, 1.2]; "
                 "  if (_i < 2) then { _m setMarkerColor " + _g + "ColorBlue" + _g + "; _m setMarkerText " + _g + "temoin" + _g + "; } "
                 "  else { _m setMarkerColor " + _g + "ColorRed" + _g + "; _m setMarkerText " + _g + "ARROSE" + _g + "; }; "
                 "} forEach HMT_DEF; "
                 "{ private _m = createMarker [format [" + _g + "hmtsup_c" + P + "1" + _g + ", _forEachIndex], getPos _x]; "
                 "  _m setMarkerType " + _g + "mil_dot" + _g + "; _m setMarkerColor " + _g + "ColorWhite" + _g + "; "
                 "  _m setMarkerText " + _g + "cible" + _g + "; } forEach HMT_CIB; "
                 "{ private _m = createMarker [format [" + _g + "hmtsup_s" + P + "1" + _g + ", _forEachIndex], getPos _x]; "
                 "  _m setMarkerType " + _g + "mil_dot" + _g + "; _m setMarkerColor " + _g + "ColorOrange" + _g + "; "
                 "  _m setMarkerText " + _g + "arroseur" + _g + "; } forEach HMT_NSUP; "
                 "{ if (isPlayer _x) then { "
                 "  private _mj = createMarker [" + _g + "hmtsup_joueur" + _g + ", getPos _x]; "
                 "  _mj setMarkerType " + _g + "mil_dot" + _g + "; _mj setMarkerColor " + _g + "ColorGreen" + _g + "; "
                 "  _mj setMarkerSize [1.4, 1.4]; _mj setMarkerText " + _g + "TOI" + _g + "; } } forEach allUnits;")
        b.send(_vrai, wait=False)
        time.sleep(3)
    elif piece >= 2:
        # PIECE 2 : les marqueurs du banc, envoyes juste avant le tir, sans accuse.
        g = chr(34)
        mk = ("{ deleteMarker _x } forEach (allMapMarkers select { (_x find " + g + "hmtp" + g + ") == 0 }); "
              "{ private _m = createMarker [format [" + g + "hmtp_d" + P + "1" + g + ", _forEachIndex], getPos _x]; "
              "  _m setMarkerType " + g + "mil_dot" + g + "; _m setMarkerColor " + g + "ColorRed" + g + "; } forEach HMT_DEF; "
              "{ private _m = createMarker [format [" + g + "hmtp_c" + P + "1" + g + ", _forEachIndex], getPos _x]; "
              "  _m setMarkerType " + g + "mil_dot" + g + "; _m setMarkerColor " + g + "ColorWhite" + g + "; } forEach HMT_CIB; "
              "{ private _m = createMarker [format [" + g + "hmtp_s" + P + "1" + g + ", _forEachIndex], getPos _x]; "
              "  _m setMarkerType " + g + "mil_dot" + g + "; _m setMarkerColor " + g + "ColorOrange" + g + "; } forEach HMT_NSUP;")
        b.send(mk, wait=False)
        print("  marqueurs envoyes", flush=True)
        time.sleep(3)

    paires = ",".join("[" + str(i) + "," + str(k) + "]" for i, k in enumerate(cible_de))
    ordre = ("{ private _c = HMT_CIB select _forEachIndex; _x reveal [_c, 4]; _x doTarget _c; "
             "_x doFire _c; } forEach HMT_DEF; "
             "{ private _i = _x select 0; private _k = _x select 1; "
             "  if (_i < count HMT_NSUP && _k < count HMT_DEF) then { "
             "    private _u = HMT_NSUP select _i; private _v = HMT_DEF select _k; "
             "    _u reveal [_v, 4]; _u doTarget _v; _u doFire _v; }; "
             "} forEach [" + paires + "];")

    print("", flush=True)
    mort_a = -1
    t = 0
    while t < a.duree:
        b.send(ordre, wait=False)
        time.sleep(periode)
        t += periode
        if t % 10 < periode or periode >= 10:
            rr = b.query("(format [" + Q + "VIF " + P + "1" + Q + ", HMT_SHOTS select 0]) call HMT_EMIT;",
                         r"VIF (\d+)", want=1, timeout=15)
            if rr:
                print("    +%2d s : VIF (%s balles)" % (t, rr[-1].group(1)), flush=True)
            else:
                print("    +%2d s : MUET" % t, flush=True)
                if mort_a < 0:
                    mort_a = t
                break

    b.send("{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_X; HMT_X = []; "
           "{ deleteMarker _x } forEach (allMapMarkers select { (_x find " + Q + "hmtp" + Q + ") == 0 }); "
           "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;", wait=False)
    time.sleep(2)
    _fermer(b)
    print("", flush=True)
    if mort_a < 0:
        print("VERDICT piece %d : SURVIT (%d s)" % (piece, a.duree), flush=True)
    else:
        print("VERDICT piece %d : MORT a +%d s  <-- COUPABLE : %s" % (piece, mort_a, NOMS[piece]), flush=True)


if __name__ == "__main__":
    main()
