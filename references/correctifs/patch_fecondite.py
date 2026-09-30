"""30/09 ( session Classes, branche fecondite ) : la fecondite du domaine 1 copiee sur le reel grec. Les ASFR sont celles
d Eurostat ( demo_frate, Grece 2024, ages simples 15 a 49, age revolu de la mere A LA NAISSANCE ) ; elles se lisent a
l age qu aura la mere au terme ; elles comptent des enfants ( jumeaux compris ) ; le temps ou une femme ne peut pas
concevoir se compte avec la vraie duree de chaque issue ; la regle des couples se recale a CHAQUE age ( un seul k pour
tous les ages gardait le total mais deformait la courbe par age ). Un seul fichier : pays/d01_population.py. Ancres
courtes, chacune dans la fonction qu elle touche ; s applique a d01 du depot ( d7159b7 ) comme a celui de la reference
d origine ( 5917fa8 + patch_faim + patch_orphelins, dans tout ordre ). Idempotent.
    python patch_fecondite.py chemin/d01_population.py"""
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
if "FAUSSE_COUCHE_J = " in s:
    print("deja :", p); sys.exit(0)


def sub(s, a, b, n=1):
    assert s.count(a) == n, (p, a[:80], s.count(a))
    return s.replace(a, b)


# 1. la table : Eurostat demo_frate 2024, ages simples
s = sub(s, "# Fecondite par groupe d age ( naissances par femme et par an ) : ISF 1,35 ( Grece 2019 : 1,34 ), age moyen a\n"
           "# l accouchement 31 ans. Ordres de grandeur Eurostat, a calibrer.\n"
           "ASFR = {15: 0.008, 20: 0.030, 25: 0.068, 30: 0.094, 35: 0.058, 40: 0.0105, 45: 0.0005}\n",
        "# Fecondite par age ( naissances vivantes par femme et par an, age revolu de la mere A LA NAISSANCE ) : Eurostat\n"
        "# demo_frate ( Fertility rates by age, successeur de demo_fasfr ), Grece 2024, agedef COMPLET, ages simples, lu\n"
        "# le 30/09/2026 : https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_frate?geo=EL&time=2024\n"
        "# Somme 1,237 ( ISF publie, demo_find TOTFERRT 2024 : 1,24 ; les meres de moins de 15 ans et de 50 ans et plus,\n"
        "# 0,4 % de l ISF, ne sont pas copiees ) ; age moyen 32,1 ( demo_find AGEMOTH 2024 : 32,2 ). ( 30/09 : la table\n"
        "# d avant, ordre de grandeur 2019 par groupes de 5 ans, ISF 1,345, faisait trop naitre de 20 a 34 ans. )\n"
        "ASFR = {15: 0.00285, 16: 0.00488, 17: 0.00720, 18: 0.00938, 19: 0.01223, 20: 0.01429, 21: 0.01633, 22: 0.01978,\n"
        "        23: 0.02328, 24: 0.02916, 25: 0.03529, 26: 0.04438, 27: 0.05434, 28: 0.06492, 29: 0.07301, 30: 0.08530,\n"
        "        31: 0.08872, 32: 0.08925, 33: 0.08886, 34: 0.08364, 35: 0.07640, 36: 0.07113, 37: 0.05978, 38: 0.04833,\n"
        "        39: 0.03970, 40: 0.02933, 41: 0.02159, 42: 0.01432, 43: 0.00875, 44: 0.00647, 45: 0.00483, 46: 0.00333,\n"
        "        47: 0.00292, 48: 0.00220, 49: 0.00114}\n"
        "AGE_FIN_FECONDITE = 50      # le dernier groupe de la table va jusqu a 49 ans revolus\n")
s = sub(s, "POST_PARTUM_J = 90           # pas de conception dans les 3 mois qui suivent un accouchement\n",
        "POST_PARTUM_J = 90           # pas de conception dans les 3 mois qui suivent un accouchement\n"
        "FAUSSE_COUCHE_J = (42, 85)   # une grossesse perdue l est de 6 a 12 semaines apres la conception ( jours, [a ; b[ )\n")
s = sub(s, "~12 % des naissances hors couple ( a calibrer )", "~16 % des naissances hors couple ( a calibrer )")
# 2. la table se remplit d une borne a la suivante ( ages simples ou groupes de 5 ans )
s = sub(s, '    """asfr[age] : naissances par femme et par an, a chaque age entier."""\n',
        '    """asfr[age] : naissances vivantes par femme et par an, a chaque age entier ( age revolu de la mere a la\n'
        '    naissance ). Chaque valeur vaut de sa borne a la suivante, la derniere jusqu a AGE_FIN_FECONDITE : une table\n'
        '    d ages simples ou de groupes de 5 ans."""\n')
s = sub(s, "        for a, f in groupes.items(): self.asfr[a:a + 5] = f * facteur\n",
        "        bornes = sorted(groupes)\n"
        "        for a, b in zip(bornes, bornes[1:] + [AGE_FIN_FECONDITE]): self.asfr[a:b] = groupes[a] * facteur\n")
