#!/usr/bin/env python3
"""smoke_champ.py — le champ de risque est-il ACTIF, et DISCRIMINE-T-IL ?

⟨regle du projet : verifier avant un run couteux, avec un smoke qui PROUVE que le
 changement est actif. Un entrainement de 30 min sur un champ constant ne se verrait pas.⟩

CE QUI FERAIT ECHOUER CE SMOKE — ecrit avant :
  S1 FORME      champ_risque doit rendre (B, 8). Sinon rien ne tourne.
  S2 DISCRIMINE l'ecart-type entre les huit directions doit etre du meme ordre que la
                moyenne. Un champ plat ne porte aucune information et l'agent ne peut rien
                en tirer. ⟨mesure du 27/07 : ecart-type 0,047 pour une moyenne 0,033⟩
  S3 COHERENCE  la direction la MOINS chere ne doit pas etre systematiquement la meme :
                si c'est toujours « vers l'arriere », le champ dit juste « fuis » et
                l'arbitrage est souffle.
  S4 COUT       le surcout de percevoir doit rester sous x2,5. ⟨x1,4 mesure le 27/07⟩
  S5 CABLAGE    moi doit avoir 16 colonnes, dont les 8 dernieres EGALES au champ.
                Sans ce controle, le champ pourrait etre calcule et jamais branche.
"""
import sys, time
sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/agent_complet.py').read()
exec(src.split('print("\\n" + "="*78, flush=True)')[0])

import torch, numpy as np

idx = I_TE[:512]
B = len(idx)          # I_TE peut etre plus court que le lot demande — on suit sa taille
ang = torch.rand(B, device=dev) * 6.2832
p = torch.stack([torch.sin(ang), torch.cos(ang)], -1) * 150.0
post = torch.zeros(B, dtype=torch.long, device=dev)

print("\n" + "="*70)
C = champ_risque(p, post, idx)
ok1 = tuple(C.shape) == (B, 8)
print(f"  S1 FORME      champ_risque -> {tuple(C.shape)}   attendu ({B}, 8)   "
      f"-> {'OK' if ok1 else 'ECHEC'}")

ecart = C.std(dim=1).mean().item()
moyen = C.mean().item()
ok2 = ecart > 0.3 * moyen
print(f"  S2 DISCRIMINE ecart-type entre directions {ecart:.4f} · moyenne {moyen:.4f} "
      f"· rapport {ecart/max(moyen,1e-9):.2f}   -> {'OK' if ok2 else 'ECHEC : champ plat'}")

best = C.argmin(dim=1)
rep = torch.bincount(best, minlength=8).float() / B
ok3 = rep.max().item() < 0.60
print(f"  S3 COHERENCE  direction la moins chere, repartition sur les 8 :")
print(f"                {' '.join(f'{v:.2f}' for v in rep.tolist())}")
print(f"                la plus frequente : {rep.max().item():.0%}   "
      f"-> {'OK' if ok3 else 'ECHEC : le champ souffle toujours la meme direction'}")

moi, ent = percevoir(p, post, idx)
ok5 = moi.shape[1] == 16 and torch.allclose(moi[:, 8:], C, atol=1e-5)
print(f"  S5 CABLAGE    moi a {moi.shape[1]} colonnes · les 8 dernieres == champ : "
      f"{'oui' if moi.shape[1] == 16 and torch.allclose(moi[:, 8:], C, atol=1e-5) else 'NON'}"
      f"   -> {'OK' if ok5 else 'ECHEC : calcule mais pas branche'}")

torch.cuda.synchronize(); t0 = time.time()
for _ in range(30): percevoir(p, post, idx)
torch.cuda.synchronize(); t_avec = (time.time()-t0)/30

torch.cuda.synchronize(); t0 = time.time()
for _ in range(30): expo(p, post, idx)
torch.cuda.synchronize(); t_expo = (time.time()-t0)/30
print(f"  S4 COUT       percevoir {t_avec*1000:.2f} ms · un expo seul {t_expo*1000:.2f} ms "
      f"· rapport {t_avec/max(t_expo,1e-9):.1f}")
ok4 = t_avec < 0.05
print(f"                {'OK' if ok4 else 'ATTENTION : cout eleve'}   "
      f"(un pas d'entrainement en fait un seul)")

print("="*70)
tout = ok1 and ok2 and ok3 and ok5
print(f"  {'LE CHAMP EST ACTIF ET INFORMATIF — on peut entrainer.' if tout else 'NE PAS ENTRAINER : voir le controle qui a lache.'}")
print("="*70)
sys.exit(0 if tout else 1)
