"""Rejoue formation.pt et logge les vraies trajectoires des 8 agents (grappe -> forme -> avance vers l'objectif)
pour colonne/coin/ligne -> JSON, pour animation."""
import sys, json, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
sys.path.insert(0, "/home/younes/arma3-marl")
from formation_env import FormationEnv, NAMES
from train_koth_gpu import Net
DEV = "cpu"
net = Net(11, 9, 512, 3).to(DEV); net.load_state_dict(torch.load("/home/younes/compose-embodiment/formation.pt", map_location=DEV)); net.eval()
out = {"S": 200.0, "spacing": 9.0, "formations": []}
for fname in ["colonne", "coin", "ligne"]:
    fi = NAMES.index(fname)
    env = FormationEnv(num_envs=1, A=8, device=DEV, seed=fi + 11)
    env.reset(); env.fidx[:] = fi; obs = env._obs()
    obj = [round(float(env.objx[0]), 1), round(float(env.objy[0]), 1)]
    steps = []
    for t in range(48):
        steps.append([[round(float(env.apx[0, i]), 1), round(float(env.apy[0, i]), 1)] for i in range(8)])
        with torch.no_grad(): a = net.a_logits(obs).argmax(-1)
        obs, rw, done, info = env.step(a); env.fidx[:] = fi
        if bool(done[0]): break
    out["formations"].append({"name": fname, "obj": obj, "steps": steps})
json.dump(out, open("/home/younes/arma3-marl/formation_rollout.json", "w"))
print("OK " + " ".join("%s:%d pas" % (f["name"], len(f["steps"])) for f in out["formations"]))
