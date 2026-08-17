import re, glob
"""BLOC 0 — MINAGE DES JOURNAUX DE LA PORTE, zéro serveur.
   ⚠️ « C'est le résidu de serveur » est mon NEUVIÈME pari. La lecture de Fable lui donne
   deux concurrents. SIGNATURES ÉCRITES AVANT D'OUVRIR :
     H1 · SUPERPOSITION — chaque faux-reçu est ADJACENT (rang r−1 ou r−2) à un muet.
          Cause : le plafond d'attente est GLOBAL (40 × 1,9 s) contre un prévol de durée
          VARIABLE ; au dépassement python enchaîne pendant que le spawn tourne encore,
          et deux prévols écrivent dans les mêmes globales.
     H2 · FEU DE LA SCÈNE — les faux-reçus portent `connu>0` ou `degats>0` : le testeur
          a été abattu (ni l'acte 2 ni l'acte 3 n'ont `allowDamage false`).
     H3 · DESTIN DE SERVEUR — ni l'un ni l'autre.
   Et sur les muets : leurs RANGS par lot. « Exactement 2 par lot, cinq fois de suite » a une
   probabilité ridicule sous tirage indépendant — si les rangs sont constants, c'est déterministe."""
S = []
for f in sorted(glob.glob("/mnt/data/porte/lot*.txt"), key=lambda x: int(re.search(r"lot(\d+)", x).group(1))):
    lot = int(re.search(r"lot(\d+)", f).group(1))
    seq, prev = [], 0
    for l in open(f, errors="ignore").read().splitlines():
        m = re.search(r"(\d+)/12\s+vert=(\d+)\s+echec=(\d+)(.*)", l)
        if not m: continue
        r, e, d = int(m.group(1)), int(m.group(3)), m.group(4)
        if "SANS REPONSE" in d: k = "MUET"
        elif e > prev: k = "T5" if "T5 IMMOBILE" in d else ("T7" if "T7 " in d else "?")
        else: k = "."
        prev = e
        seq.append((r, k, d))
    S.append((lot, seq))

print("\n  lot  rang → 1  2  3  4  5  6  7  8  9 10 11 12")
for lot, seq in S:
    print(f"   {lot}         " + " ".join(f"{k:>2}" if k != "." else " ." for _, k, _ in seq))

print("\n  ── H1 · SUPERPOSITION : les faux-reçus suivent-ils un muet ? ──")
adj = tot = 0
for lot, seq in S:
    k = {r: kk for r, kk, _ in seq}
    for r, kk, _ in seq:
        if kk == "T5":
            tot += 1
            voisins = [k.get(r-1), k.get(r-2)]
            a = "MUET" in voisins
            adj += a
            print(f"    lot {lot} rang {r} : T5 — rangs {r-1},{r-2} = {voisins}  {'← ADJACENT À UN MUET' if a else ''}")
if tot: print(f"    → {adj}/{tot} faux-reçus adjacents à un muet")

print("\n  ── H2 · FEU DE LA SCÈNE : le testeur était-il vu ou touché ? ──")
for lot, seq in S:
    for r, kk, d in seq:
        if kk == "T5":
            c = re.search(r"connu:([\d.]+)", d); g = re.search(r"degats:([\d.]+)", d)
            print(f"    lot {lot} rang {r} : connu={c.group(1) if c else '?'}  degats={g.group(1) if g else '?'}")

print("\n  ── LES MUETS : rangs par lot ──")
for lot, seq in S:
    rangs = [r for r, kk, _ in seq if kk == "MUET"]
    print(f"    lot {lot} : {rangs}")
allr = [r for _, seq in S for r, kk, _ in seq if kk == "MUET"]
from collections import Counter
print(f"    tous rangs confondus : {sorted(Counter(allr).items())}")
print(f"    → {'RANGS CONSTANTS = déterministe' if len(set(allr)) <= 3 else 'rangs dispersés'}")
