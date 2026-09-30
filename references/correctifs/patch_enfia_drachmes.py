"""29/09 ( chef de projet ; regle 8 ) : l ENFIA en drachmes. Le tableau de la loi 4223/2013 ( art. 4 ) donne la valeur de
zone et le tarif en EUROS par m2 ; la valeur de zone du domaine 13 est en drachmes ( ses prix en euros divises par
EUROS_PAR_DRACHME ) : le tableau etait applique tel quel, « drachmes = euros ». Paliers et tarifs convertis. A appliquer
apres patch_kea.py ( l import d EUROS_PAR_DRACHME ). Le meme texte pour le depot et l arbre des references. Idempotent.
   python patch_enfia_drachmes.py racine_de_l_arbre"""
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


remplacer("monde/pays/d06_etat.py", [
    ('''# ENFIA ( loi 4223/2013, art. 4 ) : impot principal = surface x tarif de base de la zone ( drachmes par m2, selon la
# valeur de zone en drachmes par m2 ) x coefficients ( age, etage, facades : 1 par defaut ). Tableau de 2014, a verifier ;
# l impot complementaire et les baisses de 2019-2022 ne sont pas modelises.
ENFIA_ZONES = ((550.0, 2.0), (750.0, 2.8), (1050.0, 2.9), (1500.0, 3.7), (2000.0, 4.5), (2500.0, 6.0), (3000.0, 6.8),
               (3500.0, 7.5), (4000.0, 9.0), (4500.0, 9.5), (5000.0, 10.2), (math.inf, 11.1))
''', '''# ENFIA ( loi 4223/2013, art. 4 ) : impot principal = surface x tarif de base de la zone ( selon la valeur de zone par m2 )
# x coefficients ( age, etage, facades : 1 par defaut ). Tableau de 2014, a verifier ; l impot complementaire et les
# baisses de 2019-2022 ne sont pas modelises. ( 29/09, regle 8 ) La loi est en EUROS par m2 ( valeur de zone et tarif ) ;
# la valeur de zone du domaine 13 est en drachmes : paliers et tarifs convertis ( appliques tels quels jusqu au 29/09 ).
ENFIA_ZONES_EUROS = ((550.0, 2.0), (750.0, 2.8), (1050.0, 2.9), (1500.0, 3.7), (2000.0, 4.5), (2500.0, 6.0), (3000.0, 6.8),
                     (3500.0, 7.5), (4000.0, 9.0), (4500.0, 9.5), (5000.0, 10.2), (math.inf, 11.1))
ENFIA_ZONES = tuple((b / EUROS_PAR_DRACHME, t / EUROS_PAR_DRACHME) for b, t in ENFIA_ZONES_EUROS)
'''),
])
