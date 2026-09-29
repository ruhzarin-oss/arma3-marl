"""Correctif ( 29/09, HMT-140 cause 5 ) : les sites industriels naissent avec leurs stocks d ouverture ( matieres et
consommables, demi-produits ), au bilan d ouverture du domaine 3. Applique au domaine 10 d un arbre. Idempotent."""
import os, sys
f = os.path.join(sys.argv[1], "monde", "pays", "d10_industrie.py")
s = open(f, encoding="utf-8").read()
if "JOURS_MATIERES" in s:
    print("deja corrige :", f); sys.exit(0)
def remplacer(s, a, b):
    if s.count(a) != 1: raise SystemExit(f"{f} : ancre introuvable ou multiple ( {s.count(a)} ) : {a[:70]!r}")
    return s.replace(a, b)
s = remplacer(s, "def valeur_stocks(p, entreprise):\n",
    "# ( 29/09, HMT-140 cause 5 ) Une usine en marche possede ses stocks : ils naissent avec elle, au bilan d ouverture. Sans\n"
    "# eux, aucun atelier des fonderies ne produisait les dix premiers jours ( la chaine mine -> carriere -> fonderie met ce\n"
    "# temps a livrer, le gazole des mines partait de zero ) et le domaine 4 mettait tout l effectif present sans heure en\n"
    "# disponibilite vers le jour 5 ( 171 salaries sur 172, Altis, tronc f670702 ). Le niveau est celui du reel, pas celui\n"
    "# qui fait marcher : Sidenor ( acier de ferraille, Grece ), etats financiers 2019, note 13 : matieres premieres et\n"
    "# auxiliaires, consommables 15,05 M euros, demi-produits 0,83 M, pour 301,69 M de stocks passes en cout des ventes ;\n"
    "# les matieres pesant ~70 % du cout, 15,05 / ( 0,7 x 301,69 ) x 365 = ~26 jours de consommation ; les demi-produits,\n"
    "# 0,83 / 301,69 x 365 = ~1 jour. https://sidenor.gr/wp-content/uploads/2020/09/Sidenor-FS-31.12.2019-EN-Final.pdf\n"
    "JOURS_MATIERES = 26.0\n"
    "JOURS_DEMI_PRODUITS = 1.0\n"
    "DEMI_PRODUITS = (\"fonte\", \"acier\")\n"
    "\n"
    "\n"
    "def _besoins_nominaux(s):\n"
    "    \"\"\"Ce qu un site consomme par jour a plein regime : les intrants materiels de ses recettes ( comme _besoin_site ) et\n"
    "    le gazole de ses gisements ( comme _acheter_gazole ).\"\"\"\n"
    "    besoin = {}\n"
    "    for a in s.ateliers:\n"
    "        nominal = s.equipe * a.part * HEURES_POSTE * a.productivite()\n"
    "        if a.recette is not None:\n"
    "            for b, k in a.recette.entrees.items():\n"
    "                if b != \"electricite\": besoin[b] = besoin.get(b, 0.0) + k * nominal\n"
    "        elif a.gisement is not None and a.gisement.reserve_t > 0:\n"
    "            g = a.gisement.type\n"
    "            besoin[\"carburant\"] = besoin.get(\"carburant\", 0.0) + (s.equipe * a.part * HEURES_POSTE * g.materiel_t_h\n"
    "                                                                     * g.gazole_l_t / LITRES_PAR_UNITE_CARBURANT)\n"
    "    return besoin\n"
    "\n"
    "\n"
    "def _stocks_d_ouverture(p, D_):\n"
    "    \"\"\"A l installation : chaque site recoit JOURS_MATIERES jours de ses matieres et consommables et JOURS_DEMI_PRODUITS\n"
    "    de ses demi-produits ( une source declaree, motif stock_initial ), puis le domaine 3 les met au bilan d ouverture.\"\"\"\n"
    "    L = p.socle.livre; cat = p.socle.catalogue\n"
    "    X = importlib.import_module(\".d07_exterieur\", __package__)\n"
    "    for s in D_.sites:\n"
    "        e = s.entreprise\n"
    "        for b, q in sorted(_besoins_nominaux(s).items()):\n"
    "            q *= JOURS_DEMI_PRODUITS if b in DEMI_PRODUITS else JOURS_MATIERES\n"
    "            if q <= 1e-9: continue\n"
    "            if b in BIENS_E1: L.source(X.StockE1(e.stocks, cat), cat.id(b), q, \"produit\", \"stock_initial\")\n"
    "            else: L.source(s.stock, cat.id(b), q, \"produit\", \"stock_initial\")\n"
    "        if p.a(\"economie\") and hasattr(ECO, \"ouvrir_stocks\"): ECO.ouvrir_stocks(p, e)\n"
    "\n"
    "\n"
    "def valeur_stocks(p, entreprise):\n")
s = remplacer(s,
    "    for e in w.entreprises.values():\n"
    "        if e.type == \"pharmacie\": D_.vu_pharmacie[e.id] = sum(e.produit_du_jour.values())\n",
    "    _stocks_d_ouverture(p, D_)                      # ( HMT-140 ) une usine en marche possede ses stocks\n"
    "    for e in w.entreprises.values():\n"
    "        if e.type == \"pharmacie\": D_.vu_pharmacie[e.id] = sum(e.produit_du_jour.values())\n")
open(f, "w", encoding="utf-8").write(s); print("corrige :", f)
