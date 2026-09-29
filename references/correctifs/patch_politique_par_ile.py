"""Correctif ( 29/09, HMT-140 ) : la politique ne grandit pas avec l echelle. Chaque ile a un gouvernement, celui d E1
( 1 chef de gouvernement, 6 ministres ) ; ceux que l echelle aurait faits ministres naissent marchands, comme les patrons
sans entreprise ( patch_patrons ). Trois cibles, comme patch_patrons : le tronc ( population.effectifs ), l archive des
references et l ancien moteur temoin ( _effectif_patrons ). Idempotent.
   python patch_politique_par_ile.py <racine>   ( racine/monde/population.py pour un depot, racine/population.py pour le temoin )"""
import os, sys
racine = sys.argv[1]
base = os.path.join(racine, "monde") if os.path.exists(os.path.join(racine, "monde", "population.py")) else racine
f = os.path.join(base, "population.py")
s = open(f, encoding="utf-8").read()
if "POLITIQUES_PAR_ILE" in s:
    print("deja corrige :", f); sys.exit(0)
def remplacer(s, a, b):
    if s.count(a) != 1: raise SystemExit(f"{f} : ancre introuvable ou multiple ( {s.count(a)} ) : {a[:70]!r}")
    return s.replace(a, b)
CONST = ("# ( HMT-140, 29/09 ) La politique ne grandit pas avec l echelle : un gouvernement par ile, celui d E1 ( 1 chef, 6\n"
         "# ministres ). A 10 000 habitants, l echelle en faisait 20 et 120 ( 76 ministres a l echelle 12,75 ), soit ~57 euros par\n"
         "# habitant et par mois de remunerations politiques. Le reel des petits Etats insulaires : Nauru ( 12 000 habitants ), un\n"
         "# president et 5 ministres ; Tuvalu ( 11 000 ), un Premier ministre et 7 ministres ; Malte ( 520 000 ), 17 ministres ;\n"
         "# la Grece ( 10,4 millions ), ~20 ministres. Ceux que l echelle aurait faits ministres naissent marchands ( comme les\n"
         "# patrons sans entreprise ).\n"
         "POLITIQUES_PAR_ILE = (\"chef_gouvernement\", \"ministre\")\n"
         "POLITIQUE_SANS_GOUVERNEMENT = \"marchand\"\n\n\n")
if "def effectifs(carte, echelle, entiers=True):\n" in s:          # le tronc
    s = remplacer(s, "def effectifs(carte, echelle, entiers=True):\n", CONST + "def effectifs(carte, echelle, entiers=True):\n")
    s = remplacer(s,
        "    eff[PATRON_SANS_ENTREPRISE] += eff[\"patron\"] - garde\n    eff[\"patron\"] = garde\n",
        "    eff[PATRON_SANS_ENTREPRISE] += eff[\"patron\"] - garde\n    eff[\"patron\"] = garde\n"
        "    for r in POLITIQUES_PAR_ILE:                         # ( HMT-140 ) un gouvernement par ile, pas par unite d echelle\n"
        "        k = arrondi(C.ROLES[r][0])\n"
        "        eff[POLITIQUE_SANS_GOUVERNEMENT] += eff[r] - k\n"
        "        eff[r] = k\n")
else:                                                                # l archive et le temoin
    s = remplacer(s, "def _effectif_patrons(carte, role, n, echelle):\n", CONST + "def _effectif_patrons(carte, role, n, echelle):\n")
    s = remplacer(s,
        "    k = max(1, int(round(n * echelle)))\n    if role not in (\"patron\", \"marchand\"): return k\n",
        "    k = max(1, int(round(n * echelle)))\n"
        "    if role in POLITIQUES_PAR_ILE: return max(1, int(round(n)))              # ( HMT-140 ) un gouvernement par ile\n"
        "    if role == POLITIQUE_SANS_GOUVERNEMENT:\n"
        "        k += sum(max(1, int(round(C.ROLES[r][0] * echelle))) - max(1, int(round(C.ROLES[r][0]))) for r in POLITIQUES_PAR_ILE)\n"
        "    if role not in (\"patron\", \"marchand\"): return k\n")
open(f, "w", encoding="utf-8").write(s); print("corrige :", f)
