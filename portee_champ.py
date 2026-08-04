#!/usr/bin/env python3
"""portee_champ.py — A QUELLE PORTEE le champ de risque discrimine-t-il ?

Le smoke a refuse le champ a 35 m : ecart-type 0,079 pour une moyenne 0,434, soit 18 % de
variation entre directions, quand il en fallait 30.

JE NE DEPLACE PAS LE SEUIL. Je cherche la cause, et elle est geometrique : a 150 m d'un
defenseur, un pas de 35 m ne fait tourner l'angle relatif que de 13°, pour un demi-cone
mesure a 35°. Le pas est trop court pour faire basculer dedans/dehors, sauf si l'on est
deja au bord.

⟨le choix « 35 m, echelle de la manoeuvre » a ete depose le 27/07 dans un AUTRE
 environnement, ou le depart etait a 250 m et la fonction d'exposition differente. Le
 reprendre tel quel sans le verifier serait la quatrieme supposition de la soiree.⟩

On mesure donc, a plusieurs portees et a plusieurs distances de depart :
  · le rapport ecart-type / moyenne entre les huit directions
  · la part des cas ou la direction la moins chere n'est pas toujours la meme
Puis on choisit SUR PIECES.
"""
import sys
sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/agent_complet.py').read()
exec(src.split('print("\\n" + "="*78, flush=True)')[0])

import torch

idx = I_TE[:512]
B = len(idx)
torch.manual_seed(3)

def champ_a(p, post, idx, portee):
    q = (p.unsqueeze(1) + DIRS_CHAMP.unsqueeze(0) * portee).reshape(len(p)*8, 2)
    return expo(q, post.repeat_interleave(8), idx.repeat_interleave(8)).reshape(len(p), 8)

print("\n" + "="*74)
print("  rapport ECART-TYPE / MOYENNE entre les huit directions   (seuil du smoke : 0,30)")
print("  " + "-"*72)
print(f"  {'depart':>8s} " + "".join(f"{p:>9.0f} m" for p in [20, 35, 50, 70, 100, 140]))
for rayon in [150.0, 120.0, 90.0, 60.0]:
    ang = torch.rand(B, device=dev) * 6.2832
    p = torch.stack([torch.sin(ang), torch.cos(ang)], -1) * rayon
    post = torch.zeros(B, dtype=torch.long, device=dev)
    ligne = f"  {rayon:6.0f} m  "
    for portee in [20, 35, 50, 70, 100, 140]:
        C = champ_a(p, post, idx, float(portee))
        r = (C.std(dim=1).mean() / C.mean().clamp(min=1e-9)).item()
        ligne += f"{r:>10.2f}"
    print(ligne)
print("="*74)

print("\n  ET LA DIRECTION LA MOINS CHERE RESTE-T-ELLE VARIEE ? (part de la plus frequente)")
print("  ⟨si une seule direction domine, le champ ne donne plus un prix : il souffle la reponse⟩")
ang = torch.rand(B, device=dev) * 6.2832
p = torch.stack([torch.sin(ang), torch.cos(ang)], -1) * 150.0
post = torch.zeros(B, dtype=torch.long, device=dev)
for portee in [20, 35, 50, 70, 100, 140]:
    C = champ_a(p, post, idx, float(portee))
    rep = torch.bincount(C.argmin(dim=1), minlength=8).float() / B
    print(f"     {portee:3d} m : plus frequente {rep.max().item():.0%}   "
          f"[{' '.join(f'{v:.2f}' for v in rep.tolist())}]")

print("\n  RAPPEL DU CONTROLE DE COUT : le champ fait 8 appels a expo, quelle que soit la portee.")
print("  Changer la portee ne change RIEN au cout — seulement ce que le champ voit.")
