"""29/09 ( HMT-145, la demande chiffree ) : aucun domaine ne lisait le budget des menages ; la part reservee a une division
qu aucun domaine n encaissait restait dans la caisse ( epargne 16 %, reel -2,5 % ). Deux parties :
  - le socle ( socle/comptes.py ) : le grand livre peut suivre les paiements de classes de payeurs, par payeur et par motif
    ( suivre_payeurs, vider_payeurs ) ; sans abonne, rien ne change ;
  - le domaine 3 ( pays/d03_economie.py ) : le logement suit le statut d occupation, et chaque menage tient une enveloppe
    par division servie par un domaine ; ce que le domaine n encaisse pas s achete au commerce sous sa division.
Le meme texte pour le depot et pour l arbre des references. A placer en fin de chaine. Ancres courtes, propres aux
fonctions touchees. Chaque remplacement deja fait est saute : idempotent.
   python patch_enveloppes.py racine_de_l_arbre   ( racine/monde/socle/comptes.py et racine/monde/pays/d03_economie.py )"""
import os, sys

# ================================================================== le socle
SOCLE = []
# ancres courtes, presentes dans le socle du tronc ET dans celui de l arbre des references ( 5917fa8, sans enregistreur )
SOCLE.append(('''"net_cumule", "n_transferts"''', '''"net_cumule", "n_transferts", "par_payeur"'''))
SOCLE.append(('''        self.n_transferts = 0
''', '''        self.n_transferts = 0
        self.par_payeur = None     # ( HMT-145 ) ( classes suivies, { ( classe, id, motif ) : paye } ) ; None : rien de suivi
'''))
SOCLE.append(('''        self._ranger(motif, type(de).__name__, type(vers).__name__, paye)
''', '''        self._ranger(motif, type(de).__name__, type(vers).__name__, paye)
        try: s = self.par_payeur                       # ( HMT-145 ) les paiements des classes suivies, par payeur et motif
        except AttributeError: s = None                # un instantane d avant HMT-145
        if s is not None and type(de).__name__ in s[0]: k = (type(de).__name__, de.id, motif); s[1][k] = s[1].get(k, 0.0) + paye
'''))
SOCLE.append(('''    # ------------------------------------------------------------------ l argent, a l interieur
''', '''    # ------------------------------------------------------------------ ( HMT-145 ) les paiements par payeur
    def suivre_payeurs(self, *classes):
        """Compte desormais, par payeur et par motif, ce que paient les objets de ces classes ( noms de classe, par
        exemple Menage ) : ce que chaque payeur a reellement paye, paiements partiels compris. Un seul abonnement : le
        dernier remplace le precedent et son cumul."""
        self.par_payeur = (frozenset(classes), {})

    def vider_payeurs(self):
        """Le cumul { ( classe, id, motif ) : paye } depuis le dernier vidage, remis a vide ; {} sans abonnement."""
        s = getattr(self, "par_payeur", None)
        if s is None: return {}
        cumul = s[1]; self.par_payeur = (s[0], {})
        return cumul

    # ------------------------------------------------------------------ l argent, a l interieur
'''))

# ================================================================== le domaine 3
D03 = []
D03.append(('''   s use. Tables eparses : proprietaires ( entreprise -> habitant ),
''', '''   s use. ( HMT-145 ) Colonnes eco_env_<division> : l enveloppe du menage pour chaque division servie par un domaine
   ( recue chaque soir, diminuee de ce que le domaine encaisse ; l exces s achete au commerce sous sa division ) ; le
   logement suit le statut d occupation ( d13 ). Tables eparses : proprietaires ( entreprise -> habitant ),
'''))
# ancres courtes, presentes dans d03 du tronc ET de l arbre des references ( sans part_bien )
D03.append(('''"exceptionnelle", "recalibrage", "faillites"''', '''"exceptionnelle", "recalibrage", "faillites", "sans_division", "env_compte"'''))
D03.append(('''        self.recalibrage = 0.0''', '''        self.sans_division = {}    # ( HMT-145 ) motif d achat paye par un menage que rien ne classe -> drachmes ( reste vide )
        self.env_compte = np.zeros((3, K))   # ( HMT-145 ) par division : entrees, encaisse par les domaines, substitue ( cumul )
        self.recalibrage = 0.0'''))
