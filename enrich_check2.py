"""Diagnostic enrichissement v2 : avec capture ATTEIGNABLE (secure_n=1, cap_need=3), les nuls s'effondrent-ils
et les captures montent-elles ? Évalue league_maneuver2 dans SON env. Compare au repère ancien league_learner."""
import torch
from torch.distributions import Categorical
from koth_gpu import KothGPU
from train_koth_gpu import Net
DEV = "cuda:0"; N = 4096; T = 200


def run(ckpt, secure_n, cap_need):
    env = KothGPU(num_envs=N, device=DEV, attrition_win=False, secure_n=secure_n, cap_need=cap_need, seed=0)
    net = Net(10, 4, 512, 3).to(DEV); net.load_state_dict(torch.load(ckpt, map_location=DEV)); net.eval()
    ot = list(env.reset()); ah = torch.zeros(4, device=DEV); caps = dec = done_n = 0
    with torch.no_grad():
        for t in range(T):
            acts = []
            for c in range(env.C):
                a = Categorical(logits=net.a_logits(ot[c])).sample(); ah += torch.bincount(a.reshape(-1), minlength=4).float(); acts.append(a)
            ot2, _, done, info = env.step(acts)
            dm = done.bool() if torch.is_tensor(done) else torch.as_tensor(done, device=DEV).bool()
            caps += int(info["secured"].sum()); dec += int(((info["winner"] >= 0) & dm).sum()); done_n += int(dm.sum())
            ot = list(ot2)
    h = ah / ah.sum() * 100
    draws = (done_n - dec) / done_n if done_n else 0
    return h, caps / max(1, done_n), dec, done_n, draws


print("=== ENRICH v2 — capture atteignable (secure_n=1, cap_need=3) ===")
print("%-26s | %-26s | cap/partie | nuls%%" % ("exécuteur", "HOLD/AV/SUP/COUV %"))
for ckpt, sn, cn in (("league_maneuver_learner.pt", 2, 6), ("league_maneuver2_learner.pt", 1, 3)):
    try:
        h, cpg, dec, dn, dr = run(ckpt, sn, cn)
        print("%-26s | %5.1f %5.1f %5.1f %5.1f      |   %.2f     | %4.0f%%" % (ckpt, h[0], h[1], h[2], h[3], cpg, 100 * dr))
    except Exception as e:
        print("%-26s | ERREUR: %s" % (ckpt, e))
print("\nSi league_maneuver2 : nuls << 69%% et cap/partie >> 0.20 -> capture atteignable, maneuver->victoire est un chemin payant.")
