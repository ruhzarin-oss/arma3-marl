"""29/09 ( Classes, diag 204 ; chef de projet ) : le chomeur n est jamais « hors marche ».
Le marche du travail du matin ecartait par son METIER quiconque etait elu, patron ou marchand ( HORS_MARCHE ), meme
CHOMEUR : le chomeur du recensement porte le metier qu il cherche ou a quitte, et 222 chomeurs marchands de Stratis ne
recevaient jamais d offre ( jour 3, 59 postes du tourisme vacants ). Un chomeur cherche un emploi ( definition du BIT ) :
« hors marche » ne vaut que pour qui EXERCE ( l elu en fonction, le patron, le marchand qui tient son commerce ). Le meme
texte pour le depot et l arbre des references. Idempotent ( chaque insertion a sa premiere ligne propre ).
   python patch_chomeur_hors_marche.py racine_de_l_arbre"""
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
    ('''    ok &= (tb.vivant[:n] == 1) & ~np.isin(tb.role[:n], _codes(HORS_MARCHE)) & (tb.domicile[:n] >= 0)
''', '''    # ( 29/09 ) « hors marche » ne vaut que pour qui EXERCE ( elu, patron, marchand en commerce ) : un chomeur cherche
    # un emploi ( BIT ), quel que soit le metier qu il cherche ou a quitte
    ok &= (tb.vivant[:n] == 1) & ~(np.isin(tb.role[:n], _codes(HORS_MARCHE)) & (st != CHOMEUR)) & (tb.domicile[:n] >= 0)
'''),
])
