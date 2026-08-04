#!/usr/bin/env python3
"""lire_banc150.py — DEPOUILLEMENT DU BANC A 150 M.

Les quatre portes ont ete ecrites AVANT le run, dans generer_banc150.py et banc150.sqf.
Elles sont recopiees ici telles quelles, et le programme REFUSE de conclure si l'une cede.

  P1 PRESENCE  : la ligne droite doit etre reperee. Sinon la position ne voit rien.
  P2 DYNAMIQUE : ecart interquartile des distances >= 27 m (25 % des 110 m utiles).
                 C'est LE controle qui manquait au banc a 80 m, ou il valait 8 m.
  P3 NUL       : droite et droite_bis a moins de 15 m d'ecart median.
  P4 REUSSITE  : oracle_libre repere >= 25 % plus loin que la droite.

⟨REGLE DE DEPOUILLEMENT, payee le 04/08 : « jamais repere » (-1) et « repere des le premier
 metre » sont deux resultats OPPOSES. L'ancien depouilleur les ramenait tous deux a la valeur
 du rayon de depart, et dans la correlation le -1 entrait au rang le plus BAS alors qu'il est
 le MEILLEUR resultat. On les separe ici, partout.⟩
"""
import re, sys
import numpy as np

LOG   = sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/harmattan-sandbox/logs/serverBA.out'
R_DEP, R_ARR = 150.0, 40.0
BRAS = ['droite', 'oracle', 'oracle_libre', 'droite_bis']

ess, cfgs = {}, {}
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|B150\|essai\|(\d+)\|(\w+)\|know\|([\d.]+)\|reste\|(\d+)\|dist_detect\|(-?\d+)\|points\|(\d+)', l)
    if m:
        ess.setdefault(int(m.group(1)), {})[m.group(2)] = dict(
            know=float(m.group(3)), reste=int(m.group(4)), dd=int(m.group(5)), n=int(m.group(6)))
    m = re.search(r'HMT\|B150\|config\|(\d+)\|defenseurs\|(\d+)\|derive_max\|([\d.]+)', l)
    if m:
        cfgs[int(m.group(1))] = dict(n=int(m.group(2)), derive=float(m.group(3)))

comp = sorted(c for c in ess if all(b in ess[c] for b in BRAS))
print(f"  configurations completes : {len(comp)} / 20   (4 bras chacune)")
if not comp:
    n = sum(len(v) for v in ess.values())
    print(f"  ({n} essais enregistres — le run n'est pas fini)"); sys.exit(1)

der = [cfgs[c]['derive'] for c in comp if c in cfgs]
if der:
    print(f"  derive des defenseurs a la pose : mediane {np.median(der):.1f} m · "
          f"max {max(der):.1f} m")
    bouge = [c for c in comp if cfgs.get(c, {}).get('derive', 0) > 3]
    if bouge:
        print(f"  ⟨configurations ou Arma a deplace les defenseurs de plus de 3 m : {bouge}")
        print(f"   leurs positions ne sont plus celles sur lesquelles l'oracle a ete calcule⟩")

# ------------------------------------------------------------------ les distances, par bras
def dist(c, b):
    """distance a l'objectif au reperage. None = JAMAIS repere : ce n'est pas une distance,
    c'est un succes complet, et on ne le noie pas dans une valeur numerique."""
    v = ess[c][b]['dd']
    return None if v < 0 else float(v)

D = {b: [dist(c, b) for c in comp] for b in BRAS}
jam = {b: sum(1 for v in D[b] if v is None) for b in BRAS}
vus = {b: [v for v in D[b] if v is not None] for b in BRAS}

print("\n  " + "="*72)
print("  bras            repere a (m de l'objectif)      jamais repere")
print("  " + "-"*72)
for b in BRAS:
    v = vus[b]
    med = np.median(v) if v else float('nan')
    print(f"  {b:14s}  mediane {med:6.1f}   min {min(v) if v else 0:5.1f}  max {max(v) if v else 0:5.1f}"
          f"        {jam[b]:2d} / {len(comp)}")
print("  " + "="*72)

# ------------------------------------------------------------------ P1 PRESENCE
p1 = jam['droite'] <= len(comp)*0.2
print(f"\n  P1 PRESENCE  : la ligne droite est reperee dans "
      f"{len(comp)-jam['droite']}/{len(comp)} configurations  -> {'OK' if p1 else 'ECHEC'}")
