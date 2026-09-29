"""Correctif ( 29/09, HMT-140, la ration ) : la transmission du cours mondial au prix de detail de la nourriture, en couts
( part des matieres premieres s = 0,14, USDA ERS ; Peersman 2018 ). Applique au domaine 3 d un arbre. Ancres courtes : la
ligne def et la ligne return de _prix_de_reference. Idempotent."""
import os, sys
f = os.path.join(sys.argv[1], "monde", "pays", "d03_economie.py")
s = open(f, encoding="utf-8").read()
if "PART_MATIERES = " in s:
    print("deja corrige :", f); sys.exit(0)
def remplacer(s, a, b):
    if s.count(a) != 1: raise SystemExit(f"{f} : ancre introuvable ou multiple ( {s.count(a)} ) : {a[:70]!r}")
    return s.replace(a, b)
s = remplacer(s, "def _prix_de_reference(p, em, m, b):\n",
    "# 29/09 ( HMT-140, la ration ) : la TRANSMISSION du cours mondial au prix de detail. Le cours mondial de la nourriture\n"
    "# ( domaine 7 ) est un cours de matiere premiere ( indice FAO ) ; au detail, il ne pese que sa part des couts : la\n"
    "# reference d un bien de cette table est un prix en couts, prix d installation x ( 1 - s + s x cours lisse / cours de\n"
    "# depart ). s : la part des matieres premieres agricoles dans la depense alimentaire finale, ~14 % ( USDA ERS, cite par\n"
    "# Peersman, International Food Commodity Prices and Missing ( Dis ) Inflation in the Euro Area, 2018, notes 1 et 13 ).\n"
    "# Controle : Peersman mesure +0,10 % ( non transforme ) et +0,15 % ( transforme ) de l IPCH alimentaire pour +1 % de\n"
    "# cours, 0,13 aux poids de l IPCH. Avant : 100 %, et la zone morte transmettait au detail -9 a +17 % de cours par an\n"
    "# ( graines 131 a 133 ). Les autres biens gardent la transmission entiere ( a sourcer bien par bien ).\n"
    "PART_MATIERES = {\"nourriture\": 0.14}\n\n\n"
    "def _prix_de_reference(p, em, m, b):\n")
s = remplacer(s, "    return prix0 * pml / pm0 if pm0 > 0.0 else prix0\n",
    "    if pm0 <= 0.0: return prix0\n"
    "    part = PART_MATIERES.get(b)\n"
    "    return prix0 * (1.0 - part + part * pml / pm0) if part is not None else prix0 * pml / pm0\n")
open(f, "w", encoding="utf-8").write(s); print("corrige :", f)
