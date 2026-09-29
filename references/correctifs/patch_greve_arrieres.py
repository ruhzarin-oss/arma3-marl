"""HMT-143 ( 29/09 ) : une greve pour arrieres de salaire ne pouvait jamais finir par un paiement. Les grevistes n ont
pas de bulletin, et le domaine 4 ne faisait regler ses arrieres qu a un employeur qui avait des bulletins ce jour-la :
un etablissement tout entier en greve n en a aucun, ses arrieres restaient figes, caisse pleine, et la greve expirait
puis repartait ( raffinerie d Altis, graine 1 : jours 74, 84, 94, arriere fige a 49 548 drachmes ). Desormais, chaque
jour a la paie, TOUT employeur debiteur regle ses arrieres dans la limite de sa caisse, les salaires d abord ( Code de
procedure civile grec, art. 977A par. 2 et 975 par. 3 ), qu il ait des bulletins ou non. Le meme texte pour le depot
et pour l arbre des references ( la paie y est identique ). A placer en fin de chaine. Chaque remplacement deja fait
est saute : idempotent.   python patch_greve_arrieres.py racine_de_l_arbre   ( racine/monde/pays/d04_travail.py )"""
import os, sys

FICHE_AVANT = '''   socle ( salaire, cotisation, impot, cotisation syndicale ; pension en retard ), reglee d abord a la paie suivante :
   jamais un salaire qui n a pas existe. Caisse : variation = cotisations recues + financement de l Etat - prestations -
'''
FICHE_APRES = '''   socle ( salaire, cotisation, impot, cotisation syndicale ; pension en retard ), reglee d abord a la paie suivante,
   que l employeur ait des bulletins ce jour-la ou non ( HMT-143 ), les salaires avant les retenues ( Code de procedure
   civile, art. 977A et 975 ) : jamais un salaire qui n a pas existe. Caisse : variation = cotisations recues +
   financement de l Etat - prestations -
'''

PAIE_AVANT = '''    for k, (x, lignes) in parts.items():
        _payer_employeur(p, d, x, lignes, agg)
    # --- 3. les independants, comme le moteur : benefice des marchands, revenu des cooperatives agricoles
'''
PAIE_APRES = '''    for k, (x, lignes) in parts.items():
        _payer_employeur(p, d, x, lignes, agg)
    # --- 2 ter. ( 29/09, HMT-143 ) l employeur SANS bulletin ce jour-la regle aussi ses arrieres, dans la limite de sa
    # caisse : un etablissement tout entier en greve n a aucun bulletin, et sa greve pour arrieres ne pouvait pas finir
    _regler_arrieres_sans_bulletin(p, d, {id(x) for x, _ in parts.values()}, agg)
    # --- 3. les independants, comme le moteur : benefice des marchands, revenu des cooperatives agricoles
'''

