"""29/09 ( HMT-140, chef de projet ) : le travail par rotation et le plafond des licenciements collectifs au domaine 4.
Sans eux, les postes sans travail des le premier jour ( convoyeurs, fonderies, carrieres : 603 dans l Altis par defaut )
entraient ensemble en disponibilite et etaient licencies ensemble 90 jours plus tard ( 212 le jour 97 ). A appliquer
apres patch_menages_a.py ( la disponibilite de HMT-126 ). Le meme texte pour le depot et l arbre des references.
Idempotent ( chaque insertion a sa premiere ligne propre ).
   python patch_rotation.py racine_de_l_arbre"""
import os, sys
R = sys.argv[1]


def _nouveau(a, b):
    return next((l for l in b.splitlines() if l.strip() and l not in a.splitlines()), None)


def remplacer(chemin, paires):
    f = os.path.join(R, chemin)
    if not os.path.exists(f): print("absent :", f); return
    s = open(f).read(); n = 0
    for a, b in paires:
        m = _nouveau(a, b)
        if b in s or (m is not None and m in s): continue
        if s.count(a) != 1: raise SystemExit(f"{chemin} : {s.count(a)} fois {a!r}")
        s = s.replace(a, b); n += 1
    open(f, "w").write(s); print("corrige :" if n else "deja :", f)


REGLE = '''JOURS_AVANT_DISPONIBILITE = 5
# ( 29/09, HMT-140 ) LE TRAVAIL PAR ROTATION ( εκ περιτροπής εργασία : art. 2 de la loi 3846/2010 ) - l employeur dont
# l activite est restreinte peut, au lieu de licencier, faire travailler ses salaries par rotation, moins de jours payes
# au prorata, jusqu a NEUF mois par annee civile, apres information des representants du personnel. Le modele : chaque
# jour, chez un employeur du prive dont une partie des salaries presents n a aucune heure, les heures creditees du jour
# se partagent entre tous ses salaries presents, au prorata de leur journee reguliere - la masse de l employeur ne
# change pas ( la somme des taux x heures ) ; en rotation, personne n est sans travail ( ni disponibilite ). La rotation
# est collective ( toute l entreprise dont l activite baisse, pas quelques salaries : KEPEA-GSEE, fiche « Εκ περιτροπής
# εργασία » ). Au-dela de ROTATION_MAX_AN_J jours de rotation dans l annee, le salarie en sort. CHOIX ( pas dans la loi,
# qui ne fixe aucun minimum ; ecrit avant la mesure, a trancher par Younes ) : pas de rotation sous ROTATION_PART_MIN de
# l activite ( moins d un jour sur cinq ) - l employeur presque sans travail paierait presque rien pendant neuf mois a
# des salaries qui, employes, n ont pas droit a l indemnite de chomage ; il met en disponibilite, puis licencie.
# LE PLAFOND DES LICENCIEMENTS COLLECTIFS ( art. 1 de la loi 1387/1983, modifie par l art. 74 de la loi 3863/2010 ) :
# dans un mois civil, au-dela de 6 licenciements de 20 a 150 salaries, de 5 % et au plus 30 au-dela, c est un
# licenciement collectif ( consultation des representants, information de l inspection ) ; sous 20 salaries, pas de
# plafond. La disponibilite epuisee licencie dans ce plafond ; au-dela, le salarie attend le mois suivant, toujours en
# disponibilite ( demi-salaire ), les plus anciens en disponibilite d abord ( simplification ecrite : la procedure du
# licenciement collectif n est pas modelisee ). Sans cela, 603 postes sans travail des le premier jour ( convoyeurs,
# fonderies, carrieres, Altis par defaut ) etaient licencies ensemble, 212 le jour 97.
ROTATION_MAX_AN_J = 9 * MOIS_J
ROTATION_PART_MIN = 0.2
PLAFOND_COLLECTIF = True


def plafond_collectif(effectif):
    """Les licenciements economiques d un mois civil au-dela desquels c est un licenciement collectif."""
    if effectif < 20: return 10 ** 9
    if effectif <= 150: return 6
    return min(30, int(0.05 * effectif))
'''

