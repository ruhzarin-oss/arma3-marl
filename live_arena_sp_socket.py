"""ÉTAPE C.4 (SOLO, voie PONT-SOCKET) — identique à live_arena_sp.py MAIS le pont écrit dans
/tmp/hmt_bridge, que la DLL hmt_ext_x64 lit au niveau OS (contourne le gel d'index du client solo).
Prérequis : build_ext.sh passé (DLL en place) + harmattan_actuator_ext.sqf chargé par l'init de la mission.
Lance-moi, PUIS mets la mission en jeu (Preview/host)."""
import glob, os, time, numpy as np, torch
from arma_env_koth import ArmaEnvKoth
from train_koth_gpu import Net
PFX = "/mnt/data/harmattan-sandbox/Steam/steamapps/compatdata/107410/pfx/drive_c/users/steamuser"
RPTDIR = PFX + "/AppData/Local/Arma 3"
MIS = PFX + "/Documents/Arma 3/missions/HarmattanKoth.Altis"
# Le pont = C:\hmt_bridge côté jeu = drive_c du prefixe Proton côté Linux (partagé host<->conteneur)
BRIDGE_TMP = "/mnt/data/harmattan-sandbox/Steam/steamapps/compatdata/107410/pfx/drive_c/hmt_bridge"

def latest_rpt():
    return sorted(glob.glob(RPTDIR + "/*.rpt"), key=os.path.getmtime)[-1]

LOG = latest_rpt()
print("RPT courant:", os.path.basename(LOG), flush=True)
env = ArmaEnvKoth(num_envs=1, n=10, mission=MIS, log=LOG, move=36, max_steps=120, settle=1.0, step_wait=2.8, spawn_settle=10, acc=1.0, seed=11)  # n=20/faction = 60 agents (jouable/filmable)
# Repointage pont-socket : Python écrit dans /tmp/hmt_bridge (lu par la DLL via Z:)
os.makedirs(BRIDGE_TMP, exist_ok=True)
env.b.bridge = BRIDGE_TMP
BR = env.b.bridge
print("PONT-SOCKET : cmd écrites dans", BR, "(DLL lit Z:\\tmp\\hmt_bridge)", flush=True)
def clear_cmds():
    for f in glob.glob(BR + "/cmd_*.sqf"):
        try: os.remove(f)
        except Exception: pass

print("EN ATTENTE de ton jeu (mets la mission en Preview ; je reessaie le spawn toutes les ~15s)...", flush=True)
MORTAL = '{ _x removeAllEventHandlers "HandleDamage" } forEach allUnits;'   # mortalité réelle : retire le plafond 0.85 posé au spawn
obs = None; tries = 0
while obs is None:
    tries += 1
    clear_cmds()
    env.b.log = latest_rpt()
    try:
        cand = env.reset()
        alive = [int(env._alive(c).sum()) for c in range(3)]
        if sum(alive) > 0:
            obs = cand; print("PONT OK ! vivants BLU/OPF/IND = %d/%d/%d -> bataille !" % tuple(alive), flush=True)
            env.b.send(MORTAL, wait=False)   # les balles tuent pour de vrai dès le spawn
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
    try:
        a = [act(obs[c]) for c in range(3)]
        obs, rew, done, info = env.step(*a); caps += int(info["captured"].sum()); i += 1
        if bool(done[0]):                                  # mortalité réelle : pas de résurrection -> respawn complet entre épisodes
            print("épisode fini (capture/temps/anéantissement) -> respawn complet", flush=True)
            obs = env.reset(); env.b.send(MORTAL, wait=False)
            continue
        ox, oy = int(env.objx[0]), int(env.objy[0])
        if i % 2 == 0:
            env.b.send('HMT_OBJ_SP=[%d,%d];' % (ox, oy), wait=False)  # informe la mission de la position de la colline (économie/zone) — plus de téléport forcé
        if i % 4 == 0:
            inz = [int(((((env.px[c]-env.objx[:,None])**2+(env.py[c]-env.objy[:,None])**2) <= env.secure_r**2) & env._alive(c)).sum()) for c in range(3)]
            print("boucle %d | colline=(%d,%d) | zone BLU/OPF/IND=%d/%d/%d | captures %d" % (i, ox, oy, inz[0], inz[1], inz[2], caps), flush=True)
    except TimeoutError:
        print("  (commande non reçue — l'actuateur a peut-être un retard, je réessaie)", flush=True); time.sleep(1)
    except Exception as e:
        print("  (souci passager: %s, je continue)" % type(e).__name__, flush=True); time.sleep(1)
