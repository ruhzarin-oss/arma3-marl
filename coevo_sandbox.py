"""coevo_sandbox — CO-EVOLUTION par MEILLEURE-REPONSE ALTERNEE sur toy_selfplay.

Idee (Younes) : un ATTAQUANT (camp 0) menace un objectif tenu par un DEFENSEUR (camp 1).
A chaque ROUND on GELE un camp et on entraine l'autre a le battre (best-response).
On suit l'ECHELLE de la course aux armements :
  - quand l'attaquant s'entraine contre le defenseur gele -> son taux de victoire monte ;
  - quand on GELE cet attaquant et qu'on entraine le defenseur -> si SON taux remonte,
    c'est qu'il a trouve une PARADE qu'il n'avait pas (= la "nouvelle solution").
On logue aussi le MELANGE de macros (HOLD/AVANCER/SUPPRESSER/COUVERT) de chaque camp
pour VOIR la strategie qui emerge, pas seulement un chiffre.

Reutilise TON code : ToySelfPlay (env), FF (train_mem), ppo_update (train_selfplay).
"""
import time, argparse, json
import numpy as np
import torch
from torch.distributions import Categorical
from toy_selfplay import ToySelfPlay
from train_mem import FF
from train_selfplay import ppo_update

MACROS = ["HOLD", "AVANCER", "SUPPRESSER", "COUVERT"]


def train_segment(env, learn_net, learn_opt, froz_net, learn_side, iters, T, cfg, dev):
    """Entraine learn_net (camp=learn_side) contre froz_net GELE. Renvoie (winrate, melange_macros)."""
    o0, o1 = env.reset()
    ot = [torch.as_tensor(o0, dtype=torch.float32, device=dev),
          torch.as_tensor(o1, dtype=torch.float32, device=dev)]
    N, A, O = ot[0].shape
    wins, decided = [], []
    act_count = np.zeros(4)
    late = int(0.7 * iters)  # ne mesurer la strategie convergee que sur la fin
    for it in range(iters):
        buf = dict(obs=torch.zeros(T, N, A, O, device=dev),
                   act=torch.zeros(T, N, A, dtype=torch.long, device=dev),
                   logp=torch.zeros(T, N, A, device=dev),
                   rew=torch.zeros(T, N, device=dev),
                   val=torch.zeros(T, N, device=dev),
                   done=torch.zeros(T, N, device=dev))
        for t in range(T):
            with torch.no_grad():
                dl = Categorical(logits=learn_net.a_logits(ot[learn_side])); al = dl.sample()
                lpl = dl.log_prob(al); vl = learn_net.value(ot[learn_side])
                df = Categorical(logits=froz_net.a_logits(ot[1 - learn_side])); af = df.sample()
            a = [None, None]
            a[learn_side] = al.cpu().numpy(); a[1 - learn_side] = af.cpu().numpy()
            no0, no1, r0, r1, done, info = env.step(a[0], a[1])
            rl = r0 if learn_side == 0 else r1
            buf["obs"][t] = ot[learn_side]; buf["act"][t] = al; buf["logp"][t] = lpl; buf["val"][t] = vl
            buf["rew"][t] = torch.as_tensor(rl, device=dev); buf["done"][t] = torch.as_tensor(done, device=dev)
            win_l = info["win0"] if learn_side == 0 else info["win1"]
            for n in np.where(done)[0]:
                if info["decided"][n]:
                    wins.append(float(win_l[n])); decided.append(1.0)
                else:
                    decided.append(0.0)
            if it >= late:
                ac = al.cpu().numpy().reshape(-1)
                for m in range(4):
                    act_count[m] += int((ac == m).sum())
            ot = [torch.as_tensor(no0, dtype=torch.float32, device=dev),
                  torch.as_tensor(no1, dtype=torch.float32, device=dev)]
        with torch.no_grad():
            lv = learn_net.value(ot[learn_side])
        ppo_update(learn_net, learn_opt, buf["obs"], buf["act"], buf["logp"],
                   buf["rew"], buf["val"], buf["done"], lv, cfg, dev)
    wr = float(np.mean(wins[-3000:])) if wins else 0.0
    mix = (act_count / max(act_count.sum(), 1.0)).round(3)
    return wr, mix


def main(rounds=6, seg_iters=100, envs=512, hidden=64, lr=3e-4, T=24,
         hit=0.16, secn=2, seed=0, tag="coevo"):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"  # CUDA_VISIBLE_DEVICES epingle le GPU
    cfg = dict(gamma=0.99, gae=0.95, clip=0.2, epochs=4, vf=0.5, ent=0.01)
    env = ToySelfPlay(num_envs=envs, hit=hit, secure_n=secn, seed=seed)
    o0, o1 = env.reset(); N, A, O = o0.shape
    att = FF(O, env.n_actions, A, hidden).to(dev)
    dfn = FF(O, env.n_actions, A, hidden).to(dev)
    att_opt = torch.optim.Adam(att.parameters(), lr=lr)
    dfn_opt = torch.optim.Adam(dfn.parameters(), lr=lr)
    print("CO-EVOLUTION | dev=%s | N=%d A=%d O=%d | rounds=%d seg_iters=%d" % (dev, N, A, O, rounds, seg_iters), flush=True)
    print("camp0=ATTAQUANT (assaut objectif)  camp1=DEFENSEUR (tient l'objectif)\n", flush=True)
    ladder = []
    t0 = time.time()
    for r in range(rounds):
        awr, amix = train_segment(env, att, att_opt, dfn, 0, seg_iters, T, cfg, dev)
        dwr, dmix = train_segment(env, dfn, dfn_opt, att, 1, seg_iters, T, cfg, dev)
        ladder.append(dict(round=r, att_winrate=round(awr, 3), def_winrate=round(dwr, 3),
                           att_mix=amix.tolist(), def_mix=dmix.tolist()))
        amx = dict(zip(MACROS, amix.tolist())); dmx = dict(zip(MACROS, dmix.tolist()))
        print("ROUND %d  (%.0fs)" % (r, time.time() - t0), flush=True)
        print("  ATT s'entraine vs DEF gele -> ATT gagne %.2f | macros %s" % (awr, amx), flush=True)
        print("  puis DEF s'entraine vs cet ATT gele -> DEF gagne %.2f | macros %s" % (dwr, dmx), flush=True)
        print("  -> parade defenseur = %s\n" % ("OUI (%.2f)" % dwr if dwr > 0.5 else "faible (%.2f)" % dwr), flush=True)
    torch.save(att.state_dict(), "/home/younes/arma3-marl/%s_att.pt" % tag)
    torch.save(dfn.state_dict(), "/home/younes/arma3-marl/%s_def.pt" % tag)
    json.dump(ladder, open("/home/younes/arma3-marl/%s_ladder.json" % tag, "w"), indent=2)
    print("[fini] echelle -> %s_ladder.json | poids -> %s_att.pt / %s_def.pt" % (tag, tag, tag), flush=True)
    return ladder


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rounds", type=int, default=6)
    p.add_argument("--seg_iters", type=int, default=100)
    p.add_argument("--envs", type=int, default=512)
    p.add_argument("--tag", type=str, default="coevo")
    a = p.parse_args()
    main(rounds=a.rounds, seg_iters=a.seg_iters, envs=a.envs, tag=a.tag)
