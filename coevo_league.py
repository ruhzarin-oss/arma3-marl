"""coevo_league — CO-EVOLUTION v2 : LEAGUE (anti-oubli) + env ASYMETRIQUE (assaut vs tenue).

Corrige les 2 pathologies du v1 (coevo_sandbox.py) :
  - OUBLI : au lieu d'entrainer chaque camp contre la SEULE derniere version adverse,
    on l'entraine contre un POOL de TOUTES les versions passees (fictitious self-play / AlphaStar-lite).
    Une parade qui marchait avant ne peut plus etre oubliee : le champion doit battre TOUT le pool.
  - BIAIS DU DERNIER : comme on mesure le winrate contre le pool entier (pas juste le dernier gele),
    plus de saturation 0/1 automatique du dernier qui s'entraine.

Env ASYMETRIQUE (ToyAssault) : camp1=DEFENSEUR depart PROCHE de l'objectif (le tient),
camp0=ATTAQUANT depart LOIN (doit traverser et le prendre). Modele « groupe qui menace un territoire ».

A la fin : matrice de CROSS-EVAL (chaque attaquant-champion vs chaque defenseur-champion)
pour voir si l'echelle MONTE (versions tardives battent les anciennes) ou CYCLE (pierre-papier-ciseaux).
Reutilise TON code : ToySelfPlay, FF (train_mem), ppo_update (train_selfplay).
"""
import time, argparse, json
import numpy as np
import torch
from torch.distributions import Categorical
from toy_selfplay import ToySelfPlay
from train_mem import FF
from train_selfplay import ppo_update

MACROS = ["HOLD", "AVANCER", "SUPPRESSER", "COUVERT"]
RNG = np.random.default_rng(0)


class ToyAssault(ToySelfPlay):
    """Asymetrique : camp1 (DEFENSEUR) tient l'objectif (depart proche), camp0 (ATTAQUANT) assaut de loin."""
    def __init__(self, *a, d_def=60.0, d_att=140.0, **k):
        super().__init__(*a, **k)
        self.d_def = d_def; self.d_att = d_att

    def _reset_rows(self, idx):
        n = len(idx)
        if n == 0:
            return
        A = self.A
        cx = self.rng.uniform(-30, 30, n); cy = self.rng.uniform(-30, 30, n)
        self.ox[idx] = cx; self.oy[idx] = cy
        # ATTAQUANT (0) loin a gauche ; DEFENSEUR (1) proche a droite (tient le terrain)
        self.px[0][idx] = cx[:, None] - self.d_att + (np.arange(A)[None] % 2) * 6
        self.py[0][idx] = cy[:, None] + (np.arange(A)[None] - 1) * 8
        self.px[1][idx] = cx[:, None] + self.d_def - (np.arange(A)[None] % 2) * 6
        self.py[1][idx] = cy[:, None] + (np.arange(A)[None] - 1) * 8
        self.dmg[:, idx] = 0.0; self.supp[:, idx] = 0.0; self.ctrl_time[:, idx] = 0.0
        self.t[idx] = 0
        for s in range(2):
            self.prev_d[s][idx] = self._dist(s, idx)


def snap(net):
    return {k: v.detach().clone() for k, v in net.state_dict().items()}


def _t(x, dev):
    return torch.as_tensor(x, dtype=torch.float32, device=dev)


