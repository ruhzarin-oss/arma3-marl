import re
"""CRITÈRES de DEPOT_PORTE_PLACEUR.md, écrits avant :
   grandeur = faux-reçus (lieu REÇU où T5 échoue) ; seuil = ZÉRO ; n minimum = 50 réceptions.
   0 → le banc sort de panne (domaine déclaré) · 1-2 → réduit sans borner · ≥3 → v2 insuffisant."""
L = open("/mnt/data/harmattan-sandbox/logs/serverPV_PORTE.out", errors="ignore").read()
recus = re.findall(r"CANDIDAT\|n\|\d+\|x\|(\d+)\|y\|(\d+)\|verdict\|recu\|metres\|(\d+)", L)
rej   = re.findall(r"CANDIDAT\|n\|\d+\|x\|\d+\|y\|\d+\|verdict\|(\w[\w ]*)\|metres\|(\d+)", L)
ess   = [int(x) for x in re.findall(r"candidats_essayes\|(\d+)", L)]
# T5 vu par le socle : nt/m par tirage, dans l'ordre
t5 = [int(m) for m in re.findall(r"HMT\|SOCLE\|T5\|nt\|\d+\|fps\|\d+\|m\|(\d+)", L)]
n_recep = len(ess)
print(f"\n  ── PORTE-CERTIFICATION DU PLACEUR v2 ──\n")
print(f"  réceptions          : {n_recep} (n minimum exigé : 50)")
print(f"  candidats essayés   : {sum(ess)}   soit {sum(ess)/max(n_recep,1):.2f} par réception")
from collections import Counter
c = Counter(v.strip() for v, _ in rej)
print(f"  verdicts du placeur : {dict(c)}")
prat = c.get("recu", 0) / max(sum(c.values()), 1)
print(f"  lieux praticables   : {100*prat:.0f} % des candidats tirés au hasard")
print(f"\n  ── CE QUE T5 A RENDU AUX LIEUX REÇUS ──")
print(f"  traverses T5 : {sorted(t5)}")
fr = sum(1 for m in t5 if m < 10)
print(f"  faux-reçus (T5 < 10 m) : {fr} sur {len(t5)}")
mt = [int(m) for _, _, m in recus]
print(f"  traverse mesurée PAR LE PLACEUR aux lieux reçus : {sorted(mt)}")
print(f"\n  ── LE VERDICT, SUR LE CRITÈRE ÉCRIT AVANT ──")
if n_recep < 50:
    print(f"  ⚠️ n = {n_recep} < 50 : le critère NE SE LIT PAS en toute rigueur.")
if fr == 0:
    print(f"  ➤ ZÉRO FAUX-REÇU — le placeur BORNE le résidu. Le banc SORT de panne.")
elif fr <= 2:
    print(f"  ➤ {fr} FAUX-REÇUS — le placeur RÉDUIT SANS BORNER. Le banc RESTE en panne.")
else:
    print(f"  ➤ {fr} FAUX-REÇUS — LE PLACEUR v2 NE SUFFIT PAS. Il manque un test.")
print(f"\n  ── LE SEUIL DE 18 m EST-IL LE FAUTIF ? ──")
if mt and t5:
    bas = [m for m in mt if m < 22]; haut = [m for m in mt if m >= 22]
    print(f"  lieux reçus juste au-dessus du seuil (18-21 m) : {len(bas)}")
    print(f"  lieux reçus à 22 m ou plus                     : {len(haut)}")
    print(f"  → si les faux-reçus ({fr}) ≈ les lieux à 18-21 m ({len(bas)}), relever le seuil suffit")
