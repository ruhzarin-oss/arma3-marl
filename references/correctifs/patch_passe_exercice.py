"""Correctif ( 29/09, suite de HMT-143, 6e cas du transitoire d installation ) : le controle d une entreprise ne
reconstitue le passe d avant le monde qu a partir d un exercice entier observe ( 365 jours ) ; avant, il ne redresse que
l impot elude qu il a vu. Applique au domaine 6 d un arbre ( apres patch_controle_entreprises ). Idempotent."""
import os, sys
f = os.path.join(sys.argv[1], "monde", "pays", "d06_etat.py")
s = open(f, encoding="utf-8").read()
if "EXERCICE_OBSERVE_J" in s:
    print("deja corrige :", f); sys.exit(0)
def remplacer(s, a, b):
    if s.count(a) != 1: raise SystemExit(f"{f} : ancre introuvable ou multiple ( {s.count(a)} ) : {a[:70]!r}")
    return s.replace(a, b)
s = remplacer(s, "OBSERVATION_MIN_J = 90\n",
    "OBSERVATION_MIN_J = 90\n"
    "# ( 29/09 ) Une entreprise : l administration redresse exercice par exercice, sur pieces ( exercice fiscal grec = annee\n"
    "# civile ; prescription de 5 ans, code de procedure fiscale ). Tant qu aucun exercice entier n est observe dans le monde,\n"
    "# le controle ne redresse que l impot elude qu il a vu ; le passe d avant le monde ne se reconstitue qu au rythme d un\n"
    "# exercice entier. Avant : le rythme du premier mois beneficiaire, extrapole sur 5 ans ( x 61, puis x 21 avec le minimum\n"
    "# d un trimestre ) : la raffinerie d Altis redressee de 169 283 + 84 642 de penalite au 2e mois ( bras HMT-143 ).\n"
    "EXERCICE_OBSERVE_J = 365\n")
a_tri = ("        mois = max(OBSERVATION_MIN_J / EC.MOIS_J, (p.jour - f.jour0) / EC.MOIS_J)\n"
         "        redr = dos.elude * (1.0 + 12.0 * avant / mois)\n")
a_un = ("        mois = max(1.0, (p.jour - f.jour0) / EC.MOIS_J)\n"
        "        redr = dos.elude * (1.0 + 12.0 * avant / mois)\n")
b = ("        observe = p.jour - f.jour0\n"
     "        mois = max(1.0, observe / EC.MOIS_J)\n"
     "        passe = 12.0 * avant / mois if observe >= EXERCICE_OBSERVE_J else 0.0     # ( 29/09 ) un exercice entier d abord\n"
     "        redr = dos.elude * (1.0 + passe)\n")
if s.count(a_tri) == 1: s = s.replace(a_tri, b)
else: s = remplacer(s, a_un, b)
open(f, "w", encoding="utf-8").write(s); print("corrige :", f)
