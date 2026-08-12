#!/usr/bin/env python3
"""chasse_lieux_2_3.py — LES LIEUX DES GESTES N°2 (APPUI-FEU) ET N°3 (COUVERT SOUS LE FEU).

⟨Fable, 08/08⟩ Les deux geometries traduites en cases de 50 m, sur la carte du bati relevee
le 07/08 (163x163, pas 50 m). Ce script NE CERTIFIE RIEN : il propose des CANDIDATS. Chaque
lieu devra passer sa PORTE 0 — le professeur scripte contre son temoin — avant de juger un
agent. ⟨« On ne juge jamais un agent sur un lieu sans certificat. »⟩

N°2 — APPUI-FEU. Deux axes vers le meme objectif :
  - AXE D APPUI : une case a 2-4 cases de l objectif (100-200 m, la bande ou le toucher vaut
    encore quelque chose ⟨courbe 1 : 75 % a 25 m, 26 % a 200 m⟩), avec TOUTES les cases
    intermediaires OUVERTES — c est la ligne de vue, lisible directement sur la carte.
  - AXE D ASSAUT : 4 cases depuis un azimut ecarte de l appui, avec >= 2 masques et >= 1
    ouverte — l alternance du n°1, pour que l assaut soit jouable.
  ⚠️ FABLE DEMANDAIT 60-90° D ECART. La carte au pas de 50 m n offre que des multiples de 45°.
  Je prends donc 90° EXACTEMENT — la seule valeur representable DANS sa bande. Ce n est pas
  son critere au degre pres, et c est ecrit ici plutot que tu dans un coin.

N°3 — PRISE DE COUVERT SOUS LE FEU. Le sel est SOUS le pas de la carte : les masques utiles
sont a 10-20 m du trajet, invisibles a 50 m de resolution. Donc DEUX ETAGES :
  - etage 1 (ici) : une traversee de 3-4 cases MAJORITAIREMENT OUVERTES vers un couvert
    d arrivee, avec des cases MASQUEES ADJACENTES au couloir — la promesse qu il y a de la
    matiere a cote du chemin ;
  - etage 2 (en jeu, pas ici) : un geometre mesure les objets REELS a moins de 15 m de la
    ligne de marche. SANS CE SECOND ETAGE ON CERTIFIERAIT DES LIEUX OU LE GESTE EST IMPOSSIBLE.
  Et l objectif n a PAS besoin de bati dense ici : les 81 agregats sont trop rares pour etre
  gaspilles ou ils ne servent pas.
"""
import numpy as np

z = np.load('/home/younes/arma3-marl/leviathan/bati_stratis.npz')
MAI, ARB, ROU = z['MAISONS'], z['ARBRES'], z['ROUTE']
pas, taille = int(z['pas']), int(z['taille'])
n = MAI.shape[0]

masque = (MAI >= 1) | (ARB >= 3)
ouvert = (MAI == 0) & (ARB < 3)
print(f"\n  carte {n}x{n} au pas de {pas} m · masques {masque.mean():.1%} · ouvert {ouvert.mean():.1%}")

DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
def az(di, dj):
    return int(round(np.degrees(np.arctan2(-di, -dj)) % 360))

def dedans(a, b):
    return 0 <= a < n and 0 <= b < n

# ⚠️ ECART MINIMAL ENTRE LIEUX RETENUS. Le premier jet rendait 8 « objectifs distincts » qui
# etaient en verite TROIS VILLAGES : des cases voisines de 50 m. Or on tient 2 lieux a l ecart
# pour juger l agent sur du jamais-vu — a 50 m du terrain d entrainement, ce n est pas du
# jamais-vu, c est la meme rue. ⟨la couture des blocs, deja rencontree au decoupage⟩
ECART_MIN = 500.0

def espace(retenus, cle, c):
    p = np.array(c[cle], dtype=float)
    return all(np.hypot(*(p - np.array(r[cle], dtype=float))) >= ECART_MIN for r in retenus)

# =====================================================================================
# N°2 — APPUI-FEU
# =====================================================================================
obj = [(i, j) for j in range(2, n - 2) for i in range(2, n - 2)
       if MAI[j, i] >= 3 and MAI[j-2:j+3, i-2:i+3].sum() >= 12]
print(f"\n{'='*78}\n  N°2 APPUI-FEU · objectifs a bati dense : {len(obj)}")

