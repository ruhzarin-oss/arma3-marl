#!/usr/bin/env python3
"""agent_axe.py — L'AGENT CHOISIT SON AXE D'APPROCHE.

TROIS ÉCHECS ONT MENÉ ICI, et chacun a été attrapé par un critère écrit avant :
  · v1 — la distance était pénalisée à chaque pas : l'agent fonçait, et s'exposait PLUS
    qu'une ligne droite. Critère 2 : ÉCHEC.
  · v2 — j'ai retiré cette pénalité : l'agent a fui et n'est jamais arrivé. Critère 1 : ÉCHEC.
  · v3 — arrivée rendue obligatoire : la perte stagne dès l'époque 200, l'agent n'arrive qu'à
    13 %. L'optimisation ne converge pas.

LA VRAIE CAUSE. Je demandais cinquante décisions successives, avec un gradient traversant
toute la trajectoire. C'est un problème d'optimisation dur — et surtout, ce n'est PAS la
question. Le choix tactique qu'on a mesuré n'est pas « quelle direction à chaque pas », c'est
« par où j'attaque ». L'A/B comparait deux AXES, pas deux micro-trajectoires.

ICI : l'agent regarde la position défendue et produit UN axe d'approche. Le trajet en découle.
Une décision, celle qui compte.

CRITÈRES ÉCRITS AVANT DE REGARDER
  1. L'axe choisi doit être moins exposé que l'axe MOYEN d'au moins 25 %. En dessous, l'agent
     n'a rien appris d'utile.
  2. CONTRÔLE QUI PEUT TOUT FAIRE ÉCHOUER — on rejoue l'agent sur les mêmes positions avec des
     ORIENTATIONS TIRÉES AU HASARD. Son avantage doit s'effondrer d'au moins la moitié. Sinon
     il a appris la géométrie des positions, pas à lire le regard adverse.
  3. CONTRÔLE DE TRIVIALITÉ — un agent qui ne voit PAS les orientations ne doit pas faire
     mieux que le hasard. Sinon un axe est bon en soi et l'orientation n'y est pour rien.
  4. RÉFÉRENCE HAUTE — on calcule le MEILLEUR axe possible par balayage exhaustif. L'agent
     doit s'en approcher ; l'écart qui reste dit ce qu'il n'a pas appris.
"""
import numpy as np, math, json
import torch, torch.nn as nn

D = '/mnt/data/corpus/tenseurs'
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
torch.cuda.set_device(0); torch.manual_seed(3); np.random.seed(3)

print("extraction de configurations défensives réelles", flush=True)
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
T, N, _ = X.shape
configs = []
rng = np.random.default_rng(5)
for ti in rng.choice(T, 40000, replace=False):
    xt = np.asarray(X[ti]); pt = np.asarray(P[ti])
    for camp in (0, 1):
        s = pt & (xt[:,4] > 0.5) & (xt[:,5] == camp)
        if s.sum() < 4: continue
        pos = xt[s][:,1:3]; azi = xt[s][:,7]
        c = pos.mean(0); d = np.linalg.norm(pos-c, axis=1); g = d < 120
        if g.sum() < 4 or g.sum() > 12: continue
        configs.append((pos[g]-pos[g].mean(0), azi[g])); break
    if len(configs) >= 2000: break
print(f"  {len(configs)} configurations, {np.mean([len(c[0]) for c in configs]):.1f} défenseurs", flush=True)

DMAX = max(len(c[0]) for c in configs)
POS = np.zeros((len(configs), DMAX, 2), np.float32)
AZI = np.zeros((len(configs), DMAX), np.float32)
MSK = np.zeros((len(configs), DMAX), np.float32)
for i,(p,a) in enumerate(configs):
    POS[i,:len(p)]=p; AZI[i,:len(a)]=a; MSK[i,:len(p)]=1
POS=torch.tensor(POS,device=dev); AZI=torch.tensor(AZI,device=dev); MSK=torch.tensor(MSK,device=dev)

CHAMP = 60.0
R0, R1, NR = 300.0, 40.0, 24        # on suit le trajet de 300 m jusqu'à 40 m de l'objectif

def expo_axe(theta, idx):
    """exposition cumulée d'une approche en ligne droite depuis l'azimut theta.
    ⟨le poids décroît avec la distance : mesuré, l'orientation décide surtout de loin⟩"""
    r = torch.linspace(R0, R1, NR, device=dev).view(1, NR, 1)
    u = torch.stack([torch.sin(theta), torch.cos(theta)], -1).unsqueeze(1)   # (B,1,2)
    pts = u * r                                                              # (B,NR,2)
    d = POS[idx].unsqueeze(1)                                                # (B,1,DMAX,2)
    v = pts.unsqueeze(2) - d                                                 # (B,NR,DMAX,2)
    dist = v.norm(dim=-1).clamp(min=1.0)
    gis = torch.rad2deg(torch.atan2(v[...,0], v[...,1])) % 360
    ec = ((gis - AZI[idx].unsqueeze(1) + 180) % 360 - 180).abs()
    dans = torch.sigmoid((CHAMP - ec) * 0.5)          # version douce, dérivable
    proche = (1.0 - (dist/400).clamp(0,1))
    m = MSK[idx].unsqueeze(1)
    return ((dans * proche * m).sum(-1) / m.sum(-1).clamp(min=1)).mean(1)

