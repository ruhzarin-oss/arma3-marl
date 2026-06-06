# doctrine (scriptée) + 3 politiques, sur params donnés : garr_dps patrol_bite qrf_hp qrf_dps qrf_var nu
import torch, sys, subprocess
from op_gpu import OpGPU, GOALS
GI={g:i for i,g in enumerate(GOALS)}; dev="cuda:0"; N=8192
gd,pb,qh,qd,qv,nu=[float(x) for x in sys.argv[1:7]]
def run(sv):
    env=OpGPU(num_envs=N,device=dev,seed=7,garr_dps=gd,patrol_bite=pb,qrf_hp=qh,qrf_dps=qd,qrf_var=qv,nu_dps=nu)
    g=torch.full((N,4),GI["COMPLEXE"],device=dev); s=torch.tensor(sv,device=dev)[None].expand(N,4).contiguous()
    mil=torch.zeros(N,device=dev); df=torch.zeros(N,dtype=torch.bool,device=dev); pe=torch.zeros(N,device=dev); live=torch.ones(N,dtype=torch.bool,device=dev)
    for t in range(260):
        s2=torch.where((env.garr<=0)[:,None].expand(N,4), torch.full((N,4),3,device=dev), s)
        done,info=env.step(g,s2); nd=done&live
        if nd.any():
            idx=nd.nonzero(as_tuple=True)[0]; mil[idx]=info["mil"][idx].float(); pe[idx]=info["pertes"][idx]; df[idx]=True; live[idx]=False
        if not live.any(): break
    return 100*mil[df].mean().item(),100*pe[df].mean().item()
print("garr=%.3f patrol=%.3f qrf_hp=%.0f dps=%.3f var=%.2f nu=%.2f"%(gd,pb,qh,qd,qv,nu))
for n,sv in [("COMBINÉ-1s3a",[2,1,1,1]),("ZERG-4a",[1,1,1,1])]:
    m,p=run(sv); print("  %-12s : mil %.1f%% pertes %.0f%%"%(n,m,p))
