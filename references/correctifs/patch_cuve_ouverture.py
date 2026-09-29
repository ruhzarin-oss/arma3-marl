"""Correctif HMT-143 ( 29/09 ) : la cuve de brut de la raffinerie nait pleine et a elle, et elle entre au BILAN
D OUVERTURE du domaine 3 ( pas au resultat du premier soir ). Applique aux domaines 3 et 11 d un arbre ( atelier ou
archive de reference ). Idempotent. Usage : python patch_cuve_ouverture.py <arbre>"""
import os, sys

arbre = sys.argv[1]


def remplacer(s, a, b, f):
    if s.count(a) != 1: raise SystemExit(f"{f} : ancre introuvable ou multiple ( {s.count(a)} ) : {a[:70]!r}")
    return s.replace(a, b)


# 1. le domaine 3 : ouvrir_stocks
f = os.path.join(arbre, "monde", "pays", "d03_economie.py")
s = open(f, encoding="utf-8").read()
if "def ouvrir_stocks" not in s:
    a = "def reevaluer_capital(p, unite, valeur_nette, duree_vie_ans=None):\n"
    s = remplacer(s, a,
        "def ouvrir_stocks(p, unite):\n"
        "    \"\"\"( HMT-143, 29/09 ) Un domaine qui pose, a son installation, le stock d ouverture d une entreprise ( la cuve de\n"
        "    brut de la raffinerie, domaine 11 ) le fait entrer au BILAN D OUVERTURE : la valeur des stocks et les capitaux\n"
        "    propres d ouverture montent ensemble, et rien ne passe au resultat du premier jour. Le domaine 3 prend son bilan\n"
        "    d ouverture a sa propre installation, avant les domaines suivants : sans cela, la cuve entrait au resultat du\n"
        "    premier soir ( ~200 000 drachmes de benefice a Altis ), puis a l assiette de l IS et au redressement fiscal.\"\"\"\n"
        "    c = comptes(p, unite)\n"
        "    st = _valeur_stocks(p.w, unite, _marche_de(p.w, unite))\n"
        "    delta = st - c.stocks_val\n"
        "    c.stocks_val = st; c.cp += delta; c.cp0 += delta\n"
        "    return delta\n\n\n" + a, f)
    open(f, "w", encoding="utf-8").write(s); print("corrige :", f)
else: print("deja corrige :", f)

# 2. le domaine 11 : la cuve pleine, puis au bilan d ouverture
f = os.path.join(arbre, "monde", "pays", "d11_energie.py")
s = open(f, encoding="utf-8").read()
if "ECO.ouvrir_stocks" not in s:
    a = "        E.nominal_brut_j = n * DEBIT_OUVRIER_H * 8.0\n"
    s = remplacer(s, a, a +
        "        # ( HMT-143, 29/09 ) une raffinerie en marche possede son stock de brut : la cuve nait pleine et a elle, du brut\n"
        "        # achete avant le premier jour du monde ( une source declaree, motif stock_initial, comme les greniers du domaine\n"
        "        # 9 ), au bilan d ouverture du domaine 3 ( ni au resultat du premier soir, ni a l IS, ni au redressement ). Avant,\n"
        "        # l oleoduc la remplissait des le jour 1, a credit et sans echeance : ~200 000 drachmes d arrieres a la naissance.\n"
        '        q = CUVE_BRUT_J * E.nominal_brut_j - E.raffinerie.stocks.get("petrole", 0.0)\n'
        "        if q > EPS:\n"
        '            L.source(StocksE1(E.raffinerie.stocks, E.noms), E.ids["petrole"], q, "produit", "stock_initial")\n'
        '            if p.a("economie"): ECO.ouvrir_stocks(p, E.raffinerie)\n', f)
    open(f, "w", encoding="utf-8").write(s); print("corrige :", f)
else: print("deja corrige :", f)
