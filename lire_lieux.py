import re, glob
"""SIGNATURES ÉCRITES AVANT (test_lieux.sh) — grandeur : taux d'échec T5 par lieu ;
   statistique : proportion ; n minimum : 6 tirages par lieu.
     (a) SÉPARATION NETTE : le PIRE lieu vivant échoue MOINS que le MEILLEUR lieu mort
         → la cause est établie, le placeur est fautif.
     (b) PAS DE SÉPARATION → DESTIN_EST_LE_LIEU.md TOMBE.
     (c) PARTIELLE → indécis, on ne conclut pas et on ne rejoue pas."""
par = {}
for f in sorted(glob.glob("/mnt/data/lieux/s*.txt")):
    L = open(f, errors="ignore").read().splitlines()
    cur = None; prev = 0
    for l in L:
        m = re.search(r"lieu force : (\S+)", l)
        if m: cur = m.group(1); continue
        m2 = re.search(r"(\d+)/15\s+vert=(\d+)\s+echec=(\d+)", l)
        if m2 and cur:
            e = int(m2.group(3)); rouge = e > prev; prev = e
            t5 = "T5" in l
            par.setdefault(cur, []).append(("T5" if (rouge and t5) else ("R" if rouge else ".")))
print("\n  lieu                 n   verts  rouges  dont T5   taux d'échec   détail")
res = {}
for k in sorted(par, key=lambda x: (not x.startswith("vif"), x)):
    v = par[k]; n = len(v); r = sum(1 for x in v if x != "."); c5 = sum(1 for x in v if x == "T5")
    res[k] = (r / n, n, r, c5)
    print(f"  {k:20s} {n:2d}    {n-r:2d}     {r:2d}      {c5:2d}      {100*r//n:3d} %        {' '.join(v)}")
vif = {k: v for k, v in res.items() if k.startswith("vif")}
mor = {k: v for k, v in res.items() if k.startswith("mort")}
print(f"\n  ── LA SIGNATURE ──")
if not vif or not mor: print("  un groupe est vide"); raise SystemExit
pire_vif = max(v[0] for v in vif.values()); meilleur_mort = min(v[0] for v in mor.values())
print(f"  pire lieu VIVANT      : {100*pire_vif:.0f} % d'échec")
print(f"  meilleur lieu MORT    : {100*meilleur_mort:.0f} % d'échec")
nmin = min(v[1] for v in res.values())
print(f"  n minimum par lieu    : {nmin} (exigé 6)")
if nmin < 6:
    print(f"\n  ⛔ n INSUFFISANT sur au moins un lieu — le critère ne se lit pas.")
elif pire_vif < meilleur_mort:
    print(f"\n  ➤ SIGNATURE (a) — SÉPARATION NETTE. Le destin SUIT LE LIEU.")
    print(f"     La cause est établie : LE PLACEUR EST FAUTIF.")
else:
    tv = sum(v[2] for v in vif.values()) / sum(v[1] for v in vif.values())
    tm = sum(v[2] for v in mor.values()) / sum(v[1] for v in mor.values())
    print(f"\n  taux groupés : vivants {100*tv:.0f} %   morts {100*tm:.0f} %   écart {100*(tm-tv):+.0f} pts")
    if tm - tv > 0.3:
        print(f"  ➤ SIGNATURE (c) — le lieu PÈSE mais ne détermine pas. INDÉCIS : on ne conclut pas.")
    else:
        print(f"  ➤ SIGNATURE (b) — pas de séparation. DESTIN_EST_LE_LIEU.md TOMBE.")
