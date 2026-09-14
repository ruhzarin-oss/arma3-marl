"""CONTROLE STRUCTUREL de la reparation — sur une grandeur NON SATURABLE.

Le controle precedent comparait les pertes en fin d episode : elles valent 1,000 dans les
deux bras, donc il ne pouvait rien discriminer. Un controle sature ne dit pas « echec »,
il ne dit RIEN. Celui-ci compte, APRES UN SEUL PAS, combien d attaquants ont pris des
degats — la grandeur que la branche pretend restreindre.

Monde plat (relief 0) : tout le monde se voit, donc les defenseurs peuvent tirer.
2 defenseurs, 4 attaquants.

PREDICTION ECRITE AVANT :
  cible_unique=True  -> au plus 2 attaquants touches (un par defenseur)
  cible_unique=False -> STRICTEMENT PLUS
⛔ ECHEC si True depasse 2,0 : le one-hot ne restreint rien, la reparation est fausse.
⛔ INCONCLUANT si les deux bras sont egaux : le controle est aveugle, on ne conclut pas.
"""
import math, sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain


def touches_au_premier_pas(cible_unique, N=2048, seed=11):
    e = AssaultTerrain(num_envs=N, A=4, D=2, relief=0.0, hit=0.9, R_spawn=60.0,
                       device="cuda:0", seed=seed, cible_unique=cible_unique)
    e.reset()
    avant = e.admg.clone()
    bear = torch.atan2(-e.apx, -e.apy)
    e.step((torch.round(bear / (math.pi / 4)) % 8).long())
    touches = (e.admg > avant + 1e-6).float().sum(1)        # par environnement
    return touches.mean().item(), touches.max().item(), (touches > 0).float().mean().item()


mu, mx, pu = touches_au_premier_pas(True)
mf, mxf, pf = touches_au_premier_pas(False)
print("  cible_unique=True  : %.3f attaquant(s) touche(s)/env  max %.0f  envs avec tir %.0f %%"
      % (mu, mx, pu * 100))
print("  cible_unique=False : %.3f attaquant(s) touche(s)/env  max %.0f  envs avec tir %.0f %%"
      % (mf, mxf, pf * 100))
if mx > 2.0:
    print("  CONTROLE=ECHOUE la restriction ne s applique pas (max %.0f > 2)" % mx)
elif abs(mu - mf) < 1e-6:
    print("  CONTROLE=INCONCLUANT les deux bras sont identiques, le controle est aveugle")
elif mu < mf:
    print("  CONTROLE=PASSE")
else:
    print("  CONTROLE=ECHOUE le bras restreint touche PLUS que le bras libre")
