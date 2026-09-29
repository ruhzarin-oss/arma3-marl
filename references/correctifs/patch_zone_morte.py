"""Correctif ( 29/09, HMT-140, la ration ) : zone morte des prix dans la bande de couverture ( LENTEUR_DANS_LA_BANDE a 0 ).
Applique au domaine 3 d un arbre. Ancre courte : le debut de la ligne de la constante. Idempotent."""
import os, re, sys
f = os.path.join(sys.argv[1], "monde", "pays", "d03_economie.py")
s = open(f, encoding="utf-8").read()
if re.search(r"^LENTEUR_DANS_LA_BANDE = 0\.0\b", s, re.M):
    print("deja corrige :", f); sys.exit(0)
lignes = re.findall(r"^LENTEUR_DANS_LA_BANDE = 0\.25\b.*\n", s, re.M)
if len(lignes) != 1: raise SystemExit(f"{f} : ancre introuvable ou multiple ( {len(lignes)} ) : LENTEUR_DANS_LA_BANDE = 0.25")
s = s.replace(lignes[0],
    "# 29/09 ( HMT-140, la ration ) : ZONE MORTE. Dans la bande, la couverture ne bouge plus le prix : il suit sa reference\n"
    "# ( le prix d installation indexe sur le cours mondial lisse ), les ruptures le poussent, le rappel le ramene ; hors de la\n"
    "# bande, rien ne change. A 0,25, le prix glissait sans fin : deux consignes pour un seul stock ( d03 vise 2 jours a 19 h,\n"
    "# d09 livre pour 3,5 jours a 15 h 50 ) laissent la nourriture a 2,1 - 2,6 jours, et le prix HT descendait de 17 % en six\n"
    "# mois ( 0,83 au jour 180, Altis, graine 51 ; couverture -0,86 du log sur l annee, rappel +0,52 ). Un prix de detail est\n"
    "# collant et suit ses couts. Dette : d09 vise encore l ancien point de mesure ( l aube ).\n"
    "LENTEUR_DANS_LA_BANDE = 0.0\n")
open(f, "w", encoding="utf-8").write(s); print("corrige :", f)