c2 = []
for (i0, j0) in obj:
    for da, (dia, dja) in enumerate(DIRS):
        # --- l axe d APPUI : un poste a 2-4 cases, vue degagee jusqu a l objectif
        for L in (2, 3, 4):
            pts = [(i0 + dia * k, j0 + dja * k) for k in range(1, L + 1)]
            if any(not dedans(a, b) for a, b in pts):
                continue
            # toutes les cases entre le poste et l objectif doivent etre ouvertes : LA LIGNE DE VUE
            if not all(ouvert[b, a] for a, b in pts):
                continue
            appui = pts[-1]
            # --- l axe d ASSAUT : ecarte de 90° (2 crans sur 8), 4 cases, alternance
            for dd in (2, -2):
                dis, djs = DIRS[(da + dd) % 8]
                ps = [(i0 + dis * k, j0 + djs * k) for k in range(1, 5)]
                if any(not dedans(a, b) for a, b in ps):
                    continue
                m = [masque[b, a] for a, b in ps]
                o = [ouvert[b, a] for a, b in ps]
                if sum(m) < 2 or sum(o) < 1:
                    continue
                c2.append(dict(obj=(i0*pas, j0*pas),
                               appui=(appui[0]*pas, appui[1]*pas),
                               depart=(ps[-1][0]*pas, ps[-1][1]*pas),
                               d_appui=L*pas, az_ass=az(dis, djs),
                               masques=sum(m), ouverts=sum(o)))

r2 = []
for c in sorted(c2, key=lambda c: (-c['masques'], abs(c['d_appui'] - 150))):
    if not espace(r2, 'obj', c):
        continue
    r2.append(c)
    if len(r2) >= 8:
        break
print(f"  {len(c2)} couples (appui, assaut) trouves · {len(r2)} objectifs distincts retenus")
print(f"  {'objectif':>16} {'poste appui':>16} {'depart assaut':>16} {'d_app':>6} {'az':>4} {'msq':>4}")
for c in r2:
    print(f"  {str(c['obj']):>16} {str(c['appui']):>16} {str(c['depart']):>16} "
          f"{c['d_appui']:>6} {c['az_ass']:>4} {c['masques']:>4}")

# =====================================================================================
# N°3 — PRISE DE COUVERT SOUS LE FEU
# =====================================================================================
print(f"\n{'='*78}\n  N°3 COUVERT SOUS LE FEU")
c3 = []
for j0 in range(2, n - 6):
    for i0 in range(2, n - 6):
        if not masque[j0, i0]:
            continue                                   # le couvert d ARRIVEE
        for (di, dj) in DIRS:
            for L in (3, 4):
                pts = [(i0 + di * k, j0 + dj * k) for k in range(1, L + 1)]
                if any(not dedans(a, b) for a, b in pts):
                    continue
                o = [ouvert[b, a] for a, b in pts]
                if sum(o) < L - 1:                     # MAJORITAIREMENT ouvert : la traversee
                    continue
                # de la matiere A COTE du chemin — la promesse des masques sous le pas
                adj = 0
                for (a, b) in pts:
                    for (ea, eb) in ((1,0),(-1,0),(0,1),(0,-1)):
                        if dedans(a+ea, b+eb) and masque[b+eb, a+ea]:
                            adj += 1
                            break
                if adj < 2:
                    continue
                c3.append(dict(couvert=(i0*pas, j0*pas),
                               depart=(pts[-1][0]*pas, pts[-1][1]*pas),
                               long=L*pas, az=az(di, dj), ouverts=sum(o), adj=adj))

r3 = []
for c in sorted(c3, key=lambda c: (-c['adj'], -c['ouverts'])):
    if not espace(r3, 'couvert', c):
        continue
    r3.append(c)
    if len(r3) >= 8:
        break
print(f"  {len(c3)} traversees candidates · {len(r3)} couverts distincts retenus")
print(f"  {'couvert arrivee':>16} {'depart':>16} {'long':>6} {'az':>4} {'ouv':>4} {'adj':>4}")
for c in r3:
    print(f"  {str(c['couvert']):>16} {str(c['depart']):>16} {c['long']:>6} "
          f"{c['az']:>4} {c['ouverts']:>4} {c['adj']:>4}")

# =====================================================================================
print(f"\n{'='*78}")
ok = True
for nom, r, mini in (("n°2 appui-feu", r2, 6), ("n°3 couvert", r3, 6)):
    if len(r) >= mini:
        print(f"  {nom:>16} : {len(r)} candidats — de quoi en certifier 5 (3 instruits, 2 tenus a l ecart)")
    else:
        print(f"  {nom:>16} : SEULEMENT {len(r)} — geometrie trop rare sur Stratis, a elargir ou changer d ile")
        ok = False
if r2 and r3:
    np.savez('/home/younes/arma3-marl/lieux_appui.npz',
             obj=np.array([c['obj'] for c in r2]),
             appui=np.array([c['appui'] for c in r2]),
             depart=np.array([c['depart'] for c in r2]),
             az=np.array([c['az_ass'] for c in r2]))
    np.savez('/home/younes/arma3-marl/lieux_couvert.npz',
             couvert=np.array([c['couvert'] for c in r3]),
             depart=np.array([c['depart'] for c in r3]),
             az=np.array([c['az'] for c in r3]))
    print("  -> lieux_appui.npz · lieux_couvert.npz")
print("  ⚠️ AUCUN N EST CERTIFIE. Le n°3 exige EN PLUS un geometre en jeu : masques reels")
print("     a moins de 15 m de la ligne de marche. Sans lui, des lieux ou le geste est impossible.")
print("=" * 78)