# 3. le hasard de conception : des enfants ( jumeaux ), la vraie duree de chaque issue
s = sub(s, "        f = self.asfr[age]\n"
           "        occupee = f / (1.0 - FAUSSE_COUCHE) * (GESTATION_J[0] + POST_PARTUM_J) / JOURS_AN\n"
           "        return f / (1.0 - FAUSSE_COUCHE) / np.maximum(0.05, 1.0 - occupee) / JOURS_AN\n",
        "        # ( 30/09 ) l ASFR compte des ENFANTS : un accouchement sur 1 / ( 1 + JUMEAUX ) en donne deux. Une conception\n"
        "        # occupe la femme 266 + 90 jours si elle va a terme, 42 a 84 jours si elle est perdue ( la perte etait\n"
        "        # comptee comme un accouchement : le hasard sortait ~1 % trop haut )\n"
        "        c = self.asfr[age] / (1.0 + JUMEAUX) / (1.0 - FAUSSE_COUCHE)\n"
        "        duree = (1.0 - FAUSSE_COUCHE) * (GESTATION_J[0] + POST_PARTUM_J) + FAUSSE_COUCHE * sum(FAUSSE_COUCHE_J) / 2.0\n"
        "        return c / np.maximum(0.05, 1.0 - c * duree / JOURS_AN) / JOURS_AN\n")
# 4. la regle des couples, age par age
s = sub(s, "`k` recale le total : les couples conçoivent plus que\n    les femmes seules, sans changer l ISF du pays.",
        "`k` ( un par femme ) recale le total de chaque age :\n    les couples conçoivent plus que les femmes seules, sans changer l ASFR de l age.")
s = sub(s, '    """Le k qui garde le total des conceptions egal a celui d une fecondite sans distinction de couple."""\n'
           "    base = table.hasard_conception(age)\n"
           "    pondere = (base * np.where(en_couple, 1.0, FECONDITE_SOLO)).sum()\n"
           "    return float(base.sum() / pondere) if pondere > 0 else 1.0\n",
        '    """Le k de chaque candidate : A CHAQUE AGE, le total des conceptions reste celui d une fecondite sans distinction\n'
        "    de couple. La part en couple est celle des candidates du jour a cet age : mesuree dans le monde, pas supposee.\n"
        "    ( 30/09 : un seul k pour tous les ages gardait le total mais deformait la courbe - de 20 a 24 ans, rarement en\n"
        '    couple, ~0,4 fois l ASFR ; de 35 a 39 ans ~1,3 fois. )"""\n'
        "    poids = np.where(en_couple, 1.0, FECONDITE_SOLO)\n"
        "    n = np.bincount(age, minlength=AGE_MAX + 1)\n"
        "    k = n / np.maximum(np.bincount(age, weights=poids, minlength=AGE_MAX + 1), FECONDITE_SOLO)\n"
        "    return k[age]\n")
# 5. les conceptions : l age qu aura la mere a la naissance
s = sub(s, "    f = (sexe == FEMME) & (age >= 15) & (age <= 49) & (E[ids] == 0) & (p.jour - A[ids] >= POST_PARTUM_J)\n",
        "    # ( 30/09 ) l ASFR se lit a l age revolu de la mere a la naissance ( Eurostat, agedef COMPLET ) : au terme moyen\n"
        '    nj = p.col("habitant", "naissance_j")\n'
        "    terme = np.clip((p.jour + int(GESTATION_J[0]) - nj[ids].astype(np.int64)) // 365, 0, AGE_MAX)\n"
        "    f = ((sexe == FEMME) & (terme >= 15) & (terme < AGE_FIN_FECONDITE) & (E[ids] == 0)\n"
        "         & (p.jour - A[ids] >= POST_PARTUM_J))\n")
s = sub(s, "    k = facteur_couples(d.fecondite, age[f], en_couple)\n", "    k = facteur_couples(d.fecondite, terme[f], en_couple)\n")
s = sub(s, "    for i in cand[tirer_conceptions(d.fecondite, age[f], en_couple, u, k)].tolist():\n",
        "    for i in cand[tirer_conceptions(d.fecondite, terme[f], en_couple, u, k)].tolist():\n")
s = sub(s, "p.poser(int(rng.integers(42, 85)) * C.PAS_PAR_JOUR", "p.poser(int(rng.integers(*FAUSSE_COUCHE_J)) * C.PAS_PAR_JOUR")
# 6. les grossesses du recensement : des accouchements ( la table compte des enfants )
s = sub(s, "d.fecondite.asfr[a] * GESTATION_J[0] / JOURS_AN:", "d.fecondite.asfr[a] / (1.0 + JUMEAUX) * GESTATION_J[0] / JOURS_AN:")
R = "d.fecondite.asfr[int(tb.age[i])] * GESTATION_J[0] / JOURS_AN:"
if R in s: s = sub(s, R, "d.fecondite.asfr[int(tb.age[i])] / (1.0 + JUMEAUX) * GESTATION_J[0] / JOURS_AN:")
open(p, "w", encoding="utf-8").write(s); print("corrige :", p)
