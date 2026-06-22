import sys, json, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
DEV="cpu"; CKPT="/home/younes/compose-embodiment/soldier_shell.pt"; REPLICA="/home/younes/arma3-marl/replica.npz"
sd=torch.load(CKPT,map_location=DEV)
env=AssaultTerrain(num_envs=4,A=1,D=2,relief=40.0,hit=0.10,shell_obs=True,replica=True,replica_path=REPLICA,max_steps=60,device=DEV,seed=0)
net=Net(env.obs_dim,env.n_actions,512,3).to(DEV); net.load_state_dict(sd); net.eval()
obs=env.reset(); caps=[]
for t in range(60):
    with torch.no_grad(): act=net.a_logits(obs).argmax(-1)
    caps.append(int(act[0,0]) if act.dim()>1 else int(act[0]))
    obs,_,_,_=env.step(act)
json.dump(caps, open("/home/younes/compose-embodiment/caps.json","w"))
print("caps generes:", caps)
