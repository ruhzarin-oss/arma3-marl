"""calibrate_op_gpu — valide le SIM OPÉRATIONNEL : la partition SCRIPTÉE (chef d'op HARMATTAN-2, MACHINE À
PHASES explicite comme run_op) rejouée dans op_gpu doit reproduire la baseline Arma P-v3b (38 % / 72 %).
Si écart, on ajuste les constantes physiques (une à la fois). PUIS le sim entraîne le manager."""
import argparse, torch
from op_gpu import OpGPU, GOALS

p = argparse.ArgumentParser()
p.add_argument("--envs", type=int, default=8192); p.add_argument("--steps", type=int, default=300)
for k, d in [("patrol_bite", 0.010), ("garr_dps", 0.024), ("assault_dmg", 0.16),
             ("qrf_dps", 0.120), ("move_speed", 14.0), ("nu_dps", 0.08)]:
    p.add_argument("--" + k, type=float, default=d)
a = p.parse_args()
dev = "cuda:0"
env = OpGPU(num_envs=a.envs, device=dev, seed=0, patrol_bite=a.patrol_bite, garr_dps=a.garr_dps,
            assault_dmg=a.assault_dmg, qrf_dps=a.qrf_dps, move_speed=a.move_speed, nu_dps=a.nu_dps, max_steps=a.steps)
N, S = env.N, env.S
GI = {g: i for i, g in enumerate(GOALS)}
def gi(name): return torch.tensor(GI[name], device=dev)

# phases : 0 INFIL, 1 MEP, 2 ASSAUT, 3 RENFORCÉ, 4 CONSOL, 5 EXFIL — compteur par env
phase = torch.zeros(N, dtype=torch.long, device=dev)
pstep = torch.zeros(N, dtype=torch.long, device=dev)
BUDGET = torch.tensor([210, 135, 0, 0, 70, 195], device=dev)   # budgets de phase (run_op v3b ; assaut piloté par contact)


def scripted(env, phase):
    goals = torch.zeros(N, S, dtype=torch.long, device=dev)
    st = torch.zeros(N, S, dtype=torch.long, device=dev)
    P = phase[:, None].expand(N, S)
    # objectifs par phase et par escouade
    # INFIL (0) : appui->CRETE, AO->ATTENTE, AE->ATTENTE_E, RES->POSTE_RES, tous en MOVE
    G_infil = torch.tensor([GI["CRETE"], GI["ATTENTE"], GI["ATTENTE_E"], GI["POSTE_RES"]], device=dev)
    G_mep = torch.tensor([GI["CRETE"], GI["LIGNE_O"], GI["LIGNE_E"], GI["POSTE_RES"]], device=dev)
    G_cx = torch.tensor([GI["COMPLEXE"]] * 4, device=dev)
    G_lz = torch.tensor([GI["LZ"]] * 4, device=dev)
    goals = torch.where(P == 0, G_infil[None], goals)
    st = torch.where(P == 0, torch.zeros_like(st), st)                       # move
    goals = torch.where(P == 1, G_mep[None], goals)
    st = torch.where(P == 1, torch.tensor([3, 0, 0, 3], device=dev)[None], st)  # appui hold, assaut move, res hold
    # ASSAUT (2) : appui suppress, AO/AE assault, RES hold
    goals = torch.where(P == 2, G_cx[None], goals)
    st = torch.where(P == 2, torch.tensor([2, 1, 1, 3], device=dev)[None], st)
    # RENFORCÉ (3) : réserve engage aussi
    goals = torch.where(P == 3, G_cx[None], goals)
    st = torch.where(P == 3, torch.tensor([2, 1, 1, 1], device=dev)[None], st)
    # CONSOL (4) : tous hold au complexe
    goals = torch.where(P == 4, G_cx[None], goals)
    st = torch.where(P == 4, torch.tensor([3, 3, 3, 3], device=dev)[None], st)
    # EXFIL (5) : tous vers LZ en move
    goals = torch.where(P == 5, G_lz[None], goals)
    st = torch.where(P == 5, torch.zeros_like(st), st)
    return goals, st


