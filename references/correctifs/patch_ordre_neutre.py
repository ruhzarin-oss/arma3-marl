"""29/09 ( chef de projet ) : l ordre NEUTRE du marche du travail du matin.
Les candidats d un lieu etaient servis par NUMERO d habitant ( par_lieu rempli dans l ordre des numeros, trois offres au
plus par poste ) : avec un poste vacant par jour pour ~ 400 chomeurs d un lieu ( Stratis, graine 5 ), les grands numeros
n etaient jamais atteints - une file fixe, sans rien de reel. Chaque matin, l ordre des candidats de chaque lieu est
tire au hasard du jour, dans un flux a part ( travail_file : les autres tirages ne bougent pas ) ; la distance reste la
premiere cle. Servir d abord les chomeurs de longue duree serait contraire au reel ( leur chance d embauche baisse avec
la duree ). Le meme texte pour le depot et l arbre des references. Idempotent ( chaque insertion a sa premiere ligne
propre ).
   python patch_ordre_neutre.py racine_de_l_arbre"""
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
    ('''    if not par_lieu: _refaire_pointes(p, d); return
    lieux_cands = [w.carte.lieux[k] for k in sorted(par_lieu)]
''', '''    if not par_lieu: _refaire_pointes(p, d); return
    # ( 29/09 ) l ordre des candidats d un lieu, tire au hasard du jour dans un flux a part ( servis par numero, les grands
    # numeros n etaient jamais atteints ) ; la distance reste la premiere cle
    fl = p.du_jour("travail_file")
    for k in sorted(par_lieu): fl.shuffle(par_lieu[k])
    lieux_cands = [w.carte.lieux[k] for k in sorted(par_lieu)]
'''),
])
