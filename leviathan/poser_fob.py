#!/usr/bin/env python3
"""poser_fob — RECONSTRUIT une garnison de 8 defenseurs au FOB Maxwell.

⚠ A DIRE HAUT ET FORT : ce n'est PAS la garnison d'origine. Le serveur Stratis relance
aujourd'hui avec **zero unite EAST** (mesure : `est=0 unites=0 groupes=0`). La garnison de
mission qui servait de defense a l'A/B a 3 bras du 23/07 n'est pas la. On ne peut donc pas
reproduire le point zero a l'identique.

Ce qu'on reproduit, et c'est tout : **8 defenseurs qui TIENNENT le FOB Maxwell**, meme
point, meme effectif, meme comportement (COMBAT/RED, position tenue). Tout verdict tire de
ce banc est a lire comme « reconstruit », pas comme « reproduit ».
"""
import sys
import time
import math

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
P = chr(37)
ND = int(sys.argv[1]) if len(sys.argv) > 1 else 8
R = 20.0


def main():
    # THEATRE : stratis par defaut (comportement historique), altis via HMT_THEATRE.
    import os as _os
    T = theatre.use(_os.environ.get("HMT_THEATRE", "stratis").strip().lower())
    fx, fy = T.FOB
    b = NativeBridge(port=T.PORT)
    try:
        c = ["{ if (side _x == east) then { deleteVehicle _x } } forEach allUnits; "
             "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "
             "HMT_GAR = []; HMT_GG = createGroup east; "]
        for i in range(ND):
            az = 2.0 * math.pi * i / ND
            x = fx + R * math.sin(az)
            y = fy + R * math.cos(az)
            c.append("private _u = HMT_GG createUnit [" + Q + "O_Soldier_F" + Q + ", "
                     "[" + ("%.1f" % x) + "," + ("%.1f" % y) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
                     "if (!isNull _u) then { _u setPosATL [" + ("%.1f" % x) + "," + ("%.1f" % y) + ",0]; "
                     "_u setDir " + ("%.1f" % math.degrees(az)) + "; _u setSkill 0.5; "
                     "_u setUnitPos " + Q + "MIDDLE" + Q + "; "
                     "_u setBehaviour " + Q + "COMBAT" + Q + "; _u setCombatMode " + Q + "RED" + Q + "; "
                     "_u disableAI " + Q + "PATH" + Q + "; "
                     "_u enableSimulation true; _u enableDynamicSimulation false; "
                     "HMT_GAR pushBack _u }; ")
        c.append("(format [" + Q + "POSE " + P + "1" + Q + ", count HMT_GAR]) call HMT_EMIT;")
        r = b.query("".join(c), r"POSE (\d+)", want=1, timeout=90)
        print("garnison reconstruite : %s / %d" % (r[-1].group(1) if r else "ECHEC", ND))
        time.sleep(2)
        return 0 if r else 2
    finally:
        try:
            b.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