def advance_phase(env, phase, pstep):
    """Transitions : conditions d'arrivée OU budget de phase épuisé (comme les contingences run_op)."""
    d_cx = (env.spos - env.COMPLEXE[None, None]).norm(dim=-1)                 # (N,S)
    d_crete = (env.spos[:, 0] - env.goalP[GI["CRETE"]]).norm(dim=-1)
    d_att = (env.spos[:, 1] - env.goalP[GI["ATTENTE"]]).norm(dim=-1)
    d_atte = (env.spos[:, 2] - env.goalP[GI["ATTENTE_E"]]).norm(dim=-1)
    d_lo = (env.spos[:, 1] - env.goalP[GI["LIGNE_O"]]).norm(dim=-1)
    d_le = (env.spos[:, 2] - env.goalP[GI["LIGNE_E"]]).norm(dim=-1)
    d_lz = (env.spos - env.LZ[None, None]).norm(dim=-1)
    al = env.alive_squads()
    garr_down = env.garr <= 0
    budget_up = pstep >= BUDGET[phase]
    nxt = phase.clone()
    # INFIL -> MEP : 3 escouades arrivées OU budget
    arr_infil = (d_crete < 90) & (d_att < 90) & (d_atte < 90)
    nxt = torch.where((phase == 0) & (arr_infil | budget_up), phase + 1, nxt)
    # MEP -> ASSAUT : les 2 assauts sur leur ligne OU budget
    arr_mep = (d_lo < 90) & (d_le < 90)
    nxt = torch.where((phase == 1) & (arr_mep | budget_up), phase + 1, nxt)
    # ASSAUT -> RENFORCÉ : pertes >25 % (engage réserve) ; -> CONSOL si garnison déjà tombée
    pertes = 1 - env.force_frac()
    nxt = torch.where((phase == 2) & garr_down, torch.tensor(4, device=dev), nxt)
    nxt = torch.where((phase == 2) & ~garr_down & (pertes > 0.25), torch.tensor(3, device=dev), nxt)
    # RENFORCÉ -> CONSOL : garnison tombée
    nxt = torch.where((phase == 3) & garr_down, torch.tensor(4, device=dev), nxt)
    # CONSOL -> EXFIL : tenue 12 pas OU budget
    nxt = torch.where((phase == 4) & ((env.consol_t >= 12) | budget_up), torch.tensor(5, device=dev), nxt)
    # garde-fou : assaut/renforcé enlisés (budget large) -> exfil
    nxt = torch.where(((phase == 2) | (phase == 3)) & (pstep >= 220), torch.tensor(5, device=dev), nxt)
    changed = nxt != phase
    pstep = torch.where(changed, torch.zeros_like(pstep), pstep + 1)
    return nxt, pstep


succ = mil = consol = qrf = pert = ndone = torch.zeros((), device=dev)
acc = {k: torch.zeros((), device=dev) for k in ("succ", "mil", "consol", "qrf", "pert", "n")}
live = torch.ones(N, dtype=torch.bool, device=dev)
for t in range(a.steps):
    g, s = scripted(env, phase)
    done, info = env.step(g, s)
    phase, pstep = advance_phase(env, phase, pstep)
    fin = done & live
    if fin.any():
        idx = fin.nonzero(as_tuple=True)[0]
        acc["succ"] += info["succ_strict"][idx].float().sum(); acc["mil"] += info["mil"][idx].float().sum()
        acc["consol"] += info["consol"][idx].float().sum(); acc["qrf"] += info["qrf_faced"][idx].float().sum()
        acc["pert"] += info["pertes"][idx].sum(); acc["n"] += idx.numel(); live[idx] = False
    if not live.any(): break
n = acc["n"].item() or 1
print("=== SIM OP — partition SCRIPTÉE (n=%d) === [cibles Arma P-v3b : strict 38%%, mil 72%%, consol 62%%]" % acc["n"].item())
print("strict %.1f%% | militaire %.1f%% | consolidation %.1f%% | QRF affrontée %.1f%% | pertes %.0f%%"
      % (100*acc["succ"].item()/n, 100*acc["mil"].item()/n, 100*acc["consol"].item()/n,
         100*acc["qrf"].item()/n, 100*acc["pert"].item()/n))
