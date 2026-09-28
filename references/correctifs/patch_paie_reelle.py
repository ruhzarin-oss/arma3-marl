"""28/09 ( HMT-126 a, chef de projet ; diagnostic de la guerre des iles et de la session Classes ) : deux regles de paie
du domaine 4, copiees sur le reel, pour tous les mondes.
1. Le salarie que son employeur ne paie plus : sans paie nette depuis IMPAYE_RUPTURE_J jours, le contrat est rompu
   contre son gre ; il devient chomeur ( indemnite DYPA apres la carence, s il y a droit ), garde sa creance sur
   l employeur et cherche un emploi. Les militaires ne partent pas. Colonne tr_paye_j ( dernier jour de paie nette ).
2. Le marchand vit de sa marge : chaque soir a la paie, les marchands d un marche se partagent la marge brute des
   ventes HT de la veille ( ventes x marge du marche, dans la limite de sa caisse ), et non plus la moitie de la caisse
   au-dela de 20 000 x echelle ( 95 % des marchands a 0 sur Altis et Stratis ).
Le meme texte pour le depot et pour l arbre des references. Idempotent.
   python patch_paie_reelle.py racine_de_l_arbre"""
import os, sys
f = os.path.join(sys.argv[1], "monde", "pays", "d04_travail.py"); s = open(f).read()
if "IMPAYE_RUPTURE_J" in s: print("deja :", f); sys.exit(0)


def remplacer(a, b):
    global s
    if s.count(a) != 1: raise SystemExit(f"{s.count(a)} fois {a!r}")
    s = s.replace(a, b)


A = [l for l in s.split("\n") if l.startswith("ARRIERES_GREVE_J = 3.0")][0]
remplacer(A + "\n", A + "\n" + '''# ( 28/09, HMT-126 a ) Le salarie que son employeur ne paie plus. En Grece le salaire est mensuel ; le salarie impaye peut
# retenir son travail ( Code civil, art. 325 ) et tenir le non-paiement pour une rupture du fait de l employeur
# ( modification unilaterale dommageable, loi 2112/1920, art. 7 ) ; la suspension d activite par l employeur est bornee
# a trois mois par an ( loi 3198/1955, art. 10 ). Sans paie nette depuis IMPAYE_RUPTURE_J jours - un mois de salaire
# manque, A CALIBRER - le contrat est rompu contre son gre. Une ile reprise d un instantane d avant ne connait pas
# l historique : un salarie non paye la veille y est compte impaye depuis IMPAYE_RUPTURE_J - REPRISE_IMPAYE_J jours.
IMPAYE_RUPTURE_J = 30
REPRISE_IMPAYE_J = 7
MILITAIRES_RESTENT = ("soldat",)          # un militaire ne quitte pas le service parce que la solde manque
''')
remplacer('''            ("tr_fin_etudes", np.int32, -1))''',
          '''            ("tr_fin_etudes", np.int32, -1), ("tr_paye_j", np.int32, -1))''')
remplacer('''                 "hors_paie", "placements")''',
          '''                 "hors_paie", "placements", "marge_veille")''')
remplacer('''              "indemnite_ouverte", "accident_travail", "heures_non_travaillees", "arrieres_salaire"):
        J.declarer(t, "travail", "compte")''',
          '''              "indemnite_ouverte", "accident_travail", "heures_non_travaillees", "arrieres_salaire",
              "rupture_salaire_impaye"):
        J.declarer(t, "travail", "compte")''')
