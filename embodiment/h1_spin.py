import argparse, math, glob
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
obs = env.get_observations()
if isinstance(obs, tuple): obs = obs[0]
def run(label, vx, wz, n=120):
    vals = []
    for k in range(n):
        cmd.vel_command_b[:, 0] = vx; cmd.vel_command_b[:, 1] = 0.0; cmd.vel_command_b[:, 2] = wz
        with torch.inference_mode(): act = policy(obs)
        o = env.step(act)[0]
        globals()["obs"] = o
        wzr = float(robot.data.root_ang_vel_b[0, 2]); vxr = float(robot.data.root_lin_vel_b[0, 0])
        c2 = float(cmd.command[0, 2])
        if k % 20 == 0: P("  %s k=%3d : cmd_obs_wz=%+.2f wz_obtenu=%+.2f vx_obtenu=%+.2f" % (label, k, c2, wzr, vxr))
        if k > 20: vals.append(wzr)
    P(">>> %s : wz commande=%+.1f  -> wz obtenu MOYEN=%+.2f (n=%d)" % (label, wz, sum(vals)/len(vals), len(vals)))
P("=== test rotation pure (avance=0) ===")
run("TOURNE+", 0.0, 1.0)
run("TOURNE-", 0.0, -1.0)
P("=== test rotation en marchant (avance=0.8) ===")
run("MARCHE+TOURNE+", 0.8, 1.0)
P("SPIN FINI")
sim.close()
