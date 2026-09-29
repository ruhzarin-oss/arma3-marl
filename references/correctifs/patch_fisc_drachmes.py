"""29/09 ( HMT-140 ( 2 ), chef de projet ) : le fisc du domaine 6.
1. Le bareme de l IR est la loi en EUROS ; les revenus du pays sont en drachmes ( regle 8 : EUROS_PAR_DRACHME euros la
   drachme ) - tranches, reduction, supplement par enfant et seuil de degressivite etaient ecrits « drachmes = euros » :
   convertis.
2. Les dividendes et l IS hors du domaine 3 ( le tourisme ) : verser_dividende ( retenue liberatoire de 5 % a la source,
   le net au menage, compte a son revenu declare ) et impot_societes_hors_eco ( 22 %, pertes reportees cinq ans ). Les
   dividendes du domaine 3 entrent aussi au revenu declare ( ils etaient verses hors de la fenetre de 18 h que lit le
   KEA ).
A appliquer apres patch_kea.py ( l import d EUROS_PAR_DRACHME, les comptes rmg ). Le meme texte pour le depot et
l arbre des references. Idempotent ( chaque insertion a sa premiere ligne propre ).
   python patch_fisc_drachmes.py racine_de_l_arbre"""
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


API = '''# ================================================================== dividendes et IS hors du domaine 3 ( 29/09, HMT-140 )
def verser_dividende(p, payeur, menage, montant, motif="dividende"):
    """Un dividende d une entreprise qui n est pas une unite du domaine 3 ( le tourisme, domaine 28 ) : la retenue
    liberatoire de 5 % ( art. 64 ) va a l Etat a la source, le net au menage, et compte a son revenu declare ( les six
    mois du KEA et de l A21 : rmg_mois ; le dividende est verse hors de la fenetre de 18 h qu ils lisent ). Le dividende
    n entre pas au bareme de l IR ( la retenue est liberatoire ). Rend le brut verse."""
    if montant <= EPS: return 0.0
    L = p.socle.livre; w = p.w; f = _etat(p).fisc
    ret = L.transferer(payeur, w.gouv, f.taux_dividende * montant, "retenue_dividende")
    f.compte["dividendes"] += ret; p.compter("retenue_dividende", ret)
    net = L.transferer(payeur, menage, montant - ret, motif)
    _declarer_revenu(p, menage, net)
    return ret + net


def _declarer_revenu(p, menage, montant):
    """Un revenu verse hors de la fenetre de 18 h, ajoute au mois en cours du revenu declare ( rmg_mois )."""
    cm = p.colonnes["menage"]
    if montant > EPS and "rmg_mois" in cm and 0 <= menage.id < len(cm["rmg_mois"]): cm["rmg_mois"][menage.id] += montant


def impot_societes_hors_eco(p, unite, resultat):
    """L IS d un mois clos pour une entreprise hors du domaine 3 ( le tourisme ) : 22 % du resultat, les pertes reportees
    cinq ans ( un dossier par entreprise, comme les unites du domaine 3 ; aucune part cachee ). Paye de sa caisse ; le
    reste devient une creance de l Etat. Rend l impot du."""
    e = _etat(p); f = e.fisc; L = p.socle.livre; K = p.socle.creances; w = p.w
    dos = f.unites.get(unite.id)
    if dos is None: dos = f.unites[unite.id] = DossierUnite(unite.id, 0.0, False)
    impot, base = impot_societes(resultat, dos.pertes, p.jour, f.taux_is)
    dos.resultat, dos.impot = base, impot
    if impot > EPS:
        paye = L.transferer(unite, w.gouv, impot, "impot_societes")
        f.compte["impot_societes"] += paye; p.compter("impot_societes", paye)
        if impot - paye > 1e-6: f.creances.append(K.constater(w.gouv, unite, impot - paye, "impot_societes", p.jour))
    return impot


def bareme_en_drachmes(p):
    """Une ile reprise d un instantane d avant le 29/09 garde le bareme de l IR ecrit en euros : le convertir ( une fois )."""
    f = _etat(p).fisc
    if tuple(f.tranches_ir) == tuple(TRANCHES_IR_EUROS): f.tranches_ir = tuple(TRANCHES_IR)


# ================================================================== l IS et les dividendes ( fin de mois )
def _mois_fiscal(p):'''

remplacer("monde/pays/d06_etat.py", [
    ('''TRANCHES_IR = (10000.0, 20000.0, 30000.0, 40000.0)
''', '''# ( 29/09, HMT-140 ; regle 8 : une drachme n est pas un euro ) le bareme de la loi est en EUROS, les revenus du pays en
# drachmes ( EUROS_PAR_DRACHME euros la drachme ) : tranches, reduction, supplement par enfant et seuil sont convertis -
# ecrits « drachmes = euros » jusqu au 29/09, chaque tranche etait 15 % trop large et la reduction 15 % trop forte.
TRANCHES_IR_EUROS = (10000.0, 20000.0, 30000.0, 40000.0)
TRANCHES_IR = tuple(x / EUROS_PAR_DRACHME for x in TRANCHES_IR_EUROS)
'''),
    ('''REDUCTION_IR = (777.0, 810.0, 900.0, 1120.0, 1340.0)
REDUCTION_PAR_ENFANT_SUP = 220.0
SEUIL_DEGRESSIVITE = 12000.0
''', '''REDUCTION_IR_EUROS = (777.0, 810.0, 900.0, 1120.0, 1340.0)
REDUCTION_IR = tuple(x / EUROS_PAR_DRACHME for x in REDUCTION_IR_EUROS)
REDUCTION_PAR_ENFANT_SUP = 220.0 / EUROS_PAR_DRACHME
SEUIL_DEGRESSIVITE = 12000.0 / EUROS_PAR_DRACHME
'''),
    ('''# ================================================================== l IS et les dividendes ( fin de mois )
def _mois_fiscal(p):''', API),
    ('''            x = L.transferer(h.menage, w.gouv, f.taux_dividende * div, "retenue_dividende")
            f.compte["dividendes"] += x; p.compter("retenue_dividende", x)
''', '''            x = L.transferer(h.menage, w.gouv, f.taux_dividende * div, "retenue_dividende")
            f.compte["dividendes"] += x; p.compter("retenue_dividende", x)
            _declarer_revenu(p, h.menage, div - x)              # ( 29/09 ) le dividende net au revenu declare
'''),
])
