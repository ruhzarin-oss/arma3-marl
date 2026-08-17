import re, glob
"""MINAGE GRATUIT — zéro serveur. Croise le DESTIN de chaque session avec tout ce qui a été
   relevé à sa naissance. SIGNATURES ÉCRITES AVANT DE REGARDER :
     · si la CHARGE est en cause → les mortes naissent à load nettement plus haut
     · si l'HEURE / la DÉRIVE est en cause → les mortes se groupent dans le temps
     · si l'ORDRE de lancement est en cause → les mortes se groupent en début ou en fin
     · si RIEN ne sépare → aucune variable relevée n'explique le destin, et il faut payer
   Une séparation ne vaut que si elle est NETTE : chevauchement nul entre les deux groupes."""
J = open("/mnt/data/unite/JOURNAL.txt", errors="ignore").read().splitlines()
tel = {}
for l in J:
    m = re.match(r"session (\d+)\s+(\d+:\d+:\d+)\s+colocataires=(\d+)\s+load=([\d.]+)", l.strip())
    if m: tel[int(m.group(1))] = (m.group(2), int(m.group(3)), float(m.group(4)))
dest = {}
for f in glob.glob("/mnt/data/unite/s*.txt"):
    n = int(re.search(r"s(\d+)", f).group(1)); t = open(f, errors="ignore").read()
    v = int(re.search(r"── \d+ tirages : (\d+) verts", t).group(1)) if "tirages :" in t else -1
    c5 = t.count("T5 IMMOBILE"); c7 = t.count("T7 LE CANAL")
    dest[n] = (v, c5, c7)

print("\n  session  heure     colo  load   verts  T5  T7   destin")
lignes = []
for n in sorted(dest):
    v, c5, c7 = dest[n]; h, co, ld = tel.get(n, ("?", -1, -1.0))
    d = "VIVANTE" if v >= 5 else ("morte-FEU" if c7 > c5 else ("morte-JAMBES" if c5 else "mixte"))
    if 0 < v < 5: d = "mixte"
    print(f"    {n:2d}     {h}   {co}   {ld:4.2f}    {v}    {c5:2d}  {c7:2d}   {d}")
    lignes.append((n, h, co, ld, v, d))

viv = [x for x in lignes if x[5] in ("VIVANTE", "mixte")]
mor = [x for x in lignes if x[5].startswith("morte")]
print(f"\n  ── LES SIGNATURES, DANS L'ORDRE OÙ ELLES ONT ÉTÉ ÉCRITES ──")
print(f"  vivantes ou mixtes : {len(viv)}   mortes : {len(mor)}")

def sep(nom, f):
    a = sorted(f(x) for x in viv); b = sorted(f(x) for x in mor)
    if not a or not b: print(f"  {nom} : un groupe est vide"); return
    chev = not (max(a) < min(b) or max(b) < min(a))
    print(f"  {nom:22s} vivantes {a[0]:.2f}–{a[-1]:.2f} (méd {a[len(a)//2]:.2f})   "
          f"mortes {b[0]:.2f}–{b[-1]:.2f} (méd {b[len(b)//2]:.2f})   "
          f"{'CHEVAUCHENT' if chev else '➤ SÉPARÉES'}")
sep("charge (load)", lambda x: x[3])
sep("co-locataires", lambda x: float(x[2]))
sep("ordre de lancement", lambda x: float(x[0]))
hs = lambda x: sum(int(p)*f for p, f in zip(x[1].split(":"), (3600, 60, 1))) if ":" in x[1] else 0
sep("heure (secondes)", lambda x: float(hs(x)))

print(f"\n  ── ORDRE CHRONOLOGIQUE DES DESTINS ──")
print("  " + " ".join("V" if x[5] in ("VIVANTE", "mixte") else "M" for x in sorted(lignes)))
print("  (V = vivante ou mixte, M = morte ; ordre de lancement, session 1 à 12)")
