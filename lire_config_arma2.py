#!/usr/bin/env python3
"""Seconde passe. La premiere a rendu `sensitivity` et `sensitivityEar`, et a dit ou sont
les deux autres :
  · `radius` est ABSENT de CfgVehicles et `sizeOf` rend 0 sur un serveur sans unite posee
    -> il faut une unite REELLE et `boundingBoxReal` (juger l ACTE, pas la table).
  · `audibleFire`/`visibleFire` sont ABSENTS de l arme et de son mode `Single`
    -> on sonde CfgAmmo.
  · la courbe est dans les MODES de l arme, et `Single` (120-400 m) plus `FullAuto` (0-30 m)
    LAISSENT UN TROU DE 30 A 120 m. Un fusil d Arma 3 a plus de deux modes : on les ENUMERE
    au lieu de les deviner.
"""
import sys, re, json
sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
ARME, SOLDAT, MUN = "arifle_MX_F", "B_Soldier_F", "B_65x39_Caseless"
b = NativeBridge(port=PORT, timeout=20)

# ── 1. ENUMERER LES MODES. Le nom peut valoir "this" (le mode est l arme elle-meme).
SQF1 = ('_m = getArray (configFile >> "CfgWeapons" >> "%s" >> "modes"); '
        'format ["HMTNM %%1", count _m] call HMT_EMIT; '
        '{ private _s = _x; if (_s == "") then { _s = "VIDE" }; '
        'format ["HMTMODE %%1 %%2", _forEachIndex, _s] call HMT_EMIT } forEach _m;') % ARME
r = b.query(SQF1, r"HMTNM (\d+)", want=1, timeout=30)
if not r:
    sys.exit("  ⛔ pas de reponse sur l enumeration des modes")
nm = int(r[0].group(1))
modes = {}
for s in b._log_lines(3000):
    m = re.match(r"HMTMODE (\d+) (\S+)", s.strip())
    if m:
        modes[int(m.group(1))] = m.group(2)
MODES = [modes[i] for i in sorted(modes)]
print("  %s : %d modes -> %s" % (ARME, nm, MODES))

# ── 2. LA COURBE DANS CHAQUE MODE ("this" = le noeud de l arme lui-meme)
CLES = ["minRange", "minRangeProbab", "midRange", "midRangeProbab", "maxRange", "maxRangeProbab"]
chemins, etiq = [], []
for md in MODES:
    base = ('configFile >> "CfgWeapons" >> "%s"' % ARME) if md == "this" \
        else ('configFile >> "CfgWeapons" >> "%s" >> "%s"' % (ARME, md))
    for k in CLES:
        chemins.append("(%s >> \"%s\")" % (base, k)); etiq.append((md, k))
for k in ["audibleFire", "visibleFire", "hit", "typicalSpeed", "indirectHitRange"]:
    chemins.append('(configFile >> "CfgAmmo" >> "%s" >> "%s")' % (MUN, k)); etiq.append(("CfgAmmo", k))
SQF2 = ('_p = [%s]; { private _e = _x; '
        'format ["HMTV %%1 %%2 %%3", _forEachIndex, (if (isNumber _e) then {1} else {0}), '
        '(getNumber _e)] call HMT_EMIT } forEach _p; '
        'format ["HMTVEND %%1", count _p] call HMT_EMIT;') % ",".join(chemins)
r = b.query(SQF2, r"HMTVEND (\d+)", want=1, timeout=40)
vals = {}
for s in b._log_lines(4000):
    m = re.match(r"HMTV (\d+) ([01]) ([-0-9.eE+]+)", s.strip())
    if m:
        vals[int(m.group(1))] = (int(m.group(2)), float(m.group(3)))

# ── 3. LE RAYON PAR L ACTE : une unite REELLE, `boundingBoxReal`, puis on rend le groupe.
#      (`deleteVehicle` ne supprime PAS le groupe — 288 groupes par camp, plafond deja paye.)
SQF3 = ('private _g = createGroup west; '
        'private _u = _g createUnit ["%s", [2000,2000,0], [], 0, "NONE"]; '
        'private _bb = boundingBoxReal _u; private _a = _bb select 0; private _c = _bb select 1; '
        'private _dx = (_c select 0) - (_a select 0); private _dy = (_c select 1) - (_a select 1); '
        'private _dz = (_c select 2) - (_a select 2); '
        'format ["HMTBB %%1 %%2 %%3 %%4 %%5", _dx, _dy, _dz, (sizeOf "%s"), (count units _g)] call HMT_EMIT; '
        'deleteVehicle _u; { if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;'
        ) % (SOLDAT, SOLDAT)
r3 = b.query(SQF3, r"HMTBB ([-0-9.eE+]+) ([-0-9.eE+]+) ([-0-9.eE+]+) ([-0-9.eE+]+) (\d+)", want=1, timeout=40)
if not r3:
    print("  ⛔ pas de reponse sur boundingBoxReal")
    dx = dy = dz = sz = 0.0; nu = 0
else:
    dx, dy, dz, sz = [float(r3[0].group(i)) for i in (1, 2, 3, 4)]
    nu = int(r3[0].group(5))

print("\n  CONTROLE POSITIF DU RAYON (juger l ACTE) : %d unite(s) reellement posee(s)" % nu)
print("    boite englobante  %.3f x %.3f x %.3f m · sizeOf = %.3f" % (dx, dy, dz, sz))
if nu < 1 or max(dx, dy, dz) <= 0:
    print("    ⛔ aucune unite posee ou boite nulle -> le rayon N EST PAS LU")
    rayon = None
else:
    import math
    rayon = 0.5 * math.sqrt(dx * dx + dy * dy + dz * dz)   # GeometrySphere = sphere englobante
    print("    ✔ rayon de la sphere englobante = %.3f m" % rayon)

print("\n  LA COURBE, MODE PAR MODE")
out = {"boundingBoxReal": [dx, dy, dz], "sizeOf": sz, "rayon_sphere_m": rayon, "modes": MODES}
for md in MODES:
    ligne = []
    for k in CLES:
        i = etiq.index((md, k)); ex, v = vals.get(i, (0, 0.0))
        ligne.append("%s=%s%s" % (k, v, "" if ex else "(abs)"))
    print("    %-24s %s" % (md, "  ".join(ligne)))
    out[md] = {k: vals.get(etiq.index((md, k)), (0, 0.0))[1] for k in CLES}
print("\n  CfgAmmo %s" % MUN)
for k in ["audibleFire", "visibleFire", "hit", "typicalSpeed", "indirectHitRange"]:
    i = etiq.index(("CfgAmmo", k)); ex, v = vals.get(i, (0, 0.0))
    print("    %-20s %10.4f %s" % (k, v, "" if ex else "(ABSENT)"))
    out["CfgAmmo_" + k] = {"existe": bool(ex), "valeur": v}
json.dump(out, open("/home/younes/arma3-marl/config_arma3_canal2.json", "w"), indent=1)
print("\n  ecrit : config_arma3_canal2.json")
b.sock.close()