def train_vs_pool(env, learner, opt, frozen, pool, learner_side, iters, T, cfg, dev):
    """Entraine learner (camp=learner_side) contre des adversaires TIRES du pool. Renvoie (winrate_vs_pool, mix)."""
    o0, o1 = env.reset()
    ot = [_t(o0, dev), _t(o1, dev)]
    N, A, O = ot[0].shape
    wins, decided = [], []
    act_count = np.zeros(4); late = int(0.7 * iters)
    for it in range(iters):
        frozen.load_state_dict(pool[int(RNG.integers(len(pool)))])  # adversaire echantillonne du pool
        buf = dict(obs=torch.zeros(T, N, A, O, device=dev), act=torch.zeros(T, N, A, dtype=torch.long, device=dev),
                   logp=torch.zeros(T, N, A, device=dev), rew=torch.zeros(T, N, device=dev),
                   val=torch.zeros(T, N, device=dev), done=torch.zeros(T, N, device=dev))
        for t in range(T):
            with torch.no_grad():
                dl = Categorical(logits=learner.a_logits(ot[learner_side])); al = dl.sample()
                lpl = dl.log_prob(al); vl = learner.value(ot[learner_side])
                df = Categorical(logits=frozen.a_logits(ot[1 - learner_side])); af = df.sample()
            a = [None, None]; a[learner_side] = al.cpu().numpy(); a[1 - learner_side] = af.cpu().numpy()
            no0, no1, r0, r1, done, info = env.step(a[0], a[1])
            rl = r0 if learner_side == 0 else r1
            buf["obs"][t] = ot[learner_side]; buf["act"][t] = al; buf["logp"][t] = lpl; buf["val"][t] = vl
            buf["rew"][t] = _t(rl, dev); buf["done"][t] = _t(done, dev)
            win_l = info["win0"] if learner_side == 0 else info["win1"]
            for nn in np.where(done)[0]:
                if info["decided"][nn]:
                    wins.append(float(win_l[nn])); decided.append(1.0)
                else:
                    decided.append(0.0)
            if it >= late:
                ac = al.cpu().numpy().reshape(-1)
                for m in range(4):
                    act_count[m] += int((ac == m).sum())
            ot = [_t(no0, dev), _t(no1, dev)]
        with torch.no_grad():
            lv = learner.value(ot[learner_side])
        ppo_update(learner, opt, buf["obs"], buf["act"], buf["logp"], buf["rew"], buf["val"], buf["done"], lv, cfg, dev)
    wr = float(np.mean(wins[-4000:])) if wins else 0.0
    mix = (act_count / max(act_count.sum(), 1.0)).round(3)
    return wr, mix


def eval_vs(env, netA, sideA, netB, iters, T, dev):
    """Joue netA(camp sideA) vs netB SANS entrainer. Renvoie winrate de A sur parties decidees."""
    o0, o1 = env.reset(); ot = [_t(o0, dev), _t(o1, dev)]
    nets = [None, None]; nets[sideA] = netA; nets[1 - sideA] = netB
    wins = []
    for it in range(iters):
        for t in range(T):
            with torch.no_grad():
                a = [None, None]
                for s in (0, 1):
                    a[s] = Categorical(logits=nets[s].a_logits(ot[s])).sample().cpu().numpy()
            no0, no1, r0, r1, done, info = env.step(a[0], a[1])
            winA = info["win0"] if sideA == 0 else info["win1"]
            for nn in np.where(done)[0]:
                if info["decided"][nn]:
                    wins.append(float(winA[nn]))
            ot = [_t(no0, dev), _t(no1, dev)]
    return float(np.mean(wins[-4000:])) if wins else 0.0


