"""27/09 ( HMT-131 b ) : la priorite des devises au domaine 7. Sous RESERVE_PRIORITAIRE_MOIS mois d importations de
reserves, la banque centrale ne sert plus que l essentiel ( nourriture, medicaments, energie, armement ) ; le reste
n a que les reserves au-dessus de ce seuil. A appliquer APRES patch_devises.py. Idempotent.
   python patch_priorite_devises.py racine_de_l_arbre"""
import os, sys
f = os.path.join(sys.argv[1], "monde", "pays", "d07_exterieur.py"); s = open(f).read()
if "RESERVE_PRIORITAIRE_MOIS" in s: print("deja :", f); sys.exit(0)
if "def payer_en_devises" not in s: raise SystemExit("patch_devises.py d abord")


def remplacer(a, b):
    global s
    if s.count(a) != 1: raise SystemExit(f"{s.count(a)} fois {a!r}")
    s = s.replace(a, b)


A = [l for l in s.split("\n") if l.startswith("PRIORITE_RACHAT = ESSENTIELS + (\"carburant\",)")]
if len(A) != 1: raise SystemExit("PRIORITE_RACHAT introuvable")
remplacer(A[0] + "\n", A[0] + "\n" + '''# La priorite des devises ( 27/09, HMT-131 b ) : sous RESERVE_PRIORITAIRE_MOIS mois d importations de reserves, la banque
# centrale ne sert plus que l essentiel ; le reste n a que les reserves au-dessus de ce seuil. Copie du reel : en Grece,
# pendant le controle des capitaux de 2015, des comites n approuvaient que 20 millions d euros d importations par jour,
# en priorite les medicaments et la nourriture ( Financial Times, K. Hope, 04/08/2015, « Greek businesses left gasping as
# capital controls bite » ; CNBC, 24/07/2015 : les importations pharmaceutiques ). L energie ( combustible des centrales,
# gazole, petrole ) est comptee essentielle, A VERIFIER : absente de ces sources ; au Sri Lanka en 2022 la banque
# centrale reservait ses dollars au carburant et au gaz de cuisine ( New Straits Times, 20/05/2022 ). L armement aussi,
# A VERIFIER : un pays en guerre sert d abord ses importations critiques ( Ukraine 2022 ). Le seuil de 3 mois
# d importations : la regle usuelle d adequation des reserves ( FMI, a calibrer ), mesures sur les 30 derniers jours
# d importations ; pas avant PRIORITE_APRES_J jours de vie du domaine : la semaine d installation achete les stocks de
# depart ( 240 000 euros d un jour sur une Stratis de 10 000 habitants, contre 10 000 a 100 000 ensuite ) et la banque
# centrale n a pas encore d historique des importations.
RESERVE_PRIORITAIRE_MOIS = 3.0
PRIORITE_APRES_J = 37
BIENS_ESSENTIELS_DEVISES = ESSENTIELS + ("carburant", "petrole")
MOTIFS_ESSENTIELS_DEVISES = ("import_sante", "import_armement")
''')
remplacer('''def _dispo_euros(p, e):
    """Les reserves de ce moment moins le plancher, en LECTURE SEULE : les flux du grand livre depuis le dernier suivi,
    convertis au taux du jour comme les rangerait _suivre_reserves, sans les ranger."""
    L = p.socle.livre
    return e.reserves_euros + (L.ext["entree"] - L.ext["sortie"] - e.ext_reserves) * e.taux - PLANCHER_RESERVES''',
'''def _plancher_devises(p, e, essentiel):
    """Le plancher des reserves pour une demande : celui du controle pour l essentiel ; pour le reste, en plus,
    RESERVE_PRIORITAIRE_MOIS fois les importations des 30 derniers jours - des PRIORITE_APRES_J jours de vie du domaine."""
    if essentiel or p.jour - getattr(e, "jour_install", 0) < PRIORITE_APRES_J: return PLANCHER_RESERVES
    return PLANCHER_RESERVES + RESERVE_PRIORITAIRE_MOIS * math.fsum(list(e.imports_euros)[-30:])


def _dispo_euros(p, e, essentiel=True):
    """Les reserves de ce moment moins le plancher de la demande, en LECTURE SEULE : les flux du grand livre depuis le
    dernier suivi, convertis au taux du jour comme les rangerait _suivre_reserves, sans les ranger."""
    L = p.socle.livre
    return e.reserves_euros + (L.ext["entree"] - L.ext["sortie"] - e.ext_reserves) * e.taux - _plancher_devises(p, e, essentiel)''')
remplacer('''def part_en_devises(p, montant):
    """La part de `montant` ( monnaie de l ile ) que la banque centrale fournirait maintenant, en LECTURE SEULE."""
    if not p.a("exterieur") or montant <= EPS: return 1.0
    e = _ext(p); euros = montant * e.taux; d = _dispo_euros(p, e)''',
'''def part_en_devises(p, montant, essentiel=False):
    """La part de `montant` ( monnaie de l ile ) que la banque centrale fournirait maintenant, en LECTURE SEULE."""
    if not p.a("exterieur") or montant <= EPS: return 1.0
    e = _ext(p); euros = montant * e.taux; d = _dispo_euros(p, e, essentiel)''')
remplacer('''    if _dispo_euros(p, e) >= euros: return L.payer_l_exterieur(de, montant, motif)
    part = _controle_devises(p, e, euros)''',
'''    if _dispo_euros(p, e, essentiel) >= euros: return L.payer_l_exterieur(de, montant, motif)
    part = _controle_devises(p, e, euros, essentiel)''')
remplacer('''def _controle_devises(p, e, euros):
    """La banque centrale fournit-elle ces devises ? Rend la part fournie ( 0 a 1 )."""''',
'''def _controle_devises(p, e, euros, essentiel=True):
    """La banque centrale fournit-elle ces devises ? Rend la part fournie ( 0 a 1 ) ; hors de l essentiel, seulement
    ce qui depasse la reserve prioritaire ( HMT-131 b )."""''')
remplacer('''    dispo = e.reserves_euros - PLANCHER_RESERVES
    if dispo >= euros: return 1.0''',
'''    dispo = e.reserves_euros - _plancher_devises(p, e, essentiel)
    if dispo >= euros: return 1.0''')
remplacer('''    q *= _controle_devises(p, e, q * (fob + fret) * e.taux)''',
'''    q *= _controle_devises(p, e, q * (fob + fret) * e.taux, nom in BIENS_ESSENTIELS_DEVISES or motif in MOTIFS_ESSENTIELS_DEVISES)''')
remplacer('''    if _controle_devises(p, e, (valeur_fob + fret) * e.taux) < 1.0: return 0.0''',
'''    if _controle_devises(p, e, (valeur_fob + fret) * e.taux, motif in MOTIFS_ESSENTIELS_DEVISES) < 1.0: return 0.0''')
remplacer('''    if _controle_devises(p, e, prime * e.taux) < 1.0: return 0.0''',
'''    if _controle_devises(p, e, prime * e.taux, False) < 1.0: return 0.0''')
open(f, "w").write(s); print("corrige :", f)
