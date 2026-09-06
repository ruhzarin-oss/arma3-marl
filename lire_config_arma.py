#!/usr/bin/env python3
"""Les quatre lectures `configFile` qui debloquent le canal CWR — plus la courbe.

REGLE 16, CLAUSE 2 : juger l ACTE, pas l ETAT. `getNumber` rend 0 pour « absent » ET pour
« vaut zero » — deux choses tres differentes quand on cherche un parametre qui manque.
Chaque sonde emet donc DEUX nombres : `isNumber` (l entree existe-t-elle) puis la valeur.

REGLE 16, CLAUSE 1 : controle positif AVANT toute lecture. Deux temoins encadrent la serie :
  · un chemin dont la reponse est connue NON NULLE (`CfgAmmo >> B_65x39_Caseless >> hit`)
  · un chemin BIDON, qui doit rendre isNumber=0. Si le bidon rend 1, la sonde ment.

⚠️ Le SQF transmis est PURGE de tout commentaire : la mission l execute par `call compile`,
qui ne retire pas les `//` — un seul ferait echouer le bloc en silence.
"""
import sys, re, json
sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
SOLDAT = "B_Soldier_F"
ARMES = ["arifle_MX_F", "arifle_MXC_F", "arifle_SPAR_01_blk_F"]
MUN = "B_65x39_Caseless"

# (etiquette, chemin SQF). L ORDRE fait foi : l index revient dans la ligne emise.
SONDES = [
    ("TEMOIN+ hit munition",      'configFile >> "CfgAmmo" >> "%s" >> "hit"' % MUN),
    ("TEMOIN- chemin bidon",      'configFile >> "CfgVehicles" >> "%s" >> "ceci_nexiste_pas_du_tout"' % SOLDAT),
    ("sensitivity",               'configFile >> "CfgVehicles" >> "%s" >> "sensitivity"' % SOLDAT),
    ("sensitivityEar",            'configFile >> "CfgVehicles" >> "%s" >> "sensitivityEar"' % SOLDAT),
    ("camouflage",                'configFile >> "CfgVehicles" >> "%s" >> "camouflage"' % SOLDAT),
    ("audible",                   'configFile >> "CfgVehicles" >> "%s" >> "audible"' % SOLDAT),
    ("radius (CfgVehicles)",      'configFile >> "CfgVehicles" >> "%s" >> "radius"' % SOLDAT),
    ("armor",                     'configFile >> "CfgVehicles" >> "%s" >> "armor"' % SOLDAT),
    ("armorStructural",           'configFile >> "CfgVehicles" >> "%s" >> "armorStructural"' % SOLDAT),
    ("threat/accuracy",           'configFile >> "CfgVehicles" >> "%s" >> "accuracy"' % SOLDAT),
]
# audibleFire / visibleFire : on ne SAIT PAS ou ils vivent en RV3. On sonde, on ne suppose pas.
for w in ARMES:
    SONDES += [
        ("%s audibleFire (arme)" % w,      'configFile >> "CfgWeapons" >> "%s" >> "audibleFire"' % w),
        ("%s audibleFire (Single)" % w,    'configFile >> "CfgWeapons" >> "%s" >> "Single" >> "audibleFire"' % w),
        ("%s visibleFire (arme)" % w,      'configFile >> "CfgWeapons" >> "%s" >> "visibleFire"' % w),
    ]
# LA COURBE : minRange/midRange/maxRange et leurs *Probab. En RV1 elles sont dans l AmmoType ;
# en RV3 elles vivent plutot dans le MODE de tir de l arme. On sonde LES DEUX.
CLES = ["minRange", "minRangeProbab", "midRange", "midRangeProbab", "maxRange", "maxRangeProbab"]
for k in CLES:
    SONDES.append(("CfgAmmo %s" % k, 'configFile >> "CfgAmmo" >> "%s" >> "%s"' % (MUN, k)))
for k in CLES:
    SONDES.append(("MX Single %s" % k, 'configFile >> "CfgWeapons" >> "%s" >> "Single" >> "%s"' % (ARMES[0], k)))
for k in CLES:
    SONDES.append(("MX FullAuto %s" % k, 'configFile >> "CfgWeapons" >> "%s" >> "FullAuto" >> "%s"' % (ARMES[0], k)))

CHEMINS = ",".join("(%s)" % c for _, c in SONDES)
SQF = (
    '_p = [%s]; '
    '{ private _e = _x; private _o = (if (isNumber _e) then {1} else {0}); '
    'format ["HMTCFG %%1 %%2 %%3", _forEachIndex, _o, (getNumber _e)] call HMT_EMIT } forEach _p; '
    'format ["HMTSIZE %%1 %%2", (sizeOf "%s"), (count _p)] call HMT_EMIT;'
) % (CHEMINS, SOLDAT)

b = NativeBridge(port=PORT, timeout=20)
print("  pont %d ouvert, compteur a %d" % (PORT, b.counter))
res = b.query(SQF, r"HMTSIZE ([-0-9.eE]+) ([0-9]+)", want=1, timeout=40)
if not res:
    sys.exit("  ⛔ AUCUNE reponse — le pont repond-il ? (HMT_EMIT, pas diag_log)")
sizeof, n = float(res[0].group(1)), int(res[0].group(2))
lignes = b._log_lines(4000)
vals = {}
for s in lignes:
    m = re.match(r"HMTCFG (\d+) ([01]) ([-0-9.eE+]+)", s.strip())
    if m:
        vals[int(m.group(1))] = (int(m.group(2)), float(m.group(3)))
print("  %d sondes emises, %d relues · sizeOf %s = %.3f m" % (n, len(vals), SOLDAT, sizeof))

print("\n  CONTROLE POSITIF (regle 16, clause 1)")
t_plus = vals.get(0, (0, 0.0)); t_moins = vals.get(1, (1, 0.0))
print("    temoin +  hit munition : existe=%d valeur=%.3f  (doit exister et etre non nul)"
      % t_plus)
print("    temoin -  chemin bidon : existe=%d valeur=%.3f  (doit NE PAS exister)" % t_moins)
if not (t_plus[0] == 1 and t_plus[1] > 0 and t_moins[0] == 0):
    sys.exit("  ⛔ LA SONDE NE DISCRIMINE PAS — aucune lecture n est admissible.")
print("    ✔ la sonde distingue « absent » de « vaut zero »")

print("\n  LES LECTURES")
out = {"sizeOf_%s" % SOLDAT: sizeof}
for i, (nom, chemin) in enumerate(SONDES):
    ex, v = vals.get(i, (None, None))
    if ex is None:
        print("    %-30s  PAS DE REPONSE" % nom); continue
    marque = "  " if ex else "  (ABSENT)"
    print("    %-30s %10.4f%s" % (nom, v, marque))
    out[nom] = {"existe": bool(ex), "valeur": v}
json.dump(out, open("/home/younes/arma3-marl/config_arma3_canal.json", "w"), indent=1, ensure_ascii=False)
print("\n  ecrit : config_arma3_canal.json")
b.sock.close()