ROTATION = '''def _rotation(p, d, col, tb, n, statut, heures, pt):
    """18 h, avant la paie : le travail par rotation ( voir ROTATION_MAX_AN_J ). Rend les heures payees du jour."""
    if ROTATION_MAX_AN_J <= 0: return heures
    pres = (statut == SALARIE) & (tb.vivant[:n] == 1) & (tb.travail[:n] >= 0) & (pt >= PRESENCE_MIN_H)
    if not (pres & (heures <= 0.0)).any(): return heures
    g = p.w.gouv; gr = getattr(d, "grevistes", ()) or ()
    rot = col["tr_rotation_an"]; taux = col["tr_taux"]; prev = col["tr_heures_prevues"]
    paires, grp = {}, {}
    for i in np.nonzero(pres)[0].tolist():
        if i in gr: continue
        c = (int(tb.travail[i]), int(tb.role[i]))
        if c not in paires:
            x = _payeur_de(p, d, tb.par_n[c[0]].id, PO.ROLES[c[1]] if c[1] >= 0 else None)
            paires[c] = None if (x is None or x is g) else _cle_payeur(x)
        k = paires[c]
        if k is not None: grp.setdefault(k, []).append(i)
    heures = heures.copy()
    for k in sorted(grp):
        a = np.array(grp[k], np.int64)
        vide = heures[a] <= 0.0
        if not vide.any() or vide.all(): continue          # tous au travail, ou aucun travail a partager
        e = a[~vide | (rot[a] < ROTATION_MAX_AN_J)]        # qui a fait ses neuf mois reste hors de la rotation
        te = taux[e].astype(np.float64)
        W = float((te * prev[e]).sum()); H = float((te * heures[e]).sum())
        if W <= 0.0: continue
        u = H / W
        if u < ROTATION_PART_MIN or u >= 1.0: continue
        heures[e] = u * prev[e].astype(np.float64)
        rot[e] = np.minimum(32000, rot[e].astype(np.int64) + 1)
        p.compter("jours_en_rotation", float(len(e)))
    return heures


def _sans_travail(p, d, col, tb, n, statut, heures, pt):'''

