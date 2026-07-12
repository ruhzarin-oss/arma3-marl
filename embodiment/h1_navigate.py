import argparse, os, math, glob
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
def P(s): print(s, flush=True)
VER = metadata.version("rsl-rl-lib")
TASK = "Isaac-Velocity-Flat-H1-Play-v0"; DEV = "cuda:0"
CKPT = sorted(glob.glob("/home/younes/isaaclab_src/logs/rsl_rl/h1_flat/*/model_999.pt"))[-1]
P("modele : " + CKPT)
env_cfg = parse_env_cfg(TASK, device=DEV, num_envs=1)
agent_cfg = handle_deprecated_rsl_rl_cfg(load_cfg_from_registry(TASK, "rsl_rl_cfg_entry_point"), VER)
env = RslRlVecEnvWrapper(gym.make(TASK, cfg=env_cfg), clip_actions=getattr(agent_cfg, "clip_actions", None))
runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=DEV)
runner.load(handle_deprecated_rsl_rl_checkpoint(CKPT, VER))
policy = runner.get_inference_policy(device=DEV)
uenv = env.unwrapped; cmd = uenv.command_manager.get_term("base_velocity"); robot = uenv.scene["robot"]
try: cmd.cfg.resampling_time_range = (1e9, 1e9)
except Exception: pass
HC = getattr(cmd.cfg, "heading_command", False)
HAS_HT = hasattr(cmd, "heading_target")
P("heading_command=%s | a heading_target=%s" % (HC, HAS_HT))
def yaw_of(q):
    w, x, y, z = [float(v) for v in q]
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
def wrap(a): return (a + math.pi) % (2 * math.pi) - math.pi
obs = env.get_observations()
if isinstance(obs, tuple): obs = obs[0]
p0 = robot.data.root_pos_w[0]; ox, oy = float(p0[0]), float(p0[1])
yaw0 = yaw_of(robot.data.root_quat_w[0])
def bg(fwd, left):
    return (ox + fwd * math.cos(yaw0) - left * math.sin(yaw0),
            oy + fwd * math.sin(yaw0) + left * math.cos(yaw0))
GOALS = [bg(6, 1), bg(10, -4), bg(13, 4), bg(7, 0)]
ok = 0
for gi, (gx, gy) in enumerate(GOALS):
    P("--- objectif %d : (%.1f, %.1f) ---" % (gi + 1, gx, gy))
    reached = False; dist = 99
    for step in range(450):
        pos = robot.data.root_pos_w[0]; px, py = float(pos[0]), float(pos[1])
        yaw = yaw_of(robot.data.root_quat_w[0])
        dx, dy = gx - px, gy - py; dist = math.hypot(dx, dy)
        if dist < 1.0:
            P("  >>> ATTEINT en %d pas (dist %.2f m)" % (step, dist)); reached = True; ok += 1; break
        bearing = math.atan2(dy, dx)
        herr = wrap(bearing - yaw)
        align = max(0.0, math.cos(herr))
        vx = min(2.0, 0.6 * dist + 0.2) * align
        if abs(herr) > 0.6: vx = max(0.4, vx)               # avance min pour ne pas se figer
        cmd.vel_command_b[:, 0] = vx; cmd.vel_command_b[:, 1] = 0.0
        if HC and HAS_HT:
            cmd.heading_target[:] = bearing                 # *** on donne le CAP, la politique tourne ***
        else:
            cmd.vel_command_b[:, 2] = max(-1.5, min(1.5, 2.8 * herr))
        with torch.inference_mode(): act = policy(obs)
        obs = env.step(act)[0]
        wzr = float(robot.data.root_ang_vel_b[0, 2])
        if step % 40 == 0: P("  pas %d: dist=%.1f cap_err=%+.2f wz_obtenu=%+.2f vx=%.2f" % (step, dist, herr, wzr, vx))
    if not reached: P("  NON atteint (dist finale %.2f)" % dist)
P(">>> NAVIGATION : %d/%d objectifs atteints" % (ok, len(GOALS)))
sim.close(); P("FINI")
