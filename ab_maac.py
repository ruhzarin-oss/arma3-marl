import sys; sys.path.insert(0, "/home/younes/arma3-marl")
from train_harmattan import train
base = dict(iters=150, envs=256, rollout=32, hidden=64, lr=3e-4, cas_pen=0.5,
            gamma=0.99, gae=0.95, clip=0.2, epochs=4, minibatches=4, vf=0.5,
            ent=0.01, seed=0, gif=False)
res = {}
for crit in ["concat", "attn"]:
    cfg = dict(base); cfg["critic"] = crit; cfg["heads"] = 4
    print("\n========== CRITIQUE = %s ==========" % crit, flush=True)
    d = train(cfg)
    res[crit] = d
print("\n##### A/B MAAC TERMINE #####", flush=True)
print("AB_DONE", flush=True)
