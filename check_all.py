# calibre TOUTES les politiques ensemble (anti one-trajectory). Args: qrf_hp qrf_dps patrol_bite nu_dps
import torch, sys
from op_gpu import OpGPU, GOALS
GI={g:i for i,g in enumerate(GOALS)}; dev="cuda:0"; N=8192
qh,qd,pb,nu=float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4])
def run(stance_vec):  # stance_vec: liste de 4 postures initiales
    env=OpGPU(num_envs=N,device=dev,seed=7,qrf_hp=qh,qrf_dps=qd,patrol_bite=pb,nu_dps=nu)
    g=torch.full((N,4),GI["COMPLEXE"],device=dev)
    s=torch.tensor(stance_vec,device=dev)[None].expand(N,4).contiguous()
    mil=torch.zeros(N,device=dev); df=torch.zeros(N,dtype=torch.bool,device=dev); pe=torch.zeros(N,device=dev); live=torch.ones(N,dtype=torch.bool,device=dev)
    for t in range(260):
        s2=torch.where((env.garr<=0)[:,None].expand(N,4), torch.full((N,4),3,device=dev), s)
        done,info=env.step(g,s2); nd=done&live
        if nd.any():
            idx=nd.nonzero(as_tuple=True)[0]; mil[idx]=info["mil"][idx].float(); pe[idx]=info["pertes"][idx]; df[idx]=True; live[idx]=False
        if not live.any(): break
    return 100*mil[df].mean().item(),100*pe[df].mean().item()
print("qrf_hp=%.0f qrf_dps=%.3f patrol_bite=%.3f nu=%.2f"%(qh,qd,pb,nu))
for name,sv in [("ZERG-4a",[1,1,1,1]),("SPLIT-2a",[1,1,0,0]),("COMBINÉ-1s3a",[2,1,1,1]),("DOUBLE-2s2a",[2,2,1,1])]:
    m,p=run(sv); print("  %-12s : militaire %.1f%% pertes %.0f%%"%(name,m,p))
