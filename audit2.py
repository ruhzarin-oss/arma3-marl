import re, pathlib
R = pathlib.Path("/home/younes/arma3-marl")
M = pathlib.Path("/mnt/data/harmattan-sandbox/arma3server/mpmissions")
# LES BANCS EN SERVICE : ceux que les chaines lancent, ou dont un verdict de ces 2 jours depend
VIF = [
 (M/"BancLive.Stratis", None), (R/"banc_live.py", None), (R/"arma_couture.py", None),
 (M/"FeuForce.Stratis/feu_force.sqf", None), (M/"SondeDcover.Stratis/sonde_dcover.sqf", None),
 (M/"SondeTerrain.Stratis/sonde_terrain.sqf", None), (M/"ChoixSite.Stratis/choix_site.sqf", None),
 (M/"SondeImpact.Stratis/sonde_impact.sqf", None), (M/"BancAppui.Stratis/banc_appui.sqf", "GELE"),
]
F = []
for p, tag in VIF:
    if p.is_dir(): F += [(q, tag) for q in p.glob("*.sqf")]
    elif p.exists(): F.append((p, tag))

print("="*76); print("  AUDIT RESSERRE — LES BANCS EN SERVICE SEULEMENT"); print("="*76)
print(f"\n  {len(F)} fichiers\n")
print(f"  {'fichier':<34}{'arme':>7}{'disAI':>7}{'etat':>7}{'vieux':>7}")
tot = dict(arme=0, dis=0, etat=0, vieux=0)
for p, tag in sorted(F, key=lambda x: x[0].name):
    t = p.read_text(errors="ignore")
    arme  = ("createUnit" in t or "setUnitLoadout" in t) and "selectWeapon" not in t
    d = set(re.findall(r'disableAI\s+"(\w+)"', t)); e = set(re.findall(r'enableAI\s+"(\w+)"', t))
    dis   = bool(d - e) and "ALL" not in e
    etat  = bool(re.search(r'canFire|ammo\s+\(', t)) and not re.search(r'currentWeapon|"Fired"|HitPart', t)
    vieux = bool(re.search(r'^\s*[^/\n]*(surfaceNormal|terrainIntersectASL|doSuppressiveFire)', t, re.M))
    for k, v in [("arme",arme),("dis",dis),("etat",etat),("vieux",vieux)]: tot[k] += v
    m = lambda b: " ⛔" if b else "  ·"
    print(f"  {p.name[:32]:<34}{m(arme):>7}{m(dis):>7}{m(etat):>7}{m(vieux):>7}" + (f"   [{tag}]" if tag else ""))
print(f"\n  {'TOTAL':<34}{tot['arme']:>7}{tot['dis']:>7}{tot['etat']:>7}{tot['vieux']:>7}")
print("\n  arme  = createUnit/setUnitLoadout sans selectWeapon")
print("  disAI = disableAI pose sans enableAI correspondant")
print("  etat  = controle canFire/ammo sans currentWeapon/Fired")
print("  vieux = surfaceNormal / terrainIntersectASL / doSuppressiveFire, tous refutes")