D03.append(('''def achats_marchands(attente, pm, jours, achete, caisse, plancher):
''', '''# ( 29/09, HMT-145 : la demande chiffree ) LES ENVELOPPES. Aucun domaine ne lisait le budget des menages ( audit du
# 29/09 ) : loyer, factures, ecole, telecoms, sorties, sante, transport facturent des montants propres, et la part du
# budget reservee a leur division qu ils n encaissaient pas restait dans la caisse ( epargne mesuree 16 %, reel -2,5 % :
# Eurostat tec00131 ). Desormais chaque menage tient, par division servie par un domaine, une ENVELOPPE ( colonnes
# eco_env_<division> ) : chaque soir elle recoit la part du budget voulu que ni les biens du marche ni le commerce ne
# servent ( attente x ( 1 - part marchande ) ), et elle perd ce que les domaines ont reellement encaisse du menage ou de
# ses membres pour cette division ( le grand livre suit les paiements des Menage et des Habitant, par motif :
# MOTIFS_DIVISION ). Ce qui depasse J_ENVELOPPE jours d enveloppe s achete au commerce SOUS SA DIVISION ( motif
# substitution_<division> ), par lots d au moins LOT_ENVELOPPE jours : ce qu un domaine ne sert pas d une division existe
# dans le reel et c est le commerce qui le vend - logement : le fioul ( 36,6 % des menages grecs se chauffent au fioul,
# ELSTAT HBS 2024 ), l entretien et les reparations ( COICOP 04.3, 04.5 ) ; transport : ferries, bus, taxis ( 07.3 ) ;
# loisirs : sport, jeux, animaux ( 09 ) ; communications : les telephones ( 08.2 ) ; sante : dentistes et praticiens
# prives ( 06.2 ) ; divers : soins personnels ( 12.1 ). Sauf l education ( ecoles privees, universite : rien au
# commerce ), dont le reste demeure demande en attente. L achat passe par achats_marchands et le plancher des services
# marchands ( HMT-126 ) : la nourriture passe toujours avant. L enveloppe peut etre negative ( un domaine a encaisse plus
# que sa part : un loyer au-dessus du budget, une voiture ) : c est une dette de la division, qui se reconstitue avant tout
# nouvel achat. CHOIX declares avant la mesure ( sans source ) : J_ENVELOPPE = 45 jours, un cycle de facturation mensuel
# du moteur ( d11, d12, d13, d22 : 30 jours ) plus une demi-marge, pour ne jamais acheter au commerce la part d un loyer ou
# d une facture qui n est pas encore tombee ; LOT_ENVELOPPE = 7 jours, des achats hebdomadaires.
# LE LOGEMENT SUIT LE STATUT D OCCUPATION ( d13 ). ELSTAT HBS 2024 : les menages locataires consacrent 17,1 % de leur
# consommation au loyer. Avec s la part des locataires parmi les menages loges ( proprietaires et locataires ), le loyer
# pese s x 17,1 des 14,4 points du logement ( tableau 1 ) : un proprietaire, qui ne paie pas de loyer, a une part du
# logement de ( 14,4 - s x 17,1 ) / 14,4 fois la moyenne, un locataire y ajoute son loyer, 17,1 / 14,4 de plus ; ponderes
# par s, la moyenne. En Grece, s = 26,5 % ( Eurostat ilc_lvho02 2023 : 73,5 % de proprietaires, la valeur de d13 ; a
# verifier ) : 0,685 et 1,873. ( 29/09, CHOIX declare avant la mesure, remarque de Classes ) s est celle du MONDE, lue
# chaque soir sur les menages habites de l ile : d13 en loge un tiers en location ( 33 % a Altis, sonde du 29/09 ), et des
# multiplicateurs cales sur 26,5 % donneraient au logement du monde 7 % de trop par construction ; le loyer de 17,1 %
# chez les locataires est garde. Les autres divisions se renormalisent. Sans d13, ou pour un menage ni proprietaire ni
# locataire ( sans logement, abri ), la moyenne.
J_ENVELOPPE = 45.0
LOT_ENVELOPPE = 7.0
DIVISIONS_ENVELOPPE = ("logement", "sante", "transport", "communications", "loisirs", "education", "restauration", "divers")
SANS_COMMERCE = ("education",)
IDX_ENVELOPPE = tuple(NOMS_CATEGORIES.index(x) for x in DIVISIONS_ENVELOPPE)
I_LOGEMENT = NOMS_CATEGORIES.index("logement")
MOTIFS_DIVISION = {
    "loyer": "logement", "facture_electricite": "logement", "facture_eau": "logement",
    "consultation_medicale": "sante", "participation_medicaments": "sante", "participation_hospitaliere": "sante",
    "remede": "sante",
    "carburant_station": "transport", "entretien_vehicule": "transport", "reparation_vehicule": "transport",
    "vente_vehicule": "transport", "lecons_conduite": "transport", "frais_permis": "transport",
    "reprise_vehicule": "transport", "rachat_vehicule_succession": "transport",
    "abonnement_telecom": "communications",
    "spectacle": "loisirs", "panigyri": "loisirs", "abonnement_presse": "loisirs", "cotisation_club": "loisirs",
    "frontistirio": "education",
    "sortie_cafe_taverne": "restauration",
    "prime_assurance": "divers", "service_religieux": "divers"}
# les achats que le domaine 3 fait lui-meme ( nourriture, biens du marche, services marchands, substitutions ), et les
# achats d un menage qui ne sont pas de la consommation ( formation de capital, depots ) : ni enveloppe, ni fuite
MOTIFS_DU_DOMAINE_3 = ("nourriture", "remedes", "carburant", "outils", "services_marchands") + tuple(
    f"substitution_{x}" for x in DIVISIONS_ENVELOPPE)
HORS_ENVELOPPE = ("vente_logement", "frais_transaction", "vente_terrain", "travaux", "second_oeuvre", "achat_abri",
                  "import_materiaux", "investissement", "cession_liquidation", "droits_mutation", "depot_garantie")
LOYER_LOCATAIRES = 0.171      # ELSTAT HBS 2024 ( communique du 25/09/2025 ) : part du loyer chez les menages locataires
PART_LOCATAIRES_GRECE = 0.265 # Eurostat ilc_lvho02, Grece 2023 ( a verifier ) ; la reference, le monde a la sienne
LOGEMENT_ELSTAT = 0.144       # ELSTAT HBS 2024, tableau 1 : logement, eau, electricite, gaz et autres combustibles
F_PROPRIETAIRE_MIN = 0.05     # garde : si le monde logeait presque tout le monde en location, un proprietaire garde 5 %
STATUT_PROPRIETAIRE, STATUT_LOCATAIRE = 1, 2      # les codes de im_statut ( d13 : SANS, PROPRIETAIRE, LOCATAIRE, ABRI )


def multiplicateurs_occupation(part_locataires):
    """( HMT-145, fonction pure ) ( proprietaire, locataire ) : les multiplicateurs de la part du logement pour une part
    s de locataires parmi les menages loges ; ponderes par s, 1 ( sauf sous la garde ). 0,685 et 1,873 a s = 26,5 %."""
    f_p = max(F_PROPRIETAIRE_MIN, 1.0 - float(part_locataires) * LOYER_LOCATAIRES / LOGEMENT_ELSTAT)
    return f_p, f_p + LOYER_LOCATAIRES / LOGEMENT_ELSTAT


def _parts_occupation(f):
    x = PARTS_HORS_ALIM.copy(); x[I_LOGEMENT] *= f
    return x / x.sum()


ENVELOPPES = True             # le bras temoin des mesures le met a False dans son processus : le partage du tronc


def partager_le_reste(M, parts):
    """( HMT-145, fonction pure ) Le budget voulu `M` ( n x K, repartir_budget ) dont le reste, hors alimentation, est
    repartage selon `parts` ( n x K, alimentation 0, lignes de somme 1 ) : la nourriture et le total ne changent pas."""
    M = np.asarray(M, dtype=float)
    reste = M.sum(axis=1) - M[:, I_ALIM]
    out = reste[:, None] * np.asarray(parts, dtype=float)
    out[:, I_ALIM] = M[:, I_ALIM]
    return out


def parts_d_occupation(statut, habite):
    """( HMT-145, fonction pure ) Les parts du reste de chaque menage selon son statut d occupation ( codes de d13 ), les
    multiplicateurs cales sur la part de locataires parmi les menages habites et loges. Rend ( parts n x K, s )."""
    st = np.asarray(statut); hb = np.asarray(habite, dtype=bool)
    prop = int((hb & (st == STATUT_PROPRIETAIRE)).sum()); loc = int((hb & (st == STATUT_LOCATAIRE)).sum())
    s = loc / (prop + loc) if prop + loc else PART_LOCATAIRES_GRECE
    f_p, f_l = multiplicateurs_occupation(s)
    st = st[:, None]
    return np.where(st == STATUT_PROPRIETAIRE, _parts_occupation(f_p)[None, :],
                    np.where(st == STATUT_LOCATAIRE, _parts_occupation(f_l)[None, :], PARTS_HORS_ALIM[None, :])), s


def enveloppe_du_soir(E, entree, paye, achete):
    """( HMT-145, fonction pure ) L enveloppe d une division pour des menages : E + entree - paye ; l exces au-dela de
    J_ENVELOPPE jours d entree, des qu il atteint LOT_ENVELOPPE jours, pour qui fait ses courses. Rend ( E, exces )."""
    E = np.asarray(E, dtype=float) + np.asarray(entree, dtype=float) - np.asarray(paye, dtype=float)
    entree = np.asarray(entree, dtype=float)
    x = E - J_ENVELOPPE * entree
    return E, np.where(np.asarray(achete) & (entree > 0.0) & (x >= LOT_ENVELOPPE * entree), x, 0.0)


def _assurer_enveloppes(p):
    """( HMT-145 ) L abonnement du grand livre aux paiements des menages et des habitants, les motifs des substitutions
    et leurs comptes ; poses aussi sur un monde installe avant eux ( instantane relu )."""
    L = p.socle.livre
    if getattr(L, "par_payeur", None) is None: L.suivre_payeurs("Menage", "Habitant")
    for x in DIVISIONS_ENVELOPPE:
        if f"substitution_{x}" not in L.motifs: L.declarer_motif(f"substitution_{x}", "achat", "economie")
    J = p.socle.journal
    for c in ("substitution", "paye_sans_division"):
        if c not in getattr(J, "types", {}): J.declarer(c, "economie", "compte")


def _colonnes_enveloppes(p, n):
    cm = p.colonnes["menage"]
    for x in DIVISIONS_ENVELOPPE:
        if f"eco_env_{x}" not in cm: cm.ajouter(f"eco_env_{x}", np.float64, 0.0)
    cm.assurer(n)
    return {x: cm[f"eco_env_{x}"] for x in DIVISIONS_ENVELOPPE}


def _payes_par_division(p, d, n):
    """( HMT-145 ) Ce que les domaines ont encaisse depuis hier soir, par menage et par division ( n x K ) : les paiements
    d un habitant comptent pour son menage. Un motif d achat paye par un menage ou un habitant que rien ne classe ( ni
    division, ni achat du domaine 3, ni formation de capital ) est une FUITE : il laisserait l enveloppe pleine et le
    menage paierait deux fois ; il est compte ( paye_sans_division, d.sans_division ) et la porte veut 0."""
    L = p.socle.livre; tb = p.w.table
    out = np.zeros((n, K)); fuite = 0.0
    for (classe, i, motif), s in L.vider_payeurs().items():
        dv = MOTIFS_DIVISION.get(motif)
        if dv is None:
            m = L.motifs.get(motif)
            if (m is not None and m.nature == "achat" and motif not in MOTIFS_DU_DOMAINE_3 and motif not in HORS_ENVELOPPE
                    and s > 0.0):
                sd = getattr(d, "sans_division", None)
                if sd is None: sd = d.sans_division = {}                 # un monde installe avant ( instantane relu )
                fuite += s; sd[motif] = sd.get(motif, 0.0) + s
            continue
        if classe == "Habitant": i = int(tb.menage[i]) if 0 <= i < tb.n else -1
        if 0 <= i < n: out[i, NOMS_CATEGORIES.index(dv)] += s
    if fuite > 0.0: p.compter("paye_sans_division", fuite)
    return out


def _enveloppes(p, d, n, attente, pm, achete, plancher, vues, Mg, mt, marches, mi_l, tva):
    """( HMT-145 ) 19 h, apres les services marchands : chaque enveloppe recoit la part du jour que le commerce ne sert
    pas ( attente x ( 1 - part marchande ) ), perd ce que les domaines ont encaisse, et son exces s achete au commerce
    sous sa division, dans la limite du plancher des services marchands. Le menage paie TTC ; le commerce reverse la TVA."""
    w = p.w; L = p.socle.livre
    _assurer_enveloppes(p)
    payes = _payes_par_division(p, d, n)
    cols = _colonnes_enveloppes(p, n)
    ec = getattr(d, "env_compte", None)
    if ec is None: ec = d.env_compte = np.zeros((3, K))                 # un monde installe avant ( instantane relu )
    exces = np.zeros((n, K))
    for k in IDX_ENVELOPPE:
        nom = NOMS_CATEGORIES[k]
        entree = attente[:, k] * (1.0 - pm[k])
        E, x = enveloppe_du_soir(cols[nom][:n], entree, payes[:, k], achete)
        cols[nom][:n] = E
        ec[0, k] += float(entree.sum()); ec[1, k] += float(payes[:, k].sum())
        if nom not in SANS_COMMERCE: exces[:, k] = x
    voulu, ttc = achats_marchands(exces, np.ones(K), 1.0, achete, w.table.menages.caisse[:n], plancher)
    f = np.zeros(n); np.divide(ttc, voulu, out=f, where=voulu > 0.0)
    tva_m = np.zeros(len(marches)); total = 0.0
    for i in np.nonzero(ttc > 0.01)[0].tolist():
        mg = vues.get(i)
        if mg is None: mg = vues[i] = Mg(i, mt)
        km = mi_l[i]
        for k in IDX_ENVELOPPE:
            x = float(exces[i, k] * f[i])
            if x <= 0.01: continue
            nom = NOMS_CATEGORIES[k]
            paye = L.transferer(mg, marches[km], x, f"substitution_{nom}")
            cols[nom][i] -= paye; total += paye; ec[2, k] += paye
            tva_m[km] += paye * tva / (1.0 + tva)
    for k in np.nonzero(tva_m > 0.0)[0].tolist(): w.tva_percue += L.transferer(marches[k], w.gouv, float(tva_m[k]), "tva")
    p.compter("substitution", total)


def achats_marchands(attente, pm, jours, achete, caisse, plancher):
'''))
D03.append(('''    M[~ok] = 0.0
''', '''    if ENVELOPPES and "im_statut" in p.colonnes["menage"]:      # ( HMT-145 ) le logement suit le statut d occupation
        M = partager_le_reste(M, parts_d_occupation(p.col("menage", "im_statut")[:n], ok)[0])
    M[~ok] = 0.0
'''))
D03.append(('''    p.compter("services_marchands", float(ttc_s.sum()))
''', '''    p.compter("services_marchands", float(ttc_s.sum()))
    # --- ( HMT-145 ) les enveloppes : ce que les domaines n ont pas encaisse de leur division s achete au commerce
    if ENVELOPPES: _enveloppes(p, d, n, attente, pm, achete, plancher, vues, Mg, mt, marches, mi_l, tva)
'''))


def appliquer(chemin, remplacements, nom):
    s = open(chemin, encoding="utf-8").read()
    for avant, apres in remplacements:
        if apres in s: continue                      # deja fait
        if s.count(avant) != 1: raise SystemExit(f"{chemin} : ancre introuvable ou multiple : {avant[:70]!r}")
        s = s.replace(avant, apres, 1)
    open(chemin, "w", encoding="utf-8").write(s)
    print(f"{nom} : {chemin}")


if __name__ == "__main__":
    racine = sys.argv[1]
    appliquer(os.path.join(racine, "monde", "socle", "comptes.py"), SOCLE, "paiements par payeur ( socle )")
    appliquer(os.path.join(racine, "monde", "pays", "d03_economie.py"), D03, "enveloppes ( d03 )")
