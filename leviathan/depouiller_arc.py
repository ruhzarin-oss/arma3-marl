#!/usr/bin/env python3
"""depouiller_arc — deuxieme lecture des memes donnees, avec une origine de temps commune.

Le depouillement inscrit dans les criteres jette toute cellule ou l'attaquant n'a pas tire.
La regle etait faite pour eliminer les cellules cassees. Elle a un effet de bord qu'il faut
dire : aux angles AVANT, c'est le DEFENSEUR qui tire le premier et l'attaquant n'a jamais
l'occasion d'ouvrir le feu. Ces cellules-la ne sont pas cassees — elles sont le resultat.

On garde donc les deux lectures, cote a cote, sans en effacer une :

  LECTURE A (criteres, 82f3dad52683dd8f) : origine = premier tir de l'attaquant ;
            cellules sans tir attaquant JETEES.
  LECTURE B (origine commune) : les cinq cellules d'une repetition sont creees par la MEME
            commande, donc elles partagent l'horloge. Origine = le premier coup tire dans
            la repetition, quel qu'en soit l'auteur. Aucune cellule n'est jetee ; la
            comparaison entre angles reste propre puisque l'origine est commune.

Les SEUILS sont ceux des criteres, inchanges, appliques aux deux lectures.
"""
import sys
import json

LEV = "/home/younes/arma3-marl/leviathan"
F = sys.argv[1] if len(sys.argv) > 1 else LEV + "/sonde_arc_contact_lambs.json"
D = json.load(open(F))
BRUT = D["brut"]
DUREE = float(D.get("duree_s", 75))
ANGLES = [0, 45, 90, 135, 180]


def med(v):
    v = sorted(v)
    n = len(v)
    if not n:
        return float("nan")
    return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])


def table(par, titre):
    print("")
    print("=== %s ===" % titre)
    print("  %5s %4s %11s %11s %10s %9s %8s" %
          ("angle", "n", "t_riposte", "t_direction", "riposte", "impacts", "tirs_def"))
    res = {}
    for ang in ANGLES:
        v = par.get(ang, [])
        if not v:
            print("  %5d %4d   (aucune donnee)" % (ang, 0))
            continue
        res[ang] = {
            "n": len(v),
            "t_rip": med([c["lat_rip"] for c in v]),
            "t_dir": med([c["lat_dir"] for c in v]),
            "taux": sum(1 for c in v if c["lat_rip"] < DUREE - 0.01) / float(len(v)),
            "imp": sum(c["impacts"] for c in v) / float(len(v)),
            "tdef": sum(c["tirs_def"] for c in v) / float(len(v)),
            "lat": [c["lat_rip"] for c in v],
        }
        r = res[ang]
        print("  %5d %4d %11.1f %11.1f %9.0f%% %9.1f %8.1f"
              % (ang, r["n"], r["t_rip"], r["t_dir"], 100 * r["taux"], r["imp"], r["tdef"]))
    return res


def verdicts(res, nom):
    print("")
    print("--- verdicts (seuils figes) sur %s ---" % nom)
    if 0 not in res or 180 not in res:
        print("  donnees insuffisantes aux angles 0 et 180")
        return
    vite = sum(1 for x in res[0]["lat"] if x < 10.0)
    ok = vite >= max(4, int(round(0.8 * res[0]["n"])))
    print("  CANARI 0 deg : %d/%d ripostes < 10 s -> %s" % (vite, res[0]["n"], "OK" if ok else "ECHEC"))
    d = res[180]["t_rip"] - res[0]["t_rip"]
    print("  V1 : t_rip(180) - t_rip(0) = %+.1f s -> %s"
          % (d, "latence dorsale REELLE" if d >= 3.0 else "PAS d angle mort au contact"))
    jamais = sum(1 for x in res[180]["lat"] if x >= DUREE - 0.01)
    geo = jamais >= max(4, int(round(0.8 * res[180]["n"])))
    print("  V2 : %d/%d sans riposte a 180 deg -> %s"
          % (jamais, res[180]["n"], "GEOMETRIE" if geo else "COMPORTEMENT (latence)"))
    inv = [a for a in ANGLES if a in res and res[a]["t_dir"] > res[a]["t_rip"] + 0.5]
    print("  V3 : reorientation avant riposte -> %s" % ("OK partout" if not inv else "en defaut a %s" % inv))
    print("  V4 : impacts 180/0 = %.1f / %.1f = %.2f"
          % (res[180]["imp"], res[0]["imp"], res[180]["imp"] / max(res[0]["imp"], 1e-9)))
    print("  profil complet t_riposte : " + "  ".join("%d deg=%.1fs" % (a, res[a]["t_rip"]) for a in ANGLES if a in res))


# ---------- LECTURE A : celle des criteres ----------
parA = {}
jetes = 0
for c in BRUT:
    if c["tirs_att"] == 0 or c["t_att"] < 0:
        jetes += 1
        continue
    t0 = c["t_att"]
    parA.setdefault(c["angle"], []).append(dict(
        c, lat_rip=(c["t_def"] - t0) if c["t_def"] > 0 else DUREE,
        lat_dir=(c["t_dir"] - t0) if c["t_dir"] > 0 else DUREE))
print("LECTURE A : %d cellules retenues, %d jetees (attaquant muet)"
      % (sum(len(v) for v in parA.values()), jetes))
resA = table(parA, "LECTURE A — origine = premier tir de l'attaquant (criteres)")
verdicts(resA, "LECTURE A")

# ---------- LECTURE B : origine commune par repetition ----------
reps = {}
for c in BRUT:
    reps.setdefault(c["rep"], []).append(c)
parB = {}
muets = 0
for rep, cells in reps.items():
    ts = [c["t_att"] for c in cells if c["t_att"] > 0] + [c["t_def"] for c in cells if c["t_def"] > 0]
    if not ts:
        continue
    t0 = min(ts)
    for c in cells:
        if c["tirs_att"] == 0 and c["tirs_def"] == 0:
            muets += 1                      # cellule vraiment inerte : aucun des deux n a tire
            continue
        parB.setdefault(c["angle"], []).append(dict(
            c, lat_rip=(c["t_def"] - t0) if c["t_def"] > 0 else DUREE,
            lat_dir=(c["t_dir"] - t0) if c["t_dir"] > 0 else DUREE))
print("")
print("LECTURE B : %d cellules retenues, %d ecartees (aucun des deux n a tire)"
      % (sum(len(v) for v in parB.values()), muets))
resB = table(parB, "LECTURE B — origine commune a la repetition")
verdicts(resB, "LECTURE B")

# ---------- qui ouvre le feu ? ----------
print("")
print("=== QUI TIRE LE PREMIER, PAR ANGLE ===")
print("  %5s %6s %8s %8s %8s" % ("angle", "n", "def 1er", "att 1er", "att muet"))
for ang in ANGLES:
    v = [c for c in BRUT if c["angle"] == ang]
    if not v:
        continue
    dfirst = sum(1 for c in v if c["t_def"] > 0 and (c["t_att"] < 0 or c["t_def"] < c["t_att"]))
    afirst = sum(1 for c in v if c["t_att"] > 0 and (c["t_def"] < 0 or c["t_att"] <= c["t_def"]))
    amuet = sum(1 for c in v if c["tirs_att"] == 0)
    print("  %5d %6d %8d %8d %8d" % (ang, len(v), dfirst, afirst, amuet))
print("DEPOUILLE_DONE")
