#!/usr/bin/env python3
"""diag_champ.py — POURQUOI le champ est plat, et l est-il PARTOUT ?

Le smoke a refuse le lancement : a 250 m, la dispersion du champ entre les huit directions
vaut 0,0077 pour une moyenne de 0,505. Huit copies du meme nombre.

Deux causes possibles, et elles n ont pas le meme remede :
  (a) la PORTEE est trop courte — 35 m sur 250 m de rayon, c est un pas de fourmi ;
  (b) le risque appris est plat PARTOUT, et alors le champ ne peut rien porter, quelle que
      soit la portee. Ce serait la mort de l etage 1, pas un reglage.

On mesure donc la dispersion entre directions en fonction de la DISTANCE A L OBJECTIF et de
la PORTEE. On ne retouche aucun seuil : on mesure, et on rend les chiffres.
"""
import sys, math, torch
sys.argv = [sys.argv[0], '--champ', '--diag']

src = open('/home/younes/arma3-marl/agent_complet.py', encoding='utf-8').read()
# on execute le fichier jusqu a la definition du champ, pas au-dela
coupe = src.index("if '--smoke' in sys.argv:")
g = {'__name__': '__diag__'}
exec(compile(src[:coupe], 'agent_complet.py', 'exec'), g)

champ_risque, risque = g['champ_risque'], g['risque']
dev, NC = g['dev'], g['NC']
torch.manual_seed(0)

print("\n  DISPERSION DU CHAMP ENTRE LES HUIT DIRECTIONS")
print("  (le seuil du smoke est 0,010 — on ne le change pas, on regarde OU il est franchi)")
print("\n  " + "portee".rjust(8) + "".join(f"{d:>9}m" for d in (40, 60, 90, 120, 160, 200, 250)))
print("  " + "-" * 76)
B = 256
idx = torch.randint(0, NC, (B,), device=dev)
post = torch.zeros(B, dtype=torch.long, device=dev)
for portee in (35.0, 60.0, 100.0, 150.0):
    g['PORTEE_CHAMP'] = portee
    ligne = []
    for d in (40, 60, 90, 120, 160, 200, 250):
        ang = torch.rand(B, device=dev) * 2 * math.pi
        p = torch.stack([torch.sin(ang), torch.cos(ang)], -1) * d
        c = champ_risque(p, post, idx)
        ligne.append(c.std(dim=1).mean().item())
    print(f"  {portee:7.0f}m" + "".join(f"{v:>10.4f}" for v in ligne))
print("  " + "-" * 76)

# le risque appris lui-meme est-il plat ? on compare sa dispersion ENTRE POSITIONS a la
# dispersion qu il montre entre directions : si la premiere est grande et la seconde nulle,
# le champ echoue par PORTEE ; si les deux sont nulles, il echoue par NATURE.
print("\n  LE RISQUE APPRIS EST-IL PLAT PARTOUT ?")
for d in (40, 90, 160, 250):
    ang = torch.rand(B, device=dev) * 2 * math.pi
    p = torch.stack([torch.sin(ang), torch.cos(ang)], -1) * d
    r = risque(p, post, idx)
    print(f"    a {d:3d} m : risque moyen {r.mean():.4f} · ecart-type entre positions {r.std():.4f}")
print()
