#!/usr/bin/env python3
"""Le monde que j'ai fabriqué a-t-il seulement un angle mort ?

L'agent va tout droit et s'expose PLUS qu'une ligne droite. Avant d'accuser l'agent, il
faut savoir si le problème a une solution : dans ces configurations défensives, existe-t-il
une direction d'approche moins exposée que les autres ?

  · si l'écart entre le meilleur et le pire secteur est grand -> il y a un angle mort,
    et c'est l'agent qui échoue.
  · s'il est faible -> les défenseurs couvrent tous les azimuts, aucun contournement ne
    paie, et c'est MON MONDE qui est mal posé. L'agent avait raison.

⟨rappel : le banc FIBUA avait certifié que le flanc paie contre une LIGNE défensive orientée.
 Un groupe qui regarde dans toutes les directions n'a pas de flanc.⟩
"""
import numpy as np, math
D='/mnt/data/corpus/tenseurs'
X=np.load(f'{D}/noeuds.npy', mmap_mode='r'); P=np.load(f'{D}/presence.npy', mmap_mode='r')
T,N,_=X.shape
rng=np.random.default_rng(5)
configs=[]
for ti in rng.choice(T, 20000, replace=False):
    xt=np.asarray(X[ti]); pt=np.asarray(P[ti])
    for camp in (0,1):
        s=pt&(xt[:,4]>0.5)&(xt[:,5]==camp)
        if s.sum()<4: continue
        pos=xt[s][:,1:3]; azi=xt[s][:,7]
        c=pos.mean(0); d=np.linalg.norm(pos-c,axis=1); g=d<120
        if g.sum()<4 or g.sum()>12: continue
        configs.append((pos[g]-pos[g].mean(0), azi[g])); break
    if len(configs)>=800: break
print(f"{len(configs)} configurations extraites")

CHAMP=60.0
def expo_secteur(pos, azi, theta, rayon=200.0):
    """exposition d'un point placé à l'azimut theta, à distance rayon de l'objectif"""
    p=np.array([math.sin(math.radians(theta))*rayon, math.cos(math.radians(theta))*rayon])
    v=p-pos
    dist=np.maximum(np.linalg.norm(v,axis=1),1.0)
    gis=np.degrees(np.arctan2(v[:,0],v[:,1]))%360
    ec=np.abs(((gis-azi+180)%360)-180)
    poids=1.0-np.clip(dist/400,0,1)
    return float(((ec<=CHAMP)*poids).sum()/len(pos))

ecarts=[]; disp=[]
for pos,azi in configs:
    e=[expo_secteur(pos,azi,t) for t in range(0,360,10)]
    e=np.array(e)
    if e.max()>0: ecarts.append((e.max()-e.min())/e.max())
    disp.append(e.std()/max(e.mean(),1e-9))
    # dispersion des regards eux-mêmes
ecarts=np.array(ecarts); disp=np.array(disp)
print(f"\nECART entre le MEILLEUR et le PIRE secteur d'approche (36 azimuts testés)")
print(f"  médiane {np.median(ecarts):.0%}   moyenne {ecarts.mean():.0%}")
print(f"  configurations où l'écart dépasse 50 % : {(ecarts>0.5).mean():.0%}")
print(f"  configurations où l'écart dépasse 80 % : {(ecarts>0.8).mean():.0%}")

# les défenseurs regardent-ils dans la même direction ?
conc=[]
for pos,azi in configs:
    r=np.radians(azi)
    conc.append(float(np.hypot(np.cos(r).mean(), np.sin(r).mean())))
conc=np.array(conc)
print(f"\nCONCENTRATION DES REGARDS  (1 = tous dans la même direction, 0 = dispersés)")
print(f"  médiane {np.median(conc):.2f}   moyenne {conc.mean():.2f}")
print(f"  groupes où les regards sont ALIGNÉS (>0,7) : {(conc>0.7).mean():.0%}")
print(f"  groupes où les regards sont DISPERSÉS (<0,3) : {(conc<0.3).mean():.0%}")

print(f"\nLIEN entre concentration des regards et existence d'un angle mort")
for lo,hi in [(0,0.3),(0.3,0.5),(0.5,0.7),(0.7,1.01)]:
    s=(conc>=lo)&(conc<hi)
    if s.sum()<20: continue
    print(f"  regards {lo:.1f}-{hi:.1f}  n={s.sum():4d}   écart meilleur/pire secteur : {ecarts[s[:len(ecarts)]].mean():.0%}")

print()
if np.median(ecarts)<0.35:
    print("-> LE MONDE EST MAL POSÉ. Les défenseurs couvrent tous les azimuts :")
    print("   aucun contournement ne peut payer. L'agent avait raison d'aller tout droit.")
    print("   Il faut sélectionner les configurations qui ONT un angle mort.")
else:
    print("-> IL Y A UN ANGLE MORT à exploiter. C'est l'agent qui échoue, pas le monde.")
