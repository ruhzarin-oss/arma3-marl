"""M1 — A vs B : la règle de coalition (oracle) réduit-elle le RUNAWAY ?
A = pas d'officier (tout neutre). B = oracle : dans chaque partie, le LEADER courant joue 'defendre',
les autres 'presser'. Métrique anti-runaway = parmi les parties décidées, le LEADER PRÉCOCE (à K pas)
finit-il par gagner ? runaway_rate bas = la coalition rattrape le leader = officer utile.
Exécuteurs GELÉS (league_learner.pt). Symétrie des 3 camps -> on NE regarde PAS la part de victoire (moot)."""
import torch
from torch.distributions import Categorical
from koth_gpu import KothGPU
from train_koth_gpu import Net

DEV = "cuda:0"; N = 4096; T = 300; K_EARLY = 8
DEFEND = torch.tensor([4., -8., 0., 3.], device=DEV)
PRESS  = torch.tensor([-2., 1., 3., -1.], device=DEV)
NEUTRE = torch.tensor([0., 0., 0., 0.], device=DEV)

net = Net(10, 4, 512, 3).to(DEV)
net.load_state_dict(torch.load("league_learner.pt", map_location=DEV)); net.eval()


def leader_of(env):
    return torch.stack([env.ctrl_time[c] for c in range(env.C)], 0).argmax(0)   # (N,)


def run(mode):
    env = KothGPU(num_envs=N, device=DEV, seed=0)
    ot = list(env.reset())
    early = torch.full((N,), -1, device=DEV, dtype=torch.long)
    runaway = 0; overturned = 0; glen_sum = 0; glen_n = 0
    wins = torch.zeros(env.C, device=DEV)
    with torch.no_grad():
        for t in range(T):
            lead = leader_of(env)
            acts = []
            for c in range(env.C):
                lg = net.a_logits(ot[c])
                if mode == "B":
                    b = torch.where((lead == c).unsqueeze(-1), DEFEND, PRESS)   # (N,4)
                    lg = lg + b.unsqueeze(1)                                    # broadcast sur les A unités
                acts.append(Categorical(logits=lg).sample())
            tlen = env.t.clone()                                                # longueur de partie avant step
            ot2, _, done, info = env.step(acts)
            dm = done.bool() if torch.is_tensor(done) else torch.as_tensor(done, device=DEV).bool()
            w = info["winner"]
            # fixe le leader précoce quand la partie atteint K_EARLY
            newly = (env.t == K_EARLY) & (early < 0)
            early = torch.where(newly, lead, early)
            # comptage à la décision
            dec = (w >= 0) & dm & (early >= 0)
            runaway += int(((w == early) & dec).sum())
            overturned += int(((w != early) & dec).sum())
            for c in range(env.C): wins[c] += int(((w == c) & dm).sum())
            glen_sum += int((tlen[dm]).sum()); glen_n += int(dm.sum())
            early = torch.where(dm, torch.full_like(early, -1), early)          # reset tracker sur parties finies
            ot = list(ot2)
    dec_tot = runaway + overturned
    rr = runaway / dec_tot if dec_tot else 0.0
    return {"mode": mode, "runaway_rate": rr, "decided": dec_tot,
            "glen": glen_sum / glen_n if glen_n else 0, "wins": [int(x) for x in wins.tolist()]}


for mode in ("A", "B"):
    r = run(mode)
    tag = "A (pas d'officier)" if mode == "A" else "B (oracle coalition)"
    print("%-22s | runaway=%.3f (leader précoce gagne) | parties décidées=%d | durée moy=%.1f | wins/camp=%s"
          % (tag, r["runaway_rate"], r["decided"], r["glen"], r["wins"]))
print("\nLecture : runaway PLUS BAS en B = la règle de coalition rattrape le leader = levier officier UTILE.")
