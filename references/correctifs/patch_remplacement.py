"""29/09 ( HMT-161, Classes et chef de projet ) : l employeur REMPLACE le salarie parti.
Un salarie EN DISPONIBILITE ( HMT-126 : sans travail depuis 5 jours, a demi-salaire ) qui part de lui-meme pour un autre
emploi faisait baisser de 1 l effectif vise de son poste : le poste disparaissait, meme quand l employeur en avait le
travail ( Classes, graine 71 : 29 chauffeurs devenus 22 en 40 jours, les convois de 7 h perdus ; la cible des convoyeurs
valait exactement l effectif restant ). Un salarie en disponibilite n est pas un poste en trop, c est un poste sans
travail ce jour-la : son depart volontaire ne supprime le poste que si l employeur n en a plus besoin ( _besoin : l Etat,
une entreprise qui tourne aux trois quarts, ni liquidee ni en greve, un marche et ses convoyeurs ) - comme a la fin d un
CDD. Le meme texte pour le depot et l arbre des references. Idempotent ( chaque insertion a sa premiere ligne propre ).
   python patch_remplacement.py racine_de_l_arbre"""
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
    ('''        k0 = (h.travail.id, h.role); d.cible[k0] = max(0, d.cible.get(k0, 1) - 1)
''', '''        # ( 29/09, HMT-161 ) le poste ne disparait que si l employeur n en a plus besoin, comme a la fin d un CDD
        k0 = (h.travail.id, h.role)
        if not _besoin(p, d, *k0): d.cible[k0] = max(0, d.cible.get(k0, 1) - 1)
'''),
])
