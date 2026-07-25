# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Script to play a checkpoint of an RL agent from skrl.

Visit the skrl documentation (https://skrl.readthedocs.io) to see the examples structured in
a more user-friendly way.
"""

"""Launch Isaac Sim Simulator first."""

import argparse
import sys

from isaaclab.app import AppLauncher

# add argparse arguments
parser = argparse.ArgumentParser(description="Play a checkpoint of an RL agent from skrl.")
parser.add_argument("--video", action="store_true", default=False, help="Record videos during training.")
parser.add_argument("--video_length", type=int, default=200, help="Length of the recorded video (in steps).")
parser.add_argument(
    "--disable_fabric", action="store_true", default=False, help="Disable fabric and use USD I/O operations."
)
parser.add_argument("--num_envs", type=int, default=None, help="Number of environments to simulate.")
parser.add_argument("--task", type=str, default=None, help="Name of the task.")
parser.add_argument(
    "--agent",
    type=str,
    default=None,
    help=(
        "Name of the RL agent configuration entry point. Defaults to None, in which case the argument "
        "--algorithm is used to determine the default agent configuration entry point."
    ),
)
parser.add_argument("--checkpoint", type=str, default=None, help="Path to model checkpoint.")
parser.add_argument("--seed", type=int, default=None, help="Seed used for the environment")
parser.add_argument(
    "--use_pretrained_checkpoint",
    action="store_true",
    help="Use the pre-trained checkpoint from Nucleus.",
)
parser.add_argument(
    "--ml_framework",
    type=str,
    default="torch",
    choices=["torch", "jax"],
    help="The ML framework used for training the skrl agent.",
)
parser.add_argument(
    "--algorithm",
    type=str,
    default="PPO",
    help=(
        "Name of the RL algorithm to use (e.g. AMP, DDPG, IPPO, MAPPO, PPO, SAC, TD3, etc.) "
        "when several algorithms exist for the same task. For a more specific selection, use the argument --agent."
    ),
)
parser.add_argument("--real-time", action="store_true", default=False, help="Run in real-time, if possible.")

# append AppLauncher cli args
AppLauncher.add_app_launcher_args(parser)
# parse the arguments
args_cli, hydra_args = parser.parse_known_args()
# always enable cameras to record video
if args_cli.video:
    args_cli.enable_cameras = True

# clear out sys.argv for Hydra
sys.argv = [sys.argv[0]] + hydra_args
# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import os
import random
import time

import gymnasium as gym
import skrl
import torch
from packaging import version

# check for minimum supported skrl version
SKRL_VERSION = "2.0.0"
if version.parse(skrl.__version__) < version.parse(SKRL_VERSION):
    skrl.logger.error(
        f"Unsupported skrl version: {skrl.__version__}. "
        f"Install supported version using 'pip install skrl>={SKRL_VERSION}'"
    )
    exit()

if args_cli.ml_framework.startswith("torch"):
    from skrl.utils.runner.torch import Runner
elif args_cli.ml_framework.startswith("jax"):
    from skrl.utils.runner.jax import Runner

from isaaclab.envs import (
    DirectMARLEnv,
    DirectMARLEnvCfg,
    DirectRLEnvCfg,
    ManagerBasedRLEnvCfg,
    multi_agent_to_single_agent,
)
from isaaclab.utils.dict import print_dict

from isaaclab_rl.skrl import SkrlVecEnvWrapper
from isaaclab_rl.utils.pretrained_checkpoint import get_published_pretrained_checkpoint

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils import get_checkpoint_path
from isaaclab_tasks.utils.hydra import hydra_task_config

# PLACEHOLDER: Extension template (do not remove this comment)

# config shortcuts
if args_cli.agent is None:
    algorithm = args_cli.algorithm.lower()
    agent_cfg_entry_point = "skrl_cfg_entry_point" if algorithm in ["ppo"] else f"skrl_{algorithm}_cfg_entry_point"
else:
    agent_cfg_entry_point = args_cli.agent
    algorithm = agent_cfg_entry_point.split("_cfg")[0].split("skrl_")[-1].lower()


@hydra_task_config(args_cli.task, agent_cfg_entry_point)
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, experiment_cfg: dict):
    """Play with skrl agent."""
    # grab task name for checkpoint path
    task_name = args_cli.task.split(":")[-1]
    train_task_name = task_name.replace("-Play", "")

    # override configurations with non-hydra CLI arguments
    env_cfg.scene.num_envs = args_cli.num_envs if args_cli.num_envs is not None else env_cfg.scene.num_envs
    env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device

    # configure the ML framework into the global skrl variable
    if args_cli.ml_framework.startswith("jax"):
        skrl.config.jax.backend = "jax" if args_cli.ml_framework == "jax" else "numpy"

        # randomly sample a seed if seed = -1
    if args_cli.seed == -1:
        args_cli.seed = random.randint(0, 10000)

    # set the agent and environment seed from command line
    # note: certain randomization occur in the environment initialization so we set the seed here
    experiment_cfg["seed"] = args_cli.seed if args_cli.seed is not None else experiment_cfg["seed"]
    env_cfg.seed = experiment_cfg["seed"]

    # specify directory for logging experiments (load checkpoint)
    log_root_path = os.path.join("logs", "skrl", experiment_cfg["agent"]["experiment"]["directory"])
    log_root_path = os.path.abspath(log_root_path)
    print(f"[INFO] Loading experiment from directory: {log_root_path}")
    # get checkpoint path
    if args_cli.use_pretrained_checkpoint:
        resume_path = get_published_pretrained_checkpoint("skrl", train_task_name)
        if not resume_path:
            print("[INFO] Unfortunately a pre-trained checkpoint is currently unavailable for this task.")
            return
    elif args_cli.checkpoint:
        resume_path = os.path.abspath(args_cli.checkpoint)
    else:
        resume_path = get_checkpoint_path(
            log_root_path, run_dir=f".*_{algorithm}_{args_cli.ml_framework}", other_dirs=["checkpoints"]
        )
    log_dir = os.path.dirname(os.path.dirname(resume_path))

    # set the log directory for the environment (works for all environment types)
    env_cfg.log_dir = log_dir

    # create isaac environment
    env = gym.make(args_cli.task, cfg=env_cfg, render_mode="rgb_array" if args_cli.video else None)
    # --- FIX rendu noir : RR (NGX feature 13) non supporte -> passer en PathTracing + debruiteur OptiX ---
    import carb as _carb
    _S = _carb.settings.get_settings()
    print("FIXRENDU AVANT rendermode=", _S.get("/rtx/rendermode"), "newDenoiser=", _S.get("/rtx/newDenoiser/enabled"), "aaop=", _S.get("/rtx/post/aa/op"), "denoTech=", _S.get("/rtx/directLighting/sampledLighting/denoisingTechnique"), flush=True)
    _S.set_string("/rtx/rendermode", "PathTracing")
    _S.set_int("/rtx/pathtracing/optixDenoiser/enabled", 1)
    _S.set_int("/rtx/pathtracing/spp", 8)
    _S.set_int("/rtx/pathtracing/totalSpp", 32)
    _S.set_int("/rtx/pathtracing/maxBounces", 4)
    _S.set_int("/rtx/post/aa/op", 1)
    print("FIXRENDU APRES rendermode=", _S.get("/rtx/rendermode"), flush=True)


    # === BOUCLE FERMEE : le cerveau lit letat reel du G1 et decide ===
    import sys as _sys, math as _math, torch as _torch
    _sys.path.insert(0, "/home/younes/compose-embodiment")
    from assault_terrain import AssaultTerrain as _AT
    from train_koth_gpu import Net as _Net
    _sd = _torch.load("/home/younes/compose-embodiment/soldier_shell.pt", map_location="cpu")
    AT = _AT(num_envs=1, A=1, D=2, relief=40.0, hit=0.10, shell_obs=True, replica=True, replica_path="/home/younes/arma3-marl/replica.npz", max_steps=60, device="cpu", seed=0)
    BRAIN = _Net(AT.obs_dim, AT.n_actions, 512, 3); BRAIN.load_state_dict(_sd); BRAIN.eval()
    AT.reset(); _ATs=(float(AT.apx[0,0]), float(AT.apy[0,0]))
    G1 = env.unwrapped
    try: CMD = G1.command_manager.get_term("base_velocity")
    except Exception: CMD = G1.command_manager._terms["base_velocity"]
    ROB = G1.scene["robot"]; CMD._resample_command = lambda env_ids: None
    _SPEED=1.0; _K=20; _MAXC = args_cli.video_length if args_cli.video else 160; _ci=0; _g1s=[None,None]; _cap=[0]
    print("[CL] AT obs=%d act=%d start=%s" % (AT.obs_dim, AT.n_actions, _ATs), flush=True)
    # convert to single-agent instance if required by the RL algorithm
    if isinstance(env.unwrapped, DirectMARLEnv) and algorithm in ["ppo"]:
        env = multi_agent_to_single_agent(env)

    # get environment (step) dt for real-time evaluation
    try:
        dt = env.step_dt
    except AttributeError:
        dt = env.unwrapped.step_dt

    # wrap for video recording
    if args_cli.video:
        video_kwargs = {
            "video_folder": os.path.join(log_dir, "videos", "play"),
            "step_trigger": lambda step: step == 0,
            "video_length": args_cli.video_length,
            "disable_logger": True,
        }
        print("[INFO] Recording videos during training.")
        print_dict(video_kwargs, nesting=4)
        env = gym.wrappers.RecordVideo(env, **video_kwargs)

    # wrap around environment for skrl
    env = SkrlVecEnvWrapper(env, ml_framework=args_cli.ml_framework)  # same as: `wrap_env(env, wrapper="auto")`

    # configure and instantiate the skrl runner
    # https://skrl.readthedocs.io/en/latest/api/utils/runner.html
    experiment_cfg["trainer"]["close_environment_at_exit"] = False
    experiment_cfg["agent"]["experiment"]["write_interval"] = 0  # don't log to TensorBoard
    experiment_cfg["agent"]["experiment"]["checkpoint_interval"] = 0  # don't generate checkpoints
    runner = Runner(env, experiment_cfg)

    print(f"[INFO] Loading model checkpoint from: {resume_path}")
    runner.agent.load(resume_path)
    # set agent to evaluation mode
    runner.agent.enable_training_mode(False, apply_to_models=True)

    # reset environment
    obs, _ = env.reset()
    states = env.state()
    timestep = 0
    # simulate environment
    while simulation_app.is_running():
        start_time = time.time()

        # run everything in inference mode
        with torch.inference_mode():
            # agent stepping
            outputs = runner.agent.act(obs, states, timestep=0, timesteps=0)
            # - multi-agent (deterministic) actions
            if hasattr(env, "possible_agents"):
                actions = {a: outputs[-1][a].get("mean_actions", outputs[0][a]) for a in env.possible_agents}
            # - single-agent (deterministic) actions
            else:
                actions = outputs[-1].get("mean_actions", outputs[0])
            # env stepping
            if _ci % _K == 0:
                _xy = ROB.data.root_pos_w[0,:2].tolist()
                if _g1s[0] is None: _g1s[0]=_xy[0]; _g1s[1]=_xy[1]
                AT.apx[0,0]=_ATs[0]+(_xy[0]-_g1s[0]); AT.apy[0,0]=_ATs[1]+(_xy[1]-_g1s[1])
                with _torch.no_grad(): _cap[0]=int(BRAIN.a_logits(AT._obs()).argmax(-1).reshape(-1)[0])
                print("[CL] t=%3d cap=%d g1=(%.1f,%.1f) at=(%.1f,%.1f)" % (_ci,_cap[0],_xy[0],_xy[1],float(AT.apx[0,0]),float(AT.apy[0,0])), flush=True)
            _c=_cap[0]
            if _c < 8:
                CMD.heading_target[:]=_math.atan2(_math.cos(_c*_math.pi/4.0), _math.sin(_c*_math.pi/4.0))
                CMD.vel_command_b[:,0]=_SPEED; CMD.vel_command_b[:,1]=0.0
            else:
                CMD.vel_command_b[:,0]=0.0; CMD.vel_command_b[:,1]=0.0; CMD.heading_target[:]=ROB.data.heading_w
            _ci+=1
            obs, _, _, _, _ = env.step(actions)
            states = env.state()
        if args_cli.video:
            timestep += 1
            # exit the play loop after recording one video
            if timestep == args_cli.video_length:
                break

        if _ci >= _MAXC:
            print("[CL] stop", flush=True); break
        # time delay for real-time evaluation
        sleep_time = dt - (time.time() - start_time)
        if args_cli.real_time and sleep_time > 0:
            time.sleep(sleep_time)

    # close the simulator
    env.close()


if __name__ == "__main__":
    # run the main function
    main()
    # close sim app
    simulation_app.close()
