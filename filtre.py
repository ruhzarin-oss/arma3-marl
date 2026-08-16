import re, glob
"""LE FILTRE EN TÊTE DE SESSION VAUT-IL QUELQUE CHOSE ?
   Réserve éliminatoire de VERDICT_UNITE_SESSION.md. Aucun serveur démarré : on relit le
   RANG de chaque tirage dans les journaux existants.
   Critères posés AVANT le calcul :
     · session EXPLOITABLE = au plus 1 rouge sur les 5 tirages qui suivent le contrôle
       (le tirage 1 est consommé par le contrôle, il ne compte pas dans le rendement)
     · le filtre TIENT si P(exploitable | tirage 1 vert) ≥ 0,80
     · il est INUTILE si cette probabilité ne dépasse pas le taux de base des sessions
"""
SEQ = []
for f in sorted(glob.glob("/mnt/data/unite/s*.txt"), key=lambda x: int(re.search(r"s(\d+)", x).group(1))):
    n = int(re.search(r"s(\d+)", f).group(1))
    s, prev = [], 0
    for m in re.finditer(r"(\d+)/6\s+vert=(\d+)\s+echec=(\d+)(.*)", open(f, errors="ignore").read()):
        e = int(m.group(3)); s.append("R" if e > prev else "V"); prev = e
    if s: SEQ.append((n, s))

print("\n  session  séquence des 6 tirages   rouges")
for n, s in SEQ: print(f"    {n:2d}     {' '.join(s):17s}    {s.count('R')}/{len(s)}")

t1v = [(n, s) for n, s in SEQ if s and s[0] == "V"]
t1r = [(n, s) for n, s in SEQ if s and s[0] == "R"]
expl = lambda s: s[1:].count("R") <= 1          # au plus 1 rouge sur les 5 suivants
base = sum(1 for _, s in SEQ if expl(s)) / len(SEQ)

print(f"\n  ── LE FILTRE, SUR LES CRITÈRES ÉCRITS AVANT ──")
print(f"  sessions : {len(SEQ)}   tirage 1 vert : {len(t1v)}   tirage 1 rouge : {len(t1r)}")
print(f"  taux de base P(exploitable)            = {base:.2f}")
if t1v:
    pv = sum(1 for _, s in t1v if expl(s)) / len(t1v)
    print(f"  P(exploitable | tirage 1 VERT)         = {pv:.2f}   ({sum(1 for _,s in t1v if expl(s))}/{len(t1v)})")
else:
    pv = None; print("  P(exploitable | tirage 1 VERT)         = INCALCULABLE (aucun cas)")
if t1r:
    pr = sum(1 for _, s in t1r if expl(s)) / len(t1r)
    print(f"  P(exploitable | tirage 1 ROUGE)        = {pr:.2f}   ({sum(1 for _,s in t1r if expl(s))}/{len(t1r)})")

print()
if pv is None:
    print("  ⛔ LE FILTRE N'EST PAS ÉVALUABLE : aucune session n'a démarré par un vert.")
    print("     À ce taux de base, c'est en soi un résultat — le contrôle en tête échouerait")
    print("     presque toujours, et jetterait des sessions exploitables avec les autres.")
elif pv >= 0.80:
    print(f"  ➤ LE FILTRE TIENT (P = {pv:.2f} ≥ 0,80). Un serveur validé porte ses 6 épisodes.")
elif pv > base:
    print(f"  ⚠️ LE FILTRE INFORME MAIS NE SUFFIT PAS : {pv:.2f} > {base:.2f} mais < 0,80.")
    print("     Il faut un contrôle PAR ÉPISODE, ou plusieurs tirages en tête.")
else:
    print(f"  ⛔ LE FILTRE EST INUTILE : {pv:.2f} ne bat pas le taux de base {base:.2f}.")
    print("     Un tirage en tête ne prédit rien — le contrôle doit descendre DANS l'épisode.")

# combien de tirages en tête faudrait-il ?
print("\n  ── COMBIEN DE TIRAGES EN TÊTE ? ──")
for k in (1, 2, 3):
    ok = [(n, s) for n, s in SEQ if len(s) > k and all(x == "V" for x in s[:k])]
    if ok:
        q = sum(1 for _, s in ok if s[k:].count("R") == 0) / len(ok)
        print(f"    {k} vert(s) d'affilée → {len(ok)} session(s), dont {q*100:3.0f} % sans aucun rouge ensuite")
    else:
        print(f"    {k} vert(s) d'affilée → AUCUNE session ne l'atteint")
