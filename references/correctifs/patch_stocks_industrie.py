"""Correctif ( 29/09, HMT-140 cause 5 ) : les sites industriels naissent avec leurs stocks d ouverture ( matieres et
consommables, demi-produits ), au bilan d ouverture du domaine 3 ; les stocks se comptent en jours de la consommation
reelle lissee de chaque site ( 29/09 ) ; la cible en jours de demande sans plancher nominal, les demandes livrer dans le
besoin, le gisement exporte regle sur son cout et ses invendus ( HMT-155 v2, 30/09 ). Applique au domaine 10 d un arbre. Idempotent. Les blocs ( ancien, nouveau ) sont ceux du diff du moteur, contexte compris."""
import os, sys
f = os.path.join(sys.argv[1], "monde", "pays", "d10_industrie.py")
s = open(f, encoding="utf-8").read()
if "JOURS_MATIERES" in s:
    print("deja corrige :", f); sys.exit(0)
def remplacer(s, a, b):
    if s.count(a) != 1: raise SystemExit(f"{f} : ancre introuvable ou multiple ( {s.count(a)} ) : {a[:70]!r}")
    return s.replace(a, b)
BLOCS = [
    ("REGIME_MIN = 0.25                 # un atelier d un bien du moteur ne descend pas sous un quart ( le moteur : 0,1 )\n"
     "PAS_REGIME = 0.25\n"
     "RESERVE_RESEAU_MIN = 50.0        # unites du reseau du moteur laissees en plus d une journee des autres sites\n"
     "STOCK_MIN_J = 2.0                 # sans client, un atelier remplit 2 jours de sa production nominale, puis s arrete\n"
     "JOURS_STOCK = 5.0                 # avec clients : 5 jours de leur besoin\n"
     "JOURS_RATTRAPAGE = 3.0            # un manque de stock se comble en 3 jours\n"
     "JOURS_INTRANTS = 3.0              # un site garde 3 jours de ses intrants venus d ailleurs\n",
     "REGIME_MIN = 0.25                 # un atelier d un bien du moteur ne descend pas sous un quart ( le moteur : 0,1 )\n"
     "PAS_REGIME = 0.25\n"
     "RESERVE_RESEAU_MIN = 50.0        # unites du reseau du moteur laissees en plus d une journee des autres sites\n"
     "STOCK_MIN_J = 2.0                 # le producteur garde 2 jours de son besoin ( commandes, clients a leur regime ) ; ( 30/09 )\n"
     "                                  # avant, sans client, 2 jours de sa production NOMINALE : un stock proportionnel a l equipe\n"
     "JOURS_STOCK = 5.0                 # avec clients : 5 jours de leur besoin\n"
     "JOURS_RATTRAPAGE = 3.0            # un manque de stock se comble en 3 jours\n"
     "JOURS_INTRANTS = 3.0              # un site garde 3 jours de ses intrants venus d ailleurs\n"),
    ('    """Une entreprise du moteur reprise ( mine, carriere, fonderie ). Son stock du socle tient les biens nouveaux ; les\n'
     '    biens du moteur restent dans Entreprise.stocks. equipe : les travailleurs affectes ( index du moteur, au matin )."""\n'
     '    __slots__ = ("id", "entreprise", "lieu", "type", "stock", "ateliers", "equipe", "equipe_ref", "facteur_eau",\n'
     '                 "actif", "heures_j")\n'
     "\n"
     "    def __init__(self, entreprise, stock):\n"
     "        self.id, self.entreprise, self.lieu, self.type = entreprise.id, entreprise, entreprise.lieu, entreprise.type\n",
     '    """Une entreprise du moteur reprise ( mine, carriere, fonderie ). Son stock du socle tient les biens nouveaux ; les\n'
     '    biens du moteur restent dans Entreprise.stocks. equipe : les travailleurs affectes ( index du moteur, au matin )."""\n'
     '    __slots__ = ("id", "entreprise", "lieu", "type", "stock", "ateliers", "equipe", "equipe_ref", "facteur_eau",\n'
     '                 "actif", "heures_j", "besoin_lisse")\n'
     "\n"
     "    def __init__(self, entreprise, stock):\n"
     "        self.id, self.entreprise, self.lieu, self.type = entreprise.id, entreprise, entreprise.lieu, entreprise.type\n"),
    ("        self.facteur_eau = 1.0\n"
     "        self.actif = True\n"
     "        self.heures_j = 0.0\n"
     "\n"
     "\n"
     "class Chargement:\n",
     "        self.facteur_eau = 1.0\n"
     "        self.actif = True\n"
     "        self.heures_j = 0.0\n"
     "        self.besoin_lisse = {}      # bien -> ce que le site consomme par jour, lisse ( _lisser_besoins )\n"
     "\n"
     "\n"
     "class Chargement:\n"),
    ('    __slots__ = ("sites", "par_entreprise", "chargements", "prochain_chargement", "machines", "decideur", "rng_pannes",\n'
     '                 "rng_accidents", "facteur_risque", "commandes", "livre_biens", "e1_flux", "fabrications", "stats",\n'
     '                 "heures_secteur", "accidents_secteur", "attendu", "blessures", "remplacements", "co2_t",\n'
     '                 "reserve_reseau", "vu_pharmacie")\n'
     "\n"
     "    def __init__(self):\n"
     "        self.sites = []                 # Site, dans l ordre des identifiants\n",
     '    __slots__ = ("sites", "par_entreprise", "chargements", "prochain_chargement", "machines", "decideur", "rng_pannes",\n'
     '                 "rng_accidents", "facteur_risque", "commandes", "livre_biens", "e1_flux", "fabrications", "stats",\n'
     '                 "heures_secteur", "accidents_secteur", "attendu", "blessures", "remplacements", "co2_t",\n'
     '                 "reserve_reseau", "vu_pharmacie", "demandes_jour", "demande_hors_lisse", "reste_a_servir")\n'
     "\n"
     "    def __init__(self):\n"
     "        self.sites = []                 # Site, dans l ordre des identifiants\n"),
    ("        self.co2_t = 0.0\n"
     "        self.vu_pharmacie = {}          # id de la pharmacie du moteur -> sa production cumulee deja abreuvee\n"
     "        self.reserve_reseau = RESERVE_RESEAU_MIN   # unites du reseau du moteur que l industrie laisse aux autres sites\n"
     "\n"
     "\n"
     'MOTIF_PRODUCTION, MOTIF_INTRANT, MOTIF_LIVRAISON = "production_industrie", "intrant_industrie", "livraison_interne"\n',
     "        self.co2_t = 0.0\n"
     "        self.vu_pharmacie = {}          # id de la pharmacie du moteur -> sa production cumulee deja abreuvee\n"
     "        self.reserve_reseau = RESERVE_RESEAU_MIN   # unites du reseau du moteur que l industrie laisse aux autres sites\n"
     "        self.demandes_jour = {}         # ( 30/09, HMT-155 v2 ) bien -> { demandeur : [ demande du jour, servi du jour ] }\n"
     "        self.demande_hors_lisse = {}    # bien -> la demande des autres domaines ( livrer ), lissee\n"
     "        self.reste_a_servir = {}        # bien -> ce que la veille n a pas servi\n"
     "\n"
     "\n"
     'MOTIF_PRODUCTION, MOTIF_INTRANT, MOTIF_LIVRAISON = "production_industrie", "intrant_industrie", "livraison_interne"\n'),
    ("    return par_t / g.rendements[a.directeur]\n"
     "\n"
     "\n"
     "def valeur_directeur(p, a):\n"
     '    """Ce que rapporte une unite du bien directeur : le prix que le marche de la region paie au producteur pour un bien\n'
     '    du moteur ( economie ), le prix de cession pour un bien nouveau."""\n',
     "    return par_t / g.rendements[a.directeur]\n"
     "\n"
     "\n"
     "def valeur_extraction(p, a):\n"
     '    """( 30/09, HMT-155 ) Drachmes par unite du bien directeur d un gisement, TOUS ses coproduits compris : chaque bien\n'
     "    qu il rend, a ce que le marche de la region paie au producteur ( bien du moteur : fer, zinc, or ) ou a son prix de\n"
     "    cession ( bien nouveau : cuivre, calcaire ), rapporte a l unite du directeur. Un gisement polymetallique ( le skarn :\n"
     '    fer, zinc, cuivre, or ) vit de l ensemble, comme les sulfures de Chalcidique vivent de l or et des concentres."""\n'
     "    g = a.gisement; m = p.w.marches[a.site.entreprise.lieu.marche.id]\n"
     "    v = math.fsum(r * (BIENS[b][2] if b in BIENS else m.prix[b] * (1.0 - m.marge)) for b, r in g.rendements.items())\n"
     "    return v / g.rendements[a.directeur]\n"
     "\n"
     "\n"
     "def _exportable(p, b):\n"
     '    """( 30/09, HMT-155 v2 ) Vrai si le negoce du domaine 7 exporte ce bien ( fer, zinc, or... )."""\n'
     '    if not p.a("exterieur"): return False\n'
     '    return b in importlib.import_module(".d07_exterieur", __package__).BIENS_IMPORT\n'
     "\n"
     "\n"
     "def _clore_demandes(D_):\n"
     '    """( 30/09, HMT-155 v2 ) Le matin, les demandes livrer de la veille : leur somme ( une fois par demandeur ) entre dans\n'
     '    la demande lissee, et ce qui n a pas ete servi devient le reste a servir. Puis la journee repart de zero."""\n'
     "    for b, par in D_.demandes_jour.items():\n"
     "        dem = math.fsum(x[0] for x in par.values())\n"
     "        D_.demande_hors_lisse[b] = (1.0 - ALPHA_BESOIN) * D_.demande_hors_lisse.get(b, 0.0) + ALPHA_BESOIN * dem\n"
     "        D_.reste_a_servir[b] = math.fsum(max(0.0, x[0] - x[1]) for x in par.values())\n"
     "    for b in list(D_.demande_hors_lisse):\n"
     "        if b not in D_.demandes_jour:\n"
     "            D_.demande_hors_lisse[b] *= (1.0 - ALPHA_BESOIN); D_.reste_a_servir[b] = 0.0\n"
     "    D_.demandes_jour = {}\n"
     "\n"
     "\n"
     "def _invendus_en_jours(p, e, b):\n"
     '    """( 30/09, HMT-155 ) Les invendus d un bien du moteur sur le site d une entreprise, en jours de la demande lissee de\n'
     '    son marche : un gisement dont les camions n emportent pas tout le voit, et descend."""\n'
     '    em = p.domaine("economie").marches[e.lieu.marche.id]\n'
     "    return max(0.0, e.stocks[b]) / max(ECO.DEMANDE_MIN, em.demande_lisse[b])\n"
     "\n"
     "\n"
     "def valeur_directeur(p, a):\n"
     '    """Ce que rapporte une unite du bien directeur : le prix que le marche de la region paie au producteur pour un bien\n'
     '    du moteur ( economie ), le prix de cession pour un bien nouveau."""\n'),
    ("    return m.prix[b] * (1.0 - m.marge)\n"
     "\n"
     "\n"
     "def _regimes(p, D_):\n"
     '    """Chaque atelier regle son regime sur son bien directeur. Un bien du moteur ( fer, zinc, outils ) : par crans de\n'
     "    0,25 sur la couverture du marche de sa region ( sous la cible : plus ; au-dela de deux fois : moins ), comme la regle\n"
     "    du moteur et de l economie ; un gisement qui donne de l or tourne plein ( l or se vend au prix mondial ). Un bien\n"
     "    nouveau : produire le besoin de ses clients ( ateliers aval a leur regime, commandes ), plus de quoi ramener le\n"
     "    stock du pays a sa cible en 3 jours ; sans client, remplir 2 jours de production et s arreter. Et le cout : un\n"
     "    atelier ne fait pas un bien nouveau a perte ( cout variable au-dessus du prix de cession : arret ) ; un bien du\n"
     "    moteur perd un cran quand son prix ne couvre plus le cout variable, comme la regle de l economie. Un four a fonte\n"
     "    electrique paie ~ 2 300 kWh par tonne : au tarif du moteur ( ~ 0,18 euro le kWh, le tarif reglemente grec ) il\n"
     '    perd de l argent, et il n existe en vrai qu avec une electricite a quelques centimes ( hydraulique norvegienne )."""\n'
     "    cat = p.socle.catalogue\n"
     "    ateliers = [a for s in D_.sites if s.actif for a in s.ateliers]\n"
     "    for a in ateliers:\n",
     "    return m.prix[b] * (1.0 - m.marge)\n"
     "\n"
     "\n"
     "def _regimes(p, D_, equilibre=False):\n"
     '    """Chaque atelier regle son regime sur son bien directeur. Un bien du moteur ( fer, zinc, outils ) : par crans de\n'
     "    0,25 sur la couverture du marche de sa region ( sous la cible : plus ; au-dela de deux fois : moins ), comme la regle\n"
     "    du moteur et de l economie ; un gisement compte ses invendus, compare son cout a tous ses coproduits et peut\n"
     "    s arreter ( 30/09 ). Un bien nouveau : produire le besoin de ses clients ( ateliers aval a leur regime, commandes ),\n"
     "    plus de quoi ramener le stock du pays a sa cible en 3 jours ; sans besoin, rien ( 30/09 ). Et le cout : un\n"
     "    atelier ne fait pas un bien nouveau a perte ( cout variable au-dessus du prix de cession : arret ) ; un bien du\n"
     "    moteur perd un cran quand son prix ne couvre plus le cout variable, comme la regle de l economie. Un four a fonte\n"
     "    electrique paie ~ 2 300 kWh par tonne : au tarif du moteur ( ~ 0,18 euro le kWh, le tarif reglemente grec ) il\n"
     "    perd de l argent, et il n existe en vrai qu avec une electricite a quelques centimes ( hydraulique norvegienne ).\n"
     "    ( 29/09 ) La cible du pays : les jours de stock que les sites clients gardent de leur consommation lissee, plus les 2\n"
     "    jours du producteur. equilibre : le monde qui nait ( _stocks_d_ouverture ) ; chaque stock est a sa cible, un bien\n"
     '    nouveau produit ce que ses clients consomment, un bien du moteur garde son regime."""\n'
     "    cat = p.socle.catalogue\n"
     "    ateliers = [a for s in D_.sites if s.actif for a in s.ateliers]\n"
     "    for a in ateliers:\n"),
    ("        if g is not None and g.reserve_t <= 0.0: a.regime = 0.0; continue\n"
     "        b = a.directeur\n"
     "        if b in BIENS: continue\n"
     '        if g is not None and "or" in g.rendements: a.regime = 1.0; a.couverture = 0.0; continue\n'
     "        couv = _demande_lissee(p, a.site.entreprise, b)\n"
     "        cible = ECO.COUVERTURE_CIBLE_J.get(b, 5.0)\n"
     "        a.couverture = couv / (2.0 * cible)\n"
     "        if couv >= 2.0 * cible or cout_variable(p, a) > valeur_directeur(p, a): a.regime = max(REGIME_MIN, a.regime - PAS_REGIME)\n"
     "        elif couv < cible: a.regime = min(1.0, a.regime + PAS_REGIME)\n"
     "    for b in ORDRE_BIENS:\n"
     "        prod = [a for a in ateliers if a.directeur == b and not (a.gisement is not None and a.gisement.reserve_t <= 0.0)]\n"
     "        for a in [a for a in prod if cout_variable(p, a) > valeur_directeur(p, a)]:\n"
     "            a.regime = 0.0; prod.remove(a)\n"
     "        if not prod: continue\n"
     "        besoin = D_.commandes.get(b, 0.0) + math.fsum(\n"
     "            a.recette.entrees[b] * a.nominal_j * a.regime for a in ateliers if a.recette is not None and b in a.recette.entrees)\n"
     "        nominal = math.fsum(a.nominal_j for a in prod)\n"
     "        if nominal <= 0.0: continue\n"
     "        cible = max(STOCK_MIN_J * nominal, JOURS_STOCK * besoin)\n"
     "        dispo = _dispo_bien(D_, b, cat.id(b))\n"
     "        r = min(1.0, max(0.0, (besoin + (cible - dispo) / JOURS_RATTRAPAGE) / nominal))\n"
     "        for a in prod: a.regime = r; a.couverture = dispo / (2.0 * cible)\n"
     "\n"
     "\n"
     "def _matin(p):\n",
     "        if g is not None and g.reserve_t <= 0.0: a.regime = 0.0; continue\n"
     "        b = a.directeur\n"
     "        if b in BIENS: continue\n"
     "        if equilibre: continue\n"
     "        if g is not None and _exportable(p, b):\n"
     "            # ( 30/09, HMT-155 v2 ) un gisement dont les produits s exportent ( d07 ) vend au prix du monde : il se regle\n"
     "            # sur son cout, coproduits compris, et sur ses invendus du site en jours de sa production a plein, pas sur la\n"
     "            # demande de l ile ( la v1, bornee par la couverture du marche local, arretait la mine : 81 t pour 515 )\n"
     "            par_j = a.nominal_j * g.rendements[b]\n"
     "            inv = max(0.0, a.site.entreprise.stocks[b]) / par_j if par_j > 0.0 else math.inf\n"
     "            a.couverture = inv / INVENDUS_MAX_J\n"
     "            if cout_variable(p, a) > valeur_extraction(p, a) or inv >= INVENDUS_MAX_J: a.regime = max(0.0, a.regime - PAS_REGIME)\n"
     "            elif inv < 0.5 * INVENDUS_MAX_J: a.regime = min(1.0, a.regime + PAS_REGIME)\n"
     "            continue\n"
     "        # ( 30/09, HMT-155 ) un gisement est borne par ses ventes : ses invendus comptent dans la couverture, son cout se\n"
     "        # compare a tous ses coproduits, et il peut s arreter ( avant : un gisement qui donne de l or tournait plein )\n"
     "        couv = _demande_lissee(p, a.site.entreprise, b) + (_invendus_en_jours(p, a.site.entreprise, b) if g is not None else 0.0)\n"
     "        cible = ECO.COUVERTURE_CIBLE_J.get(b, 5.0)\n"
     "        a.couverture = couv / (2.0 * cible)\n"
     "        valeur = valeur_extraction(p, a) if g is not None else valeur_directeur(p, a)\n"
     "        plancher = 0.0 if g is not None else REGIME_MIN\n"
     "        if couv >= 2.0 * cible or cout_variable(p, a) > valeur: a.regime = max(plancher, a.regime - PAS_REGIME)\n"
     "        elif couv < cible: a.regime = min(1.0, a.regime + PAS_REGIME)\n"
     "    for b in ORDRE_BIENS:\n"
     "        prod = [a for a in ateliers if a.directeur == b and not (a.gisement is not None and a.gisement.reserve_t <= 0.0)]\n"
     "        for a in [a for a in prod if cout_variable(p, a) > valeur_directeur(p, a)]:\n"
     "            a.regime = 0.0; prod.remove(a)\n"
     "        if not prod: continue\n"
     "        besoin = (D_.commandes.get(b, 0.0) + D_.demande_hors_lisse.get(b, 0.0)    # ( 30/09, v2 ) les demandes livrer\n"
     "                  + D_.reste_a_servir.get(b, 0.0) / JOURS_RATTRAPAGE) + math.fsum(\n"
     "            a.recette.entrees[b] * a.nominal_j * a.regime for a in ateliers if a.recette is not None and b in a.recette.entrees)\n"
     "        nominal = math.fsum(a.nominal_j for a in prod)\n"
     "        if nominal <= 0.0: continue\n"
     "        lisse = math.fsum(s.besoin_lisse.get(b, 0.0) for s in D_.sites if s.actif)\n"
     "        cible = STOCK_MIN_J * besoin + jours_de_stock(b) * lisse   # ( 30/09, HMT-155 ) en jours de DEMANDE, sans plancher nominal\n"
     "        dispo = cible if equilibre else _dispo_bien(D_, b, cat.id(b))\n"
     "        r = min(1.0, max(0.0, (besoin + (cible - dispo) / JOURS_RATTRAPAGE) / nominal))\n"
     "        for a in prod: a.regime = r; a.couverture = dispo / (2.0 * cible) if cible > 0.0 else 1.0\n"
     "\n"
     "\n"
     "def _matin(p):\n"),
    ("    D_.reserve_reseau = RESERVE_RESEAU_MIN + HEURES_POSTE * math.fsum(\n"
     '        len(w.ids_au_travail(e.lieu, e.role)) * e.intrants.get("electricite", 0.0)\n'
     '        for e in w.entreprises.values() if e.id not in p.repris and e.type != "centrale")\n'
     "    _regimes(p, D_)\n"
     "    dec = D_.decideur; parc = p.socle.parc\n"
     "    for s in D_.sites:\n"
     "        if not s.actif: continue\n",
     "    D_.reserve_reseau = RESERVE_RESEAU_MIN + HEURES_POSTE * math.fsum(\n"
     '        len(w.ids_au_travail(e.lieu, e.role)) * e.intrants.get("electricite", 0.0)\n'
     '        for e in w.entreprises.values() if e.id not in p.repris and e.type != "centrale")\n'
     "    _clore_demandes(D_)\n"
     "    _regimes(p, D_)\n"
     "    for s in D_.sites:\n"
     "        if s.actif: _lisser_besoins(s)\n"
     "    dec = D_.decideur; parc = p.socle.parc\n"
     "    for s in D_.sites:\n"
     "        if not s.actif: continue\n"),
    ('    p.compter("panne_machine")\n'
     "    rng = D_.rng_accidents\n"
     "    pa, pm = a.p_acc * D_.facteur_risque, a.p_mort * D_.facteur_risque\n"
     "    D_.attendu[0] += pa; D_.attendu[1] += pm\n"
     "    u = rng.random()\n"
     "    tb = p.w.table                                # `presents` : les numeros des presents ( _pas, en colonnes )\n"
     "    vivants = presents[tb.vivant[presents] != 0]\n"
     "    if u < pa + pm and len(vivants):\n"
     "        h = PO.Habitant(tb, int(vivants[int(rng.integers(len(vivants)))]))\n"
     "        mortel = u >= pa\n",
     '    p.compter("panne_machine")\n'
     "    rng = D_.rng_accidents\n"
     "    pa, pm = a.p_acc * D_.facteur_risque, a.p_mort * D_.facteur_risque\n"
     "    u = rng.random()\n"
     "    tb = p.w.table                                # `presents` : les numeros des presents ( _pas, en colonnes )\n"
     "    vivants = presents[tb.vivant[presents] != 0]\n"
     "    # ( 29/09 ) l attendu est la probabilite de ce tirage : une panne blesse au plus une personne, et personne si nul n est\n"
     "    # present. Avant, il ajoutait l intensite : au facteur de risque 1 000 de la porte, 1 a 12 par panne pour 1 accident\n"
     "    # possible, et l attendu des pannes depassait de ~6 fois ce que le tirage pouvait donner ( test_accidents ).\n"
     "    if len(vivants): D_.attendu[0] += min(pa, 1.0); D_.attendu[1] += min(pa + pm, 1.0) - min(pa, 1.0)\n"
     "    if u < pa + pm and len(vivants):\n"
     "        h = PO.Habitant(tb, int(vivants[int(rng.integers(len(vivants)))]))\n"
     "        mortel = u >= pa\n"),
    ("# ================================================================== l apres-midi ( 16 h ) : gazole et livraisons entre sites\n"
     "def _acheter_gazole(p, D_):\n"
     '    """Les sites qui roulent au gazole l achetent au marche de leur region, TVA comprise, comme le moteur achete les\n'
     '    intrants de ses entreprises : deux jours de reserve, sans descendre le marche sous la reserve de ses convois."""\n'
     "    w = p.w; L = p.socle.livre; g = w.gouv\n"
     "    for s in D_.sites:\n"
     "        if not s.actif: continue\n"
     "        besoin = 0.0\n"
     "        for a in s.ateliers:\n"
     "            gi = a.gisement\n"
     "            if gi is None or gi.reserve_t <= 0: continue\n"
     "            besoin += (s.equipe * a.part * HEURES_POSTE * a.regime * gi.type.materiel_t_h * gi.type.gazole_l_t\n"
     "                       / LITRES_PAR_UNITE_CARBURANT)\n"
     "        e = s.entreprise\n"
     '        if besoin <= 0.0 or e.stocks["carburant"] >= 2.0 * besoin: continue\n'
     "        m = w.marches[e.lieu.marche.id]\n"
     '        voulu = 3.0 * besoin - e.stocks["carburant"]\n'
     '        q = min(voulu, m.stocks["carburant"] - RESERVE_CARBURANT_MARCHE)\n'
     "        # 27/09 : la commande entiere est une demande, et ce que le marche ne peut pas servir est une rupture ( non servi ) :\n"
     "        # avant, une mine a sec devant un marche sous sa reserve ne laissait aucune trace, le prix ne bougeait pas, la\n",
     "# ================================================================== l apres-midi ( 16 h ) : gazole et livraisons entre sites\n"
     "def _acheter_gazole(p, D_):\n"
     '    """Les sites qui roulent au gazole l achetent au marche de leur region, TVA comprise, comme le moteur achete les\n'
     "    intrants de ses entreprises : JOURS_MATIERES jours de sa consommation lissee ( 29/09 ; avant : deux ), sans\n"
     '    descendre le marche sous la reserve de ses convois."""\n'
     "    w = p.w; L = p.socle.livre; g = w.gouv\n"
     "    for s in D_.sites:\n"
     "        if not s.actif: continue\n"
     '        besoin = s.besoin_lisse.get("carburant", 0.0)\n'
     "        e = s.entreprise\n"
     '        if besoin <= 0.0 or e.stocks["carburant"] >= (JOURS_MATIERES - 1.0) * besoin: continue   # ( 29/09 ) consommable\n'
     "        m = w.marches[e.lieu.marche.id]\n"
     '        voulu = JOURS_MATIERES * besoin - e.stocks["carburant"]\n'
     '        q = min(voulu, m.stocks["carburant"] - RESERVE_CARBURANT_MARCHE)\n'
     "        # 27/09 : la commande entiere est une demande, et ce que le marche ne peut pas servir est une rupture ( non servi ) :\n"
     "        # avant, une mine a sec devant un marche sous sa reserve ne laissait aucune trace, le prix ne bougeait pas, la\n"),
    ("\n"
     "def _livraisons(p, D_):\n"
     '    """Chaque site qui manque d un intrant venu d ailleurs ( lignite, calcaire, gypse, sable, fonte ) le fait venir du\n'
     "    site le plus proche qui en a ( au-dela de son propre jour de besoin ). Le camion part, les biens sont en route le\n"
     "    temps du trajet ( km de la carte a la vitesse des convois ) ; le gazole est achete au marche de depart par le site\n"
     "    qui recoit, qui paie aussi la marchandise au prix de cession ( ou la doit : creance du socle ). Un marche sans\n"
     '    gazole au-dela de sa reserve : pas de camion ce jour-la."""\n',
     "\n"
     "def _livraisons(p, D_):\n"
     '    """Chaque site qui manque d un intrant venu d ailleurs ( lignite, calcaire, gypse, sable, fonte ) le fait venir du\n'
     "    site le plus proche qui en a ( au-dela de ses propres jours de stock ; 29/09 : sur la consommation lissee, avant :\n"
     "    3 jours du besoin du jour, et la source gardait 1 jour ). Le camion part, les biens sont en route le\n"
     "    temps du trajet ( km de la carte a la vitesse des convois ) ; le gazole est achete au marche de depart par le site\n"
     "    qui recoit, qui paie aussi la marchandise au prix de cession ( ou la doit : creance du socle ). Un marche sans\n"
     '    gazole au-dela de sa reserve : pas de camion ce jour-la."""\n'),
    ("        biens = sorted({b for a in s.ateliers if a.recette is not None for b in a.recette.entrees if b in BIENS})\n"
     "        for b in biens:\n"
     "            bid = cat.id(b)\n"
     "            besoin = _besoin_site(s, b)\n"
     "            manque = JOURS_INTRANTS * besoin - s.stock[bid] - _en_route_vers(D_, s, bid)\n"
     "            if besoin <= 0.0 or manque < LOT_MIN_T: continue\n"
     "            sources = sorted((x for x in D_.sites if x is not s and x.actif and x.lieu.ile == s.lieu.ile),\n"
     "                             key=lambda x: (x.lieu.distance(s.lieu), x.id))\n"
     "            for src in sources:\n"
     "                q = min(manque, src.stock[bid] - _besoin_site(src, b))\n"
     "                if q < LOT_MIN_T: continue\n"
     "                km = w.carte.km_route(src.lieu, s.lieu)\n"
     "                m = w.marches[src.lieu.marche.id]\n",
     "        biens = sorted({b for a in s.ateliers if a.recette is not None for b in a.recette.entrees if b in BIENS})\n"
     "        for b in biens:\n"
     "            bid = cat.id(b)\n"
     "            besoin = s.besoin_lisse.get(b, 0.0)\n"
     "            manque = jours_de_stock(b) * besoin - s.stock[bid] - _en_route_vers(D_, s, bid)   # ( 29/09 ) le niveau reel\n"
     "            if besoin <= 0.0 or manque < LOT_MIN_T: continue\n"
     "            sources = sorted((x for x in D_.sites if x is not s and x.actif and x.lieu.ile == s.lieu.ile),\n"
     "                             key=lambda x: (x.lieu.distance(s.lieu), x.id))\n"
     "            for src in sources:\n"
     "                q = min(manque, src.stock[bid] - jours_de_stock(b) * src.besoin_lisse.get(b, 0.0))\n"
     "                if q < LOT_MIN_T: continue\n"
     "                km = w.carte.km_route(src.lieu, s.lieu)\n"
     "                m = w.marches[src.lieu.marche.id]\n"),
    ("\n"
     "def _livrer_energie(p, D_):\n"
     '    """Le lignite que le domaine 11 commande ( `commander( p, "charbon", t par jour )` ) part chaque jour aux cuves de ses\n'
     "    centrales de l ile, par sa fonction `livrer_combustible` ( il paie au prix de cession ) ; chaque site garde son\n"
     '    propre besoin du jour."""\n'
     '    q = D_.commandes.get("charbon", 0.0)\n'
     '    if q <= 0.0 or not p.a("energie"): return\n'
     '    ENE = importlib.import_module(".d11_energie", __package__); bid = p.socle.catalogue.id("charbon")\n'
     "    for s in D_.sites:\n"
     '        dispo = s.stock[bid] - _besoin_site(s, "charbon")\n'
     "        if not s.actif or dispo < LOT_MIN_T: continue\n"
     '        q -= ENE.livrer_combustible(p, s.stock, "charbon", min(q, dispo), s.entreprise, BIENS["charbon"][2], s.lieu.ile)\n'
     "        if q < LOT_MIN_T: break\n",
     "\n"
     "def _livrer_energie(p, D_):\n"
     '    """Le lignite que le domaine 11 commande ( `commander( p, "charbon", t par jour )` ) part chaque jour aux cuves de ses\n'
     "    centrales de l ile, par sa fonction `livrer_combustible` ( il paie au prix de cession ) ; chaque site garde ses\n"
     '    propres jours de stock ( 29/09 ; avant : son besoin du jour )."""\n'
     '    q = D_.commandes.get("charbon", 0.0)\n'
     '    if q <= 0.0 or not p.a("energie"): return\n'
     '    ENE = importlib.import_module(".d11_energie", __package__); bid = p.socle.catalogue.id("charbon")\n'
     "    for s in D_.sites:\n"
     '        dispo = s.stock[bid] - jours_de_stock("charbon") * s.besoin_lisse.get("charbon", 0.0)\n'
     "        if not s.actif or dispo < LOT_MIN_T: continue\n"
     '        q -= ENE.livrer_combustible(p, s.stock, "charbon", min(q, dispo), s.entreprise, BIENS["charbon"][2], s.lieu.ile)\n'
     "        if q < LOT_MIN_T: break\n"),
    ('    quantite livree."""\n'
     "    D_ = _dom(p); L = p.socle.livre; bid = p.socle.catalogue.id(bien)\n"
     "    reste = float(quantite)\n"
     "    for s in sorted((x for x in D_.sites if x.actif), key=lambda x: (-x.stock[bid], x.id)):\n"
     "        if reste <= 0.0: break\n"
     "        q = L.deplacer(s.stock, vers, bid, min(reste, s.stock[bid]), MOTIF_LIVRAISON)\n",
     '    quantite livree."""\n'
     "    D_ = _dom(p); L = p.socle.livre; bid = p.socle.catalogue.id(bien)\n"
     "    reste = float(quantite)\n"
     "    x = D_.demandes_jour.setdefault(bien, {}).setdefault(id(vers), [0.0, 0.0])   # ( 30/09, v2 ) une fois par demandeur et par jour\n"
     "    x[0] = max(x[0], float(quantite))\n"
     "    for s in sorted((x for x in D_.sites if x.actif), key=lambda x: (-x.stock[bid], x.id)):\n"
     "        if reste <= 0.0: break\n"
     "        q = L.deplacer(s.stock, vers, bid, min(reste, s.stock[bid]), MOTIF_LIVRAISON)\n"),
    ("        L.payer_ou_devoir(payeur, s.entreprise, q * (BIENS[bien][2] if prix is None else prix), MOTIF_VENTE,\n"
     "                          p.socle.creances, p.jour)\n"
     "        reste -= q\n"
     "    return float(quantite) - reste\n"
     "\n"
     "\n"
     "def valeur_stocks(p, entreprise):\n"
     '    """Drachmes : les biens nouveaux du site d une entreprise reprise, au prix de cession. Les comptes du domaine 3\n'
     "    ( _valeur_stocks ) ne voient que les biens du moteur : sans cette ligne, ce qu une carriere a mis en stock ( ciment,\n",
     "        L.payer_ou_devoir(payeur, s.entreprise, q * (BIENS[bien][2] if prix is None else prix), MOTIF_VENTE,\n"
     "                          p.socle.creances, p.jour)\n"
     "        reste -= q\n"
     "    x[1] += float(quantite) - reste\n"
     "    return float(quantite) - reste\n"
     "\n"
     "\n"
     "# ( 29/09, HMT-140 cause 5 ) Une usine en marche possede ses stocks : ils naissent avec elle, au bilan d ouverture. Sans\n"
     "# eux, aucun atelier des fonderies ne produisait les dix premiers jours ( la chaine mine -> carriere -> fonderie met ce\n"
     "# temps a livrer, le gazole des mines partait de zero ) et le domaine 4 mettait tout l effectif present sans heure en\n"
     "# disponibilite vers le jour 5 ( 171 salaries sur 172, Altis, tronc f670702 ). Le niveau est celui du reel, pas celui\n"
     "# qui fait marcher : Sidenor ( acier de ferraille, Grece ), etats financiers 2019, note 13 : matieres premieres et\n"
     "# auxiliaires, consommables 15,05 M euros, demi-produits 0,83 M, pour 301,69 M de stocks passes en cout des ventes ;\n"
     "# les matieres pesant ~70 % du cout, 15,05 / ( 0,7 x 301,69 ) x 365 = ~26 jours de consommation ; les demi-produits,\n"
     "# 0,83 / 301,69 x 365 = ~1 jour. https://sidenor.gr/wp-content/uploads/2020/09/Sidenor-FS-31.12.2019-EN-Final.pdf\n"
     "JOURS_MATIERES = 26.0\n"
     "# CHOIX DECLARE ( 30/09, HMT-155 v2 ) : un site d extraction dont les produits s exportent ralentit quand ses invendus\n"
     "# depassent JOURS_MATIERES jours de sa production a plein ( le ratio de Sidenor, faute d une source pour les stocks de\n"
     "# concentres d une mine ), et accelere sous la moitie.\n"
     "INVENDUS_MAX_J = JOURS_MATIERES\n"
     "JOURS_DEMI_PRODUITS = 1.0\n"
     'DEMI_PRODUITS = ("fonte", "acier")\n'
     "# CHOIX DECLARE ( 29/09 ) : pour les mines, les carrieres et leurs ateliers ( ciment, chaux ), aucune statistique de\n"
     "# branche lisible ( Eurostat SBS ne publie pas le niveau des stocks ; BACH ne couvre pas la Grece ) : le ratio des\n"
     "# matieres et consommables de Sidenor vaut pour toutes les branches du domaine, gazole des engins compris.\n"
     "# La politique du domaine suit le meme niveau ( avant : 3 jours d intrants, 5 jours de stock vise ) : un monde qui nait a\n"
     "# 26 jours sous une politique a 5 laissait l amont a l arret des semaines.\n"
     "\n"
     "\n"
     "def jours_de_stock(b):\n"
     '    """Les jours de besoin qu un site garde d un intrant ( et que les producteurs visent en plus de leurs 2 jours )."""\n'
     "    return JOURS_DEMI_PRODUITS if b in DEMI_PRODUITS else JOURS_MATIERES\n"
     "\n"
     "\n"
     "ALPHA_BESOIN = 1.0 / 30.0         # la consommation d un site lissee sur ~ un mois ( comme la demande d outils, d03 )\n"
     "\n"
     "\n"
     "def _besoins_du_jour(s):\n"
     '    """Ce qu un site consomme par jour a son regime : les intrants materiels de ses recettes ( comme _besoin_site ) et le\n'
     "    gazole de ses gisements. Le stock se compte en jours de cette consommation reelle, pas de la capacite : Sidenor\n"
     "    compte ses 26 jours sur ce qu il a consomme dans l annee ( 29/09 : le nominal au regime 1 faisait des annees de la\n"
     '    consommation reelle d un site en sureffectif )."""\n'
     "    besoin = {}\n"
     "    for a in s.ateliers:\n"
     "        if a.recette is not None:\n"
     "            for b, k in a.recette.entrees.items():\n"
     '                if b != "electricite": besoin[b] = besoin.get(b, 0.0) + k * a.nominal_j * a.regime\n'
     "        elif a.gisement is not None and a.gisement.reserve_t > 0:\n"
     "            g = a.gisement.type\n"
     '            besoin["carburant"] = besoin.get("carburant", 0.0) + (s.equipe * a.part * HEURES_POSTE * a.regime * g.materiel_t_h\n'
     "                                                                     * g.gazole_l_t / LITRES_PAR_UNITE_CARBURANT)\n"
     "    return besoin\n"
     "\n"
     "\n"
     "def _lisser_besoins(s):\n"
     "    du_jour = _besoins_du_jour(s)\n"
     "    for b in sorted(set(du_jour) | set(s.besoin_lisse)):\n"
     "        s.besoin_lisse[b] = (1.0 - ALPHA_BESOIN) * s.besoin_lisse.get(b, 0.0) + ALPHA_BESOIN * du_jour.get(b, 0.0)\n"
     "\n"
     "\n"
     "def _stocks_d_ouverture(p, D_):\n"
     '    """A l installation : chaque site recoit JOURS_MATIERES jours de ses matieres et consommables et JOURS_DEMI_PRODUITS\n'
     "    de ses demi-produits ( une source declaree, motif stock_initial ), puis le domaine 3 les met au bilan d ouverture. Les\n"
     "    jours se comptent sur la consommation du monde a l equilibre ( _regimes, equilibre ) : elle amorce la consommation\n"
     '    lissee. Les regimes calcules pour cela sont remis tels qu ils etaient : le premier matin les fixe."""\n'
     "    L = p.socle.livre; cat = p.socle.catalogue\n"
     '    X = importlib.import_module(".d07_exterieur", __package__)\n'
     "    avant = [(a, a.regime, a.couverture, a.nominal_j) for s in D_.sites for a in s.ateliers]\n"
     "    _regimes(p, D_, equilibre=True)\n"
     "    for s in D_.sites: s.besoin_lisse = _besoins_du_jour(s)\n"
     "    for a, r, c, n in avant: a.regime, a.couverture, a.nominal_j = r, c, n\n"
     "    for s in D_.sites:\n"
     "        e = s.entreprise\n"
     "        for b, q in sorted(s.besoin_lisse.items()):\n"
     "            q *= jours_de_stock(b)\n"
     "            if q <= 1e-9: continue\n"
     '            if b in BIENS_E1: L.source(X.StockE1(e.stocks, cat), cat.id(b), q, "produit", "stock_initial")\n'
     '            else: L.source(s.stock, cat.id(b), q, "produit", "stock_initial")\n'
     '        if p.a("economie") and hasattr(ECO, "ouvrir_stocks"): ECO.ouvrir_stocks(p, e)\n'
     "\n"
     "\n"
     "def valeur_stocks(p, entreprise):\n"
     '    """Drachmes : les biens nouveaux du site d une entreprise reprise, au prix de cession. Les comptes du domaine 3\n'
     "    ( _valeur_stocks ) ne voient que les biens du moteur : sans cette ligne, ce qu une carriere a mis en stock ( ciment,\n"),
    ("        par_an = math.fsum(parc.modeles[o.modele].prix_monde / (parc.modeles[o.modele].vie_h / (HEURES_POSTE * 365.0))\n"
     "                           for o in objets)\n"
     "        ECO.reevaluer_capital(p, e, net, net / par_an if par_an > 0 else None)\n"
     "    for e in w.entreprises.values():\n"
     '        if e.type == "pharmacie": D_.vu_pharmacie[e.id] = sum(e.produit_du_jour.values())\n'
     "    reg = p.socle.registre\n",
     "        par_an = math.fsum(parc.modeles[o.modele].prix_monde / (parc.modeles[o.modele].vie_h / (HEURES_POSTE * 365.0))\n"
     "                           for o in objets)\n"
     "        ECO.reevaluer_capital(p, e, net, net / par_an if par_an > 0 else None)\n"
     "    _stocks_d_ouverture(p, D_)                      # ( HMT-140 ) une usine en marche possede ses stocks\n"
     "    for e in w.entreprises.values():\n"
     '        if e.type == "pharmacie": D_.vu_pharmacie[e.id] = sum(e.produit_du_jour.values())\n'
     "    reg = p.socle.registre\n"),
]
for a, b in BLOCS: s = remplacer(s, a, b)
open(f, "w", encoding="utf-8").write(s); print("corrige :", f)
