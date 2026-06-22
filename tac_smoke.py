"""tac_smoke (compo partie A) : charge soldier_shell.pt (+97) et le fait PILOTER dans la sandbox
AssaultTerrain, SANS Isaac, sur CPU. Valide chargement + dims + flux daction (cap/hold/suppress)."""
import sys, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net

DEV = "cpu"
CKPT = "/home/younes/compose-embodiment/soldier_shell.pt"
REPLICA = "/home/younes/arma3-marl/replica.npz"
ACT = ["cap_N","cap_NE","cap_E","cap_SE","cap_S","cap_SW","cap_W","cap_NW","HOLD","SUPPRESS"]

sd = torch.load(CKPT, map_location=DEV)
O_ck = sd["body.0.weight"].shape[1]; NA_ck = sd["pi.weight"].shape[0]
print("[ckpt] obs_dim=%d  n_actions=%d" % (O_ck, NA_ck), flush=True)

env = AssaultTerrain(num_envs=4, A=1, D=2, relief=40.0, hit=0.10, shell_obs=True,
                     replica=True, replica_path=REPLICA, max_steps=60, device=DEV, seed=0)
print("[env ] obs_dim=%d  n_actions=%d" % (env.obs_dim, env.n_actions), flush=True)
assert env.obs_dim == O_ck and env.n_actions == NA_ck, "MISMATCH dims env vs ckpt"

net = Net(env.obs_dim, env.n_actions, 512, 3).to(DEV)
net.load_state_dict(sd); net.eval()
print("[ok  ] soldier_shell.pt charge, dims alignees", flush=True)

obs = env.reset(); neut = loss = nep = 0
print("--- flux daction (env0/agent0) ---", flush=True)
for t in range(40):
    with torch.no_grad():
        act = net.a_logits(obs).argmax(-1)
    obs, rw, done, info = env.step(act)
    a0 = int(act[0, 0]) if act.dim() > 1 else int(act[0])
    if t < 16:
        print("t=%2d  act=%s" % (t, ACT[a0]), flush=True)
    dm = done.bool()
    if dm.any():
        neut += info["neutralized"][dm].float().sum().item()
        loss += info["losses"][dm].sum().item(); nep += int(dm.sum())
print("--- bilan %d episodes : neutralises moy=%.2f  pertes moy=%.2f ---" %
      (nep, neut / max(nep, 1), loss / max(nep, 1)), flush=True)
print("TAC_SMOKE OK", flush=True)
