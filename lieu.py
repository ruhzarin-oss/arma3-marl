import re, glob
"""LE LIEU EXPLIQUE-T-IL LE DESTIN ?
   Le placeur (socle.sqf:166-177) balaye 24 points FIXES autour du premier attaquant :
   angles k*15°, rayons 250+(k mod 4)*40. AUCUN aléa. Le lieu est donc fixé par session.
   Signature : si le lieu est la cause, les sessions mortes ont des lieux distincts des
   vivantes, et la PENTE au lieu retenu doit séparer — c'est le seul critère du placeur."""
D = {}
for f in glob.glob("/mnt/data/harmattan-sandbox/logs/serverPV_p*.out"):
    s = int(re.search(r"_p(\d+)", f).group(1)); t = open(f, errors="ignore").read()
    L = re.findall(r"LIEU\|x\|(\d+)\|y\|(\d+)\|hauteur\|(-?\d+)\|eau\|(\w+)\|pente\|([\d.]+)\|meilleure_pente\|([\d.]+)", t)
    if L: D[s] = L
V = {}
for f in glob.glob("/mnt/data/pont/s*.txt"):
    s = int(re.search(r"s(\d+)", f).group(1)); t = open(f, errors="ignore").read()
    m = re.search(r"── 6 tirages : (\d+) verts", t)
    if m: V[s] = (int(m.group(1)), t.count("T5 IMMOBILE"), t.count("T7 LE CANAL"))
print("\n  sess verts  T5 T7   lieu (x,y)      haut  pente  meilleure  lieux distincts")
lig = []
for s in sorted(V):
    v, c5, c7 = V[s]; L = D.get(s, [])
    if not L: print(f"    {s:2d}    {v}    {c5:2d} {c7:2d}   (pas de journal)"); continue
    x, y, h, eau, pe, mp = L[0]
    uniq = len({(a, b) for a, b, *_ in L})
    print(f"    {s:2d}    {v}    {c5:2d} {c7:2d}   {x},{y}   {h:>4}  {pe:>5}   {mp:>5}      {uniq} sur {len(L)}")
    lig.append((s, v, float(pe), float(mp), int(h), uniq, len(L)))
viv = [x for x in lig if x[1] >= 5]; mor = [x for x in lig if x[1] == 0]
print(f"\n  ── LE LIEU EST-IL FIXE PAR SESSION ? ──")
tot = sum(x[6] for x in lig); un = sum(x[5] for x in lig)
print(f"  {un} lieux distincts pour {tot} tirages sur {len(lig)} sessions")
print(f"  ➤ {'OUI — un lieu par session, ou presque' if un < tot*0.6 else 'non, le lieu varie dans la session'}")
def sep(nom, f):
    a = sorted(f(x) for x in viv); b = sorted(f(x) for x in mor)
    if not a or not b: print(f"  {nom} : groupe vide"); return
    ch = not (max(a) < min(b) or max(b) < min(a))
    print(f"  {nom:20s} vivantes {a[0]:.3f}–{a[-1]:.3f}   mortes {b[0]:.3f}–{b[-1]:.3f}   {'chevauchent' if ch else '➤ SEPAREES'}")
print(f"\n  ── LA PENTE, seul critere du placeur ──")
print(f"  vivantes : {len(viv)}   mortes : {len(mor)}")
sep("pente au lieu", lambda x: x[2]); sep("meilleure pente", lambda x: x[3]); sep("hauteur", lambda x: float(x[4]))
