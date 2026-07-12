import argparse, math, glob, sys
from importlib import metadata
from isaaclab.app import AppLauncher
p = argparse.ArgumentParser(); AppLauncher.add_app_launcher_args(p)
a, _ = p.parse_known_args([]); a.headless = True
sim = AppLauncher(a).app
import torch, gymnasium as gym
import isaaclab_tasks
from isaaclab_tasks.utils import parse_env_cfg, load_cfg_from_registry
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper, handle_deprecated_rsl_rl_cfg, handle_deprecated_rsl_rl_checkpoint
from rsl_rl.runners import OnPolicyRunner
sys.path.insert(0, "/home/younes/arma3-marl")
from train_koth_gpu import Net
def P(s): print(s, flush=True)
DEV = "cuda:0"; VER = metadata.version("rsl-rl-lib"); TASK = "Isaac-Velocity-Flat-H1-Play-v0"
# --- corps H1 ---
CKPT = sorted(glob.glob("/home/younes/isaaclab_src/logs/rsl_rl/h1_flat/*/model_999.pt"))[-1]
env_cfg = parse_env_cfg(TASK, device=DEV, num_envs=1)
agent_cfg = handle_deprecated_rsl_rl_cfg(load_cfg_from_registry(TASK, "rsl_rl_cfg_entry_point"), VER)
env = RslRlVecEnvWrapper(gym.make(TASK, cfg=env_cfg), clip_actions=getattr(agent_cfg, "clip_actions", None))
runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=DEV)
runner.load(handle_deprecated_rsl_rl_checkpoint(CKPT, VER))
policy = runner.get_inference_policy(device=DEV)
uenv = env.unwrapped; cmd = uenv.command_manager.get_term("base_velocity"); robot = uenv.scene["robot"]
try: cmd.cfg.resampling_time_range = (1e9, 1e9)
except Exception: pass
# --- cerveau distille LAMBS (obs14 -> tactique) ---
brain = Net(14, 4, 512, 3).to(DEV)
brain.load_state_dict(torch.load("/home/younes/arma3-marl/koth_lambs_cloned14.pt", map_location=DEV))
brain.eval()
ACT = ["TENIR", "AVANCER", "SUPPRESSER", "COUVERT"]
def yaw_of(q):
    w, x, y, z = [float(v) for v in q]
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
def wrap(t): return (t + math.pi) % (2 * math.pi) - math.pi
SCALE, SIGHT = 140.0, 110.0
OBJ = (0.0, 0.0)
vpos = [0.0, -70.0]                       # agent virtuel, 70 m au sud de l objectif
enemy = None
def make_obs(sup):
    px, py = vpos; gx, gy = OBJ
    o = [(px-gx)/SCALE, (py-gy)/SCALE, (gx-px)/SCALE, (gy-py)/SCALE, 1.0, 0.0, 0.0]
    if enemy is not None:
        ex, ey = enemy[0]-px, enemy[1]-py; nd = math.hypot(ex, ey)
        vis = (ex/SCALE, ey/SCALE) if nd <= SIGHT else (0.0, 0.0)
        o += [vis[0], vis[1], sup, 0.0, 0.0, ex/SCALE, ey/SCALE]
    else:
        o += [0.0, 0.0, sup, 0.0, 0.0, 0.0, 0.0]
    return o
obs = env.get_observations()
if isinstance(obs, tuple): obs = obs[0]
yaw0 = yaw_of(robot.data.root_quat_w[0])
REF = math.atan2(OBJ[1]-vpos[1], OBJ[0]-vpos[0])     # cap virtuel initial vers l objectif
def body_heading(vdx, vdy): return wrap(yaw0 + (math.atan2(vdy, vdx) - REF))
P("=== PAS 3 : perception(obs14) -> cerveau LAMBS -> corps H1 ===")
P("objectif a 70 m. avatar avance. ennemi surgira a mi-chemin.")
prev = None
for d in range(60):
    vd = math.hypot(OBJ[0]-vpos[0], OBJ[1]-vpos[1])
    if vd < 4.0: P(">>> OBJECTIF ATTEINT (monde virtuel)"); break
    if enemy is None and vd < 40.0:
        enemy = (22.0, -28.0); P("  ! ENNEMI repere a ~%.0f m, l avatar passe sous le feu" % math.hypot(enemy[0]-vpos[0], enemy[1]-vpos[1]))
    sup = 0.0
    if enemy is not None:
        ed = math.hypot(enemy[0]-vpos[0], enemy[1]-vpos[1])
        sup = max(0.0, min(0.9, (100.0-ed)/100.0 + 0.3))
    with torch.no_grad():
        act = int(brain.a_logits(torch.tensor([make_obs(sup)], dtype=torch.float32, device=DEV)).argmax(1).item())
    # tactique -> cap + vitesse du corps
    if act == 1:   hx, hy, spd = OBJ[0]-vpos[0], OBJ[1]-vpos[1], 2.0      # avancer
    elif act == 2 and enemy is not None: hx, hy, spd = enemy[0]-vpos[0], enemy[1]-vpos[1], 0.0   # suppresser : face ennemi
    elif act == 3: hx, hy, spd = OBJ[0]-vpos[0], OBJ[1]-vpos[1], 0.7      # couvert : progresse prudemment
    else:          hx, hy, spd = OBJ[0]-vpos[0], OBJ[1]-vpos[1], 0.0      # tenir
    htgt = body_heading(hx, hy)
    if act != prev:
        P("  d=%2d | dist_obj=%4.1fm sup=%.2f | DECISION=%-10s -> corps: vitesse=%.1f cap=%+.2f" % (d, vd, sup, ACT[act], spd, htgt))
        prev = act
    # executer sur le corps (constant pendant ~20 pas physiques)
    for _ in range(20):
        cmd.vel_command_b[:, 0] = spd; cmd.vel_command_b[:, 1] = 0.0; cmd.heading_target[:] = htgt
        with torch.inference_mode(): a2 = policy(obs)
        obs = env.step(a2)[0]
    realv = float(robot.data.root_lin_vel_b[0, 0])
    # avancer le monde virtuel selon la decision
    n = math.hypot(hx, hy) + 1e-6
    vpos[0] += (hx/n)*spd*0.8; vpos[1] += (hy/n)*spd*0.8
P("corps reel : vitesse avant finale = %.2f m/s" % float(robot.data.root_lin_vel_b[0, 0]))
P("PERCEIVE FINI")
sim.close()
