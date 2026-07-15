#!/usr/bin/env python3
"""make_athens_collision.py — fabrique Athenes AVEC COLLISION (terrain + boites) pour la tache
velocity du G1. Centre ramene a z=0 (pour que le robot spawn bien) et relief adouci (x0.35, la
politique flat trebuche sur les fortes pentes). Exporte athens_collision.usd (sans robot)."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
parser.add_argument("--scale", type=float, default=0.35)
parser.add_argument("--dir", default="/home/younes/arma3-marl")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
app = AppLauncher(args_cli).app

import numpy as np
import omni.usd
from pxr import UsdGeom, Gf, Vt, UsdPhysics
from isaaclab.sim import SimulationContext, SimulationCfg
import isaaclab.sim as sim_utils

Wd = np.load("%s/world_athens.npz" % args_cli.dir)
hf = Wd["heightfield"].astype(np.float32); Wm = float(Wd["W"]); boxes = Wd["boxes"]; G = hf.shape[0]
coord = (np.arange(G) / (G - 1) - 0.5) * 2 * Wm
zc = float(hf[G // 2, G // 2]); S = args_cli.scale
def zoff(z): return (z - zc) * S                         # centre a 0, relief adouci

sim = SimulationContext(SimulationCfg(dt=1 / 60.0))
stage = omni.usd.get_context().get_stage()
print("[make] terrain (relief x%.2f, centre->0) + collision..." % S, flush=True)
st = 2; ii = np.arange(0, G, st); gg = len(ii)
pts = [(float(coord[i]), float(coord[j]), zoff(float(hf[j, i]))) for j in ii for i in ii]
idx = []
for r in range(gg - 1):
    for c in range(gg - 1):
        a = r * gg + c; idx += [a, a + 1, a + gg + 1, a + gg]
mesh = UsdGeom.Mesh.Define(stage, "/World/terrain")
mesh.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(*p) for p in pts]))
mesh.CreateFaceVertexCountsAttr(Vt.IntArray([4] * ((gg - 1) * (gg - 1))))
mesh.CreateFaceVertexIndicesAttr(Vt.IntArray(idx))
mesh.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.42, 0.47, 0.36)]))
UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr().Set("none")

print("[make] %d batiments + collision..." % len(boxes), flush=True)
for k, b in enumerate(boxes):
    cx, cy, cz, sx, sy, sz = [float(v) for v in b]
    cube = UsdGeom.Cube.Define(stage, "/World/bldg/b%d" % k); cube.CreateSizeAttr(1.0)
    xf = UsdGeom.Xformable(cube)
    xf.AddTranslateOp().Set(Gf.Vec3d(cx, cy, zoff(cz - sz / 2) + (sz * S) / 2))   # base au sol adouci
    xf.AddScaleOp().Set(Gf.Vec3f(sx, sy, sz * S))
    cube.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.7, 0.42, 0.2)]))
    UsdPhysics.CollisionAPI.Apply(cube.GetPrim())

world = UsdGeom.Xform.Define(stage, "/World")             # defaultPrim OBLIGATOIRE pour etre reference comme terrain
stage.SetDefaultPrim(world.GetPrim())
out = "%s/athens_collision.usd" % args_cli.dir
stage.Export(out)
print("[make] EXPORTE ->", out, flush=True)
app.close()
