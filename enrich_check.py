"""Diagnostic d'enrichissement : l'exécuteur entraîné en MODE MANŒUVRE (capture, pas attrition) sait-il
enfin AVANCER et CAPTURER ? Compare répertoire natif (neutre) + capture, ancien (league_learner) vs nouveau
(league_maneuver), tous deux évalués dans l'env manœuvre (attrition_win=False)."""
import torch
from torch.distributions import Categorical
from koth_gpu import KothGPU
from train_koth_gpu import Net
DEV = "cuda:0"; N = 4096; T = 200
PUSH = torch.tensor([-6., 10., -6., -2.], device=DEV)


def run(ckpt, push=False):
    env = KothGPU(num_envs=N, device=DEV, attrition_win=False, seed=0)
    net = Net(10, 4, 512, 3).to(DEV); net.load_state_dict(torch.load(ckpt, map_location=DEV)); net.eval()
    ot = list(env.reset()); ah = torch.zeros(4, device=DEV); caps = 0; dec = 0; done_n = 0
    with torch.no_grad():
        for t in range(T):
            acts = []
            for c in range(env.C):
                lg = net.a_logits(ot[c])
                if push: lg = lg + PUSH
                a = Categorical(logits=lg).sample(); ah += torch.bincount(a.reshape(-1), minlength=4).float(); acts.append(a)
            ot2, _, done, info = env.step(acts)
            dm = done.bool() if torch.is_tensor(done) else torch.as_tensor(done, device=DEV).bool()
            caps += int(info["secured"].sum()); dec += int(((info["winner"] >= 0) & dm).sum()); done_n += int(dm.sum())
            ot = list(ot2)
    h = ah / ah.sum() * 100
    return h, caps, dec, done_n


print("=== ENRICH CHECK (env manœuvre) — AVANCER ressuscité ? ===")
print("%-22s | %-26s | captures | décidées/finies" % ("exécuteur (neutre)", "HOLD/AV/SUP/COUV %"))
for ckpt in ("league_learner.pt", "league_maneuver_learner.pt"):
    try:
        h, caps, dec, dn = run(ckpt, push=False)
        print("%-22s | %5.1f %5.1f %5.1f %5.1f      | %7d  | %d/%d" % (ckpt, h[0], h[1], h[2], h[3], caps, dec, dn))
    except Exception as e:
        print("%-22s | ERREUR: %s" % (ckpt, e))
print("\nLecture : league_maneuver doit montrer AV (AVANCER) BIEN plus haut + captures BIEN plus nombreuses que league_learner.")
print("Si oui -> l'enrichissement a ressuscité la manœuvre -> les postures prendre_colline/focus_leader redeviennent réelles.")
