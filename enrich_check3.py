import torch
from torch.distributions import Categorical
from koth_gpu import KothGPU
from train_koth_gpu import Net
DEV="cuda:0"; N=4096; T=200
env=KothGPU(num_envs=N,device=DEV,attrition_win=False,timeout_decisive=True,seed=0)
net=Net(10,4,512,3).to(DEV); net.load_state_dict(torch.load("league_maneuver3_learner.pt",map_location=DEV)); net.eval()
ot=list(env.reset()); ah=torch.zeros(4,device=DEV); caps=dec=dn=0; wins=torch.zeros(3,device=DEV)
with torch.no_grad():
 for t in range(T):
  acts=[]
  for c in range(env.C):
   a=Categorical(logits=net.a_logits(ot[c])).sample(); ah+=torch.bincount(a.reshape(-1),minlength=4).float(); acts.append(a)
  ot2,_,done,info=env.step(acts); dm=done.bool() if torch.is_tensor(done) else torch.as_tensor(done,device=DEV).bool()
  caps+=int(info["secured"].sum()); w=info["winner"]
  dec+=int(((w>=0)&dm).sum()); dn+=int(dm.sum())
  for c in range(3): wins[c]+=int(((w==c)&dm).sum())
  ot=list(ot2)
h=ah/ah.sum()*100; nuls=(dn-dec)/dn if dn else 0
print("=== ENRICH v3 (no_attrition + timeout_decisive) — league_maneuver3 ===")
print("actions HOLD/AV/SUP/COUV %% : %.1f %.1f %.1f %.1f"%(h[0],h[1],h[2],h[3]))
print("nuls %.0f%% | cap/partie %.2f | wins/camp %s | finies %d"%(100*nuls,caps/max(1,dn),[int(x) for x in wins.tolist()],dn))
print("Cible : nuls << 69%, AV ~20%+, victoires moins concentrées.")
