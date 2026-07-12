"""officer_synth — SYNTHESE : l'officier choisit AXE + SCHEMA. Question honnete d'abord : le gain du schema (+6)
est-il PREVISIBLE depuis la carte ? Feature a priori : gap = expo(2e mors pince) - expo(meilleur axe).
Petit gap -> pince (2 axes surs, on divise le feu) ; gros gap -> concentre (le 2e mors mourrait).
On apprend le SEUIL sur une moitie des situations, on l'evalue sur l'autre (de-bruite). Si la regle-carte
capture du gain -> le LLM peut choisir le schema depuis la carte. Sinon : l'axe se capture (+10), pas le schema."""
import math
import torch
import terrain_gpu as TG
from train_koth_gpu import Net
from assault_terrain import AssaultTerrain
from officer_select import exposure_by_bearing
from officer_maneuver import kB_far, place, outcome
dev = "cuda:0"; K = 8


def coverage(env, kb):
    """(M,D) : le defenseur d a-t-il une LOS sur l'axe d'approche kb (quelque part le long du trajet) ?"""
    M = env.N; ts = torch.linspace(0, 1, 10, device=dev)
    th = kb.float() * 2 * math.pi / K; sx = env.R_spawn * torch.sin(th); sy = env.R_spawn * torch.cos(th)
    px = sx[:, None] * (1 - ts)[None]; py = sy[:, None] * (1 - ts)[None]  # (M,10)
    cov = torch.zeros(M, env.D, device=dev)
    for di in range(env.D):
        bx = env.dpx[:, di:di + 1].expand(M, 10); by = env.dpy[:, di:di + 1].expand(M, 10)
        cov[:, di] = TG.los_clear(env.hm, px, py, bx, by, env.terr_R).max(1).values
    return cov


def collect(net, M=2048, R=24, seed=13):
    env = AssaultTerrain(num_envs=M, relief=40.0, hit=0.15, grid_obs=True, device=dev, seed=seed)
    env.reset(); expo = exposure_by_bearing(env); kA = expo.argmin(1); kB = kB_far(expo, kA)
    eA = expo.gather(1, kA[:, None])[:, 0]; eB = expo.gather(1, kB[:, None])[:, 0]
    gap = eB - eA  # feature 1 : de combien le 2e mors est plus expose que le meilleur axe
    cA = coverage(env, kA); cB = coverage(env, kB)
    overlap = (cA * cB).sum(1) / (cA + cB - cA * cB).sum(1).clamp(min=1e-6)  # feature 2 : Jaccard des fusils couvrant les 2 mors
    NC = torch.zeros(R, M, device=dev); NP = torch.zeros(R, M, device=dev)
    for r in range(R):
        place(env, kA, kA); NC[r], _ = outcome(net, env)   # concentre
        place(env, kA, kB); NP[r], _ = outcome(net, env)   # pince
    return NC.mean(0), NP.mean(0), gap, overlap  # esperances de-bruitees + 2 features de la carte


if __name__ == "__main__":
    env0 = AssaultTerrain(num_envs=8, relief=40.0, hit=0.15, grid_obs=True, device=dev, seed=0)
    net = Net(env0.obs_dim, env0.n_actions, 256, 3).to(dev)
    net.load_state_dict(torch.load("assault_grid.pt", map_location=dev)); net.eval()
    pc, pp, gap, overlap = collect(net)
    M = pc.shape[0]; h = M // 2
    adv = pp - pc                                   # avantage pince par situation
    bf = max(pc[h:].mean().item(), pp[h:].mean().item())                  # meilleur schema fixe (test)
    orc = torch.maximum(pc[h:], pp[h:]).mean().item()                     # plafond oracle (test)
    print("=" * 72)
    print("SYNTHESE : le SCHEMA est-il choisissable depuis la CARTE ? (axe=meilleur, on varie le schema)")
    print("=" * 72)
    print("  meilleur schema FIXE (test) : %3.0f%%   |   plafond oracle : %3.0f%% (+%.0f)" % (100 * bf, 100 * orc, 100 * (orc - bf)))
    for name, feat, lo_is_pince in [("gap exposition", gap, True), ("recouvrement fusils", overlap, True)]:
        corr = torch.corrcoef(torch.stack([feat, adv]))[0, 1].item()
        ftr, pctr, pptr = feat[:h], pc[:h], pp[:h]
        best_thr, best_val = 0.0, -1.0
        for thr in torch.linspace(feat.min().item(), feat.max().item(), 31).tolist():
            pick = (ftr < thr) if lo_is_pince else (ftr > thr)
            v = torch.where(pick, pptr, pctr).mean().item()
            if v > best_val:
                best_val, best_thr = v, thr
        fte = feat[h:]; pick = (fte < best_thr) if lo_is_pince else (fte > best_thr)
        rule = torch.where(pick, pp[h:], pc[h:]).mean().item()
        print("  feature [%-20s] corr=%+.2f  seuil=%.2f  -> officier carte %3.0f%% = %+.0f pts vs fixe"
              % (name, corr, best_thr, 100 * rule, 100 * (rule - bf)))
    print(">>> regarde si une feature capture >= +3 pts ; sinon le schema n'est pas (encore) lisible sur la carte")
    print("SYNTH FINI")
