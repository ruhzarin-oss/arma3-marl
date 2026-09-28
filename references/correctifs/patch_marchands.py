"""28/09 ( HMT-126, chef de projet ; mesure de Classes : 95 % des marchands a 0 sur Altis et Stratis ) : le marchand vit
de sa marge. Chaque soir a la paie, les marchands d un marche se partagent la marge brute des ventes HT de la veille
( ventes x marge du marche, lue a 23 h 50 avant la cloture du domaine 3, dans la limite de la caisse du marche ), et non
plus la moitie de la caisse au-dela de 20 000 x echelle. Sans domaine 3, l ancienne regle du moteur. A appliquer apres
patch_menages_a.py. Le meme texte pour le depot et pour l arbre des references. Idempotent.
   python patch_marchands.py racine_de_l_arbre"""
import os, sys
f = os.path.join(sys.argv[1], "monde", "pays", "d04_travail.py"); s = open(f).read()
if "def _marge_du_jour" in s: print("deja :", f); sys.exit(0)


def remplacer(a, b):
    global s
    if s.count(a) != 1: raise SystemExit(f"{s.count(a)} fois {a!r}")
    s = s.replace(a, b)


remplacer('''                 "hors_paie", "placements")''', '''                 "hors_paie", "placements", "marge_veille")''')
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
        # ( 28/09, HMT-126 ) le commercant vit de sa marge : la marge brute des ventes HT de la veille ( domaine 3 ), dans
        # la limite de la caisse du marche ; sans domaine 3, l ancienne regle du moteur ( fonds de roulement )
        if m.lieu.id in veille: exces = min(veille[m.lieu.id], max(0.0, m.caisse)); part = 1.0
        else: exces = m.caisse - 20000.0 * getattr(m, "echelle", 1.0); part = 0.5
        if exces > 0 and marchands:
            for i in marchands:
                mg = _menage_de(tb, i)
                brut = L.transferer(m, mg, part * exces / len(marchands), "benefice marchand")''')
remplacer('''    p.routine(23 + 50 / 60, 99, "travail", _bilan_du_jour)''',
          '''    p.routine(23 + 50 / 60, 99, "travail", _bilan_du_jour)
    p.routine(23 + 50 / 60, 90, "travail", _marge_du_jour)              # HMT-126 : avant la cloture du domaine 3 ( rang 97 )''')
remplacer('''def _independants(p, d, agg):''', '''def _marge_du_jour(p):
    """23 h 50, avant la cloture du domaine 3 : la marge brute des ventes HT du jour de chaque marche ( ventes x marge ),
    que ses marchands se partageront demain a la paie ( HMT-126 )."""
    if not p.a("economie"): return
    d = p.domaine("travail"); e = p.domaine("economie"); w = p.w
    d.marge_veille = {mid: math.fsum(em.ventes_jour.values()) * w.marches[mid].marge for mid, em in e.marches.items()}


def brancher_marchands(p):
    """Une ile reprise d un instantane d avant : la marge du soir. Idempotent."""
    if not any(fn is _marge_du_jour for _, _, fn in p.routines.get(23 * 60 + 50, ())):
        p.routine(23 + 50 / 60, 90, "travail", _marge_du_jour)


def _independants(p, d, agg):''')
open(f, "w").write(s); print("corrige :", f)
