"""Applique la correction du 27/09 ( la faim copiee sur le reel ) a un arbre : config.py ( le corps s adapte, seuil de
travail ), monde.py ( le deficit s accumule apres adaptation ), d01_population.py ( la faim tue ). Idempotent.
   python patch_faim.py <racine>      ( racine/monde/... pour un depot, racine/... pour l ancien moteur temoin )"""
import os, sys
racine = sys.argv[1]
base = os.path.join(racine, "monde") if os.path.exists(os.path.join(racine, "monde", "config.py")) else racine


def lire(f): return open(os.path.join(base, f)).read()
def ecrire(f, s): open(os.path.join(base, f), "w").write(s); print("corrige :", os.path.join(base, f))
def sub(s, a, b, exige=True):
    n = s.count(a)
    if n == 0 and not exige: return s, False
    assert n == 1, (base, a[:70], n)
    return s.replace(a, b), True


# ------------------------------------------------------------------ 1. config.py
s = lire("config.py")
if "FAIM_ADAPTATION" in s: print("deja corrige :", os.path.join(base, "config.py"))
else:
    s, _ = sub(s, "ABSENCE_FAIM = 1.5                   # au-dela de cette faim accumulee, on ne va plus travailler\n",
'''# 27/09 ( copie du reel ) : `Habitant.faim` est le deficit du corps, en rations, APRES adaptation. Un corps prive abaisse
# sa depense d environ 40 % ( Keys 1950, experience du Minnesota : 24 semaines a demi-ration, metabolisme de base -40 %,
# 25 % du poids perdu, aucun mort ). Une nuit a 70 % de la ration n use donc pas le corps ; le jeune total l use de 0,6
# ration par jour. Un jour nourri repare 1 ration. On ne travaille plus au-dela de 12 ( ~20 jours de jeune total, ~120
# jours a demi-ration ) ; avant ( 1,5 ), deux soirs sans manger arretaient le pays. La mort par la faim est au domaine 1
# ( pays/d01_population.py, SEUILS_FAIM ).
FAIM_ADAPTATION = 0.4
ABSENCE_FAIM = 12.0
''')
    ecrire("config.py", s)

# ------------------------------------------------------------------ 2. monde.py
s = lire("monde.py")
if "C.FAIM_ADAPTATION" in s: print("deja corrige :", os.path.join(base, "monde.py"))
else:
    s, a = sub(s, "t.faim[membres] = np.where(affame[k], faim + manque[k] / np.maximum(v[k], 1), np.maximum(0.0, faim - 1))",
               "t.faim[membres] = np.where(affame[k], faim + np.maximum(0.0, manque[k] / np.maximum(v[k], 1) - C.FAIM_ADAPTATION), np.maximum(0.0, faim - 1))",
               exige=False)
    s, b = sub(s, "for p in vivants: p.faim = p.faim + manque / len(vivants) if manque > 1e-6 else max(0.0, p.faim - 1)",
               "for p in vivants: p.faim = p.faim + max(0.0, manque / len(vivants) - C.FAIM_ADAPTATION) if manque > 1e-6 else max(0.0, p.faim - 1)")
    assert a or b
    ecrire("monde.py", s)

# ------------------------------------------------------------------ 3. pays/d01_population.py
f = os.path.join("pays", "d01_population.py")
if os.path.exists(os.path.join(base, f)):
    s = lire(f)
    if "SEUILS_FAIM" in s: print("deja corrige :", os.path.join(base, f))
    else:
        a = 'CAUSES = ("inconnue", "naturelle", "maladie", "maternelle", "accident", "combat", "violence", "faim")\n'
        s, _ = sub(s, a, a + '''
# La faim qui tue ( 27/09, copie du reel ). Habitant.faim = deficit du corps en rations, apres adaptation
# ( config.FAIM_ADAPTATION = 0,4 : le jeune total use 0,6 ration par jour ). Un adulte meurt de faim entre 45 et 73 jours
# de jeune total ( grevistes irlandais de 1981 : 46 a 73 jours ; medecine : la mort vers 40 % du poids perdu ) ; les
# moins de 5 ans et les plus de 70 ans tiennent ~60 % de ce temps, les 5-14 ans et les 65-69 ans ~80 % ( les famines
# emportent d abord ces ages ). Risque du jour = PENTE x ( ( faim - F0 ) / ( F1 - F0 ) )^2 au-dela de F0, plafonne :
# a 0,6 par jour, 10 % des adultes sont morts au jour 54, la moitie au jour 63, 90 % au jour 73 ; a demi-ration ( 0,1 par
# jour ), F0 adulte n est atteint qu apres 260 jours - les 24 semaines de Minnesota se survivent, comme dans le reel.
SEUILS_FAIM = ((5, (16.0, 28.0)), (15, (21.0, 37.0)), (65, (26.0, 46.0)), (70, (21.0, 37.0)), (AGE_MAX + 1, (16.0, 28.0)))
PENTE_FAIM, PLAFOND_FAIM = 0.3, 0.5


def risque_faim(faim, age):
    """Le risque de mourir de faim aujourd hui, par deficit accumule ( Habitant.faim ) et par age. Fonction pure."""
    faim = np.asarray(faim, float); age = np.asarray(age)
    f0 = np.empty(faim.shape); f1 = np.empty(faim.shape); borne = 0
    for lim, (a, b) in SEUILS_FAIM:
        m = (age >= borne) & (age < lim); f0[m] = a; f1[m] = b; borne = lim
    x = np.maximum(0.0, (faim - f0) / (f1 - f0))
    return np.minimum(PLAFOND_FAIM, PENTE_FAIM * x * x)
''')
        a = '    for i in ids[tirer_deces(d.mortalite, sexe, age, u)].tolist(): deceder(p, H[i], "naturelle")\n'
        s, _ = sub(s, a, a + '''    # 1 bis. la faim qui tue ( 27/09, SEUILS_FAIM ) : un flux a part, tire pour les seuls habitants dont le deficit
    # depasse le seuil de leur age ; les autres tirages du jour ne bougent pas
    vifs = ids[tb.vivant[ids] == 1]
    r = risque_faim(tb.faim[vifs], _age_ans(p, vifs))
    k = np.nonzero(r > 0.0)[0]
    if k.size:
        u = p.du_jour("population_faim").random(k.size)
        for i in vifs[k[u < r[k]]].tolist(): deceder(p, H[i], "faim")
''')
        ecrire(f, s)
