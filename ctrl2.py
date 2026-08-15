"""Contrôle 2 refait. Le precedent testait l action 9 AU PAS 0, alors que les hommes
naissent a 170 m et que l appui exige d < 0,9 x 110 = 99 m. Impossible par arithmetique,
sans regarder une donnee. On mesure donc sur TOUT l episode."""
import sys, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from boucle import cap, jouer, monde

def script(e, t):
    a = cap(-e.apx, -e.apy)
    demi = max(1, e.A // 2)
    ap = torch.zeros(e.N, e.A, dtype=torch.bool, device=e.dev)
    if (t // 3) % 2 == 0: ap[:, demi:] = True
    else:                 ap[:, :demi] = True
    d = torch.sqrt(e.apx**2 + e.apy**2)
    return torch.where(ap & (d < e.fire_range*0.9), torch.full_like(a, 9), a)

e = monde(256, 101); e.reset()
n9, ntot, pas9 = 0, 0, []
for t in range(60):
    a = script(e, t)
    k = int((a == 9).sum()); n9 += k; ntot += a.numel()
    if k: pas9.append(t)
    _, _, done, _ = e.step(a, auto_reset=False)
    if bool(done.all()): break
print(f"  action 9 emise : {n9} fois sur {ntot} decisions ({100*n9/max(ntot,1):.1f} %)")
print(f"  premier pas ou elle sort : {pas9[0] if pas9 else 'JAMAIS'}   ·   nb de pas concernes : {len(pas9)}")
print(f"\n  seuil d appui : d < 0,9 x {e.fire_range} = {0.9*e.fire_range:.0f} m   ·   naissance a {e.R_spawn:.0f} m")
print("  ⇒ " + ("✓ PASSE — SCRIPT appuie bien, mais pas avant d etre a portee" if n9 > 0
                else "⛔ TOMBE — SCRIPT n appuie JAMAIS, ce n est pas le meme bras qu Arma"))