def observer(idx, voit_orientation=True):
    """ce que l'agent voit de la position : chaque défenseur par sa place et son regard"""
    p = POS[idx] / 150.0
    if voit_orientation:
        a = AZI[idx] * math.pi/180
        f = torch.stack([p[...,0], p[...,1], torch.sin(a), torch.cos(a)], -1)
    else:
        z = torch.zeros_like(AZI[idx])
        f = torch.stack([p[...,0], p[...,1], z, z], -1)
    return (f * MSK[idx].unsqueeze(-1)).flatten(1)

DIM = DMAX*4
class Choix(nn.Module):
    """produit un axe, sous forme de vecteur unitaire — pas d'angle brut, qui a une couture"""
    def __init__(s):
        super().__init__()
        s.f = nn.Sequential(nn.Linear(DIM,128), nn.Tanh(), nn.Linear(128,128), nn.Tanh(), nn.Linear(128,2))
    def forward(s, o):
        v = s.f(o)
        return torch.atan2(v[:,0], v[:,1])

ntr = int(len(configs)*0.8)
def entrainer(voit, epoques=600, B=256, nom=""):
    torch.manual_seed(3)
    m = Choix().to(dev); opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    for ep in range(epoques):
        idx = torch.tensor(np.random.randint(0, ntr, B), device=dev)
        perte = expo_axe(m(observer(idx, voit)), idx).mean()
        opt.zero_grad(); perte.backward(); opt.step()
        if ep % 150 == 0: print(f"    {nom} époque {ep:4d}  exposition {perte.item():.4f}", flush=True)
    return m

print("\nentraînement — l'agent VOIT les regards", flush=True)
agent = entrainer(True, nom="voyant")
print("\nentraînement — CONTRÔLE, l'agent NE VOIT PAS les regards", flush=True)
aveugle = entrainer(False, nom="aveugle")

idx_te = torch.tensor(np.arange(ntr, len(configs)), device=dev)
print(f"\névaluation sur {len(idx_te)} positions jamais vues", flush=True)

with torch.no_grad():
    # référence basse : un axe au hasard, moyenné sur 32 tirages
    hasard = torch.stack([expo_axe(torch.rand(len(idx_te), device=dev)*2*math.pi, idx_te)
                          for _ in range(32)]).mean(0)
    # référence haute : le meilleur axe, par balayage exhaustif
    grille = torch.stack([expo_axe(torch.full((len(idx_te),), a, device=dev), idx_te)
                          for a in torch.linspace(0, 2*math.pi, 72, device=dev)])
    meilleur = grille.min(0).values
    pire = grille.max(0).values
    e_agent = expo_axe(agent(observer(idx_te, True)), idx_te)
    e_aveugle = expo_axe(aveugle(observer(idx_te, False)), idx_te)
    AZI_vrai = AZI.clone(); AZI[:] = torch.rand_like(AZI)*360
    e_hasard_or = expo_axe(agent(observer(idx_te, True)), idx_te)
    AZI[:] = AZI_vrai

f = lambda x: x.mean().item()
print(f"\n  {'axe au hasard (référence basse)':38s} exposition {f(hasard):.4f}")
print(f"  {'AGENT VOYANT':38s} exposition {f(e_agent):.4f}")
print(f"  {'agent aveugle (contrôle)':38s} exposition {f(e_aveugle):.4f}")
print(f"  {'agent, regards au hasard (contrôle)':38s} exposition {f(e_hasard_or):.4f}")
print(f"  {'meilleur axe possible (référence haute)':38s} exposition {f(meilleur):.4f}")
print(f"  {'pire axe possible':38s} exposition {f(pire):.4f}")

g_ag = (f(hasard)-f(e_agent))/f(hasard)
g_av = (f(hasard)-f(e_aveugle))/f(hasard)
g_ha = (f(hasard)-f(e_hasard_or))/f(hasard)
g_max = (f(hasard)-f(meilleur))/f(hasard)

print("\n" + "="*74)
print("VERDICT — contre les critères écrits avant\n")
ok1 = g_ag >= 0.25
print(f"  1. l'agent fait {g_ag:.0%} mieux que l'axe moyen (seuil 25 %)  -> {'PASSE' if ok1 else 'ÉCHOUE'}")
ok2 = g_ha < g_ag*0.5
print(f"  2. regards au hasard : son gain tombe à {g_ha:.0%} contre {g_ag:.0%}  -> {'PASSE' if ok2 else 'ÉCHOUE'}")
ok3 = g_av < g_ag*0.5
print(f"  3. agent aveugle : {g_av:.0%} seulement  -> {'PASSE' if ok3 else 'ÉCHOUE'}")
print(f"\n  il capte {g_ag/max(g_max,1e-9):.0%} de ce qu'un choix parfait obtiendrait ({g_max:.0%})")
print()
if ok1 and ok2 and ok3:
    print("  L'AGENT CHOISIT SON AXE.")
    print("  Personne ne lui a dit de contourner. Il lit où l'adversaire regarde et attaque")
    print("  ailleurs — et il perd cet avantage dès qu'on brouille les regards.")
else:
    print("  PAS ENCORE. Voir quel critère a lâché.")

torch.save({'agent': agent.state_dict(), 'dim': DIM, 'dmax': DMAX}, '/mnt/data/corpus/agent_axe.pt')
