"""ÉTAPE C.4 (SOLO/éditeur) — arène KotH patiente. Attend que ton aperçu réponde (réessaie le spawn en boucle),
puis pilote les 3 factions avec koth_finetuned.pt et te téléporte sur la colline. Lance-moi, PUIS mets en Preview."""
import glob, os, time, numpy as np, torch
from arma_env_koth import ArmaEnvKoth
from train_koth_gpu import Net
PFX = "/mnt/data/harmattan-sandbox/Steam/steamapps/compatdata/107410/pfx/drive_c/users/steamuser"
RPTDIR = PFX + "/AppData/Local/Arma 3"
MIS = PFX + "/Documents/Arma 3/missions/HarmattanKoth.Altis"

def latest_rpt():
    return sorted(glob.glob(RPTDIR + "/*.rpt"), key=os.path.getmtime)[-1]

LOG = latest_rpt()
print("RPT courant:", os.path.basename(LOG), flush=True)
env = ArmaEnvKoth(num_envs=1, mission=MIS, log=LOG, move=36, max_steps=120, settle=1.0, step_wait=2.6, spawn_settle=7, seed=11)
BR = env.b.bridge
def clear_cmds():
    for f in glob.glob(BR + "/cmd_*.sqf"):
        try: os.remove(f)
        except Exception: pass

print("EN ATTENTE de ton apercu (mets la mission en Preview ; je reessaie le spawn toutes les ~15s)...", flush=True)
obs = None; tries = 0
while obs is None:
    tries += 1
    clear_cmds()
    env.b.log = latest_rpt()  # suit le RPT courant
    try:
        cand = env.reset()
        alive = [int(env._alive(c).sum()) for c in range(3)]
        if sum(alive) > 0:
            obs = cand; print("PONT OK ! vivants BLU/OPF/IND = %d/%d/%d -> bataille !" % tuple(alive), flush=True)
        else:
            print("essai %d : spawn vide, je reessaie..." % tries, flush=True); time.sleep(2)
    except Exception as e:
        print("essai %d : pas encore en jeu (%s), j'attends..." % (tries, type(e).__name__), flush=True); time.sleep(2)

dev = "cuda:0"; net = Net(10, 4, 512, 3).to(dev)
net.load_state_dict(torch.load("/home/younes/arma3-marl/koth_finetuned.pt", map_location=dev)); net.eval()
def act(o):
    with torch.no_grad():
        return torch.distributions.Categorical(logits=net.a_logits(torch.as_tensor(o, dtype=torch.float32, device=dev))).sample().cpu().numpy()
i = 0; caps = 0
while True:
    a = [act(obs[c]) for c in range(3)]
    obs, rew, done, info = env.step(*a); caps += int(info["captured"].sum()); i += 1
    ox, oy = int(env.objx[0]), int(env.objy[0])
    if i % 2 == 0:
        env.b.send('{ if (isPlayer _x && {(_x distance2D [%d,%d]) > 700}) then { _x setPosATL [%d,%d,0]; }; } forEach allUnits;' % (ox, oy, ox, oy + 130), wait=False)
    if i % 4 == 0:
        inz = [int(((((env.px[c]-env.objx[:,None])**2+(env.py[c]-env.objy[:,None])**2) <= env.secure_r**2) & env._alive(c)).sum()) for c in range(3)]
        print("boucle %d | colline=(%d,%d) | zone BLU/OPF/IND=%d/%d/%d | captures %d" % (i, ox, oy, inz[0], inz[1], inz[2], caps), flush=True)
