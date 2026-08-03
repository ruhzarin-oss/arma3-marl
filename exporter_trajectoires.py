#!/usr/bin/env python3
"""exporter_trajectoires.py — sortir l'agent du gymnase pour l'emmener au certificateur.

L'agent est un réseau PyTorch ; Arma ne sait pas le lire. Mais en évaluation il est
DÉTERMINISTE : pour une configuration défensive donnée, il produit toujours la même
trajectoire. On exporte donc ces trajectoires, et Arma les rejoue sur les MÊMES
configurations — plus la ligne droite comme témoin.

⟨règle du projet : Arma certifie, la sandbox est un gymnase. Juillet : 96 % en sandbox,
 0/38 dans Arma. Un agent non certifié ne vaut rien.⟩
"""
import numpy as np, torch, json, math, sys
sys.argv = [sys.argv[0]]                     # neutralise le mode "court" hérité
exec(open('/home/younes/arma3-marl/agent_complet.py').read().split('print("\\n" + "="*78, flush=True)')[0])

RAYON = 80.0                                  # distance réellement tenue par l'agent à agrégation MAXIMUM
# ⟨l'agent précédent tenait 125 m, mais contre une exposition MOYENNÉE — un monde indulgent
#  que le banc Arma a refusé de certifier (écart 12 % contre 25 % exigés). Avec l'agrégation
#  corrigée au maximum, il ne tient plus que 80 m. On certifie ce qu'il sait faire, pas ce
#  qu'il savait faire dans un monde qui mentait.⟩
N = 30                                        # configurations exportées
DEPART_COURANT = RAYON

pol, journal, bloque = entrainer(1, 1.75)
print(f"\nexport : palier atteint {journal[-1][0] if journal else '?'} m", flush=True)

idx = I_TE[:N]
sorties = []
with torch.no_grad():
    for essai in range(2):                    # deux tirages d'angle de départ
        ang = torch.linspace(0, 2*math.pi, len(idx), device=dev) + essai*0.7
        p = torch.stack([torch.sin(ang), torch.cos(ang)], -1) * RAYON
        post = torch.zeros(len(idx), dtype=torch.long, device=dev)
        traj = [p.cpu().numpy().copy()]
        posts = [post.cpu().numpy().copy()]
        for t in range(NPAS):
            moi, ent = percevoir(p, post, idx)
            dr, al, po, _ = pol(moi, ent, MSK[idx])
            dr = dr / dr.norm(dim=-1, keepdim=True).clamp(min=1e-6)
            wa = torch.nn.functional.one_hot(al.argmax(-1),3).float()
            wp = torch.nn.functional.one_hot(po.argmax(-1),3).float()
            post = wp.argmax(-1)
            vit = (wa*ALLURES).sum(-1) * (wp*POSTURES_V).sum(-1)
            dehors = (p.norm(dim=-1) > ARRIVE).float()
            p = p + dr * vit.unsqueeze(-1) * dehors.unsqueeze(-1)
            if t % 4 == 3:
                traj.append(p.cpu().numpy().copy()); posts.append(post.cpu().numpy().copy())
        T = np.stack(traj, 1)                 # (N, pts, 2)
        P = np.stack(posts, 1)
        for i in range(len(idx)):
            j = int(idx[i])
            d = POS[j][MSK[j] > 0].cpu().numpy()
            a = AZI[j][MSK[j] > 0].cpu().numpy()
            sorties.append(dict(
                config=essai*1000 + i,
                defenseurs=[[float(x[0]), float(x[1]), float(az)] for x, az in zip(d, a)],
                agent=[[float(x), float(y)] for x, y in T[i]],
                postures=[int(v) for v in P[i]],
                depart=[float(T[i][0][0]), float(T[i][0][1])],
            ))

json.dump(sorties, open('/mnt/data/corpus/trajectoires_agent.json','w'))
print(f"  {len(sorties)} trajectoires exportées, {len(sorties[0]['agent'])} points chacune")
print(f"  defenseurs par config : {np.mean([len(s['defenseurs']) for s in sorties]):.1f}")
pcouche = np.mean([np.mean([p==2 for p in s['postures']]) for s in sorties])
print(f"  part de trajet couché : {pcouche:.0%}")
