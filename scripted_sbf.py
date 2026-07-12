"""Valide le COEUR du combat collaboratif : coordonner le FEU (supprimer quand on a la LOS+portee) bat-il
FONCER tete baissee, contre des defenseurs LETAUX ? Si oui -> la refonte 'gagner par le feu' est la bonne."""
import math, torch
from assault_terrain import AssaultTerrain
import terrain_gpu as TG
dev = "cuda:0"

def run(policy, relief=40.0, hit=0.20, N=2048, steps=60, seed=21):
    e = AssaultTerrain(num_envs=N, relief=relief, hit=hit, device=dev, seed=seed); e.reset()
    dk = []; aa = []   # defenseurs tues, attaquants vivants (en fin d'episode)
    for _ in range(steps):
        bear = torch.atan2(-e.apx, -e.apy); adv = (torch.round(bear / (math.pi / 4)) % 8).long()
        # ai-je un defenseur a portee ET en LOS ? (-> je peux SUPPRIMER = action 9)
        ex = e.dpx.unsqueeze(1) - e.apx.unsqueeze(2); ey = e.dpy.unsqueeze(1) - e.apy.unsqueeze(2)
        dist = (ex * ex + ey * ey).sqrt(); inrng = (dist < e.fire_range) & e._dalive().unsqueeze(1)  # (N,A,D)
        # LOS vers le defenseur le plus proche en portee
        ed2 = torch.where(inrng, dist, torch.tensor(1e9, device=dev)); km = ed2.argmin(2)
        bx = torch.gather(e.dpx, 1, km); by = torch.gather(e.dpy, 1, km)
        los = TG.los_clear(e.hm, e.apx, e.apy, bx, by, e.terr_R)
        can_fire = (inrng.any(2) & (los > 0.5))
        if policy == "fonce":
            a = adv                                  # toujours avancer (jamais supprimer)
        else:  # coordonne : si je peux tirer un defenseur -> SUPPRESS, sinon j'avance
            a = torch.where(can_fire, torch.full_like(adv, 9), adv)
        _, r, done, info = e.step(a); dm = done.bool()
        if dm.any():
            dk.append((e.D - e._dalive()[dm].float().sum(1)).mean().item()); aa.append(e._aalive()[dm].float().sum(1).mean().item())
    import statistics as st
    return (st.mean(dk) if dk else 0), (st.mean(aa) if aa else 0)

print("FEU COORDONNE vs FONCER (defenseurs letaux hit=0.20) :")
for pol in ["fonce", "coordonne"]:
    d, a = run(pol)
    print("  %-10s : defenseurs neutralises %.1f/%d | attaquants survivants %.1f/%d" % (pol, d, 4, a, 4))
