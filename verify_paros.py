"""verify_paros — controle chaque point du theatre Paros : terre/eau, bati (spawns hors des murs),
altitude, LOS vers l'objectif. Pre-vol obligatoire avant de lancer une op (anti-bug eau/mur)."""
import re
import paros as P
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
PTS = [("COMPLEXE", P.COMPLEXE), ("CRETE", P.CRETE), ("ATTENTE", P.ATTENTE), ("ATTENTE_E", P.ATTENTE_E),
       ("LIGNE_O", P.LIGNE_O), ("LIGNE_E", P.LIGNE_E), ("FLANC_O", P.FLANC_O), ("FLANC_E", P.FLANC_E),
       ("INF_O", P.INF_O), ("INF_E", P.INF_E), ("POSTE_RES", P.POSTE_RES), ("QRF_PT", P.QRF_PT), ("LZ", P.LZ),
       ("SPAWN_APPUI", P.SPAWN_APPUI), ("SPAWN_ASSAUT", P.SPAWN_ASSAUT), ("SPAWN_A_EST", P.SPAWN_A_EST), ("SPAWN_RESERVE", P.SPAWN_RESERVE)]
env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
cx, cy = P.COMPLEXE
sqf = "private _cz=(getTerrainHeightASL [%d,%d])+1.5;\n" % (cx, cy)
for name, (x, y) in PTS:
    sqf += ('diag_log format ["HARMATTAN_V %s h=%%1 eau=%%2 bat=%%3 los=%%4", round (getTerrainHeightASL [%d,%d]), '
            'surfaceIsWater [%d,%d,0], count (nearestObjects [[%d,%d,0],["House"],18]), '
            '!(terrainIntersectASL [[%d,%d,(getTerrainHeightASL [%d,%d])+1.5],[%d,%d,_cz]])];\n'
            % (name, x, y, x, y, x, y, x, y, x, y, cx, cy))
ls = env._query(sqf, settle=2.0)
print("=== PRE-VOL THEATRE PAROS ===")
print("  %-13s %5s %6s %5s %5s   %s" % ("point", "alt", "terre", "bati", "LOS", "verdict"))
ok = True
for name, _ in PTS:
    m = next((re.search(r"HARMATTAN_V %s h=(-?\d+) eau=(\w+) bat=(\d+) los=(\w+)" % name, l) for l in ls if "HARMATTAN_V %s " % name in l), None)
    if not m:
        print("  %-13s  (pas lu)" % name); ok = False; continue
    h, eau, bat, los = int(m.group(1)), m.group(2), int(m.group(3)), m.group(4)
    water = (eau == "true")
    spawn_in_wall = name.startswith("SPAWN") and bat > 0
    bad = water or spawn_in_wall
    verdict = "EAU!" if water else ("SPAWN DANS MUR!" if spawn_in_wall else "ok")
    if bad: ok = False
    print("  %-13s %4dm %6s %5d %5s   %s" % (name, h, "non" if not water else "OUI", bat, "oui" if los == "true" else "-", verdict))
print("\n>>> %s" % ("THEATRE VALIDE : tous les points sur terre, spawns degages." if ok else "A CORRIGER : voir les points marques."))
