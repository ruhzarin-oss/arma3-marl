import torch, sys
from op_gpu import OpGPU, GOALS
GI={g:i for i,g in enumerate(GOALS)}; dev="cuda:0"; N=8192
nu=float(sys.argv[1])
env=OpGPU(num_envs=N,device=dev,seed=7,nu_dps=nu)
g=torch.full((N,4),GI["COMPLEXE"],device=dev)
# 1 suppress + 3 assault, tous vers le complexe
s=torch.ones(N,4,dtype=torch.long,device=dev); s[:,0]=2  # esc0 suppress, 1-3 assault
mil=torch.zeros(N,device=dev); df=torch.zeros(N,dtype=torch.bool,device=dev); pe=torch.zeros(N,device=dev); live=torch.ones(N,dtype=torch.bool,device=dev)
for t in range(260):
    gd=(env.garr<=0)[:,None].expand(N,4)
    s2=torch.where(gd, torch.full((N,4),3,device=dev), s)  # hold après prise
    done,info=env.step(g,s2); nd=done&live
    if nd.any():
        idx=nd.nonzero(as_tuple=True)[0]; mil[idx]=info["mil"][idx].float(); pe[idx]=info["pertes"][idx]; df[idx]=True; live[idx]=False
    if not live.any(): break
print("nu=%.2f COMBINÉ 1supp+3assaut : militaire %.1f%% pertes %.0f%%"%(nu,100*mil[df].mean().item(),100*pe[df].mean().item()))
