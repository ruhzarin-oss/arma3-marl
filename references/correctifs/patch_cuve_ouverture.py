"""Correctif HMT-143 ( 29/09 ) : la cuve de brut de la raffinerie nait pleine et a elle. Applique au domaine 11 d un
arbre ( atelier ou archive de reference ). Idempotent. Usage : python patch_cuve_ouverture.py <arbre>"""
import os, sys

arbre = sys.argv[1]
f = os.path.join(arbre, "monde", "pays", "d11_energie.py")
s = open(f, encoding="utf-8").read()
if "HMT-143" in s:
    print("deja corrige :", f); sys.exit(0)
avant = "        E.nominal_brut_j = n * DEBIT_OUVRIER_H * 8.0\n"
if s.count(avant) != 1: raise SystemExit(f"ancre introuvable ou multiple ( {s.count(avant)} )")
s = s.replace(avant, avant +
    "        # ( HMT-143, 29/09 ) une raffinerie en marche possede son stock de brut : la cuve nait pleine et a elle, du brut\n"
    "        # achete avant le premier jour du monde ( une source declaree, motif stock_initial, comme les greniers du domaine\n"
    "        # 9 ). Avant, l oleoduc la remplissait des le jour 1, a credit et sans echeance : la raffinerie naissait avec ~200 000\n"
    "        # drachmes d arrieres envers le puits ( 233 000 au jour 10 d Altis, graine 1 ).\n"
    '        q = CUVE_BRUT_J * E.nominal_brut_j - E.raffinerie.stocks.get("petrole", 0.0)\n'
    '        if q > EPS: L.source(StocksE1(E.raffinerie.stocks, E.noms), E.ids["petrole"], q, "produit", "stock_initial")\n')
open(f, "w", encoding="utf-8").write(s)
print("corrige :", f)
