import re, glob, sys
"""LES QUATRE LIGNES de DEPOT_PORTE_PLEIN_CHEMIN.md, ecrites AVANT. Vertes ENSEMBLE ou panne."""
lots = []
for f in sorted(glob.glob("/mnt/data/porte/lot*.txt"), key=lambda x: int(re.search(r"lot(\d+)", x).group(1))):
    n = int(re.search(r"lot(\d+)", f).group(1)); t = open(f, errors="ignore").read()
    seq, prev = [], 0
    for l in t.splitlines():
        m = re.search(r"(\d+)/12\s+vert=(\d+)\s+echec=(\d+)(.*)", l)
        if not m: continue
        e, d = int(m.group(3)), m.group(4)
        if "ECARTE" in d or "abandonne" in d: k = "ECARTE"
        elif "PONT MUET" in d: k = "PONT"
        elif "PREVOL PLANTE" in d: k = "PLANTE"
        elif "PREVOL LENT" in d: k = "LENT"
        elif e > prev: k = "T5" if "T5 IMMOBILE" in d else ("T7" if "T7 " in d else "AUTRE")
        else: k = "."
        prev = e
        seq.append(k)
    lots.append((n, seq))

print("\n  lot  rang → 1  2  3  4  5  6  7  8  9 10 11 12   verts")
tot = {}
for n, s in lots:
    for k in s: tot[k] = tot.get(k, 0) + 1
    print(f"   {n}        " + " ".join(f"{k[:2]:>2}" if k != "." else " ." for k in s) + f"     {s.count('.')}")
N = sum(len(s) for _, s in lots)
print(f"\n  {N} tirages : " + "  ".join(f"{k}={v}" for k, v in sorted(tot.items())))

recep = tot.get(".", 0) + tot.get("T5", 0) + tot.get("T7", 0) + tot.get("AUTRE", 0)
print(f"\n  ══ LIGNE 1 · FAUX-RECUS INEXPLIQUES ══")
print(f"  receptions (le placeur a recu un lieu) : {recep}   exige : >= 50")
print(f"  faux-recus T5 : {tot.get('T5', 0)}   autres echecs : {tot.get('T7',0)} T7, {tot.get('AUTRE',0)} non identifies")
l1 = tot.get("T5", 0) == 0 and recep >= 50
print(f"  → {'✓ VERTE' if l1 else '⛔ ROUGE'}  (zero faux-recu T5 sur >= 50 receptions)")

print(f"\n  ══ LIGNE 2 · MUETS DECOMPOSES ══")
print(f"  pont muet : {tot.get('PONT',0)}   prevol lent : {tot.get('LENT',0)}   prevol PLANTE : {tot.get('PLANTE',0)}   ecartes : {tot.get('ECARTE',0)}")
l2 = tot.get("PLANTE", 0) == 0
print(f"  → {'✓ VERTE' if l2 else '⛔ ROUGE'}  (zero PLANTE tolere ; lent et pont comptes a part)")

print(f"\n  ══ LIGNE 3 · REGROUPEMENT PAR SERVEUR ══")
ok_l = [(n, s.count("."), len(s)) for n, s in lots]
p = sum(v for _, v, _ in ok_l) / sum(t for _, _, t in ok_l)
X2 = sum(t * ((v/t) - p)**2 for _, v, t in ok_l) / (p*(1-p)) if 0 < p < 1 else 0
seuil = {4: 9.49, 5: 11.07}.get(len(lots), 9.49)
print(f"  taux de verts par lot : " + "  ".join(f"{v}/{t}" for _, v, t in ok_l))
print(f"  X2 = {X2:.2f}   ddl = {len(lots)-1}   seuil 5 % = {seuil}")
l3 = X2 <= seuil
print(f"  → {'✓ VERTE' if l3 else '⛔ ROUGE'}  (pas de surdispersion entre serveurs)")

print(f"\n  ══ LIGNE 4 · LES QUATRE SABOTAGES ══")
print(f"  traverse et tir : rejoues au smoke du 17/08 — les deux font REFUSER")
print(f"  munitions (T4) et jambes (T5) : NON rejoues depuis le socle 2.7.0")
l4 = False
print(f"  → ⛔ ROUGE  (deux sabotages sur quatre non rejoues sur ce hash)")

print(f"\n  ══════ VERDICT ══════")
if l1 and l2 and l3 and l4: print("  ➤ LES QUATRE LIGNES SONT VERTES — LE BANC SORT DE PANNE DIAGNOSTIQUE.")
else:
    rouges = [i+1 for i, x in enumerate([l1,l2,l3,l4]) if not x]
    print(f"  ➤ LIGNE(S) ROUGE(S) : {rouges} — LE BANC RESTE EN PANNE.")
    if rouges == [4]:
        print("     Mais la seule rouge est une PROCEDURE non rejouee, pas une mesure du monde :")
        print("     les trois lignes qui jugent le monde sont vertes. Rejouer les deux sabotages")
        print("     manquants sur ce hash suffit — c est dix minutes, et rien d autre a mesurer.")
