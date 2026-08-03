#!/usr/bin/env python3
"""poser_fob_ligne — la garnison en LIGNE, la geometrie que le projet a deja certifiee.

Pourquoi ce fichier existe : mon premier poseur (`poser_fob.py`) placait les 8 defenseurs
en ANNEAU a 20 m autour du FOB. C'est exactement la forme dont la certification du 22/07
dit qu'elle ne recompense PAS le contournement — « on ne flanque pas un point ». L'eclaireur
lance dessus a rendu « le flanc ne paie nulle part », ce qui mesurait mon anneau et pas Arma.

La geometrie certifiee est une LIGNE : les defenseurs etales en arc DEVANT l'objectif, sur
l'axe d'ou vient l'assaut, chacun FACE AU DEHORS. Contourner le BOUT de la ligne devient
alors possible — c'est ce qui donne sa raison d'etre au debordement.

Parametres repris du banc fige (DURETE_FIGEE.md, 0eeae9efcdd67572) :
    rline = 37 m devant l'objectif, etalement +-20 deg, face a l'exterieur.
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
RLINE = 37.0
SPREAD = 20.0


def main():
    T = theatre.use("stratis")
    fx, fy = T.FOB
    az0 = math.radians(T.APPROACH_AZ)      # l'axe d'ou vient l'assaut
    b = NativeBridge(port=T.PORT)
    try:
        c = ["{ if (side _x == east) then { deleteVehicle _x } } forEach allUnits; "
             "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "
             "HMT_GAR = []; HMT_GG = createGroup east; "]
        for i in range(ND):
            frac = (i / max(ND - 1, 1) - 0.5) * 2.0          # -1..1
            az = az0 + frac * math.radians(SPREAD)
            x = fx + RLINE * math.sin(az)
            y = fy + RLINE * math.cos(az)
            c.append("private _u = HMT_GG createUnit [" + Q + "O_Soldier_F" + Q + ", "
                     "[" + ("%.1f" % x) + "," + ("%.1f" % y) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
                     "if (!isNull _u) then { _u setPosATL [" + ("%.1f" % x) + "," + ("%.1f" % y) + ",0]; "
                     "_u setDir " + ("%.1f" % math.degrees(az)) + "; "            # face au DEHORS
                     "_u setSkill 0.5; _u setUnitPos " + Q + "MIDDLE" + Q + "; "
                     "_u setBehaviour " + Q + "COMBAT" + Q + "; _u setCombatMode " + Q + "RED" + Q + "; "
                     "_u disableAI " + Q + "PATH" + Q + "; "                       # la ligne TIENT
                     "_u enableSimulation true; _u enableDynamicSimulation false; "
                     "HMT_GAR pushBack _u }; ")
        c.append("(format [" + Q + "POSE " + P + "1" + Q + ", count HMT_GAR]) call HMT_EMIT;")
        r = b.query("".join(c), r"POSE (\d+)", want=1, timeout=90)
        print("ligne defensive posee : %s / %d (rline %.0f m, etalement +-%.0f deg, face dehors)"
              % (r[-1].group(1) if r else "ECHEC", ND, RLINE, SPREAD))
        time.sleep(2)
        return 0 if r else 2
    finally:
        try:
            b.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
