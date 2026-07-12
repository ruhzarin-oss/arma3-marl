import argparse, os
from importlib import metadata
from isaaclab.app import AppLauncher
p = argparse.ArgumentParser(); AppLauncher.add_app_launcher_args(p)
a, _ = p.parse_known_args([]); a.headless = True
sim = AppLauncher(a).app
import torch, gymnasium as gym
import isaaclab_tasks  # registers tasks
from isaaclab_tasks.utils import parse_env_cfg, load_cfg_from_registry
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper, handle_deprecated_rsl_rl_cfg, handle_deprecated_rsl_rl_checkpoint
from rsl_rl.runners import OnPolicyRunner
def P(s): print(s, flush=True)
VER = metadata.version("rsl-rl-lib")
TASK = "Isaac-Velocity-Flat-H1-Play-v0"; DEV = "cuda:0"
CKPT = "/home/younes/isaaclab_src/logs/rsl_rl/h1_flat/2026-06-15_16-33-50/model_999.pt"
env_cfg = parse_env_cfg(TASK, device=DEV, num_envs=1)
agent_cfg = load_cfg_from_registry(TASK, "rsl_rl_cfg_entry_point")
agent_cfg = handle_deprecated_rsl_rl_cfg(agent_cfg, VER)
env = gym.make(TASK, cfg=env_cfg)
env = RslRlVecEnvWrapper(env, clip_actions=getattr(agent_cfg, "clip_actions", None))
runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=DEV)
runner.load(handle_deprecated_rsl_rl_checkpoint(CKPT, VER))
policy = runner.get_inference_policy(device=DEV)
P("politique chargée: model_999")
uenv = env.unwrapped
cmd = uenv.command_manager.get_term("base_velocity")
try:
    cmd.cfg.resampling_time_range = (1.0e9, 1.0e9)
except Exception:
    pass
robot = uenv.scene["robot"]
obs = env.get_observations()
if isinstance(obs, tuple):
    obs = obs[0]


def drive(obs, vx, vy, wz, steps, label):
    vs, ws = [], []
    for i in range(steps):
        cmd.vel_command_b[:, 0] = vx; cmd.vel_command_b[:, 1] = vy; cmd.vel_command_b[:, 2] = wz
        with torch.inference_mode():
            act = policy(obs)
        obs = env.step(act)[0]
        vs.append(float(robot.data.root_lin_vel_b[0, 0])); ws.append(float(robot.data.root_ang_vel_b[0, 2]))
    n = min(15, len(vs)); mv = sum(vs[-n:]) / n; mw = sum(ws[-n:]) / n
    P("[%-15s] CMD vx=%.1f wz=%.2f -> REEL vx=%.2f m/s, wz=%.2f rad/s (%.0f deg/s)" % (label, vx, wz, mv, mw, abs(mw) * 57.3))
    return obs


obs = drive(obs, 2.0, 0, 0, 90, "AVANCE @2")
obs = drive(obs, 0, 0, 1.5, 60, "TOURNE @1.5")
obs = drive(obs, 1.5, 0, 1.0, 60, "AVANCE+TOURNE")
obs = drive(obs, 0, 0, 0, 40, "STOP")
P(">>> AVATAR OK — le corps obeit aux commandes externes")
sim.close(); P("FINI")
