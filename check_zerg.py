import torch, sys
from op_gpu import OpGPU, GOALS
GI={g:i for i,g in enumerate(GOALS)}; dev="cuda:0"; N=8192
qd,gd_=float(sys.argv[1]),float(sys.argv[2])
env=OpGPU(num_envs=N, device=dev, seed=7, qrf_dps=qd, garr_dps=gd_)
g=torch.full((N,4),GI["COMPLEXE"],device=dev); s=torch.ones(N,4,dtype=torch.long,device=dev)
mil=torch.zeros(N,device=dev); df=torch.zeros(N,dtype=torch.bool,device=dev); pe=torch.zeros(N,device=dev); live=torch.ones(N,dtype=torch.bool,device=dev)
for t in range(260):
    s2=torch.where((env.garr<=0)[:,None].expand(N,4), torch.full((N,4),3,device=dev), s)
    done,info=env.step(g,s2); nd=done&live
    if nd.any():
        idx=nd.nonzero(as_tuple=True)[0]; mil[idx]=info["mil"][idx].float(); pe[idx]=info["pertes"][idx]; df[idx]=True; live[idx]=False
    if not live.any(): break
print("ZERG qrf=%.3f garr=%.3f : militaire %.1f%% pertes %.0f%%"%(qd,gd_,100*mil[df].mean().item(),100*pe[df].mean().item()))
