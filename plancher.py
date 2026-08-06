#!/usr/bin/env python3
"""plancher.py — LE PREDICTEUR DIT-IL JAMAIS « TU ES EN SECURITE » ?

Le crochet achete +10,4 points de temps hors des cones et perd quand meme. Mes deux
explications de la soiree sont tombees. Reste l arithmetique : si la sortie du predicteur ne
descend jamais bas, alors etre hors du cone n achete RIEN, et seule la longueur du chemin
compte — ce qui est exactement ce qu on observe.

On mesure donc le PLANCHER de la sortie, et ce qu il donne une fois converti en mort par pas.
"""
import sys, math

sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/agent_complet.py', encoding='utf-8').read()
h = {'__name__': '__plancher__'}
exec(compile(src[:src.index("def percevoir")], 'agent_complet.py', 'exec'), h)
t = h['torch']; dev = h['dev']; NC = h['NC']

t.manual_seed(0)
idx = t.randint(0, NC, (4096,), device=dev)
post = t.zeros(4096, dtype=t.long, device=dev)
vals = []
for r in (60.0, 120.0, 250.0):
    a = t.rand(4096, device=dev) * 2 * math.pi
    p = t.stack([t.sin(a), t.cos(a)], -1) * r
    vals.append(h['risque'](p, post, idx))
v = t.cat(vals)

print("\n" + "=" * 74)
print("  LA SORTIE DU PRÉDICTEUR, telle qu'elle est utilisée comme LOI DE MORT")
print("  " + "-" * 72)
print(f"     min {v.min():.3f} · médiane {v.median():.3f} · max {v.max():.3f}")
print(f"     mortalité RÉELLE du corpus à 30 s : 10,00 %")
print("  " + "-" * 72)
pm = 1 - (1 - v.min().item()) ** (1 / 9.15)
print(f"     le PLANCHER converti en mort par pas : {pm:.2%}")
print(f"     survie sur 14 pas (224 m, la droite)  au plancher : {(1-pm)**14:.1%}")
print(f"     survie sur 16 pas (256 m, le crochet) au plancher : {(1-pm)**16:.1%}")
print("\n" + "=" * 74)
if v.min().item() > 0.3:
    print("  LE PRÉDICTEUR NE DIT JAMAIS « EN SÉCURITÉ ». Sa sortie est un SCORE de classement,")
    print("  pas une probabilité : sur un corpus à 10 % de morts, un modèle calibré rendrait")
    print("  0,10 en moyenne, pas une valeur centrée sur 0,5.")
    print("  -> le traiter comme une probabilité de mourir est une ERREUR DE CATÉGORIE, et")
    print("     elle est de moi, introduite ce soir avec la loi-prédicteur.")
    print("  -> hors du cône n'achète rien, seule la longueur du chemin compte, et le crochet")
    print("     perd mécaniquement. C'est exactement ce que la PORTE 0 a mesuré.")
else:
    print("  Le plancher descend bas : l'explication est ailleurs.")
print("  " + "=" * 72)
