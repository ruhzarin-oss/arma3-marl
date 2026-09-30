"""29/09 ( HMT-147, chef de projet ) : l ordinaire de caserne au budget de la defense.
Le domaine 25 nourrit ses appeles ( l ordinaire de caserne ) : l Etat achete leurs rations au marche de leur base sous le
motif « ordinaire_caserne ». Le compte de l Etat du domaine 6 range ce motif aux achats de la DEFENSE ( sans lui, aux
achats « autres » ). Sans domaine 25 ( l arbre des references ), le motif n existe pas : rien ne change. Le meme texte
pour le depot et l arbre des references. Idempotent ( chaque insertion a sa premiere ligne propre ).
   python patch_ordinaire_defense.py racine_de_l_arbre"""
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


remplacer("monde/pays/d06_etat.py", [
    ('''        elif m == "subvention": parts = {("subventions", "transferts"): s}
''', '''        elif m == "ordinaire_caserne": parts = {("defense", "achats"): s}      # ( 29/09 ) l ordinaire des appeles
        elif m == "subvention": parts = {("subventions", "transferts"): s}
'''),
])
