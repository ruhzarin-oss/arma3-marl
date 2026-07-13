#!/usr/bin/env python3
"""isaac_g1_athens.py — ETAPE 3 : pose le robot G1 dans Athenes (avec COLLISION) et le laisse
se tenir sur le terrain sous la physique. Rend une image rapprochee sur le robot + exporte le USD.
Lancer via run_g1.sh (venv python, EULA, PAS de CUDA_VISIBLE_DEVICES)."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
parser.add_argument("--name", default="athens"); parser.add_argument("--dir", default="/home/younes/arma3-marl")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import carb
_st = carb.settings.get_settings()                          # rendu PathTracing (evite le NGX noir)
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

print("[etape3] app OK, chargement du monde...", flush=True)
Wd = np.load("%s/world_%s.npz" % (args_cli.dir, args_cli.name))
hf = Wd["heightfield"].astype(np.float32); Wm = float(Wd["W"]); boxes = Wd["boxes"]; G = hf.shape[0]
coord = (np.arange(G) / (G - 1) - 0.5) * 2 * Wm
zc = float(hf[G // 2, G // 2])                              # hauteur du terrain au centre (0,0) -> ou poser le robot

sim = SimulationContext(SimulationCfg(dt=1 / 200.0))
stage = omni.usd.get_context().get_stage()
sim_utils.DomeLightCfg(intensity=1200.0, color=(0.9, 0.9, 0.92)).func("/World/Light", sim_utils.DomeLightCfg(intensity=1200.0))

def add_collision(prim):
    UsdPhysics.CollisionAPI.Apply(prim)

# --- terrain (maillage + COLLISION) ---
print("[etape3] relief + collision...", flush=True)
st = 2; ii = np.arange(0, G, st); gg = len(ii)
pts = [(float(coord[i]), float(coord[j]), float(hf[j, i])) for j in ii for i in ii]
idx = []
for r in range(gg - 1):
    for c in range(gg - 1):
        a = r * gg + c; idx += [a, a + 1, a + gg + 1, a + gg]
mesh = UsdGeom.Mesh.Define(stage, "/World/terrain")
mesh.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(*p) for p in pts]))
mesh.CreateFaceVertexCountsAttr(Vt.IntArray([4] * ((gg - 1) * (gg - 1))))
mesh.CreateFaceVertexIndicesAttr(Vt.IntArray(idx))
mesh.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.42, 0.47, 0.36)]))
add_collision(mesh.GetPrim())
mca = UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()); mca.CreateApproximationAttr().Set("none")

# --- batiments (boites + collision) ---
print("[etape3] %d batiments + collision..." % len(boxes), flush=True)
for k, b in enumerate(boxes):
    cx, cy, cz, sx, sy, sz = [float(v) for v in b]
    cube = UsdGeom.Cube.Define(stage, "/World/bldg/b%d" % k); cube.CreateSizeAttr(1.0)
    xf = UsdGeom.Xformable(cube); xf.AddTranslateOp().Set(Gf.Vec3d(cx, cy, cz)); xf.AddScaleOp().Set(Gf.Vec3f(sx, sy, sz))
    cube.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.7, 0.42, 0.2)]))
    add_collision(cube.GetPrim())

# --- robot G1 ---
print("[etape3] spawn du robot G1 au centre (z terrain = %.1f m)..." % zc, flush=True)
robot_cfg = G1_MINIMAL_CFG.replace(prim_path="/World/Robot")
robot_cfg.init_state.pos = (0.0, 0.0, zc + 0.85)            # legerement au-dessus du sol -> il se pose
robot = Articulation(robot_cfg)

cam = Camera(CameraCfg(prim_path="/World/cam", height=760, width=1140, data_types=["rgb"],
                       spawn=sim_utils.PinholeCameraCfg(focal_length=28.0, clipping_range=(0.05, 2000.0))))
print("[etape3] reset + stabilisation physique...", flush=True)
sim.reset(); robot.reset()
sim_dt = sim.get_physics_dt()
# EPINGLER le bassin debout (pas de politique d'equilibre a l'etape 3) -> mannequin debout dans Athenes
rz = zc + 0.74
base_pose = torch.tensor([[0.0, 0.0, rz, 1.0, 0.0, 0.0, 0.0]], dtype=torch.float32, device=sim.device)
zero_vel = torch.zeros((1, 6), dtype=torch.float32, device=sim.device)
for i in range(90):
    robot.write_root_pose_to_sim(base_pose); robot.write_root_velocity_to_sim(zero_vel)
    robot.set_joint_position_target(robot.data.default_joint_pos)
    robot.write_data_to_sim(); sim.step(); robot.update(sim_dt)
print("[etape3] robot epingle debout, bassin z = %.2f (sol %.2f)" % (float(robot.data.root_pos_w[0, 2]), zc), flush=True)

# camera rapprochee sur le robot
cam.set_world_poses_from_view(torch.tensor([[5.0, -5.0, rz + 2.2]], dtype=torch.float32, device=sim.device),
                              torch.tensor([[0.0, 0.0, rz + 0.1]], dtype=torch.float32, device=sim.device))
for _ in range(60):
    sim.step(); cam.update(sim_dt)
rgb = cam.data.output["rgb"][0].detach().cpu().numpy()
if rgb.dtype != np.uint8:
    rgb = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
out = "%s/isaac_g1_%s.png" % (args_cli.dir, args_cli.name)
plt.imsave(out, rgb[..., :3]); print("[etape3] IMAGE ECRITE ->", out, flush=True)
stage.Export("%s/isaac_g1_%s.usd" % (args_cli.dir, args_cli.name)); print("[etape3] USD EXPORTE", flush=True)
simulation_app.close()
