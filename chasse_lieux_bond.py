#!/usr/bin/env python3
"""chasse_lieux_bond.py — TROUVER LES COULOIRS QUI FORCENT LE BOND PAR BINOME.

⟨Fable, 07/08, fiche n°1⟩ « couloir de 150-250 m vers une ligne de defenseurs, masques tous
les 30-50 m : chaque bond doit finir derriere un masque avant la fin du sursis. »

Le sursis est mesure : l arc met **4 s** a s ouvrir. Un bond de 40 m a la course (16 m/pas,
un pas = 3,28 s) prend ~8 s. Donc un masque tous les 30-50 m est la geometrie qui rend le
bond jouable — plus espace, on meurt entre deux ; plus serre, avancer ensemble suffit.

CE QU ON CHERCHE, sur la carte du bati relevee hier (bati_stratis.npz, pas 50 m) :
  - un OBJECTIF : de la ou l on part, un point avec du bati (la ligne de defenseurs)
  - un COULOIR de 150 a 250 m qui y mene
  - des MASQUES le long : des cases avec du bati ou des arbres, espacees de 30 a 50 m
  - et PAS un tunnel : le couloir ne doit pas etre bati de bout en bout, sinon tout le monde
    est a couvert tout le temps et le geste ne s achete rien ⟨la lecon du 23/07 : couvert
    UNIFORME = tous les chemins equivalents⟩

CE SCRIPT NE CERTIFIE RIEN. Il propose des CANDIDATS. Chaque lieu devra passer sa PORTE 0 —
le geste scripte contre son temoin, quelques centaines de passages — avant d avoir le droit
de juger un agent.
"""
import numpy as np

z = np.load('/home/younes/arma3-marl/leviathan/bati_stratis.npz')
MAI, ARB, ROU = z['MAISONS'], z['ARBRES'], z['ROUTE']
pas, taille = int(z['pas']), int(z['taille'])
n = MAI.shape[0]
print(f"\n  carte : {n}x{n} au pas de {pas} m · monde {taille} m")

# une case est un MASQUE si elle porte du bati ou des arbres
masque = (MAI >= 1) | (ARB >= 3)
# une case est OUVERTE si elle ne porte rien
ouvert = (MAI == 0) & (ARB < 3)
print(f"  masques {masque.mean():.1%} des cases · ouvert {ouvert.mean():.1%}")

# --- objectifs candidats : agregats de bati (une ligne de defenseurs a quelque chose a tenir)
obj = []
for j in range(2, n - 2):
    for i in range(2, n - 2):
        if MAI[j, i] >= 3 and MAI[j-2:j+3, i-2:i+3].sum() >= 12:
            obj.append((i, j))
print(f"  objectifs candidats (bati dense) : {len(obj)}")

DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
cands = []
for (i0, j0) in obj:
    for (di, dj) in DIRS:
        # le couloir part de l objectif et remonte de 200 m (4 cases de 50 m)
        L = 5                                   # 5 cases = 250 m
        pts = [(i0 + di * k, j0 + dj * k) for k in range(1, L + 1)]
        if any(not (0 <= a < n and 0 <= b < n) for a, b in pts):
            continue
        m = np.array([masque[b, a] for a, b in pts])
        o = np.array([ouvert[b, a] for a, b in pts])
        # ce qu on veut : de l ALTERNANCE. Ni tunnel (tout masque), ni desert (tout ouvert).
        n_m, n_o = int(m.sum()), int(o.sum())
        if n_m < 2 or n_o < 2:
            continue
        # les masques ne doivent pas etre colles : au moins un ouvert entre deux masques
        alt = sum(1 for k in range(L - 1) if m[k] != m[k + 1])
        if alt < 2:
            continue
        x0, y0 = (i0 + di * L) * pas, (j0 + dj * L) * pas
        cands.append(dict(obj=(i0 * pas, j0 * pas), depart=(x0, y0),
                          masques=n_m, ouverts=n_o, alternances=alt,
                          az=int(round(np.degrees(np.arctan2(-di, -dj)) % 360))))

cands.sort(key=lambda c: (-c['alternances'], -c['masques']))
print(f"\n  {len(cands)} couloirs candidats trouves")
print("  " + "-" * 70)
print(f"  {'objectif':>16} {'depart':>16} {'az':>4} {'masques':>8} {'ouverts':>8} {'altern':>7}")
# ECART MINIMAL : sans lui la liste rend des cases VOISINES de 50 m — le meme village compte
# huit fois. Or on tient des lieux A L ECART pour juger sur du jamais-vu ; a 50 m du terrain
# d entrainement ce n est pas du jamais-vu. ⟨la couture des blocs, revenue par la fenetre⟩
import math
ECART_MIN = 500.0
retenus = []
for c in cands:
    if any(math.hypot(c['obj'][0]-r['obj'][0], c['obj'][1]-r['obj'][1]) < ECART_MIN
           for r in retenus):
        continue
    retenus.append(c)
    print(f"  {str(c['obj']):>16} {str(c['depart']):>16} {c['az']:>4} "
          f"{c['masques']:>8} {c['ouverts']:>8} {c['alternances']:>7}")
    if len(retenus) >= 8:
        break

print("\n" + "=" * 74)
if len(retenus) >= 6:
    print(f"  {len(retenus)} CANDIDATS RETENUS — de quoi en certifier 5 (3 d entrainement,")
    print("  2 tenus a l ecart). Aucun n a encore d opinion : chacun doit passer sa PORTE 0,")
    print("  le geste scripte contre son temoin, avant de juger le moindre agent.")
    np.savez('/home/younes/arma3-marl/lieux_bond.npz',
             obj=np.array([c['obj'] for c in retenus]),
             depart=np.array([c['depart'] for c in retenus]),
             az=np.array([c['az'] for c in retenus]))
    print("  -> lieux_bond.npz")
else:
    print(f"  SEULEMENT {len(retenus)} CANDIDATS. Stratis ne porte peut-etre pas assez de")
    print("  couloirs de cette forme — a elargir (autre pas, autre longueur) ou changer d ile.")
print("  " + "=" * 72)