def main(rounds=6, seg_iters=120, envs=512, hidden=64, lr=3e-4, T=24,
         hit=0.16, secn=2, seed=0, tag="league"):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    cfg = dict(gamma=0.99, gae=0.95, clip=0.2, epochs=4, vf=0.5, ent=0.01)
    env = ToyAssault(num_envs=envs, hit=hit, secure_n=secn, seed=seed)
    o0, o1 = env.reset(); N, A, O = o0.shape
    att = FF(O, env.n_actions, A, hidden).to(dev); dfn = FF(O, env.n_actions, A, hidden).to(dev)
    fz_a = FF(O, env.n_actions, A, hidden).to(dev); fz_d = FF(O, env.n_actions, A, hidden).to(dev)
    att_opt = torch.optim.Adam(att.parameters(), lr=lr); dfn_opt = torch.optim.Adam(dfn.parameters(), lr=lr)
    pool_att = [snap(att)]; pool_def = [snap(dfn)]  # versions 0 = naives (init aleatoire)
    print("CO-EVOLUTION LEAGUE | dev=%s | N=%d A=%d O=%d | rounds=%d seg_iters=%d" % (dev, N, A, O, rounds, seg_iters), flush=True)
    print("camp0=ATTAQUANT (assaut de loin)  camp1=DEFENSEUR (tient l'objectif)\n", flush=True)
    ladder = []; t0 = time.time()
    for r in range(rounds):
        awr, amix = train_vs_pool(env, att, att_opt, fz_d, pool_def, 0, seg_iters, T, cfg, dev)
        pool_att.append(snap(att))
        dwr, dmix = train_vs_pool(env, dfn, dfn_opt, fz_a, pool_att, 1, seg_iters, T, cfg, dev)
        pool_def.append(snap(dfn))
        ladder.append(dict(round=r, att_wr_vs_pool=round(awr, 3), def_wr_vs_pool=round(dwr, 3),
                           att_mix=amix.tolist(), def_mix=dmix.tolist()))
        print("ROUND %d  (%.0fs)  |pool_att=%d pool_def=%d" % (r, time.time() - t0, len(pool_att), len(pool_def)), flush=True)
        print("  ATT vs POOL defenseurs -> gagne %.2f | macros %s" % (awr, dict(zip(MACROS, amix.tolist()))), flush=True)
        print("  DEF vs POOL attaquants -> gagne %.2f | macros %s\n" % (dwr, dict(zip(MACROS, dmix.tolist()))), flush=True)

    # CROSS-EVAL : att champion i (lignes) vs def champion j (colonnes) — winrate attaquant
    print("=== CROSS-EVAL : winrate ATTAQUANT (ligne=att vN, colonne=def vN) ===", flush=True)
    na = len(pool_att); nd = len(pool_def)
    mat = np.zeros((na, nd))
    for i in range(na):
        fz_a.load_state_dict(pool_att[i])
        for j in range(nd):
            fz_d.load_state_dict(pool_def[j])
            mat[i, j] = eval_vs(env, fz_a, 0, fz_d, 15, T, dev)
    hdr = "       " + " ".join("d%-4d" % j for j in range(nd))
    print(hdr, flush=True)
    for i in range(na):
        print("att%-2d  " % i + " ".join("%-5.2f" % mat[i, j] for j in range(nd)), flush=True)
    # lecture echelle : le dernier defenseur tient-il contre TOUS les attaquants ? (1 - winrate att)
    last_def_hold = float(1.0 - mat[:, -1].mean()); last_att_break = float(mat[-1, :].mean())
    print("\nDEF final tient %.2f en moyenne contre tous les attaquants passes" % last_def_hold, flush=True)
    print("ATT final passe  %.2f en moyenne contre tous les defenseurs passes" % last_att_break, flush=True)

    out = dict(ladder=ladder, cross_eval=mat.round(3).tolist(),
               last_def_hold=round(last_def_hold, 3), last_att_break=round(last_att_break, 3))
    json.dump(out, open("/home/younes/arma3-marl/%s_result.json" % tag, "w"), indent=2)
    torch.save(att.state_dict(), "/home/younes/arma3-marl/%s_att.pt" % tag)
    torch.save(dfn.state_dict(), "/home/younes/arma3-marl/%s_def.pt" % tag)
    print("\n[fini] -> %s_result.json | %s_att.pt / %s_def.pt" % (tag, tag, tag), flush=True)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rounds", type=int, default=6)
    p.add_argument("--seg_iters", type=int, default=120)
    p.add_argument("--envs", type=int, default=512)
    p.add_argument("--tag", type=str, default="league")
    a = p.parse_args()
    main(rounds=a.rounds, seg_iters=a.seg_iters, envs=a.envs, tag=a.tag)
