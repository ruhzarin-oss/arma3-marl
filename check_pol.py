# teste 3 politiques : doctrine(scriptée via calibrate), zerg-4, et split-2 (2 assault no-supp)
import torch, sys
from op_gpu import OpGPU, GOALS
GI={g:i for i,g in enumerate(GOALS)}; dev="cuda:0"; N=8192
nu=float(sys.argv[1])
def run(nass):
    env=OpGPU(num_envs=N,device=dev,seed=7,nu_dps=nu)
    g=torch.full((N,4),GI["COMPLEXE"],device=dev)
    s=torch.zeros(N,4,dtype=torch.long,device=dev); s[:,:nass]=1  # nass escouades assault, reste move
    mil=torch.zeros(N,device=dev); df=torch.zeros(N,dtype=torch.bool,device=dev); pe=torch.zeros(N,device=dev); live=torch.ones(N,dtype=torch.bool,device=dev)
    for t in range(260):
        s2=torch.where((env.garr<=0)[:,None].expand(N,4), torch.full((N,4),3,device=dev), s)
        done,info=env.step(g,s2); nd=done&live
        if nd.any():
            idx=nd.nonzero(as_tuple=True)[0]; mil[idx]=info["mil"][idx].float(); pe[idx]=info["pertes"][idx]; df[idx]=True; live[idx]=False
        if not live.any(): break
    return 100*mil[df].mean().item(),100*pe[df].mean().item()
for nass in (2,4):
    m,p=run(nass); print("nu=%.2f ASSAUT-NU %d esc : militaire %.1f%% pertes %.0f%%"%(nu,nass,m,p))
