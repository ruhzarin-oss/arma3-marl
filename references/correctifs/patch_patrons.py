"""28/09 ( HMT-126 b, suite ) : un patron a au moins une entreprise privee ( un site de production hors ferme ) ; les
patrons en trop sont marchands. A l echelle 20, Altis avait 160 patrons pour 12 entreprises, 148 sans rien et payes 0.
Sur Altis, rien ne change jusqu a l echelle 1,5 ( 12 patrons au plus ) ; au-dela, les patrons en trop naissent marchands,
avec la classe du marchand. La population du tronc ( monde/population.py, `effectifs` ) le fait deja ; ce correctif
l applique a la generation d un arbre d origine et a l ancien moteur temoin, qui n ont que la boucle des effectifs d E1
( et Altis, dont les metiers industriels ont deja leurs postes ). Idempotent.
   python patch_patrons.py <racine>      ( racine/monde/population.py pour un depot, racine/population.py pour le temoin )"""
import os, sys
racine = sys.argv[1]
base = os.path.join(racine, "monde") if os.path.exists(os.path.join(racine, "monde", "population.py")) else racine
f = os.path.join(base, "population.py")
s = open(f).read()
if "_effectif_patrons" in s or "PATRON_SANS_ENTREPRISE" in s: print("deja :", f); sys.exit(0)
a = '''    for role, (n, classe, _) in C.ROLES.items():
        for _ in range(max(1, int(round(n * echelle)))):
'''
assert s.count(a) == 1, (f, "boucle des effectifs introuvable")
s = s.replace(a, '''    for role, (n, classe, _) in C.ROLES.items():
        for _ in range(_effectif_patrons(carte, role, n, echelle)):
''')
a = '''def generer(carte, rng, echelle=1.0'''
assert s.count(a) == 1, (f, "generer introuvable")
s = s.replace(a, '''def _effectif_patrons(carte, role, n, echelle):
    """28/09 : l effectif d un metier a la naissance ; un patron a au moins une entreprise privee ( un site de production
    hors ferme ), les patrons en trop naissent marchands ( patch_patrons.py ; population.effectifs dans le tronc )."""
    k = max(1, int(round(n * echelle)))
    if role not in ("patron", "marchand"): return k
    p = max(1, int(round(C.ROLES["patron"][0] * echelle)))
    garde = min(p, len(carte.de_type(*[t for t in C.RECETTES if t != "ferme"])))
    return garde if role == "patron" else k + p - garde


''' + a)
open(f, "w").write(s); print("corrige :", f)