# la paie : le dernier jour de paie nette
remplacer('''    _accidents(p, d, heures)
''', '''    _accidents(p, d, heures)
    pj = col["tr_paye_j"]; pj[:n] = np.where(col["tr_net_jour"][:n] > 0.0, p.jour, pj[:n])     # HMT-126 a
''')
# les marchands : la marge brute de la veille
remplacer('''    for m in w.marches.values():
        marchands = _ids_filtres(w, m.lieu, "marchand")
        exces = m.caisse - 20000.0 * getattr(m, "echelle", 1.0)     # le fonds de roulement du marche ( moteur, 26/09 )
        if exces > 0 and marchands:
            for i in marchands:
                mg = _menage_de(tb, i)
                brut = L.transferer(m, mg, 0.5 * exces / len(marchands), "benefice marchand")''',
          '''    veille = getattr(d, "marge_veille", None) or {}
    for m in w.marches.values():
        marchands = _ids_filtres(w, m.lieu, "marchand")
        # ( 28/09, HMT-126 a ) le commercant vit de sa marge : la marge brute des ventes HT de la veille ( domaine 3 ),
        # dans la limite de la caisse du marche ; sans domaine 3, l ancienne regle du moteur ( fonds de roulement )
        if m.lieu.id in veille: exces = min(veille[m.lieu.id], max(0.0, m.caisse)); part = 1.0
        else: exces = m.caisse - 20000.0 * getattr(m, "echelle", 1.0); part = 0.5
        if exces > 0 and marchands:
            for i in marchands:
                mg = _menage_de(tb, i)
                brut = L.transferer(m, mg, part * exces / len(marchands), "benefice marchand")''')
# le soir : la marge du jour, lue avant la cloture du domaine 3 ; la rupture des impayes, le matin
remplacer('''    p.routine(23 + 50 / 60, 99, "travail", _bilan_du_jour)''',
          '''    p.routine(23 + 50 / 60, 99, "travail", _bilan_du_jour)
    p.routine(23 + 50 / 60, 90, "travail", _marge_du_jour)              # HMT-126 a : avant la cloture du domaine 3 ( rang 97 )''')
remplacer('''    # fins de CDD
''', '''    # salaires impayes ( 28/09, HMT-126 a ) : sans paie nette depuis IMPAYE_RUPTURE_J jours, le contrat est rompu
    pj = col["tr_paye_j"][:n]
    rup = np.nonzero((st[:n] == SALARIE) & (p.jour - np.maximum(pj, col["tr_debut_j"][:n]) >= IMPAYE_RUPTURE_J)
                     & (w.table.vivant[:n] == 1) & ~np.isin(w.table.role[:n], _codes(MILITAIRES_RESTENT)))[0]
    for i in rup.tolist():
        h = H[i]
        if h.travail is None or i in d.grevistes: continue
        p.compter("rupture_salaire_impaye")
        rompre_contrat(p, h, "salaire_impaye", involontaire=True)
    # fins de CDD
''')
remplacer('''def _independants(p, d, agg):''', '''def _marge_du_jour(p):
    """23 h 50, avant la cloture du domaine 3 : la marge brute des ventes HT du jour de chaque marche ( ventes x marge ),
    que ses marchands se partageront demain a la paie ( HMT-126 a )."""
    if not p.a("economie"): return
    d = p.domaine("travail"); e = p.domaine("economie"); w = p.w
    d.marge_veille = {mid: math.fsum(em.ventes_jour.values()) * w.marches[mid].marge for mid, em in e.marches.items()}


def brancher_impayes(p):
    """Une ile reprise d un instantane d avant HMT-126 a : la colonne tr_paye_j ( l historique manque : un salarie non paye
    la veille est compte impaye depuis IMPAYE_RUPTURE_J - REPRISE_IMPAYE_J jours ), le compte des ruptures, la marge du
    soir. Idempotent."""
    col = p.colonnes["habitant"]; n = p.w.table.n
    if "tr_paye_j" not in col:
        col.ajouter("tr_paye_j", np.int32, -1); col.assurer(n)
        col["tr_paye_j"][:n] = np.where(col["tr_net_jour"][:n] > 0.0, p.jour - 1, p.jour - IMPAYE_RUPTURE_J + REPRISE_IMPAYE_J)
    J = p.socle.journal
    if "rupture_salaire_impaye" not in getattr(J, "types", {}): J.declarer("rupture_salaire_impaye", "travail", "compte")
    if not any(fn is _marge_du_jour for _, _, fn in p.routines.get(23 * 60 + 50, ())):
        p.routine(23 + 50 / 60, 90, "travail", _marge_du_jour)


def _independants(p, d, agg):''')
open(f, "w").write(s); print("corrige :", f)
