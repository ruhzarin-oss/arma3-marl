#!/usr/bin/env python3
"""test_r1 — L'ARRIVEE SUR SEGMENT repare-t-elle le palier 30 sans deplacer le palier 150 ?

Trois lectures, dans cet ordre :
  1. NON-REGRESSION — bouton ETEINT : le gymnase doit rendre EXACTEMENT les chiffres du
     30/08 (30 m : 81,3 / 11,1 / 0,0 · 150 m : 100,0 / 0,5 / 0,0). Sinon j'ai change le
     monde au lieu de reparer l'instrument, et rien de ce qui suit ne vaut.
  2. PALIER 150 bouton ALLUME : doit RESTER trois-sur-trois dans les IC d'Arma.
  3. PALIER 30 bouton ALLUME : la doctrine rejoint-elle [93,0 ; 100] ?
"""
import sys, math, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA

DEV, N = "cuda:0", 2000
CIB = {30: {"DOCTRINE": (93.0,100.0), "ALEATOIRE": (5.5,23.4), "NOOP": (0.0,7.0)},
       150:{"DOCTRINE": (91.6,100.0), "ALEATOIRE": (0.0, 8.4), "NOOP": (0.0,8.4)}}
AVANT = {(30,"DOCTRINE"):81.3, (30,"ALEATOIRE"):11.1, (30,"NOOP"):0.0,
         (150,"DOCTRINE"):100.0, (150,"ALEATOIRE"):0.5, (150,"NOOP"):0.0}

def wilson(k,n,z=1.96):
    ph=k/n; d=1+z*z/n; c=(ph+z*z/(2*n))/d
    h=z*((ph*(1-ph)/n+z*z/(4*n*n))**0.5)/d
    return (max(0.,c-h)*100, min(1.,c+h)*100)

def cap(dx,dy): return (torch.round(torch.atan2(dx,dy)/(math.pi/4.0)).long() % 8)

def jouer(nom, R, rayon, pas, seg):
    torch.manual_seed(1234)
    cfg = dict(MONDE_ARMA); cfg.update(dict(secure_only=True, postures=True, arrivee_segment=seg))
    e = AssaultTerrain(num_envs=N, A=1, D=1, D_min=1, R_spawn=float(R), secure_r=float(rayon),
                       max_steps=pas, device=DEV, seed=7, **cfg)
    e.reset(); e.ddmg[:] = 0.95
    pris = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    for t in range(pas):
        vers = cap(-e.apx, -e.apy)
        if nom == "NOOP": a = torch.full_like(vers, 8)
        elif nom == "ALEATOIRE":
            g = torch.randint(0, 13, vers.shape, device=e.dev); a = torch.where(g == 8, vers, g)
        else: a = vers
        _,_,done,info = e.step(a, auto_reset=False)
        pris |= info["took"] & ~fini; fini |= done.bool()
        if bool(fini.all()): break
    return float(pris.float().mean())*100, int(pris.sum())

for seg in [False, True]:
    print(f"\n{'='*74}\n arrivee_segment = {seg}\n{'='*74}")
    for R, rayon, pas in [(30,6,6), (150,15,23)]:
        print(f"  --- palier {R} m, rayon {rayon} m ---")
        for nom in ["DOCTRINE","ALEATOIRE","NOOP"]:
            taux,k = jouer(nom,R,rayon,pas,seg)
            lo,hi = wilson(k,N); alo,ahi = CIB[R][nom]
            v = "DANS" if alo<=taux<=ahi else "HORS"
            if not seg:
                ecart = taux - AVANT[(R,nom)]
                print(f"    {nom:10s} {taux:6.1f}% [{lo:5.1f};{hi:5.1f}]  Arma [{alo:5.1f};{ahi:5.1f}] {v}   avant {AVANT[(R,nom)]:5.1f}%  ecart {ecart:+5.1f}")
            else:
                print(f"    {nom:10s} {taux:6.1f}% [{lo:5.1f};{hi:5.1f}]  Arma [{alo:5.1f};{ahi:5.1f}] {v}")
