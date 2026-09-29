"""Correctif ( 29/09, suite de HMT-143 ) : le controle fiscal d une ENTREPRISE extrapole son impot elude sur au moins un
trimestre d observation ( OBSERVATION_MIN_J ), comme celui d un menage. Applique au domaine 6 d un arbre. Idempotent."""
import os, sys
f = os.path.join(sys.argv[1], "monde", "pays", "d06_etat.py")
s = open(f, encoding="utf-8").read()
if "OBSERVATION_MIN_J / EC.MOIS_J" in s:
    print("deja corrige :", f); sys.exit(0)
a = "        mois = max(1.0, (p.jour - f.jour0) / EC.MOIS_J)\n"
if s.count(a) != 1: raise SystemExit(f"{f} : ancre introuvable ou multiple ( {s.count(a)} )")
s = s.replace(a,
    "        # ( 29/09 ) au moins un trimestre de pieces, comme pour un menage : au 2e mois, un seul mois observe multipliait\n"
    "        # l elude par 61 sur 5 ans de passe ( la raffinerie d Altis redressee de 27 318 + 13 659 de penalite, HMT-143 )\n"
    "        mois = max(OBSERVATION_MIN_J / EC.MOIS_J, (p.jour - f.jour0) / EC.MOIS_J)\n")
open(f, "w", encoding="utf-8").write(s); print("corrige :", f)
