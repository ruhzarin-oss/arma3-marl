#!/usr/bin/env python3
"""sonde_arbitre — LA DETTE DE FABLE. Le SQF de l arbitre n a jamais touche le pont.

Une erreur SQF avale la requete ENTIERE en silence : on ne recoit rien, on croit a une
desynchro, et on cherche le bug au mauvais endroit. La seule parade est de tester les blocs
UN PAR UN, du plus petit au plus gros, en s arretant au premier muet.

Aucun jugement ici, aucune mesure : on demande seulement « est-ce que ca REPOND ».
"""
import sys, time, json
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from marge import scene
import arbitre as A

E = A.E
OK, KO = [], []

def essai(nom, sqf, motif, timeout=40):
    try:
        r = b.query(sqf, motif, want=1, timeout=timeout)
    except Exception as ex:
        KO.append((nom, type(ex).__name__)); print("  ⛔ %-26s MUET (%s)" % (nom, type(ex).__name__), flush=True); return None
    if not r:
        KO.append((nom, "vide")); print("  ⛔ %-26s AUCUNE REPONSE" % nom, flush=True); return None
    OK.append(nom); print("  ✅ %-26s %s" % (nom, " ".join(r[0].groups())[:70]), flush=True); return r[0]

b = NativeBridge(port=5801, timeout=90)
print("=" * 92); print(" SONDE — les quatre blocs SQF de l arbitre, un par un"); print("=" * 92, flush=True)
print("\n─── scene ───", flush=True)
print("  %s" % (scene(b, 0),), flush=True); time.sleep(3)

print("\n─── 0. primitives isolees ───", flush=True)
essai("getSuppression", E("Z %1", "round (1000 * getSuppression (leader HMT_GB))"), r"Z (\d+)")
essai("getTerrainHeightASL", E("Z %1", "round (getTerrainHeightASL [(getPosATL (leader HMT_GB)) select 0, (getPosATL (leader HMT_GB)) select 1])"), r"Z (-?\d+)")
essai("terrainIntersectASL", E("Z %1", "if (terrainIntersectASL [eyePos (leader HMT_GB), getPosASL (leader HMT_GO)]) then {1} else {0}"), r"Z (\d+)")
essai("lineIntersectsSurfaces", E("Z %1", "count (lineIntersectsSurfaces [eyePos (leader HMT_GB), getPosASL (leader HMT_GO), leader HMT_GB, objNull])"), r"Z (\d+)")
essai("hid pose par la scene", E("Z %1", "(leader HMT_GB) getVariable ['hid',-99]"), r"Z (-?\d+)")
essai("HMT_POS existe", E("Z %1", "if (isNil 'HMT_POS') then {0} else {1}"), r"Z (\d+)")

print("\n─── 1. SQF_ARMER ───", flush=True)
essai("armer (handlers + eid)", A.SQF_ARMER + E("HMTAA %1 %2 %3",
      "count (units HMT_GB)", "count (units HMT_GO)", "if (isNil 'HMT_OBJ') then {0} else {1}"),
      r"HMTAA (\d+) (\d+) (\d+)")

print("\n─── 2. SQF_ETAT ───", flush=True)
r = essai("etat (amis+contacts+evts)", A.SQF_ETAT + E("HMTAE %1 %2 %3 %4", "HMT_NBB", "HMT_RB", "HMT_RO", "HMT_RE"),
          r"HMTAE (\d+) (\S*) (\S*) (\S*)", timeout=60)

print("\n─── 3. SQF_ANNOTER ───", flush=True)
# un contact fictif et deux candidats, injectes en POSITIONS comme le fait l arbitre
pos = b.query(E("Z %1 %2", "round ((getPosATL (leader HMT_GB)) select 0)", "round ((getPosATL (leader HMT_GB)) select 1)"), r"Z (-?\d+) (-?\d+)", want=1, timeout=30)
if pos:
    x, y = (int(g) for g in pos[0].groups())
    ctc = "[%d,%d,1]" % (x, y + 200)
    dem = "[0,[[%d,%d],[%d,%d]]]" % (x + 15, y, x, y + 15)
    sqf = A.SQF_ANNOTER.replace("__CTC__", "[%s]" % ctc).replace("__DEM__", "[%s]" % dem)
    essai("annoter (1 contact, 2 cand)", sqf + E("HMTAN %1", "HMT_RA"), r"HMTAN (\S*)", timeout=60)

print("\n─── 4. SQF_MESURE ───", flush=True)
essai("mesure de fin", A.SQF_MESURE, r"HMTAM v=(\d+) d=(\d+) a=(-?\d+)")

print("\n─── 5. le monde a-t-il des morts a offrir ? (garde du tableau vide) ───", flush=True)
essai("tuer tous les bleus", '{ _x setDamage 1 } forEach (units HMT_GB);' + E("Z %1", "{alive _x} count (units HMT_GB)"), r"Z (\d+)")
essai("mesure sur ZERO vivant", A.SQF_MESURE, r"HMTAM v=(\d+) d=(\d+) a=(-?\d+)")
essai("etat sur ZERO vivant", A.SQF_ETAT + E("HMTAE %1 %2 %3 %4", "HMT_NBB", "HMT_RB", "HMT_RO", "HMT_RE"),
      r"HMTAE (\d+) (\S*) (\S*) (\S*)", timeout=60)

b.close()
print("\n" + "=" * 92)
print("  %d blocs repondent, %d muets" % (len(OK), len(KO)))
if KO:
    print("  ⛔ LA DETTE N EST PAS SOLDEE — a reparer avant tout banc :")
    for n, w in KO: print("     · %-28s (%s)" % (n, w))
else:
    print("  ✅ LES QUATRE BLOCS REPONDENT, y compris sur un monde SANS AUCUN VIVANT.")
    print("     La regle « tester les primitives une par une » est honoree.")
json.dump({"ok": OK, "ko": KO}, open('/mnt/data/sonde_arbitre.json', 'w'), indent=1)
