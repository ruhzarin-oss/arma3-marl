import sys, torch, json
sys.path.insert(0, "/home/younes/compose-embodiment"); sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
DEV="cuda:0"; A=8; D=12; N=512; T=80
env = AssaultTerrain(num_envs=N, A=A, D=D, device=DEV, seed=20250625, shell_obs=True, team_obs=True,
                     suffer=True, relief=35.0, fire_range=110.0, secure_r=25.0, max_steps=T)
net = Net(env.obs_dim, env.n_actions, 512, 3).to(DEV)
net.load_state_dict(torch.load("/home/younes/compose-embodiment/bounding.pt", map_location=DEV)); net.eval()
obs = env.reset()
APX=[];APY=[];AAL=[];ACT=[];DPX=[];DPY=[];DAL=[]
with torch.no_grad():
    for t in range(T):
        a = net.a_logits(obs).argmax(-1)
        APX.append(env.apx.clone());APY.append(env.apy.clone());AAL.append(env._aalive().clone());ACT.append(a.clone())
        DPX.append(env.dpx.clone());DPY.append(env.dpy.clone());DAL.append(env._dalive().clone())
        obs, rw, done, info = env.step(a, auto_reset=False)
APX=torch.stack(APX);APY=torch.stack(APY);AAL=torch.stack(AAL);ACT=torch.stack(ACT)
DPX=torch.stack(DPX);DPY=torch.stack(DPY);DAL=torch.stack(DAL)        # (T,N,*)
galive=DAL.sum(2)                                                     # (T,N)
victory=(galive==0)
has=victory.any(0); vstep=torch.where(has, victory.float().argmax(0), torch.full((N,),999.0,device=DEV))
idx=torch.arange(N,device=DEV)
vclamp=vstep.clamp(max=T-1).long()
surv=AAL[vclamp, idx].sum(1)                                          # survivants a la victoire
cand=has & (vstep>=14) & (vstep<=58)
score=surv.float() + cand.float()*1000 - (vstep/100.0)               # victoire + max survivants + plutot tot
n=int(score.argmax().item()); vs=int(vstep[n].item()); end=min(vs+3, T)
traj=[]
for t in range(end):
    squad=[[round(APX[t,n,i].item(),1),round(APY[t,n,i].item(),1),int(AAL[t,n,i].item()),int(ACT[t,n,i].item()==9)] for i in range(A)]
    guards=[[round(DPX[t,n,j].item(),1),round(DPY[t,n,j].item(),1),int(DAL[t,n,j].item())] for j in range(D)]
    traj.append({"squad":squad,"guards":guards})
json.dump({"traj":traj,"vstep":vs,"surv":int(AAL[min(vs,T-1),n].sum().item()),"A":A,"D":D}, open("/home/younes/harmattan-dossier/harmattan-figures/bounding_traj.json","w"))
print("VICTOIRE env %d au pas %d | survivants %d/%d | %d frames" % (n, vs, int(AAL[min(vs,T-1),n].sum().item()), A, end))
print("envs avec victoire:", int(has.sum().item()), "/", N)
