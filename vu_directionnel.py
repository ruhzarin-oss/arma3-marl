#!/usr/bin/env python3
"""vu_directionnel.py — LA COLONNE MANQUANTE EST-ELLE DEJA DERIVABLE ?

⟨regle 6, amendee ce soir : « une propriete du monde se lit dans son CODE avant qu on ne
 batisse dessus. »⟩

Fable veut une colonne DIRECTIONNELLE — « il me voit, MOI » — et prevoit une nuit d Arma pour
la capturer. Avant de la payer, on verifie qu elle n est pas deja derivable.

CE QUE LE CODE DIT (hmt_capture_v9_battlelines.sqf, ligne 257) :
    _i = lineIntersectsSurfaces [eyePos _a, aimPos _b, _a, _b, true, 1, "VIEW", "FIRE"];
La colonne `vu` est une LIGNE DE VUE PURE entre deux points — donc symetrique. C est
exactement pourquoi la paire vu/non-vu n a rien separe sur le banc-matrice : -0,3 point.

MAIS l orientation existe deja : `a_lui` est l angle sous lequel je suis dans SON champ.

    il me voit  =  ligne de vue  ET  je suis dans son cone (35 degres, MESURE)

FICHES RELUES avant ce chantier (regle 10) : fibua-line-bench-certified, etre-vu-tue-deux-fois-plus,
angle-mort-certifie-arma, knowsabout-est-de-camp-pas-de-soldat. Aucune ne porte deja ce calcul.

CRITERE, ecrit avant : la paire « vu directionnel » doit separer la mortalite d au moins
3 POINTS, dans le sens connu (etre vu tue plus), a suppression subie constante. C est la meme
taille de porte que le banc-matrice. Si elle passe, la nuit d Arma est INUTILE.
"""
import sys, numpy as np

DEMI_CONE = 35.0
ECART_MIN = 0.03

sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
g = {'__name__': '__vd__'}
exec(compile(src.split('print(f"  apprentissage')[0], 'sonde1.py', 'exec'), g)
SOI, ENN, MASQ, Y = g['SOI'], g['ENN'], g['MASQ'], g['Y']

viv = MASQ > 0.5
vu_sym = ENN[..., 1] > 0.5
mesure = ENN[..., 2] > 0.5          # la vue a-t-elle ete MESUREE (sinon -1 -> 0, masque)
a_lui = ENN[..., 4] * 180.0
supp = SOI[:, 5]

sym = (vu_sym & viv).any(axis=1)
dirn = (vu_sym & viv & mesure & (a_lui < DEMI_CONE)).any(axis=1)
cone_seul = (viv & (a_lui < DEMI_CONE)).any(axis=1)

print(f"\n  {len(Y)} instants · mortalite {Y.mean():.2%}")
print(f"  vue MESUREE sur au moins une arete : {(mesure & viv).any(axis=1).mean():.1%}")
print(f"  vu SYMETRIQUE   {sym.mean():.1%} des instants")
print(f"  dans un CONE    {cone_seul.mean():.1%}")
print(f"  vu DIRECTIONNEL {dirn.mean():.1%}   (ligne de vue ET dans le cone)")


def ecart(masque):
    tr = [(supp <= 0.01), (supp > 0.01) & (supp <= 0.3), (supp > 0.3)]
    num = den = 0.0
    na = nb = 0
    for m in tr:
        a, b = masque & m, (~masque) & m
        if a.sum() < 500 or b.sum() < 500:
            continue
        w = a.sum() + b.sum()
        num += (Y[a].mean() - Y[b].mean()) * w
        den += w
        na += int(a.sum()); nb += int(b.sum())
    return (num / den if den else float('nan')), na, nb


print("\n" + "=" * 76)
print("  LES TROIS DEFINITIONS, a suppression subie constante")
print("  " + "-" * 74)
for nom, m in (("vu SYMETRIQUE  ", sym), ("dans un CONE   ", cone_seul),
               ("vu DIRECTIONNEL", dirn)):
    e, na, nb = ecart(m)
    ok = e >= ECART_MIN
    print(f"     {nom}  ecart {e:+.2%}  ({na} contre {nb})"
          f"   -> {'SEPARE' if ok else 'ne separe pas'}")

e_d, _, _ = ecart(dirn)
print("\n" + "=" * 76)
if e_d >= ECART_MIN:
    print("  LA COLONNE EST DEJA DERIVABLE. « Il me voit » = ligne de vue ET dans le cone, et")
    print("  cette paire separe la mortalite dans le sens connu. LA NUIT D ARMA EST INUTILE :")
    print("  le corpus portait deja les deux morceaux, il manquait seulement de les croiser.")
else:
    print("  LA DERIVATION NE SUFFIT PAS. La colonne directionnelle doit etre CAPTUREE sur")
    print("  Arma — la nuit se justifie, et ce refus en est le motif ecrit.")
print("  " + "=" * 74)
