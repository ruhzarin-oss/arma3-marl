#!/usr/bin/env python3
"""garnison — photographie puis REPOSE la garnison EAST a l'identique entre deux episodes.

Sans ca, le balayage est fausse en silence : chaque episode tue des defenseurs, et
l'episode suivant part avec une garnison amputee. Les runs du 23/07 le montrent deja
(east_start = 8, puis 7, puis 8). Un balayage de rapport de forces ne veut rien dire si le
denominateur bouge tout seul.

  garnison.py photo    -> ecrit garnison_<theatre>.json (type, x, y, cap, posture)
  garnison.py repose   -> supprime tout EAST et recree exactement la photo
"""
import sys
import json
import time

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
P = chr(37)
LEV = "/home/younes/arma3-marl/leviathan"


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "photo"
    th = sys.argv[2] if len(sys.argv) > 2 else "stratis"
    T = theatre.use(th)
    F = LEV + "/garnison_%s.json" % th
    b = NativeBridge(port=T.PORT)
    try:
        if cmd == "photo":
            q = ("private _o = " + Q + Q + "; "
                 "{ _o = _o + format [" + Q + P + "1|" + P + "2|" + P + "3|" + P + "4;" + Q + ", "
                 "  typeOf _x, round (getPosATL _x select 0), round (getPosATL _x select 1), round (getDir _x)]; "
                 "} forEach (allUnits select {side _x == east}); "
                 "(format [" + Q + "GAR " + P + "1" + Q + ", _o]) call HMT_EMIT;")
            r = b.query(q, r"GAR (\S+)", want=1, timeout=40)
            if not r:
                print("PAS DE REPONSE")
                return 2
            g = []
            for it in r[-1].group(1).strip(";").split(";"):
                p = it.split("|")
                if len(p) == 4:
                    g.append({"type": p[0], "x": int(p[1]), "y": int(p[2]), "dir": int(p[3])})
            json.dump(g, open(F, "w"), indent=1)
            print("garnison photographiee : %d unites EAST -> %s" % (len(g), F))
            return 0

        g = json.load(open(F))
        c = ["{ if (side _x == east) then { deleteVehicle _x } } forEach allUnits; "
             "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "
             "HMT_GAR = []; "]
        for i, u in enumerate(g):
            if i % 8 == 0:
                c.append("HMT_GG = createGroup east; ")
            c.append("private _u = HMT_GG createUnit [" + Q + u["type"] + Q + ", "
                     "[" + str(u["x"]) + "," + str(u["y"]) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
                     "if (!isNull _u) then { _u setPosATL [" + str(u["x"]) + "," + str(u["y"]) + ",0]; "
                     "_u setDir " + str(u["dir"]) + "; _u setSkill 0.5; "
                     "_u setBehaviour " + Q + "COMBAT" + Q + "; _u setCombatMode " + Q + "RED" + Q + "; "
                     "_u disableAI " + Q + "PATH" + Q + "; "
                     "_u enableSimulation true; _u enableDynamicSimulation false; "
                     "HMT_GAR pushBack _u }; ")
        c.append("(format [" + Q + "REP " + P + "1" + Q + ", count HMT_GAR]) call HMT_EMIT;")
        r = b.query("".join(c), r"REP (\d+)", want=1, timeout=90)
        print("garnison reposee : %s / %d attendues" % (r[-1].group(1) if r else "ECHEC", len(g)))
        time.sleep(2)
        return 0 if r else 2
    finally:
        try:
            b.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
