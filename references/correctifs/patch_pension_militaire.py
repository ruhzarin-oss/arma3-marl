"""29/09 ( HMT-147, chef de projet ) : la pension militaire, sans la penalite civile d avant 67 ans.
Un militaire de carriere qui part avec 25 ans de service et 60 ans, ou 40 ans de service ( loi 4387/2016 modifiee par la
loi 4670/2020 ; bulletin des pensions de l etat-major de l armee de terre, 2024 ) prend sa pension sans la penalite de
1/200 par mois d avance du droit commun : prendre_retraite, _liquider et _liquider_i recoivent un parametre penalite
( vrai par defaut : rien ne change pour qui ne le passe pas ; seul le domaine 25 le passe a faux ). Le meme texte pour le
depot et l arbre des references. Idempotent ( chaque insertion a sa premiere ligne propre ).
   python patch_pension_militaire.py racine_de_l_arbre"""
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


remplacer("monde/pays/d04_travail.py", [
    ('''def _liquider(p, d, h, age, nature="vieillesse", ecrire=True):
''', '''def _liquider(p, d, h, age, nature="vieillesse", ecrire=True, penalite=True):
'''),
    ('''    return _liquider_i(p, d, h.id, age, nature, ecrire)
''', '''    return _liquider_i(p, d, h.id, age, nature, ecrire, penalite)
'''),
    ('''def _liquider_i(p, d, i, age, nature="vieillesse", ecrire=True):
''', '''def _liquider_i(p, d, i, age, nature="vieillesse", ecrire=True, penalite=True):
'''),
    ('''    tot, nat, _, pen = calculer_pension(jours, assiette, age, invalidite=nature == "invalidite")
''', '''    # ( 29/09 ) penalite=False : la pension militaire ( domaine 25 ), sans la penalite d avant l age legal
    tot, nat, _, pen = calculer_pension(jours, assiette, age if penalite else max(age, AGE_LEGAL), invalidite=nature == "invalidite")
'''),
    ('''def prendre_retraite(p, h):
''', '''def prendre_retraite(p, h, penalite=True):
'''),
    ('''    return _liquider(p, d, h, POP.age_de(p, h))
''', '''    return _liquider(p, d, h, POP.age_de(p, h), penalite=penalite)
'''),
])
