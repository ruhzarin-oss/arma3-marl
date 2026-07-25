#!/usr/bin/env python3
"""bake_map.py — extrait le PLAN RÉEL autour de l'objectif (bâtiments + routes) depuis Arma en cours.

Sert de FOND DE CARTE aux schémas d'analyse : sans les murs et les rues, on ne peut pas juger
un contournement (« il est passé par où ? derrière quoi ? »).

Pour chaque objet : position, orientation, dimensions -> une empreinte au sol dessinable.
Sortie : leviathan/map_<monde>_<x>_<y>.json  (relu par analyse_run.py)

Usage : python bake_map.py --theatre altis [--radius 320]
"""
import sys, json, argparse, time
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

ap = argparse.ArgumentParser()
ap.add_argument("--radius", type=float, default=320.0)
ap.add_argument("--fob", default=None)
ap.add_argument("--chunk", type=int, default=45)
theatre.add_theatre_arg(ap)
a = ap.parse_args(); TH = theatre.apply_theatre_arg(a)
b = NativeBridge(port=TH.PORT)
fx, fy = [int(v) for v in (a.fob or TH.fob_str).split(",")] if a.fob else TH.FOB

r = b.query('(format ["W %1", worldName]) call HMT_EMIT;', r"W (\S+)", want=1, timeout=12)
world = r[-1].group(1) if r else "?"
print("=== plan de %s autour de [%d,%d] (rayon %.0f m) ===" % (world, fx, fy, a.radius), flush=True)

KINDS = {
    "bat": '["HOUSE","BUILDING","CHURCH","FORTRESS","HOSPITAL","FUELSTATION","LIGHTHOUSE","WALL","BUNKER","TOWER"]',
    "route": '["ROAD","MAIN ROAD","TRACK"]',
}


def collect(kind_sqf, tag):
    """récupère les empreintes par paquets (x, y, cap, largeur, longueur)."""
    n = b.query('HMT_BK = nearestTerrainObjects [[%d,%d,0], %s, %f]; (format ["N %%1", count HMT_BK]) call HMT_EMIT;'
                % (fx, fy, kind_sqf, a.radius), r"N (\d+)", want=1, timeout=40)
    total = int(n[-1].group(1)) if n else 0
    print("  %-6s : %d objets" % (tag, total), flush=True)
    out = []
    for start in range(0, total, a.chunk):
        # on garde AUSSI la HAUTEUR : sans elle, un muret de 80 cm bloque la vue autant qu'un immeuble
        # (c'est ce qui rendait les mesures d'appui et de couverture inexploitables le 25/07).
        q = ('private _o = ""; '
             'for "_i" from %d to (%d min ((count HMT_BK) - 1)) do { '
             '  private _x = HMT_BK select _i; private _p = getPosATL _x; private _bb = boundingBoxReal _x; '
             '  private _mn = _bb select 0; private _mx = _bb select 1; '
             '  _o = _o + format ["%%1,%%2,%%3,%%4,%%5,%%6;", round ((_p select 0) - %d), round ((_p select 1) - %d), '
             '        round (getDir _x), round ((_mx select 0) - (_mn select 0)), round ((_mx select 1) - (_mn select 1)), '
             '        round (10 * ((_mx select 2) - (_mn select 2)))]; '
             '}; (format ["CH %%1", _o]) call HMT_EMIT;') % (start, start + a.chunk - 1, fx, fy)
        rr = b.query(q, r"CH (.*)", want=1, timeout=40)
        if not rr:
            print("    (paquet %d sans réponse)" % start, flush=True); continue
        for t in rr[-1].group(1).strip().rstrip(";").split(";"):
            f = t.split(",")
            if len(f) >= 6 and f[0].lstrip("-").isdigit():
                out.append([int(f[0]), int(f[1]), int(f[2]), int(f[3]), int(f[4]), int(f[5]) / 10.0])
    return out


data = {"world": world, "cx": fx, "cy": fy, "radius": a.radius}
for tag, sqf in KINDS.items():
    data[tag] = collect(sqf, tag)
    time.sleep(0.2)

out = "/home/younes/arma3-marl/leviathan/map_%s_%d_%d.json" % (world.lower(), fx, fy)
json.dump(data, open(out, "w"))
print("\n-> %s  (%d bâtiments, %d segments de route)" % (out, len(data["bat"]), len(data["route"])), flush=True)
print("BAKE_DONE", flush=True)