remplacer("monde/pays/d04_travail.py", [
    ("JOURS_AVANT_DISPONIBILITE = 5\n", REGLE),
    ('''COLONNES_HMT126 = (("tr_sans_travail_j", np.int16, 0), ("tr_dispo_j", np.int32, -1), ("tr_dispo_an", np.int16, 0))
EVENEMENTS_HMT126 = ("mise_en_disponibilite", "licenciement_economique", "indemnite_licenciement",
                     "indemnite_licenciement_due")
''', '''COLONNES_HMT126 = (("tr_sans_travail_j", np.int16, 0), ("tr_dispo_j", np.int32, -1), ("tr_dispo_an", np.int16, 0),
                   ("tr_rotation_an", np.int16, 0))
EVENEMENTS_HMT126 = ("mise_en_disponibilite", "licenciement_economique", "indemnite_licenciement",
                     "indemnite_licenciement_due", "jours_en_rotation", "licenciement_differe")
'''),
    ('''    ch = p.colonnes["habitant"]
    if "tr_dispo_an" not in ch:
''', '''    ch = p.colonnes["habitant"]
    if "tr_dispo_an" not in ch or "tr_rotation_an" not in ch:           # ( 29/09 ) la rotation, sur un instantane d avant
'''),
    ('''def _sans_travail(p, d, col, tb, n, statut, heures, pt):''', ROTATION),
    ('''    # --- 2. les salaires, employeur par employeur ( ordre des identifiants : deterministe )
''', '''    # --- 1 bis. ( 29/09, HMT-140 ) le travail par rotation : les heures du jour partagees chez l employeur a court de travail
    heures = _rotation(p, d, col, tb, n, statut, heures, pt)
    # --- 2. les salaires, employeur par employeur ( ordre des identifiants : deterministe )
'''),
    ('''        col["tr_dispo_an"][:n] = 0; deb = col["tr_dispo_j"][:n]; deb[deb >= 0] = p.jour
''', '''        col["tr_dispo_an"][:n] = 0; deb = col["tr_dispo_j"][:n]; deb[deb >= 0] = p.jour
        col["tr_rotation_an"][:n] = 0                     # ( 29/09 ) et neuf mois de rotation
'''),
    ('''def _disponibilites_epuisees(p, d, col, H, n):
    """6 h 10 : la disponibilite qui a atteint ses 90 jours dans l annee finit en licenciement economique."""
    deb = col["tr_dispo_j"][:n]
    for i in np.nonzero((deb >= 0) & (col["tr_dispo_an"][:n].astype(np.int64) + (p.jour - deb.astype(np.int64))
                                      >= DISPONIBILITE_MAX_AN_J))[0].tolist():
        h = H[i]
        if not h.vivant or col["tr_statut"][i] != SALARIE or h.travail is None: col["tr_dispo_j"][i] = -1; continue
        licencier_economique(p, h, "disponibilite_epuisee")
''', '''def _disponibilites_epuisees(p, d, col, H, n):
    """6 h 10 : la disponibilite qui a atteint ses 90 jours dans l annee finit en licenciement economique - ( 29/09 ) dans
    le plafond des licenciements collectifs du mois civil ( plafond_collectif ), les plus anciens en disponibilite
    d abord ; au-dela, le salarie attend le mois suivant ( compte licenciement_differe ). L effectif de reference de chaque
    employeur est lu au premier passage du mois ( 6 h 10 du premier jour )."""
    deb = col["tr_dispo_j"][:n]
    mois = p.socle.calendrier.date(p.w.pas).strftime("%Y-%m")
    fait = getattr(d, "licencies_mois", None)
    if fait is None or fait.get("mois") != mois:        # l effectif de reference : celui du premier matin du mois
        fait = d.licencies_mois = {"mois": mois, "effectifs": _effectifs_par_employeur(p, d, col, n) if PLAFOND_COLLECTIF else {}}
    effectifs = fait["effectifs"]
    cand = np.nonzero((deb >= 0) & (col["tr_dispo_an"][:n].astype(np.int64) + (p.jour - deb.astype(np.int64))
                                    >= DISPONIBILITE_MAX_AN_J))[0]
    if not len(cand): return
    cand = cand[np.lexsort((cand, deb[cand]))]
    for i in cand.tolist():
        h = H[i]
        if not h.vivant or col["tr_statut"][i] != SALARIE or h.travail is None: col["tr_dispo_j"][i] = -1; continue
        x = _payeur(p, d, h); k = _cle_payeur(x) if x is not None else None
        if PLAFOND_COLLECTIF and k is not None:
            if fait.get(k, 0) >= plafond_collectif(effectifs.get(k, 0)):
                p.compter("licenciement_differe"); continue
            fait[k] = fait.get(k, 0) + 1
        licencier_economique(p, h, "disponibilite_epuisee")


def _effectifs_par_employeur(p, d, col, n):
    """{ cle de l employeur : ses salaries } ( le plafond des licenciements collectifs )."""
    tb = p.w.table; g = p.w.gouv; paires, out = {}, {}
    for i in np.nonzero((col["tr_statut"][:n] == SALARIE) & (tb.vivant[:n] == 1) & (tb.travail[:n] >= 0))[0].tolist():
        c = (int(tb.travail[i]), int(tb.role[i]))
        if c not in paires:
            x = _payeur_de(p, d, tb.par_n[c[0]].id, PO.ROLES[c[1]] if c[1] >= 0 else None)
            paires[c] = None if (x is None or x is g) else _cle_payeur(x)
        k = paires[c]
        if k is not None: out[k] = out.get(k, 0) + 1
    return out
'''),
    ('''                 "hors_paie", "placements", "marge_veille")''',
     '''                 "hors_paie", "placements", "marge_veille", "licencies_mois")'''),
])
