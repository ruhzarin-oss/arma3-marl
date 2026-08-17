import re, glob
"""SIGNATURES ÉCRITES AVANT (sonde_pont.sh) :
   (a) les mortes ont jetes>0, les vivantes jetes=0, SÉPARATION NETTE → le pont est la cause
   (b) jetes=0 partout, ou >0 partout sans lien avec le destin → L'HYPOTHÈSE MEURT
   (c) corrélation sans séparation → indécis, et on NE REJOUE PAS la même sonde"""
S = []
for f in sorted(glob.glob("/mnt/data/pont/s*.txt"), key=lambda x: int(re.search(r"s(\d+)", x).group(1))):
    n = int(re.search(r"s(\d+)", f).group(1)); t = open(f, errors="ignore").read()
    m = re.search(r"── 6 tirages : (\d+) verts", t)
    if not m: continue
    v = int(m.group(1))
    j = re.findall(r"jetes ring=(\d+) send=(\d+) ligne=(\d+)", t)
    deb, fin = (j[0] if j else ("?", "?", "?")), (j[-1] if j else ("?", "?", "?"))
    S.append((n, v, t.count("T5 IMMOBILE"), t.count("T7 LE CANAL"), deb, fin))
tot_v = sum(v for _, v, _, _, _, _ in S); tot_t = 6 * len(S)
print(f"\n  ── SONDE DU PONT, ère 1.2 — {len(S)} sessions, {tot_t} tirages ──\n")
print("  sess  verts  T5  T7   jetes début (r/s/l)   jetes fin (r/s/l)")
for n, v, c5, c7, d, f in S:
    print(f"    {n:2d}     {v}    {c5:2d}  {c7:2d}      {d[0]}/{d[1]}/{d[2]}                 {f[0]}/{f[1]}/{f[2]}")
print(f"\n  verts : {tot_v}/{tot_t} = {100*tot_v//tot_t} %   (ère 1.1, sonde d'unité : 19/72 = 26 %)")
viv = [x for x in S if x[1] >= 5]; mor = [x for x in S if x[1] == 0]
print(f"  sessions vivantes (≥5/6) : {len(viv)}   mortes (0/6) : {len(mor)}   mixtes : {len(S)-len(viv)-len(mor)}")
jv = {tuple(x[5]) for x in viv}; jm = {tuple(x[5]) for x in mor}
print(f"\n  ── LA SIGNATURE ──")
print(f"  compteurs de fin, sessions VIVANTES : {sorted(jv) if jv else 'aucune'}")
print(f"  compteurs de fin, sessions MORTES   : {sorted(jm) if jm else 'aucune'}")
if jv and jm and jv == jm:
    print(f"\n  ➤ SIGNATURE (b) — COMPTEURS IDENTIQUES entre vivantes et mortes.")
    print(f"     L'HYPOTHÈSE DU PONT MEURT. Les jetés ne séparent pas les destins.")
elif jv and jm and not (jv & jm):
    print(f"\n  ➤ SIGNATURE (a) — SÉPARATION NETTE. Le pont est la cause.")
else:
    print(f"\n  ➤ SIGNATURE (c) — corrélation sans séparation. INDÉCIS, on ne rejoue pas.")
# le destin persiste-t-il ?
seq = "".join("V" if x[1] >= 5 else ("M" if x[1] == 0 else "m") for x in S)
print(f"\n  destins : {seq}   (V vivante, m mixte, M morte)")
p = tot_v / tot_t
var_obs = sum((x[1]/6 - p)**2 for x in S) / len(S); var_bin = p*(1-p)/6
X2 = sum(6*(x[1]/6 - p)**2 for x in S) / (p*(1-p))
print(f"  surdispersion ×{var_obs/var_bin:.2f}   X² = {X2:.1f}  ddl = {len(S)-1}  (seuil 5 % ≈ {19.68 if len(S)==12 else 'n/a'})")
print(f"  ➤ le DESTIN DE SESSION {'PERSISTE' if X2 > 19.68 else 'ne se retrouve pas'} en ère 1.2")
