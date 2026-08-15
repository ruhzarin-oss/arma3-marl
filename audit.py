import re, pathlib, subprocess, collections
R = pathlib.Path("/home/younes/arma3-marl")
M = pathlib.Path("/mnt/data/harmattan-sandbox/arma3server/mpmissions")

print("="*78); print("  AUDIT — LES NEUF FAMILLES DE FAUTES, PASSEES SUR TOUS LES BANCS"); print("="*78)

SQF = sorted(list((R/"bancs/arma").glob("*.sqf")) + list(M.glob("*/*.sqf")))
PY  = [R/"banc_live.py", R/"arma_couture.py", R/"porter_boucle.py", R/"boucle.py"]
FICH = [f for f in SQF + PY if f.exists()]
print(f"\n  {len(FICH)} fichiers examines\n")

def lit(f):
    try: return f.read_text(errors="ignore")
    except: return ""

FAM = []
# ── 1. arme : rendue au sac sans etre remise en main
h = []
for f in FICH:
    t = lit(f)
    if re.search(r'setUnitLoadout|removeAllWeapons|createUnit', t) and "selectWeapon" not in t:
        if re.search(r'forceWeaponFire|SuppressiveFire|Fired|doFire', t) or "createUnit" in t:
            h.append(f.name)
FAM.append(("1. ARME AU SAC — createUnit/setUnitLoadout sans selectWeapon", h))

# ── 2. disableAI pose, jamais rendu
h = []
for f in FICH:
    t = lit(f)
    d = set(re.findall(r'disableAI\s+"(\w+)"', t)); e = set(re.findall(r'enableAI\s+"(\w+)"', t))
    manque = d - e - ({"ALL"} if "ALL" in e else set())
    if manque and "ALL" not in e: h.append(f"{f.name} ({','.join(sorted(manque))})")
FAM.append(("2. disableAI POSE SANS ETRE RENDU", h))

# ── 3. controle d ETAT au lieu d ACTE
h = []
for f in FICH:
    t = lit(f)
    if re.search(r'canFire|ammo\s+\(', t) and not re.search(r'currentWeapon|"Fired"|HitPart', t):
        h.append(f.name)
FAM.append(("3. CONTROLE D ETAT (canFire/ammo) SANS ACTE (currentWeapon/Fired)", h))

# ── 4. grandeurs redefinies localement
GR = collections.defaultdict(list)
for f in FICH:
    t = lit(f)
    for g, pat in [("slope/gradient", r'getTerrainHeightASL\s*\[[^\]]*\+6\.25'),
                   ("los",            r'checkVisibility|terrainIntersectASL'),
                   ("dcover",         r'_dcell|dcover')]:
        if re.search(pat, t): GR[g].append(f.name)
FAM.append(("4. GRANDEURS REDEFINIES DANS PLUSIEURS FICHIERS",
            [f"{g} : {len(v)} fichiers — {', '.join(v[:4])}{'...' if len(v)>4 else ''}" for g, v in GR.items() if len(v) > 1]))

# ── 5. vieilles definitions interdites
h = []
for f in FICH:
    t = lit(f)
    for bad, why in [("surfaceNormal", "pente bornee a 0,40"), ("terrainIntersectASL", "relief SEUL"),
                     ("doSuppressiveFire", "oriente sans declencher")]:
        if re.search(r'^\s*[^/\n]*' + bad, t, re.M): h.append(f"{f.name} : {bad} ({why})")
FAM.append(("5. VIEILLES DEFINITIONS DEJA REFUTEES, ENCORE PRESENTES", h))

# ── 6. seuil decimal contre grandeur quantifiee (n/30)
h = []
for f in FICH:
    for m in re.finditer(r'0\.0(2[0-9]|3[0-9])\b', lit(f)):
        h.append(f"{f.name} : seuil {m.group(0)} (1/30 = 0,03333)")
FAM.append(("6. SEUIL DECIMAL CONTRE GRANDEUR QUANTIFIEE", sorted(set(h))))

for nom, h in FAM:
    print(f"  {'⛔' if h else '✓ '} {nom}")
    for x in h[:6]: print(f"        {x}")
    if len(h) > 6: print(f"        ... et {len(h)-6} de plus")
print()
