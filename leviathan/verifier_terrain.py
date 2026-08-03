#!/usr/bin/env python3
"""verifier_terrain.py — LE BANC EST-IL POSE SUR UN TERRAIN QUI MESURE QUELQUE CHOSE ?

Trois questions, en dur, dans le moteur :
  1. eau ou terre ? (objectif, depart, et les deux flancs)
  2. relief plat ou pas ? (une plaine salee donne les memes signes que du bon terrain
     tout en detruisant l asymetrie de couvert qui justifie ce theatre)
  3. le couvert est-il vraiment ASYMETRIQUE ? batiments et objets a 40 m de l objectif,
     puis dans le couloir frontal contre les deux flancs.

Ne modifie rien. Une seule connexion, quelques requetes, puis close().
"""
import sys, os, math, json
sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

T = theatre.use(os.environ.get("HMT_THEATRE", "altis").strip().lower())
fx, fy = T.FOB
sx, sy = T.SPAWN
Q = chr(34)

b = NativeBridge(port=T.PORT)


def q(sqf, motif, timeout=25):
    r = b.query(sqf, motif, want=1, timeout=timeout)
    return r[-1] if r else None


def point(nom, x, y):
    sqf = ("private _p = [%.0f,%.0f]; "
           "(format [%sPT %%1 %%2 %%3%s, str (surfaceIsWater _p), "
           "round (getTerrainHeightASL _p), count (nearestTerrainObjects [_p, [], 40])]) call HMT_EMIT;"
           % (x, y, Q, Q))
    m = q(sqf, r"PT (\w+) (-?\d+) (\d+)")
    if not m:
        print("  %-22s : MUET" % nom); return None
    eau, alt, obj = m.group(1), int(m.group(2)), int(m.group(3))
    print("  %-22s : %s | altitude %4d m | %3d objets a 40 m"
          % (nom, "EAU" if eau.lower() == "true" else "terre", alt, obj))
    return {"eau": eau.lower() == "true", "alt": alt, "objets_40m": obj}


def relief(nom, x, y, R=120, N=8):
    """ecart d altitude sur un cercle : plat = plaine salee, accidente = terrain qui porte"""
    parts = []
    for i in range(N):
        a = 2 * math.pi * i / N
        parts.append("round (getTerrainHeightASL [%.0f,%.0f])" % (x + R * math.cos(a), y + R * math.sin(a)))
    sqf = ("(format [%sREL " % Q + " ".join(["%%%d" % (i + 1) for i in range(N)]) + "%s, " % Q
           + ", ".join(parts) + "]) call HMT_EMIT;")
    m = q(sqf, r"REL " + " ".join([r"(-?\d+)"] * N))
    if not m:
        print("  %-22s : MUET" % nom); return None
    h = [int(m.group(i + 1)) for i in range(N)]
    print("  %-22s : altitudes %s -> amplitude %d m" % (nom, h, max(h) - min(h)))
    return {"altitudes": h, "amplitude": max(h) - min(h)}


if __name__ == "__main__":
    print("=== VERIFICATION DU TERRAIN — theatre %s, objectif (%d,%d) ===" % (T.NAME, fx, fy))
    az = math.radians(T.APPROACH_AZ)
    # les deux flancs, perpendiculaires a l axe d approche, a 80 m de l objectif
    gx, gy = fx + math.sin(az + math.pi / 2) * 80, fy + math.cos(az + math.pi / 2) * 80
    dx, dy = fx + math.sin(az - math.pi / 2) * 80, fy + math.cos(az - math.pi / 2) * 80
    res = {}
    res["objectif"] = point("objectif (FOB)", fx, fy)
    res["depart"] = point("depart attaquants", sx, sy)
    res["mi_chemin"] = point("mi-chemin frontal", (fx + sx) / 2, (fy + sy) / 2)
    res["flanc_gauche"] = point("flanc gauche 80 m", gx, gy)
    res["flanc_droit"] = point("flanc droit 80 m", dx, dy)
    print("")
    res["relief"] = relief("relief autour du FOB", fx, fy)
    print("")
    print("=== LECTURE ===")
    eaux = [k for k, v in res.items() if isinstance(v, dict) and v.get("eau")]
    if eaux:
        print("  !! DANS L EAU : %s — le banc ne mesure rien." % eaux)
    else:
        print("  aucun point dans l eau.")
    o = res.get("objectif") or {}
    fr = res.get("mi_chemin") or {}
    fl = [(res.get("flanc_gauche") or {}).get("objets_40m", 0), (res.get("flanc_droit") or {}).get("objets_40m", 0)]
    print("  couvert : objectif %s | couloir frontal %s | flancs %s"
          % (o.get("objets_40m"), fr.get("objets_40m"), fl))
    if fr.get("objets_40m") is not None and fl and max(fl) > 0:
        rap = max(fl) / max(fr.get("objets_40m"), 1)
        print("  asymetrie flanc/frontal : x%.2f  (%s)"
              % (rap, "le flanc est PLUS couvert — c est ce qu on veut" if rap > 1.3
                 else "couvert UNIFORME — le flanc ne peut pas se distinguer ici"))
    amp = (res.get("relief") or {}).get("amplitude")
    if amp is not None:
        print("  relief : amplitude %d m sur 120 m de rayon  (%s)"
              % (amp, "terrain qui porte" if amp >= 5 else "PLAT — plaine, le relief ne joue aucun role"))
    json.dump(res, open("/home/younes/arma3-marl/leviathan/verif_terrain_%s.json" % T.NAME, "w"), indent=1)
    b.close()
    print("VERIF_DONE")
