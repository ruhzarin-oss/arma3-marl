#!/usr/bin/env python3
"""isaac_g1_hulldown.py — ETAPE 4 : le HULL-DOWN pour de vrai. Un muret de 1 m, le robot G1
DEBOUT (torse expose au-dessus) vs ACCROUPI (masque, tete seule). Deux images = la demo de tout
le thread : la posture qui paie par la GEOMETRIE, pas par un knob. Vue depuis le cote 'ennemi'."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
parser.add_argument("--dir", default="/home/younes/arma3-marl")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
app_launcher = AppLauncher(args_cli); simulation_app = app_launcher.app

import carb
_st = carb.settings.get_settings()
_st.set("/rtx/rendermode", "PathTracing"); _st.set("/rtx/pathtracing/spp", 8)
_st.set("/rtx/pathtracing/totalSpp", 128); _st.set("/rtx/post/aa/op", 1)

import numpy as np, torch
import omni.usd
from pxr import UsdGeom, Gf, Vt, UsdPhysics
import isaaclab.sim as sim_utils
from isaaclab.sim import SimulationContext, SimulationCfg
from isaaclab.sensors import Camera, CameraCfg
from isaaclab.assets import Articulation
from isaaclab_assets.robots.unitree import G1_MINIMAL_CFG

D = args_cli.dir
Wd = np.load("%s/world_athens.npz" % D); hf = Wd["heightfield"].astype(np.float32); Wm = float(Wd["W"]); G = hf.shape[0]
coord = (np.arange(G) / (G - 1) - 0.5) * 2 * Wm; zc = float(hf[G // 2, G // 2])

sim = SimulationContext(SimulationCfg(dt=1 / 200.0)); stage = omni.usd.get_context().get_stage()
sim_utils.DomeLightCfg(intensity=450.0, color=(0.9, 0.9, 0.92)).func("/World/Light", sim_utils.DomeLightCfg(intensity=450.0))
sim_utils.DistantLightCfg(intensity=1400.0, angle=2.0).func("/World/Sun", sim_utils.DistantLightCfg(intensity=1400.0), translation=(0, 0, 50), orientation=(0.86, 0.35, 0.0, 0.0))

# --- sol plat local + collision (on n'a besoin que d'un sol autour du muret pour la demo) ---
gp = UsdGeom.Mesh.Define(stage, "/World/ground")
S = 30.0
gp.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(-S, -S, zc), Gf.Vec3f(S, -S, zc), Gf.Vec3f(S, S, zc), Gf.Vec3f(-S, S, zc)]))
gp.CreateFaceVertexCountsAttr(Vt.IntArray([4])); gp.CreateFaceVertexIndicesAttr(Vt.IntArray([0, 1, 2, 3]))
gp.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.4, 0.45, 0.35)]))
UsdPhysics.CollisionAPI.Apply(gp.GetPrim()); UsdPhysics.MeshCollisionAPI.Apply(gp.GetPrim()).CreateApproximationAttr().Set("none")

# --- muret de 1 m (le couvert) ---
WALL_X, WALL_TOP = 3.0, 1.0
wall = UsdGeom.Cube.Define(stage, "/World/wall"); wall.CreateSizeAttr(1.0)
xf = UsdGeom.Xformable(wall); xf.AddTranslateOp().Set(Gf.Vec3d(WALL_X, 0.0, zc + WALL_TOP / 2)); xf.AddScaleOp().Set(Gf.Vec3f(0.4, 4.0, WALL_TOP))
wall.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.62, 0.5, 0.38)])); UsdPhysics.CollisionAPI.Apply(wall.GetPrim())

# --- robot ---
ROB_X = 4.1
robot_cfg = G1_MINIMAL_CFG.replace(prim_path="/World/Robot"); robot_cfg.init_state.pos = (ROB_X, 0.0, zc + 0.74)
robot = Articulation(robot_cfg)
cam = Camera(CameraCfg(prim_path="/World/cam", height=820, width=1180, data_types=["rgb"],
                       spawn=sim_utils.PinholeCameraCfg(focal_length=30.0, clipping_range=(0.05, 500.0))))
sim.reset(); robot.reset(); dt = sim.get_physics_dt()
zero_vel = torch.zeros((1, 6), dtype=torch.float32, device=sim.device)
# camera cote 'ennemi' (x negatif), a hauteur du haut du muret
cam.set_world_poses_from_view(torch.tensor([[-6.0, 0.0, zc + 1.35]], dtype=torch.float32, device=sim.device),
                              torch.tensor([[ROB_X, 0.0, zc + 0.9]], dtype=torch.float32, device=sim.device))

def shoot(base_z, overrides, out):
    q = robot.data.default_joint_pos.clone()
    for pat, val in overrides:
        ids, _ = robot.find_joints(pat); q[:, ids] = val
    bp = torch.tensor([[ROB_X, 0.0, base_z, 1.0, 0.0, 0.0, 0.0]], dtype=torch.float32, device=sim.device)
    robot.write_joint_state_to_sim(q, torch.zeros_like(q))
    for _ in range(50):
        robot.write_root_pose_to_sim(bp); robot.write_root_velocity_to_sim(zero_vel)
        robot.set_joint_position_target(q); robot.write_data_to_sim(); sim.step(); robot.update(dt)
    for _ in range(50):
        sim.step(); cam.update(dt)
    rgb = cam.data.output["rgb"][0].detach().cpu().numpy()
    if rgb.dtype != np.uint8: rgb = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.imsave(out, rgb[..., :3]); print("[etape4] ECRIT ->", out, flush=True)

print("[etape4] rendu DEBOUT...", flush=True)
shoot(zc + 0.74, [], "%s/g1_debout.png" % D)
print("[etape4] rendu ACCROUPI...", flush=True)
shoot(zc + 0.50, [(".*_hip_pitch_joint", -1.0), (".*_knee_joint", 1.7), (".*_ankle_pitch_joint", -0.7)], "%s/g1_accroupi.png" % D)
print("[etape4] termine.", flush=True)
simulation_app.close()
