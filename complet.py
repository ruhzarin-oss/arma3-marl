import re, glob
"""LE CHIFFRE COMPLET — par session, par rang, ET PAR TEST.
   ⚠️ Mes deux dépouillements précédents ne comptaient pas la même chose : l un comptait
   `T5 IMMOBILE`, l autre TOUS les échecs de prévol. La session 10 en est la preuve — 0
   rouge T5 et 6 échecs. Ici, chaque test est compté séparément."""
R = []
for f in sorted(glob.glob("/mnt/data/unite/s*.txt"), key=lambda x: int(re.search(r"s(\d+)", x).group(1))):
    n = int(re.search(r"s(\d+)", f).group(1)); txt = open(f, errors="ignore").read()
    seq, prev = [], 0
    for m in re.finditer(r"(\d+)/6\s+vert=(\d+)\s+echec=(\d+)(?:\s+←\s+(.*))?", txt):
        e = int(m.group(3)); d = (m.group(4) or "")
        if e > prev:
            seq.append("5" if "T5" in d else "7" if "T7" in d else "4" if "T4" in d else "?")
        else: seq.append(".")
        prev = e
    if seq: R.append((n, seq))

print("\n  ── LE CHIFFRE COMPLET : 12 sessions × 6 tirages ──")
print("     '.' vert   '5' T5   '7' T7   '4' T4\n")
print("  session  rang → 1 2 3 4 5 6   verts  T5  T7  T4")
tv = t5 = t7 = t4 = tt = 0
for n, s in R:
    v = s.count("."); c5 = s.count("5"); c7 = s.count("7"); c4 = s.count("4")
    tv += v; t5 += c5; t7 += c7; t4 += c4; tt += len(s)
    print(f"    {n:2d}            {' '.join(s)}     {v}    {c5}   {c7}   {c4}")
print(f"\n  TOTAL sur {tt} tirages : {tv} verts ({100*tv//tt} %)   T5 {t5}   T7 {t7}   T4 {t4}")

r1 = [s[0] for _, s in R]
print(f"\n  ── LE RANG 1 ──")
print(f"  sessions dont le PREMIER tirage est rouge : {sum(1 for x in r1 if x != '.')}/{len(R)}")
for k in range(6):
    col = [s[k] for _, s in R if len(s) > k]
    print(f"    rang {k+1} : {sum(1 for x in col if x == '.')}/{len(col)} verts")

print(f"\n  ── LE FILTRE EN TÊTE : CE QU'ON PEUT ET NE PEUT PAS DIRE ──")
t1v = [(n, s) for n, s in R if s[0] == "."]
print(f"  P(exploitable | rang 1 vert) repose sur n = {len(t1v)} session(s).")
print(f"  ⛔ NON ÉVALUABLE : un seuil de 0,80 franchi sur n=1 n'a aucune puissance.")
print(f"     Mon critère écrit avant fixait le seuil et PAS le n minimum — même faute que")
print(f"     la médiane non déclarée du banc des jambes. Le critère était incomplet.")
print(f"\n  Ce qui EST lisible : le filtre en tête jetterait {sum(1 for x in r1 if x != '.')} serveurs sur {len(R)},")
print(f"  dont {sum(1 for _, s in R if s[0] != '.' and s[1:].count('.') >= 4)} qui deviennent bons après leur premier tirage.")

t2v = [(n, s) for n, s in R if len(s) > 1 and s[1] == "."]
if t2v:
    ok = sum(1 for _, s in t2v if s[2:].count(".") >= len(s[2:]) - 1)
    print(f"\n  ── EN JETANT LE RANG 1 (échauffement) ET EN CONTRÔLANT SUR LE RANG 2 ──")
    print(f"  n = {len(t2v)} sessions, dont {ok} exploitables → {ok}/{len(t2v)}")
    print(f"  Toujours trop peu pour un verdict, mais c'est LA piste, et elle se mesure.")
