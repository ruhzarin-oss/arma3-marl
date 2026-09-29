"""Bras d essai HMT-143 ( 29/09 ) : la raffinerie a l effectif reel. Applique a monde/population.py et au domaine 11
d un arbre. Idempotent. Usage : python patch_effectif_raffinerie.py <arbre>"""
import os, sys

arbre = sys.argv[1]


def remplacer(s, avant, apres, f):
    if s.count(avant) != 1: raise SystemExit(f"{f} : ancre introuvable ou multiple ( {s.count(avant)} ) : {avant[:70]!r}")
    return s.replace(avant, apres)


f = os.path.join(arbre, "monde", "population.py")
s = open(f, encoding="utf-8").read()
if "DEBIT_REEL_RAFFINEUR_H" not in s:
    a = 'POSTES_PAR_SITE = {"mineur": {"mine": 10, "carriere": 10}, "petrolier": {"puits": 15}, "ouvrier": C.OUVRIERS_PAR_SITE}\n'
    s = remplacer(s, a,
        "# ( HMT-143, 29/09 ) La raffinerie a l effectif REEL. Le debit de celle d Altis est deja grec par habitant ( 8 080 unites\n"
        "# de brut par jour, ~508 barils, pour 10 000 habitants : 51 barils par jour pour 1 000 habitants, comme la Grece, ~530 000\n"
        "# pour 10,4 millions ) ; son effectif ne l etait pas : 202 ouvriers, 2 % de la population, contre 0,035 % en Grece. La\n"
        "# societe de raffinage d HELLENiQ ENERGY a produit 15,4 millions de tonnes en 2024 avec 2 233 employes ( rapport annuel\n"
        "# 2024 de HELLENIC PETROLEUM R.S.S.O.P.P. ), soit ~6 900 tonnes par employe et par an : ~401 unites de brut du moteur\n"
        "# ( 8,6 kg ) par heure travaillee ( 2 000 heures par an ). L ouvrier du moteur en traitait 5 ( config.RECETTES ) : les\n"
        "# postes de la raffinerie sont ceux d E1 divises dans ce rapport, pour le meme debit nominal ; d11 lit cette productivite.\n"
        "# Les autres ouvriers vont aux metiers ouverts de l ile ( _vers_le_reel ).\n"
        '#   https://m.helpe.gr/userfiles/09deccd3-a8a9-4ae2-b7da-a27a010c9bf8/2024-Annual-Report-EN%20_HELPE-RSSOPP.pdf\n'
        'HEURES_TRAVAILLEES_AN = 2000.0\n'
        'DEBIT_MOTEUR_RAFFINEUR_H = C.RECETTES["raffinerie"][1]["petrole"]\n'
        'DEBIT_REEL_RAFFINEUR_H = 15.4e9 / 2233.0 / HEURES_TRAVAILLEES_AN / 8.6     # kg par an / employes / heures / kg par unite\n'
        'POSTES_PAR_SITE = {"mineur": {"mine": 10, "carriere": 10}, "petrolier": {"puits": 15},\n'
        '                   "ouvrier": {**C.OUVRIERS_PAR_SITE, "raffinerie": C.OUVRIERS_PAR_SITE["raffinerie"]\n'
        '                               * DEBIT_MOTEUR_RAFFINEUR_H / DEBIT_REEL_RAFFINEUR_H}}\n', f)
    a = ("def _lieux_ponderes(carte, role):\n")
    s = remplacer(s, a, "def _lieux_ponderes(carte, role, n=None):\n", f)
    a = ("    g = 0\n"
         "    for l in lieux: g = math.gcd(g, int(poids[l.type]))\n"
         "    return [l for l in lieux for _ in range(int(poids[l.type]) // g)]\n")
    s = remplacer(s, a,
        "    if all(float(poids[l.type]).is_integer() for l in lieux):\n"
        "        g = 0\n"
        "        for l in lieux: g = math.gcd(g, int(poids[l.type]))\n"
        "        return [l for l in lieux for _ in range(int(poids[l.type]) // g)]\n"
        "    # ( HMT-143 ) des postes non entiers ( la raffinerie a l effectif reel ) : pour `n` personnes, les quotas exacts au\n"
        "    # plus fort reste, un poste au moins par site ; sans `n` ( un cycle pour une porte ), les poids rapportes au plus\n"
        "    # petit, arrondis. Des postes entiers gardent le partage d avant, au bit.\n"
        "    w = [float(poids[l.type]) for l in lieux]\n"
        "    if n is None:\n"
        "        m = min(w)\n"
        "        return [l for l, x in zip(lieux, w) for _ in range(max(1, int(round(x / m))))]\n"
        "    q = _quotas(int(n), w)\n"
        "    if n >= len(lieux):\n"
        "        for i in np.nonzero(q == 0)[0].tolist():\n"
        "            j = int(np.argmax(q)); q[j] -= 1; q[i] += 1\n"
        "    return [l for l, k in zip(lieux, q.tolist()) for _ in range(k)]\n", f)
    a = ("        else: cands = _lieux_ponderes(carte, h.role)   # les ouvriers vont ou il faut des bras : la raffinerie d abord\n")
    s = remplacer(s, a,
        "        else:                                           # les ouvriers vont ou il faut des bras ( un partage par metier )\n"
        "            cands = partages.get(h.role)\n"
        "            if cands is None: cands = partages[h.role] = _lieux_ponderes(carte, h.role, eff.get(h.role))\n", f)
    a = ("    # lieux de travail : repartition equilibree sur les lieux du bon type\n    compteur = {}\n")
    s = remplacer(s, a, "    # lieux de travail : repartition equilibree sur les lieux du bon type\n    compteur = {}; partages = {}\n", f)
    open(f, "w", encoding="utf-8").write(s); print("corrige :", f)
