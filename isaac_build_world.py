#!/usr/bin/env python3
"""isaac_build_world.py — ETAPE 2 : charge world_<nom>.npz dans ISAAC et construit la scene 3D
(relief en maillage + batiments en boites) + une camera, capture une image, exporte un .usd.
Lancer :  ~/isaaclab_src/isaaclab.sh -p isaac_build_world.py --headless --enable_cameras
Geometrie seule (pas de physique ici) — but = PROUVER que notre monde se charge dans le moteur Isaac."""
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--name", default="athens")
parser.add_argument("--dir", default="/home/younes/arma3-marl")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# --- suite ---
import carb                                                 # FIX rendu noir headless : PathTracing (OptiX) au lieu du temps-reel (NGX/DLSS qui echoue)
_st = carb.settings.get_settings()
_st.set("/rtx/rendermode", "PathTracing")
_st.set("/rtx/pathtracing/spp", 8)
_st.set("/rtx/pathtracing/totalSpp", 128)
_st.set("/rtx/pathtracing/clampSpp", 128)
_st.set("/rtx/post/aa/op", 1)                                # anti-aliasing NON-DLSS (evite NGX)
import numpy as np, torch, os
import omni.usd
from pxr import UsdGeom, Gf, Vt
import isaaclab.sim as sim_utils
from isaaclab.sim import SimulationContext, SimulationCfg
from isaaclab.sensors import Camera, CameraCfg

print("[etape2] app lancee, chargement du monde...", flush=True)
Wd = np.load("%s/world_%s.npz" % (args_cli.dir, args_cli.name))
hf = Wd["heightfield"].astype(np.float32); Wm = float(Wd["W"]); boxes = Wd["boxes"]
G = hf.shape[0]; coord = (np.arange(G) / (G - 1) - 0.5) * 2 * Wm

sim = SimulationContext(SimulationCfg(dt=1 / 60.0))
stage = omni.usd.get_context().get_stage()

# --- lumiere ---
sim_utils.DomeLightCfg(intensity=2500.0, color=(0.85, 0.87, 0.9)).func("/World/Light", sim_utils.DomeLightCfg(intensity=2500.0))
sim_utils.DistantLightCfg(intensity=2000.0, angle=1.0).func("/World/Sun", sim_utils.DistantLightCfg(intensity=2000.0), translation=(0, 0, 200))

# --- terrain en maillage (relief) ---
print("[etape2] construction du relief (maillage)...", flush=True)
st = 2                                                    # sous-echantillonnage
ii = np.arange(0, G, st); gg = len(ii)
pts = []
for j in ii:
    for i in ii:
        pts.append((float(coord[i]), float(coord[j]), float(hf[j, i])))
idx = []
for r in range(gg - 1):
    for c in range(gg - 1):
        a = r * gg + c; b = a + 1; d = a + gg; e = d + 1
        idx += [a, b, e, d]
mesh = UsdGeom.Mesh.Define(stage, "/World/terrain")
mesh.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(*p) for p in pts]))
mesh.CreateFaceVertexCountsAttr(Vt.IntArray([4] * ((gg - 1) * (gg - 1))))
mesh.CreateFaceVertexIndicesAttr(Vt.IntArray(idx))
mesh.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.45, 0.5, 0.38)]))

# --- batiments (boites) ---
print("[etape2] pose des %d batiments..." % len(boxes), flush=True)
for k, b in enumerate(boxes):
    cx, cy, cz, sx, sy, sz = [float(v) for v in b]
    cube = UsdGeom.Cube.Define(stage, "/World/bldg/b%d" % k)
    cube.CreateSizeAttr(1.0)
    xf = UsdGeom.Xformable(cube)
    xf.AddTranslateOp().Set(Gf.Vec3d(cx, cy, cz))
    xf.AddScaleOp().Set(Gf.Vec3f(sx, sy, sz))
    cube.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.71, 0.4, 0.11)]))

# --- camera ---
cam = Camera(CameraCfg(prim_path="/World/cam", height=760, width=1140, data_types=["rgb"],
                       spawn=sim_utils.PinholeCameraCfg(focal_length=22.0, clipping_range=(0.1, 3000.0))))
print("[etape2] reset sim + warmup rendu...", flush=True)
sim.reset()
cam.set_world_poses_from_view(torch.tensor([[240.0, -240.0, 165.0]], device=sim.device),
                              torch.tensor([[0.0, 0.0, 12.0]], device=sim.device))
for _ in range(60):                                          # PathTracing accumule les echantillons sur plusieurs frames
    sim.step(); cam.update(1 / 60.0)

rgb = cam.data.output["rgb"][0].detach().cpu().numpy()
if rgb.dtype != np.uint8:
    rgb = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
out_png = "%s/isaac_%s.png" % (args_cli.dir, args_cli.name)
plt.imsave(out_png, rgb[..., :3])
print("[etape2] IMAGE ECRITE ->", out_png, flush=True)

out_usd = "%s/isaac_%s.usd" % (args_cli.dir, args_cli.name)
stage.Export(out_usd)
print("[etape2] USD EXPORTE ->", out_usd, flush=True)
simulation_app.close()
