"""02/10 ( HMT-191, etape 0b d Arma a fond ) : les classes Arma du registre du domaine 25 verifiees sur le catalogue lu
dans les fichiers du jeu ( guerre/arsenal/configs.py, porte du lecteur franchie le 02/10 ; sonde_registre.py ). La
lunette x10 du tireur d elite portait un nom que CUP ne livre pas ( CUP_optic_LeupoldMk4_10x40_LRT ) : CUP n a que les
variantes _Woodland et _Desert ( scope 2 ). CHOIX : _Woodland. Ne change que le classname du modele au Parc ( aucune
dynamique du monde ). Le meme texte pour le depot et l arbre des references ( sans domaine 25 : absent ). Idempotent.
   python patch_classes_arma.py racine_de_l_arbre"""
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


remplacer("monde/pays/d25_armee.py", [
    ('''    CaracOptique("lunette_x10", 10, 1000, 0.60, 1800, "CUP_optic_LeupoldMk4_10x40_LRT",''',
     '''    CaracOptique("lunette_x10", 10, 1000, 0.60, 1800, "CUP_optic_LeupoldMk4_10x40_LRT_Woodland",   # ( 02/10 ) le nom de CUP'''),
])
