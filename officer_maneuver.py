"""officer_maneuver — MANOEUVRES RICHES : l'officier ne choisit plus juste l'axe mais le SCHEMA.
CONCENTRE = toute l'escouade sur le meilleur axe (defile). PINCE = 2 elements sur 2 axes eloignes (>=135 deg)
pour diviser le feu ennemi. Question : choisir le schema SELON la situation bat-il le meilleur schema FIXE ?
On mesure la VALEUR DE SELECTION (oracle : par env, le meilleur des 2 schemas) vs le meilleur schema fixe.
C'est le +14 applique au schema. Zero reentrainement (equipe assault_grid.pt)."""
import math
import torch
from train_koth_gpu import Net
from assault_terrain import AssaultTerrain
import terrain_gpu as TG
from officer_select import exposure_by_bearing
dev = "cuda:0"; K = 8


def kB_far(expo, kA):
    """Meilleur axe a >=135 deg (3 crans) de kA -> le 2e mors de la pince, dans un autre secteur."""
    idx = torch.arange(K, device=dev)
    ang = torch.minimum((idx[None] - kA[:, None]) % K, (kA[:, None] - idx[None]) % K)
    e = expo.clone(); e[ang < 3] = 9.0
    return e.argmin(1)


def place(env, kA, kB):
    """1re moitie de l'escouade au cap kA, 2e moitie au cap kB (kA==kB => concentre). Reset episode."""
    N, A = env.N, env.A; half = A // 2; ar = torch.arange(A, device=dev)
    cap = torch.where(ar[None] < half, kA[:, None], kB[:, None]).float() * 2 * math.pi / K
    sx = env.R_spawn * torch.sin(cap); sy = env.R_spawn * torch.cos(cap)
    off = ((ar % half).float() - (half - 1) / 2) * 6
    env.apx = sx + (ar[None] % 2).float() * 6 - 3
    env.apy = sy + off[None]
    env.admg.zero_(); env.t.zero_(); env.last_supp.zero_(); env._prev_dk.zero_()
    env.ddmg.zero_(); env.dsupp.zero_()   # CRITIQUE : santé + suppression des defenseurs remises a zero (sinon cumul entre tirages)
    env.prev_d = torch.sqrt(env.apx ** 2 + env.apy ** 2).mean(1) / env.scale


def outcome(net, env, steps=60):
    """Un episode par env (auto_reset=False) -> neutralise (N,) et pertes (N,), captures au 1er done."""
    obs = env._obs(); N = env.N
    fin = torch.zeros(N, dtype=torch.bool, device=dev); neut = torch.zeros(N, device=dev); loss = torch.zeros(N, device=dev)
    for _ in range(steps):
        with torch.no_grad():
            a = torch.distributions.Categorical(logits=net.a_logits(obs)).sample()
        obs, _, done, info = env.step(a, auto_reset=False)
        nd = done.bool() & ~fin
        if nd.any():
            neut[nd] = info["neutralized"][nd].float(); loss[nd] = info["losses"][nd]; fin |= nd
    return neut, loss


def rollouts(net, M=1024, R=24, seed=11):
    """M situations distinctes, chacune jouee R fois par schema -> matrices (R,M) de neutralise.
    R tirages = on estime l'ESPERANCE de chaque schema par situation (anti malediction-du-vainqueur)."""
    env = AssaultTerrain(num_envs=M, relief=40.0, hit=0.15, grid_obs=True, device=dev, seed=seed)
    env.reset(); expo = exposure_by_bearing(env); kA = expo.argmin(1); kB = kB_far(expo, kA)
    NC = torch.zeros(R, M, device=dev); NP = torch.zeros(R, M, device=dev)
    LC = torch.zeros(R, M, device=dev); LP = torch.zeros(R, M, device=dev)
    for r in range(R):
        place(env, kA, kA); NC[r], LC[r] = outcome(net, env)     # concentre (terrain inchange, RNG du tir varie)
        place(env, kA, kB); NP[r], LP[r] = outcome(net, env)     # pince
    return NC, NP, LC, LP


if __name__ == "__main__":
    env0 = AssaultTerrain(num_envs=8, relief=40.0, hit=0.15, grid_obs=True, device=dev, seed=0)
    net = Net(env0.obs_dim, env0.n_actions, 256, 3).to(dev)
    net.load_state_dict(torch.load("assault_grid.pt", map_location=dev)); net.eval()
    NC, NP, LC, LP = rollouts(net)
    R = NC.shape[0]; h = R // 2
    pc, pp = NC.mean(0), NP.mean(0)                              # esperance par situation (de-bruitee)
    mc, mp = pc.mean().item(), pp.mean().item(); best_fixed = max(mc, mp)
    # (a) oracle de-bruite : par situation, la meilleure ESPERANCE (plafond, encore un peu optimiste a R fini)
    better = pp > pc; orc = torch.where(better, pp, pc).mean().item()
    # (b) hold-out NON BIAISE : decider le schema sur la 1re moitie des tirages, l'evaluer sur la 2e
    dec = NP[:h].mean(0) > NC[:h].mean(0)
    cap = torch.where(dec, NP[h:].mean(0), NC[h:].mean(0)).mean().item()
    bf_test = max(NC[h:].mean().item(), NP[h:].mean().item())
    print("=" * 72)
    print("MANOEUVRES : choisir le SCHEMA par situation paie-t-il (mesure DE-BRUITEE) ?")
    print("=" * 72)
    print("  CONCENTRE (fixe)        : neutralise %3.0f%% | pertes %3.0f%%" % (100 * mc, 100 * LC.mean()))
    print("  PINCE (fixe)            : neutralise %3.0f%% | pertes %3.0f%%" % (100 * mp, 100 * LP.mean()))
    print("  pince meilleure (esperance) dans %.0f%% des situations" % (100 * better.float().mean()))
    print("  --- valeur de selection du schema ---")
    print("  (a) oracle de-bruite    : %3.0f%%  -> +%.0f pts vs meilleur fixe (plafond)" % (100 * orc, 100 * (orc - best_fixed)))
    print("  (b) HOLD-OUT non biaise : %3.0f%%  -> %+.0f pts vs meilleur fixe (le VRAI gain capturable)" % (100 * cap, 100 * (cap - bf_test)))
    print(">>> %s" % ("CHOISIR LE SCHEMA PAR SITUATION PAIE (gain reel hold-out) -> manoeuvre riche utile"
                      if (cap - bf_test) >= 0.03 else
                      "schema fixe ~ suffit : l axe est le levier dominant, le schema apporte peu une fois le bruit retire"))
    print("MANOEUVRE FINI")