if not p1:
    print("     la position ne voit rien. Rien de ce qui suit ne vaut."); sys.exit(1)

# ------------------------------------------------------------------ P2 DYNAMIQUE
tous = [v for b in BRAS for v in vus[b]]
iqr = float(np.percentile(tous, 75) - np.percentile(tous, 25))
dyn = iqr / (R_DEP - R_ARR)
p2 = iqr >= 27
print(f"  P2 DYNAMIQUE : ecart interquartile {iqr:.0f} m sur {R_DEP-R_ARR:.0f} m utiles "
      f"= {dyn:.0%}  -> {'OK' if p2 else 'ECHEC'}")
print(f"     ⟨le banc a 80 m valait 8 m, soit 20 % : il ne separait rien⟩")

# ------------------------------------------------------------------ P3 CONTROLE NUL
paires = [(dist(c, 'droite'), dist(c, 'droite_bis')) for c in comp]
ecarts = [abs(a-b) for a, b in paires if a is not None and b is not None]
acc = sum(1 for a, b in paires if (a is None) == (b is None))
e_med = float(np.median(ecarts)) if ecarts else float('nan')
p3 = (not ecarts or e_med < 15) and acc >= len(comp)*0.8
print(f"  P3 NUL       : droite vs droite_bis — ecart median {e_med:.1f} m, "
      f"meme verdict sur {acc}/{len(comp)}  -> {'OK' if p3 else 'ECHEC'}")
if not p3:
    print("     la variance entre repetitions depasse ce qu'on veut mesurer. On ne conclut rien.")

# ------------------------------------------------------------------ P4 REGION DE REUSSITE
# apparie : on ne compare que les configurations ou LES DEUX bras ont ete reperes, et on
# compte a part celles ou l'un des deux a totalement echappe.
def ecart_bras(b):
    a_p, b_p, mieux, pire = [], [], 0, 0
    for c in comp:
        x, y = dist(c, 'droite'), dist(c, b)
        if x is None and y is None: continue
        if y is None: mieux += 1; continue          # le bras echappe la ou la droite non
        if x is None: pire += 1; continue
        a_p.append(x); b_p.append(y)
    if not a_p: return None, mieux, pire, 0
    return (np.mean(b_p)-np.mean(a_p))/np.mean(a_p), mieux, pire, len(a_p)

print()
for b in ['oracle', 'oracle_libre']:
    e, mieux, pire, n = ecart_bras(b)
    s = f"{e:+.0%}" if e is not None else "   ."
    print(f"  {b:14s} repere {s} plus loin que la droite  (sur {n} paires ; "
          f"{mieux} fois totalement invisible la ou la droite est vue)")

e_lib, mieux_lib, _, n_lib = ecart_bras('oracle_libre')
p4 = (e_lib is not None and e_lib >= 0.25) or mieux_lib >= len(comp)*0.25
print(f"\n  P4 REUSSITE  : le chemin PARFAIT achete-t-il 25 % de distance ?  "
      f"-> {'OK' if p4 else 'ECHEC'}")

# ------------------------------------------------------------------ le verdict
print("\n  " + "="*72)
if p1 and p2 and p3 and p4:
    print("  LE BANC EST UN INSTRUMENT. Il separe les trajectoires, et il a une region de")
    print("  reussite : un chemin parfait y gagne de la distance. On peut y certifier un agent.")
    print("  Prochain pas : entrainer l'agent A CE RAYON, cliquet corrige, puis le presenter ici.")
elif p1 and p2 and p3 and not p4:
    print("  L'INSTRUMENT MESURE, MAIS LA TACHE EST TROP DURE. Les distances s'etalent, les")
    print("  repetitions concordent — mais meme le chemin optimal n'achete pas 25 %.")
    print("  Ce n'est donc pas l'agent qu'il faut changer, c'est le SEUIL ou la TACHE.")
elif not p2:
    print("  L'INSTRUMENT NE SEPARE TOUJOURS RIEN. Reculer encore le rayon de depart, ou")
    print("  changer la grandeur mesuree. Aucune certification n'a de sens en attendant.")
else:
    print("  UN CONTROLE A CEDE. Voir ci-dessus — on ne conclut pas.")
print("  " + "="*72)