REGLER_AVANT = '''def _regler_arrieres(p, d, x, agg):
    """L employeur regle d abord ses arrieres, les plus anciens en premier : les salaires, puis ce qu il doit a la
    caisse, a l Etat et aux syndicats ( sous le motif d origine : un salaire paye en retard reste un salaire )."""
    K = p.socle.creances; L = p.socle.livre
    for motifs in (MOTIFS_SALAIRE, MOTIFS_RETENUES):
        for cr in list(K.de(x)):
            if x.caisse <= TOL: return
            if cr.motif not in motifs: continue
            creancier = cr.creancier
            v = K.regler(cr, L)
            agg["arrieres_payes"] += v
            if creancier is d.caisse: _cote(p, d, cr.motif, v)
            elif type(creancier) is Syndicat: creancier.cotisations += v
'''
REGLER_APRES = '''def _regler_arrieres(p, d, x, agg):
    """L employeur regle d abord ses arrieres, les plus anciens en premier : les salaires, puis ce qu il doit a la
    caisse, a l Etat et aux syndicats ( sous le motif d origine : un salaire paye en retard reste un salaire ).
    ( 29/09, HMT-143 ) L ordre copie le droit grec de la distribution des biens d un debiteur a ses creanciers
    ( saisie : Code de procedure civile, art. 975 a 978 ; faillite : les memes, loi 4738/2020 art. 167 ) : les
    salaires impayes jusqu a six mois, dans la limite de 275 % du salaire minimum par mois et par salarie, passent avant
    toute autre creance ( art. 977A par. 2, le « super-privilege », loi 4512/2018 ) ; au-dela, les salaires des deux
    dernieres annees sont au rang des impots retenus et des cotisations sociales ( art. 975 par. 3 ), au marc le franc
    ( art. 977 par. 2 ). Simplifications ecrites : tout l arriere de salaire passe avant les retenues ( deux mois
    d arrieres valent licenciement, art. 58 de la loi 4635/2019 ; le plafond de 275 % ne mord pas sur les salaires du
    moteur ) ; les comptes de salaire sont soldes l un apres l autre, pas au marc le franc entre salaries ; hors saisie
    et faillite, la loi ne dicte pas l ordre des paiements d un employeur solvable : on y prend celui de la
    distribution."""
    K = p.socle.creances; L = p.socle.livre
    for motifs in (MOTIFS_SALAIRE, MOTIFS_RETENUES):
        for cr in list(K.de(x)):
            if x.caisse <= TOL: return
            if cr.motif not in motifs: continue
            creancier = cr.creancier
            v = K.regler(cr, L)
            agg["arrieres_payes"] += v
            if creancier is d.caisse: _cote(p, d, cr.motif, v)
            elif type(creancier) is Syndicat: creancier.cotisations += v


def _regler_arrieres_sans_bulletin(p, d, faits, agg):
    """( 29/09, HMT-143 ) A la paie, TOUT employeur qui doit des arrieres de salaire ou de retenues les regle dans la
    limite de sa caisse, meme sans bulletin ce jour-la ( `faits` : les id des employeurs deja passes par
    _payer_employeur, qui ont regle les leurs avant leurs bulletins ). Avant, seul un employeur qui avait des bulletins
    reglait : un etablissement tout entier en greve n en a aucun ( un greviste n est pas paye ), sa greve pour arrieres
    ne finissait jamais par le paiement - elle expirait et repartait ( raffinerie d Altis, graine 1 : greves aux jours
    74, 84 et 94, arriere fige a 49 548 drachmes, caisse jusqu a 72 000, rien de raffine ) ; un employeur sans travail
    a donner ce jour-la ( raffinerie sans brut, jour chome ) gardait de meme ses arrieres et sa caisse. Un arriere paye
    est le salaire d heures DEJA faites ; les heures de greve restent impayees ( aucun bulletin ). Les menages ne sont
    pas des employeurs : leurs dettes d impot sont au domaine 6. Ordre : celui du registre des creances
    ( deterministe )."""
    K = p.socle.creances; motifs = MOTIFS_SALAIRE + MOTIFS_RETENUES
    for x in [x for x in K.par_debiteur if id(x) not in faits and not isinstance(x, PO.Menage)]:
        if getattr(x, "caisse", 0.0) > TOL and any(c.motif in motifs for c in K.de(x)):
            _regler_arrieres(p, d, x, agg)
'''

BLOCS = ((FICHE_AVANT, FICHE_APRES), (PAIE_AVANT, PAIE_APRES), (REGLER_AVANT, REGLER_APRES))

chemin = os.path.join(sys.argv[1], "monde", "pays", "d04_travail.py")
s = open(chemin).read()
faits = deja = 0
for vieux, neuf in BLOCS:
    if neuf in s: deja += 1; continue
    if s.count(vieux) != 1: sys.exit(f"motif introuvable ( {s.count(vieux)} fois ) : {chemin} : {vieux[:100]!r}")
    s = s.replace(vieux, neuf); faits += 1
if faits: open(chemin, "w").write(s)
print("corrige :" if faits else "deja corrige :", chemin, faits, "remplacements", deja, "deja faits")
