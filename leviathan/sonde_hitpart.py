#!/usr/bin/env python3
"""PEUT-ON COMPTER LES IMPACTS SUR UNE CIBLE INVULNERABLE ?

Le banc de suppression est coince entre deux exigences qui se contredisent :
  - compter les impacts passe par `HandleDamage`, qui n'existe que si la cible est
    vulnerable ;
  - une cible vulnerable MEURT, et son tireur devient muet — trois seances annulees le
    28/07 pour cette raison, plus le 13e defaut silencieux : `HandleDamage` renvoyant 0 ne
    protege pas.

`HitPart` se declenche quand le projectile touche le MODELE, pas quand le degat s'applique.
S'il survit a `allowDamage false`, le probleme tombe : compteur d'un cote, cible immortelle
de l'autre.

On ne le suppose pas, on le mesure. Deux cibles cote a cote, le meme tireur :
  A  allowDamage false + HitPart      <- l'hypothese
  B  vulnerable        + HandleDamage <- le temoin, dont on sait qu'il compte

Si A compte comme B, on adopte. Si A reste a zero, `HitPart` ne passe pas et on cherche
ailleurs. Si B lui-meme reste a zero, le tireur n'a rien touche et on ne conclut RIEN.
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


def main():
    T = theatre.use("altis")
    b = NativeBridge(port=T.PORT)
    print("=== HITPART SURVIT-IL A allowDamage false ? ===", flush=True)
    if not b.query("(format [" + Q + "P " + P + "1" + Q + ", round diag_tickTime]) call HMT_EMIT;",
                   r"P (\d+)", want=1, timeout=25):
        print("  pont MUET — serveur pas pret"); b.close(); return

    cel = json.load(open(LEV + "/cellules_altis.json"))["serie"]
    x, y = cel[0][0], cel[0][1]
    D = "[" + str(x) + "," + str(y) + ",0]"
    A = "[" + str(x - 15) + "," + str(y + 100) + ",0]"
    B = "[" + str(x + 15) + "," + str(y + 100) + ",0]"

    c = ("if (!isNil " + Q + "HMT_X" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_X }; "
         "HMT_X = []; HMT_TIR = 0; HMT_A = 0; HMT_B = 0; HMT_TA = -9; HMT_TB = -9; "
         "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "
         # --- le tireur, un seul, qui arrosera les deux cibles a tour de role
         "private _g = createGroup east; "
         "HMT_D = _g createUnit [" + Q + "O_Soldier_F" + Q + ", " + D + ", [], 0, " + Q + "NONE" + Q + "]; "
         "HMT_D setPosATL " + D + "; HMT_D setSkill 0.5; HMT_D allowDamage false; "
         "HMT_D setBehaviour " + Q + "COMBAT" + Q + "; HMT_D setCombatMode " + Q + "RED" + Q + "; "
         "HMT_D disableAI " + Q + "PATH" + Q + "; HMT_D disableAI " + Q + "AUTOTARGET" + Q + "; "
         "HMT_D addEventHandler [" + Q + "Fired" + Q + ", { HMT_TIR = HMT_TIR + 1 }]; "
         # --- A : INVULNERABLE, compte par HitPart (l'hypothese a prouver)
         "private _ha = createGroup west; "
         "HMT_CA = _ha createUnit [" + Q + "B_Soldier_F" + Q + ", " + A + ", [], 0, " + Q + "NONE" + Q + "]; "
         "HMT_CA setPosATL " + A + "; HMT_CA allowDamage false; "
         "HMT_CA disableAI " + Q + "PATH" + Q + "; HMT_CA disableAI " + Q + "AUTOTARGET" + Q + "; "
         "HMT_CA disableAI " + Q + "TARGET" + Q + "; HMT_CA setBehaviour " + Q + "CARELESS" + Q + "; "
         "HMT_CA addEventHandler [" + Q + "HitPart" + Q + ", { "
         "  if (diag_tickTime - HMT_TA > 0.05) then { HMT_TA = diag_tickTime; "
         "    if (((_this select 0) select 1) == HMT_D) then { HMT_A = HMT_A + 1 } }; }]; "
         # --- B : VULNERABLE, compte par HandleDamage (le temoin, dont on sait qu'il compte)
         "private _hb = createGroup west; "
         "HMT_CB = _hb createUnit [" + Q + "B_Soldier_F" + Q + ", " + B + ", [], 0, " + Q + "NONE" + Q + "]; "
         "HMT_CB setPosATL " + B + "; "
         "HMT_CB disableAI " + Q + "PATH" + Q + "; HMT_CB disableAI " + Q + "AUTOTARGET" + Q + "; "
         "HMT_CB disableAI " + Q + "TARGET" + Q + "; HMT_CB setBehaviour " + Q + "CARELESS" + Q + "; "
         "HMT_CB addEventHandler [" + Q + "HandleDamage" + Q + ", { "
         "  if (diag_tickTime - HMT_TB > 0.05) then { HMT_TB = diag_tickTime; "
         "    if ((_this select 3) == HMT_D) then { HMT_B = HMT_B + 1 } }; 0 }]; "
         "HMT_X = [HMT_D, HMT_CA, HMT_CB]; "
         "(format [" + Q + "PRET " + P + "1" + Q + ", count HMT_X]) call HMT_EMIT;")
    if not b.query(c, r"PRET (\d+)", want=1, timeout=90):
        print("  MORT DES LA POSE"); b.close(); return
    print("  1 tireur, 2 cibles a 100 m (A invulnerable, B vulnerable)", flush=True)

    for cible, nom in (("HMT_CA", "A invulnerable / HitPart"), ("HMT_CB", "B vulnerable / HandleDamage")):
        print("", flush=True)
        print("  --- on arrose %s pendant 30 s ---" % nom, flush=True)
        for _ in range(7):
            b.send("HMT_D setVehicleAmmo 1; HMT_D reveal [" + cible + ", 4]; "
                   "HMT_D doTarget " + cible + "; HMT_D doFire " + cible + ";", wait=False)
            time.sleep(4)
        r = b.query("(format [" + Q + "R " + P + "1 " + P + "2 " + P + "3 " + P + "4" + Q +
                    ", HMT_TIR, HMT_A, HMT_B, (if (alive HMT_CB) then {1} else {0})]) call HMT_EMIT;",
                    r"R (\d+) (\d+) (\d+) (\d+)", want=1, timeout=30)
        if not r:
            print("    pas de reponse — on ne conclut rien"); b.close(); return
        tir, na, nb, viv = (int(r[-1].group(i)) for i in (1, 2, 3, 4))
        print("    tirs cumules %d | impacts A(HitPart) %d | impacts B(HandleDamage) %d | B vivante %d"
              % (tir, na, nb, viv), flush=True)
        etat = {"tirs": tir, "A": na, "B": nb, "B_vivante": viv}

    print("", flush=True)
    if etat["A"] == 0 and etat["B"] == 0:
        print("  >>> AUCUN des deux compteurs ne bouge : le tireur n'a rien touche.", flush=True)
        print("      ON NE CONCLUT RIEN sur HitPart.", flush=True)
    elif etat["A"] > 0:
        print("  >>> HitPart COMPTE sur une cible invulnerable (%d impacts)." % etat["A"], flush=True)
        print("      Le banc peut garder ses cibles vivantes ET compter ses impacts.", flush=True)
    else:
        print("  >>> HitPart reste a ZERO alors que HandleDamage compte %d." % etat["B"], flush=True)
        print("      Il ne passe pas avec allowDamage false : chercher ailleurs.", flush=True)

    b.send("{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_X; HMT_X = []; "
           "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;", wait=False)
    time.sleep(2)
    b.close()
    print("HITPART_DONE", flush=True)


if __name__ == "__main__":
    main()