else: print("deja corrige :", f)

f = os.path.join(arbre, "monde", "pays", "d11_energie.py")
s = open(f, encoding="utf-8").read()
if "PO.DEBIT_REEL_RAFFINEUR_H" not in s:
    a = 'DEBIT_OUVRIER_H = C.RECETTES["raffinerie"][1]["petrole"]   # unites de brut par ouvrier et par heure : la productivite du\n'
    s = remplacer(s, a,
        '# ( HMT-143, 29/09 ) la productivite REELLE d un ouvrier de raffinerie ( HELLENiQ 2024 ), lue dans population.py ou elle\n'
        '# dimensionne les postes : le debit nominal de la raffinerie ne change pas, ses postes si. Avant : celle du moteur,\n'
        'DEBIT_OUVRIER_H = PO.DEBIT_REEL_RAFFINEUR_H   # unites de brut par ouvrier et par heure ; avant : la productivite du\n', f)
    a = ("        n = _vivants_au_travail(w, E.raffinerie.lieu, E.raffinerie.role)\n"
         "        E.nominal_brut_j = n * DEBIT_OUVRIER_H * 8.0\n")
    s = remplacer(s, a,
        "        n = _vivants_au_travail(w, E.raffinerie.lieu, E.raffinerie.role)\n"
        "        # ( HMT-143 ) la raffinerie est dimensionnee pour raffiner le brut de son puits : ses postes, a la productivite\n"
        "        # reelle, sont ouverts au marche du travail ( domaine 4 ), qui pourvoit ceux que le chomage d ouverture a vides\n"
        "        if E.puits is not None and E.puits.lieu.ile == E.raffinerie.lieu.ile and E.nominal_puits_j > 0:\n"
        "            postes = max(1, math.ceil(E.nominal_puits_j / (DEBIT_OUVRIER_H * 8.0) - 1e-9))\n"
        "            if p.a(\"travail\"):\n"
        "                importlib.import_module(\".d04_travail\", __package__).ouvrir_postes(p, E.raffinerie.lieu.id, E.raffinerie.role, postes)\n"
        "            n = max(n, postes)\n"
        "        E.nominal_brut_j = n * DEBIT_OUVRIER_H * 8.0\n", f)
    open(f, "w", encoding="utf-8").write(s); print("corrige :", f)
else: print("deja corrige :", f)
