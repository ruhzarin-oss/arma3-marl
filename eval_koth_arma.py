"""eval_koth_arma — ÉVAL A/B en Arma KOTH d'un cerveau (frozen) contre une RÉFÉRENCE FIXE.
Le cerveau testé pilote le CAMP 0 ; la référence (identique pour tous les bras) pilote les camps 1 et 2.
Même env (brouillard via sight), mêmes serveurs, mêmes seeds -> le taux de victoire camp 0 est comparable
entre bras A et B. Réutilise MultiKoth (16 serveurs ArmaEnvKoth threadés). Suppose les serveurs DÉJÀ bootés.
Sortie : JSON {winrate, capture_rate, pertes_moy, n_decided, n_done}."""
import argparse, json, time
import numpy as np
import torch
from torch.distributions import Categorical
from train_koth_gpu import Net
from train_koth_finetune import MultiKoth

DEV = "cuda:0"


def load(path, O, NA, hidden=512, layers=3):
    net = Net(O, NA, hidden, layers).to(DEV)
    net.load_state_dict(torch.load(path, map_location=DEV)); net.eval()
    return net


def act(net, o):
    with torch.no_grad():
        return Categorical(logits=net.a_logits(torch.as_tensor(o, dtype=torch.float32, device=DEV))).sample().cpu().numpy()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--brain", required=True)                 # cerveau testé (camp 0)
    p.add_argument("--ref", required=True)                   # référence fixe (camps 1,2)
    p.add_argument("--servers", type=int, default=16)
    p.add_argument("--per_server", type=int, default=3)
    p.add_argument("--steps", type=int, default=450)         # pas de jeu (auto-reset -> ~plusieurs parties/env)
    p.add_argument("--max_steps", type=int, default=90)      # durée max d'une partie KOTH (capture sinon timeout-contrôle)
    p.add_argument("--move", type=int, default=40)
    p.add_argument("--out", default="ab_eval.json")
    p.add_argument("--label", default="brain")
    a = p.parse_args()

    env = MultiKoth(num_servers=a.servers, per_server=a.per_server, move=a.move, max_steps=a.max_steps)
    O, NA = env.obs_dim, env.n_actions
    brain = load(a.brain, O, NA); ref = load(a.ref, O, NA)
    print("[eval %s] env prêt N=%d O=%d | brain=%s vs ref=%s" % (a.label, env.N, O, a.brain, a.ref), flush=True)

    ot = list(env.reset())
    n_done = n_dec = n_win0 = 0; caps = 0; pertes = []; t0 = time.time()
    for t in range(a.steps):
        a0 = act(brain, ot[0]); a1 = act(ref, ot[1]); a2 = act(ref, ot[2])
        ot2, rew, done, info = env.step([a0, a1, a2])
        dm = done.astype(bool); dec = info["decided"].astype(bool)
        n_done += int(dm.sum()); n_dec += int((dec & dm).sum())
        n_win0 += int(((info["winner"] == 0) & dm & dec).sum())
        caps += int(info["captured"].sum())
        ot = list(ot2)
        if t % 20 == 0:
            wr = n_win0 / n_dec if n_dec else 0.0
            print("[eval %s] t%03d | done %d | decided %d | win0 %d | winrate %.3f | %.1fs"
                  % (a.label, t, n_done, n_dec, n_win0, wr, time.time() - t0), flush=True)

    winrate = n_win0 / n_dec if n_dec else 0.0
    res = {"label": a.label, "brain": a.brain, "ref": a.ref, "winrate_camp0": winrate,
           "n_decided": n_dec, "n_done": n_done, "captures": caps, "steps": a.steps,
           "servers": a.servers, "per_server": a.per_server}
    with open(a.out, "w") as f: json.dump(res, f, indent=2)
    print("[eval %s] FINI | winrate_camp0 = %.3f sur %d parties décidées -> %s" % (a.label, winrate, n_dec, a.out), flush=True)


if __name__ == "__main__":
    main()
