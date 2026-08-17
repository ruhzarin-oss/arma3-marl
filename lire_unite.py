import re, glob, math
"""LES SEUILS SONT CEUX DE L EN-TETE DE sonde_unite.sh, ECRITS AVANT QU ELLE TOURNE.
   X² = Σ k(p_i − p̂)² / (p̂(1−p̂)), 11 ddl.   X² > 19,68 → SESSION.   X² ≤ 19,68 → TIRAGE.
   Puissance déclarée : tranche un effet FORT ; un effet faible sortirait « TIRAGE » à tort."""
S = []
for f in sorted(glob.glob("/mnt/data/unite/s*.txt"), key=lambda x: int(re.search(r"s(\d+)", x).group(1))):
    t = open(f, errors="ignore").read()
    k = len(re.findall(r"\d+/6\s+vert=", t))
    # REVUE 17/08 : `prevol.py` imprime chaque ecart DEUX fois (en ligne au tirage, puis
    # dans la recapitulation), donc les rouges etaient comptes double : p_chapeau pouvait
    # depasser 1, et alors p(1-p) <= 0 rendait le X2 negatif ou divisait par zero.
    r = min(t.count("T5 IMMOBILE"), k)
    if k: S.append((int(re.search(r"s(\d+)", f).group(1)), k, r))
tot_k = sum(k for _, k, _ in S); tot_r = sum(r for _, _, r in S)
p = tot_r / tot_k
print(f"\n  sessions : {len(S)}   tirages : {tot_k}   rouges T5 : {tot_r}   taux de base p̂ = {p:.3f}\n")
print("  session  tirages  rouges  taux")
for s, k, r in S: print(f"    {s:2d}      {k:2d}      {r:2d}    {r/k:5.2f}  {'█'*r}")
X2 = sum(k * (r/k - p)**2 for _, k, r in S) / (p * (1 - p))
ddl = len(S) - 1
# seuils chi2 a 5 % pour les ddl plausibles
SEUIL = {5:11.07, 6:12.59, 7:14.07, 8:15.51, 9:16.92, 10:18.31, 11:19.68, 12:21.03}
s5 = SEUIL.get(ddl, 19.68)
var_obs = sum((r/k - p)**2 for _, k, r in S) / len(S)
var_bin = p * (1 - p) / (tot_k / len(S))
print(f"\n  variance observée des taux de session : {var_obs:.4f}")
print(f"  variance binomiale attendue           : {var_bin:.4f}")
print(f"  SURDISPERSION                         : ×{var_obs/var_bin:.2f}")
print(f"\n  X² = {X2:.2f}   ddl = {ddl}   seuil 5 % = {s5}")
if X2 > s5:
    print(f"\n  ➤ L'UNITÉ EST LA SESSION  (X² = {X2:.1f} > {s5})")
    bonnes = sum(1 for _, k, r in S if r == 0)
    tiers = sum(1 for _, k, r in S if r / k <= 0.34)
    print(f"     sessions PARFAITES (0 rouge)      : {bonnes}/{len(S)} = {100*bonnes//len(S)} %")
    print(f"     sessions exploitables (≤ 1/3)     : {tiers}/{len(S)} = {100*tiers//len(S)} %")
    if tiers:
        print(f"     coût d'une campagne : ≈ ×{len(S)/tiers:.1f} en démarrages de serveur")
        print(f"     P(1er tirage vert | session exploitable) élevée → le filtre en tête de session tient")
else:
    print(f"\n  ➤ PAS DE SURDISPERSION DÉCELABLE — on traite comme TIRAGE (avec la réserve de puissance)")
