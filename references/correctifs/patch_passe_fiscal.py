"""Correctif ( 28/09, chef de projet ; diagnostic de justice test_delais_grecs ) : le passe d un menage controle
s estimait au rythme d impot elude MESURE DEPUIS L INSTALLATION, extrapole sur les annees d avant ( jusqu a 5 ). Un
controle du 4e jour multipliait 5 jours de demarrage par 365/5 et par 4,5 ans : 336 drachmes eludees devenaient un
redressement de 111 762 ( plus de 100 000 EUR : une fraude PENALE ), et le petit tribunal du pays s engorgeait. Le
rythme se mesure desormais sur au moins un TRIMESTRE ( la periode de la TVA grecque ; en deca, le controleur n a pas
plus d un trimestre de pieces pour extrapoler ; a calibrer ). Le meme texte pour le depot et pour l arbre des
references. Idempotent.   python patch_passe_fiscal.py racine_de_l_arbre"""
import os, sys
f = os.path.join(sys.argv[1], "monde", "pays", "d06_etat.py"); s = open(f).read()
ancien = "        ecoule = max(1, p.jour - f.jour0 + 1)\n        arr += float(elude_i.sum()) / ecoule * JOURS_AN * avant\n"
nouveau = ("        ecoule = max(OBSERVATION_MIN_J, p.jour - f.jour0 + 1)     # 28/09 : au moins un trimestre de pieces\n"
           "        arr += float(elude_i.sum()) / ecoule * JOURS_AN * avant\n")
const_a = "def controler(p, controleur, cible, cle=None, action=-1):\n"
const_n = ("# Le rythme d impot elude d avant l installation se mesure sur au moins un trimestre ( periode de la TVA grecque ;\n"
           "# 28/09, a calibrer ) : quelques jours de demarrage extrapoles sur 5 ans faisaient des fraudes penales.\n"
           "OBSERVATION_MIN_J = 90\n\n\n" + const_a)
if nouveau in s: print(f"deja : {f}"); sys.exit(0)
if s.count(ancien) != 1 or s.count(const_a) != 1: sys.exit(f"motif introuvable : {f}")
s = s.replace(ancien, nouveau).replace(const_a, const_n)
open(f, "w").write(s); print(f"corrige : {f}")
