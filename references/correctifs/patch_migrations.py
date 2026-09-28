"""27/09 ( HMT-114 ) : les migrations du domaine 7 au taux reel. ( 1 ) Un couple part au taux d une personne : chaque
adulte d un couple tire a la moitie du taux ( son conjoint part avec lui ) ; ( 2 ) les taux par age sont ceux des
emigrants de 2019 ( Eurostat migr_emi2 ramene au total ELSTAT 95 020 ) ; ( 3 ) les arrivees se tirent par menage : le
taux d immigration ( des personnes ) est divise par la taille moyenne d un menage immigrant ; ( 4 ) la faim fait partir
1,9 % de personnes de plus par point de prevalence ( PAM 2017 ). Mesure du 27/09 : le pays grec emigrait et immigrait
~2 fois trop. Idempotent.
   python patch_migrations.py chemin/d07_exterieur.py"""
import sys
p = sys.argv[1]; s = open(p).read()
if "TAILLE_MOYENNE_IMMIGRANTS" in s: print("deja :", p); sys.exit(0)


def sub(a, b):
    global s
    assert s.count(a) == 1, (p, a[:70], s.count(a))
    s = s.replace(a, b)


sub('''EMIGRATION_AN = ((18, 0.008), (20, 0.020), (40, 0.009), (65, 0.002))   # par personne et par an, selon l age ( a calibrer )
''', '''# 27/09 ( HMT-114 ) : les taux par age sont ceux des PERSONNES qui partent, adultes ; les mineurs suivent leurs parents.
# Emigrants de 2019 par age ( Eurostat migr_emi2, revise : 18-19 ans 3 478, 20-39 ans 60 326, 40-64 ans 27 883, 65 ans
# et plus 3 621, mineurs 16 295, total 111 603 ) ramenes au total publie par ELSTAT pour 2019 ( 95 020, communique du
# 30/12/2020 ), sur la population au 1er janvier 2020 par age ( meme communique, tableau 2 ; 18-19 ans : deux
# cinquiemes des 15-19 ans ). L ancien tableau ( 0,8 / 2,0 / 0,9 / 0,2 % ) etait a calibrer.
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/migr_emi2?geo=EL&time=2019&sex=T&agedef=COMPLET&unit=NR
#   https://www.statistics.gr/documents/20181/8db90789-197d-04e0-9313-8343518637a0
EMIGRATION_AN = ((18, 0.0135), (20, 0.0209), (40, 0.0063), (65, 0.0013))   # par personne et par an, selon l age
''')
sub('''TAILLE_IMMIGRANTS = ((1, 0.60), (2, 0.25), (3, 0.10), (4, 0.05))   # adultes seuls, couples, familles ( a calibrer )
''', '''TAILLE_IMMIGRANTS = ((1, 0.60), (2, 0.25), (3, 0.10), (4, 0.05))   # adultes seuls, couples, familles ( a calibrer )
# 27/09 ( HMT-114 ) : IMMIGRATION_AN compte des PERSONNES ; les arrivees se tirent par menage ( 1,6 personne en moyenne ) :
# le nombre de menages arrives est le taux divise par leur taille moyenne ( sans cela, x1,6 ).
TAILLE_MOYENNE_IMMIGRANTS = sum(t * q for t, q in TAILLE_IMMIGRANTS)
''')
sub('''    hz = np.where(age >= EMIGRATION_AN[0][0], hz, 0.0)
''', '''    hz = np.where(age >= EMIGRATION_AN[0][0], hz, 0.0)
    # 27/09 ( HMT-114 ) : un conjoint part avec celui qui tire ( _unite_de_depart ). Tires chacun au taux d une personne,
    # les deux adultes d un couple partaient chacun a ~2 fois ce taux : chacun tire a la moitie, le couple part au taux
    # d une personne. Avec les mineurs qui suivent, le pays emigrait ~2 fois trop ( 35 jours du pays grec, 27/09 ).
    cj = p.col("habitant", "conjoint")[ids].astype(np.int64)
    c0 = np.maximum(cj, 0)
    couple = (cj >= 0) & (w.table.vivant[c0] == 1) & (w.table.menage[c0] == w.table.menage[ids])
    hz = np.where(couple, 0.5 * hz, hz)
''')
sub('''FACTEUR_FAIM_EMIGRATION = 1.0    # un menage qui a eu faim tous les soirs de la semaine voit ses jeunes partir deux fois plus
''', '''# 27/09 ( HMT-114 ) : chaque point de prevalence de la sous-alimentation fait partir 1,9 % de personnes de plus ( PAM,
# « At the root of exodus », 2017 : sorties de refugies pour 1 000 habitants, entre pays ). Un menage qui a eu faim tous
# les soirs de la semaine ( faim = 1 ) pese 100 points : 1 + 1,9 x faim ; en moyenne sur le pays, 1 + 0,019 x la
# prevalence en points. A calibrer : une relation entre pays, surtout en guerre ; l ancien 1,0 n avait pas de source.
#   https://docs.wfp.org/api/documents/WFP-0000015358/download/
FACTEUR_FAIM_EMIGRATION = 1.9
''')
sub('''    lam = IMMIGRATION_AN * vivants / JOURS_AN * e.facteur_migration
''', '''    lam = IMMIGRATION_AN * vivants / JOURS_AN * e.facteur_migration / TAILLE_MOYENNE_IMMIGRANTS   # menages ( 27/09 )
''')
open(p, "w").write(s); print("corrige :", p)
