import sys; sys.path.insert(0, "/home/younes/arma3-marl")
import os, numpy as np, torch
from toy2d import VectorizedToy2D
from train_harmattan import ActorCritic, train
dev = "cuda:0" if torch.cuda.is_available() else "cpu"
O, NACT, TRAIN_A = 11, 5, 5
EVAL_A = [5, 10, 20, 30]
def evaluate(model_pt, critic, eval_A, n_envs=512, max_steps=80):
    net = ActorCritic(O, NACT, TRAIN_A, 64, critic=critic, heads=4)
    net.load_state_dict(torch.load(model_pt, map_location=dev), strict=False)
    net.to(dev).eval()
    g = 12 if eval_A <= 30 else 20
    env = VectorizedToy2D(num_envs=n_envs, n_agents=eval_A, grid=g, seed=999)
    obs = torch.as_tensor(env.reset(), dtype=torch.float32, device=dev)
    succ, cas = [], []; ep_cas = np.zeros(env.N)
    for _ in range(max_steps * 6):
        with torch.no_grad():
            a = net.actor(obs).argmax(-1).cpu().numpy()
        nobs, r, c, done, info = env.step(a); ep_cas += c
        for n in np.where(done)[0]:
            succ.append(float(info["success"][n])); cas.append(ep_cas[n]); ep_cas[n] = 0
        obs = torch.as_tensor(nobs, dtype=torch.float32, device=dev)
        if len(succ) >= 3000: break
    return (float(np.mean(succ)) if succ else float("nan"), float(np.mean(cas)) if cas else float("nan"))
base = dict(iters=200, envs=256, rollout=32, hidden=64, lr=3e-4, cas_pen=0.5, gamma=0.99, gae=0.95,
            clip=0.2, epochs=4, minibatches=4, vf=0.5, ent=0.01, seed=0, gif=False, agents=TRAIN_A)
res = {}
for critic in ["concat", "attn"]:
    cfg = dict(base); cfg["critic"] = critic; cfg["heads"] = 4
    print("\n######### ENTRAINEMENT A=%d critic=%s #########" % (TRAIN_A, critic), flush=True)
    rd = train(cfg); mp = os.path.join(rd, "model.pt")
    res[critic] = {k: evaluate(mp, critic, k) for k in EVAL_A}
print("\n===== TEST DECHELLE : entraine A=%d, joue a 5/10/20/30 (succes / pertes-par-episode) =====" % TRAIN_A, flush=True)
hdr = "critic   | " + " | ".join("A=%-2d" % k for k in EVAL_A)
print(hdr, flush=True)
for critic in ["concat", "attn"]:
    cells = ["%.2f/%.2f" % res[critic][k] for k in EVAL_A]
    print("%-8s | %s" % (critic, " | ".join("%-9s" % c for c in cells)), flush=True)
print("SCALE_DONE", flush=True)
