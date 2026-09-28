"""28/09 ( HMT-139 ) : le patron d une entreprise tire une remuneration de gerance, charge d exploitation versee avant tout
dividende ; une entreprise en cessation des paiements au sens de la loi grecque ( 4738/2020 ) est liquidee, et son patron
entre au registre des chomeurs. Idempotent.   python patch_patrons.py <racine>"""
import os, sys
racine = sys.argv[1]
f = os.path.join(racine, "monde", "pays", "d03_economie.py"); s = open(f).read()
if "GERANCE_EUROS_MOIS" in s: print("deja corrige :", f); sys.exit(0)


def sub(a, b):
    global s
    assert s.count(a) == 1, (f, a[:70], s.count(a)); s = s.replace(a, b)


sub('''JOURS_CESSATION = 3
''', '''JOURS_CESSATION = 3
# 28/09 ( HMT-139 ) : la cessation des paiements du droit grec ( loi 4738/2020, art. 77 : l impossibilite generale et
# permanente de payer ses dettes exigibles ). Presomption de la loi : des dettes echues impayees depuis au moins six mois,
# pour au moins 40 % de ce qui est du, et plus de 30 000 euros. Ici toutes les creances sur l entreprise comptent ( la loi
# nomme l Etat, la securite sociale et les banques ; les salaires impayes sont le premier signe reel ). Avant : seule une
# entreprise aux capitaux propres negatifs tombait, et le capital fixe au cout ( 3 a 337 millions a Altis ) gardait en vie
# dix entreprises a l arret depuis des mois, sans caisse ni salaire paye.
CESSATION_J = 180
PART_CESSATION = 0.4
SEUIL_CESSATION_EUROS = 30000.0
# La remuneration de gerance du patron ( 28/09, HMT-139 ) : la moyenne des gains bruts mensuels des cadres dirigeants en
# Grece ( Eurostat, enquete sur la structure des salaires 2018, earn_ses18_48, ISCO OC1 : 3 521 euros ; tous metiers :
# 1 446 ). Une charge d exploitation, versee chaque jour apres les salaires et avant tout dividende, si la caisse le
# permet et si aucun salaire n est en retard ( les salaires passent avant ) ; sinon le patron s en passe.
GERANCE_EUROS_MOIS = 3521.0
MOTIFS_ARRIERES_SALAIRE = ("salaire", "salaire public", "indemnite_licenciement")
''')

sub('''def _apres_paie(p):
    """18 h : ce que la paie a verse a chaque menage entre dans son revenu lisse ; une entreprise que la paie a videe a
    une tresorerie nulle."""
    w = p.w; d = p.domaine("economie")
''', '''def _gerance(p, d):
    """18 h, apres les salaires : chaque entreprise vivante paie a son patron sa remuneration de gerance du jour, si sa
    caisse le permet et si elle ne doit aucun salaire ; l impot sur le revenu comme pour les dividendes."""
    w = p.w; L = p.socle.livre; g = w.gouv; K_ = p.socle.creances
    dis = p.col("menage", "dissous")
    jour = GERANCE_EUROS_MOIS / _euros_par_drachme() / MOIS_J
    for c in d.unites:
        h = d.proprietaires.get(c.id)
        if h is None or c.liquidee or c.nature != "entreprise" or not h.vivant or h.menage is None or dis[h.menage.id]: continue
        e = c.unite
        if e.caisse <= 1.0: continue
        if any(cr.motif in MOTIFS_ARRIERES_SALAIRE for cr in K_.de(e)): continue
        paye = L.transferer(e, h.menage, min(jour, e.caisse), "remuneration_gerance")
        if paye > 0:
            L.transferer(h.menage, g, paye * g.impot_revenu, "impot")
            p.compter("remuneration_gerance", paye)


def _euros_par_drachme():
    try:
        from . import pays as _PAYS
        return float(_PAYS.EUROS_PAR_DRACHME)
    except (ImportError, AttributeError):
        return 1.15


def _apres_paie(p):
    """18 h : ce que la paie a verse a chaque menage entre dans son revenu lisse ; une entreprise que la paie a videe a
    une tresorerie nulle. ( 28/09 : la gerance du patron est payee d abord, et entre dans son revenu lisse. )"""
    w = p.w; d = p.domaine("economie")
    _gerance(p, d)
''')

sub('''def _faillites(p, d):
    for c in d.unites:
        if c.nature != "entreprise" or c.liquidee: continue
        c.cessation = c.cessation + 1 if (c.cp < 0.0 and c.tresorerie_nulle) else 0
        if c.cessation >= JOURS_CESSATION: liquider(p, c.unite)
''', '''def en_cessation_des_paiements(p, e):
    """La presomption de la loi 4738/2020 : des dettes echues impayees depuis au moins CESSATION_J jours ( un compte
    d arrieres ouvert depuis ce jour et jamais solde ), pour plus de SEUIL_CESSATION_EUROS et au moins PART_CESSATION de
    toutes ses dettes echues. Rend ( en cessation ?, vieilles, toutes ) en drachmes."""
    toutes = vieilles = 0.0
    for cr in p.socle.creances.de(e):
        toutes += cr.montant
        if p.jour - cr.nee >= CESSATION_J: vieilles += cr.montant
    seuil = SEUIL_CESSATION_EUROS / _euros_par_drachme()
    return (vieilles > seuil and vieilles >= PART_CESSATION * toutes), vieilles, toutes


def _faillites(p, d):
    for c in d.unites:
        if c.nature != "entreprise" or c.liquidee: continue
        c.cessation = c.cessation + 1 if (c.cp < 0.0 and c.tresorerie_nulle) else 0
        if c.cessation >= JOURS_CESSATION: liquider(p, c.unite); continue
        if en_cessation_des_paiements(p, c.unite)[0]: liquider(p, c.unite, "cessation_des_paiements")
''')

sub('''    e.activite = 0.0
    c.liquidee, c.liquidee_j = True, p.jour
''', '''    e.activite = 0.0
    c.liquidee, c.liquidee_j = True, p.jour
    # 28/09 ( HMT-139 ) : le patron perd son entreprise ; s il n en possede pas d autre, il entre au registre des chomeurs
    if h is not None:
        d.proprietaires.pop(e.id, None)
        if h.vivant and not any(x is h for x in d.proprietaires.values()): licencier(p, h, "faillite_de_son_entreprise")
''')

sub('''    L.declarer_motif("apport_capital", "financier", "economie")
''', '''    L.declarer_motif("apport_capital", "financier", "economie")
    L.declarer_motif("remuneration_gerance", "remuneration", "economie")
''')
sub('''              "dividende_verse"):
''', '''              "dividende_verse", "remuneration_gerance"):
''')
open(f, "w").write(s); print("corrige :", f)
