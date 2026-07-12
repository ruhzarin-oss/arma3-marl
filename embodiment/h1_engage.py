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
brain = Net(14, 4, 512, 3).to(DEV)
brain.load_state_dict(torch.load("/home/younes/arma3-marl/koth_lambs_cloned14.pt", map_location=DEV)); brain.eval()
ACT = ["TENIR", "AVANCER", "SUPPRESSER", "COUVERT"]
def yaw_of(q):
    w, x, y, z = [float(v) for v in q]; return math.atan2(2*(w*z+x*y), 1-2*(y*y+z*z))
def wrap(t): return (t + math.pi) % (2*math.pi) - math.pi
SCALE, SIGHT = 110.0, 110.0
OBJ = (0.0, 0.0); EN = (16.0, -28.0)
vpos = [0.0, -70.0]; sup = 0.0; stance = 0.0; enhp = 100.0
def make_obs():
    px, py = vpos; gx, gy = OBJ
    o = [(px-gx)/SCALE, (py-gy)/SCALE, (gx-px)/SCALE, (gy-py)/SCALE, 1.0, 0.0, 0.0]
    ex, ey = EN[0]-px, EN[1]-py; nd = math.hypot(ex, ey); seen = enhp > 0 and nd <= SIGHT
    o += [ex/SCALE if seen else 0.0, ey/SCALE if seen else 0.0, sup, 0.0, stance,
          ex/SCALE if enhp > 0 else 0.0, ey/SCALE if enhp > 0 else 0.0]
    return o
obs = env.get_observations()
if isinstance(obs, tuple): obs = obs[0]
yaw0 = yaw_of(robot.data.root_quat_w[0])
REF = math.atan2(OBJ[1]-vpos[1], OBJ[0]-vpos[0])
def body_heading(vdx, vdy): return wrap(yaw0 + (math.atan2(vdy, vdx) - REF))
P("=== COMBAT INCARNE : perception -> cerveau LAMBS -> CORPS H1 ===")
prev = None
for d in range(80):
    vdo = math.hypot(OBJ[0]-vpos[0], OBJ[1]-vpos[1]); ed = math.hypot(EN[0]-vpos[0], EN[1]-vpos[1])
    if vdo < 6.0: P(">>> OBJECTIF TENU par l avatar (PV ennemi=%.0f)" % enhp); break
    incoming = (enhp/100.0) * max(0.0, 1.4 - 1.9*stance) if (enhp > 0 and ed <= SIGHT) else 0.0
    sup = max(0.0, min(0.95, sup + (0.26*incoming - 0.12)))
    tgt = 1.0 if sup > 0.6 else (0.5 if sup > 0.3 else 0.0)
    stance += max(-0.34, min(0.34, tgt - stance))
    with torch.no_grad():
        act = int(brain.a_logits(torch.tensor([make_obs()], dtype=torch.float32, device=DEV)).argmax(1).item())
    if act == 1:   hx, hy, spd = OBJ[0]-vpos[0], OBJ[1]-vpos[1], 2.0
    elif act == 2: hx, hy, spd = EN[0]-vpos[0], EN[1]-vpos[1], 0.0      # face a l ennemi pour riposter
    elif act == 3: hx, hy, spd = EN[0]-vpos[0], EN[1]-vpos[1], 0.0
    else:          hx, hy, spd = OBJ[0]-vpos[0], OBJ[1]-vpos[1], 0.0
    htgt = body_heading(hx, hy)
    if act != prev:
        P("  d=%2d | dist_obj=%4.1f PV_en=%3.0f sup=%.2f stance=%.2f | DECISION=%-10s (corps: v=%.1f)" % (d, vdo, enhp, sup, stance, ACT[act], spd))
        prev = act
    for _ in range(15):
        cmd.vel_command_b[:, 0] = spd; cmd.vel_command_b[:, 1] = 0.0; cmd.heading_target[:] = htgt
        with torch.inference_mode(): a2 = policy(obs)
        obs = env.step(a2)[0]
    realv = float(robot.data.root_lin_vel_b[0, 0]); realyaw = yaw_of(robot.data.root_quat_w[0])
    facing_err = abs(wrap(htgt - realyaw))
    if act == 2 and enhp > 0 and ed <= SIGHT and facing_err < 0.6:    # riposte SI le corps fait face
        enhp = max(0.0, enhp - 7.0*max(0.25, 1.0-ed/130.0))
    elif act == 1:
        n = vdo + 1e-6; vpos[0] += (OBJ[0]-vpos[0])/n*spd*1.6; vpos[1] += (OBJ[1]-vpos[1])/n*spd*1.6
    if act in (1, 2):
        P("     corps -> v_reelle=%.2f m/s, ecart_de_cap=%.2f rad %s" % (realv, facing_err, "(fait face)" if (act==2 and facing_err<0.6) else ""))
P("PV ennemi final=%.0f" % enhp); P("ENGAGE FINI"); sim.close()
