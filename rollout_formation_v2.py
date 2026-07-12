"""Rejoue formation_v2.pt sur des transitions forcees (approche -> assaut) et logge positions + phase
(approche/assaut) + point de bascule -> JSON pour animation."""
import sys, json, torch
sys.path.insert(0, "/home/younes/compose-embodiment"); sys.path.insert(0, "/home/younes/arma3-marl")
from formation_env import FormationEnv, NAMES
from train_koth_gpu import Net
DEV = "cpu"
net = Net(11, 9, 512, 3).to(DEV); net.load_state_dict(torch.load("/home/younes/compose-embodiment/formation_v2.pt", map_location=DEV)); net.eval()
PAIRS = [("colonne", "ligne"), ("file", "coin"), ("colonne", "vee")]
out = {"S": 200.0, "formations": []}
for app, ass in PAIRS:
    ai = NAMES.index(app); si = NAMES.index(ass)
    env = FormationEnv(num_envs=1, A=8, device=DEV, seed=ai * 7 + si + 3, transition=True)
    env.reset(); env.fidx[:] = ai; env.fi2[:] = si; obs = env._obs()
    obj = [round(float(env.objx[0]), 1), round(float(env.objy[0]), 1)]; steps = []; phase = []
    for t in range(52):
        steps.append([[round(float(env.apx[0, i]), 1), round(float(env.apy[0, i]), 1)] for i in range(8)])
        phase.append(int(env._curfi()[0].item() == si))
        with torch.no_grad(): a = net.a_logits(obs).argmax(-1)
        obs, rw, done, info = env.step(a); env.fidx[:] = ai; env.fi2[:] = si
        if bool(done[0]): break
    sw = next((i for i, p in enumerate(phase) if p == 1), len(phase))
    out["formations"].append({"name": "%s → %s" % (app.capitalize(), ass), "obj": obj, "steps": steps, "switch": sw})
json.dump(out, open("/home/younes/arma3-marl/formation_v2_rollout.json", "w"))
print("OK " + " ".join("%s:%dpas bascule@%d" % (f["name"], len(f["steps"]), f["switch"]) for f in out["formations"]))
