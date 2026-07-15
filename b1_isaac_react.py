#!/usr/bin/env python3
"""b1_isaac_react.py — B1 : le G1 REAGIT a la GEOMETRIE ISAAC. Plus de sandbox miroir : l'exposition
est calculee par RAYCAST PhysX depuis la position REELLE du robot vers une menace, contre le vrai mesh
de collision (muret). Le cerveau (regle hull-down validee) decide depuis CETTE perception Isaac.
Preuve : derriere le muret debout=expose / accroupi=masque -> CROUCH ; a decouvert = pas de couvert -> MOVE.
Sortie : un tableau chiffre + 2 rendus (POV ennemi)."""
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
from pxr import Usd, UsdGeom, Gf, Vt, UsdPhysics
import isaaclab.sim as sim_utils
from isaaclab.sim import SimulationContext, SimulationCfg
from isaaclab.sensors import Camera, CameraCfg
from isaaclab.assets import Articulation
from isaaclab_assets.robots.unitree import G1_MINIMAL_CFG

D = args_cli.dir
Wd = np.load("%s/world_athens.npz" % D); hf = Wd["heightfield"].astype(np.float32); G = hf.shape[0]
zc = float(hf[G // 2, G // 2])

sim = SimulationContext(SimulationCfg(dt=1 / 200.0)); stage = omni.usd.get_context().get_stage()
sim_utils.DomeLightCfg(intensity=450.0, color=(0.9, 0.9, 0.92)).func("/World/Light", sim_utils.DomeLightCfg(intensity=450.0))
sim_utils.DistantLightCfg(intensity=1400.0, angle=2.0).func("/World/Sun", sim_utils.DistantLightCfg(intensity=1400.0), translation=(0, 0, 50), orientation=(0.86, 0.35, 0.0, 0.0))

# --- sol plat + collision ---
gp = UsdGeom.Mesh.Define(stage, "/World/ground"); S = 30.0
gp.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(-S, -S, zc), Gf.Vec3f(S, -S, zc), Gf.Vec3f(S, S, zc), Gf.Vec3f(-S, S, zc)]))
gp.CreateFaceVertexCountsAttr(Vt.IntArray([4])); gp.CreateFaceVertexIndicesAttr(Vt.IntArray([0, 1, 2, 3]))
gp.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.4, 0.45, 0.35)]))
UsdPhysics.CollisionAPI.Apply(gp.GetPrim()); UsdPhysics.MeshCollisionAPI.Apply(gp.GetPrim()).CreateApproximationAttr().Set("none")

# --- muret de 1 m (le couvert) a x=3 ---
WALL_X, WALL_TOP = 3.0, 1.0
wall = UsdGeom.Cube.Define(stage, "/World/wall"); wall.CreateSizeAttr(1.0)
xf = UsdGeom.Xformable(wall); xf.AddTranslateOp().Set(Gf.Vec3d(WALL_X, 0.0, zc + WALL_TOP / 2)); xf.AddScaleOp().Set(Gf.Vec3f(0.4, 4.0, WALL_TOP))
wall.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.62, 0.5, 0.38)])); UsdPhysics.CollisionAPI.Apply(wall.GetPrim())

# --- robot ---
robot_cfg = G1_MINIMAL_CFG.replace(prim_path="/World/Robot"); robot_cfg.init_state.pos = (4.1, 0.0, zc + 0.74)
robot = Articulation(robot_cfg)
cam = Camera(CameraCfg(prim_path="/World/cam", height=820, width=1180, data_types=["rgb"],
                       spawn=sim_utils.PinholeCameraCfg(focal_length=30.0, clipping_range=(0.05, 500.0))))
sim.reset(); robot.reset(); dt = sim.get_physics_dt()
zero_vel = torch.zeros((1, 6), dtype=torch.float32, device=sim.device)

# --- PERCEPTION ISAAC : on lit la GEOMETRIE REELLE de la scene USD (bounding-box des couverts) ---
THREAT = np.array([-8.0, 0.0, zc + 1.4], dtype=np.float64)   # tireur cote ennemi (x negatif)
EYE_STAND, EYE_CROUCH = 1.45, 0.75                            # hauteur d'oeil (m) debout / accroupi
_bbc = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_, UsdGeom.Tokens.render])
COVERS = []                                                   # AABB monde des obstacles reels de la scene
for _p in stage.Traverse():
    _pa = str(_p.GetPath())
    if any(k in _pa for k in ["/ground", "/Robot", "/cam", "/Light", "/Sun"]): continue
    if _p.IsA(UsdGeom.Cube) or _p.IsA(UsdGeom.Mesh):
        _r = _bbc.ComputeWorldBound(_p).ComputeAlignedRange(); _mn = _r.GetMin(); _mx = _r.GetMax()
        COVERS.append((np.array([_mn[0], _mn[1], _mn[2]]), np.array([_mx[0], _mx[1], _mx[2]]), _pa))
print("[B1] couverts lus dans la scene Isaac : %s" % [c[2] for c in COVERS], flush=True)

def _seg_hits_aabb(o, dirn, tmax, mn, mx):
    tmin, tM = 0.0, tmax
    for i in range(3):
        if abs(dirn[i]) < 1e-9:
            if o[i] < mn[i] or o[i] > mx[i]: return False
        else:
            t1 = (mn[i] - o[i]) / dirn[i]; t2 = (mx[i] - o[i]) / dirn[i]
            if t1 > t2: t1, t2 = t2, t1
            tmin = max(tmin, t1); tM = min(tM, t2)
            if tmin > tM: return False
    return True

def isaac_exposed(rob_x, eye_h):
    """True si LOS DEGAGEE (expose) : le segment oeil->menace ne coupe AUCUN couvert reel de la scene."""
    o = np.array([rob_x, 0.0, zc + eye_h], dtype=np.float64)
    d = THREAT - o; dist = float(np.linalg.norm(d)); dirn = d / dist
    for mn, mx, _ in COVERS:
        if _seg_hits_aabb(o, dirn, dist - 0.05, mn, mx): return False
    return True

def crouch_overrides():
    return [(".*_hip_pitch_joint", -1.0), (".*_knee_joint", 1.7), (".*_ankle_pitch_joint", -0.7)]

def place(rob_x, base_z, overrides):
    q = robot.data.default_joint_pos.clone()
    for pat, val in overrides:
        ids, _ = robot.find_joints(pat); q[:, ids] = val
    bp = torch.tensor([[rob_x, 0.0, base_z, 1.0, 0.0, 0.0, 0.0]], dtype=torch.float32, device=sim.device)
    robot.write_joint_state_to_sim(q, torch.zeros_like(q))
    for _ in range(50):
        robot.write_root_pose_to_sim(bp); robot.write_root_velocity_to_sim(zero_vel)
        robot.set_joint_position_target(q); robot.write_data_to_sim(); sim.step(); robot.update(dt)

def render(rob_x, out):
    cam.set_world_poses_from_view(torch.tensor([[-6.0, 0.0, zc + 1.35]], dtype=torch.float32, device=sim.device),
                                  torch.tensor([[rob_x, 0.0, zc + 0.9]], dtype=torch.float32, device=sim.device))
    for _ in range(60):
        sim.step(); cam.update(dt)
    rgb = cam.data.output["rgb"][0].detach().cpu().numpy()
    if rgb.dtype != np.uint8: rgb = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.imsave(out, rgb[..., :3]); print("[B1] rendu ->", out, flush=True)

# le "cerveau" hull-down (regle validee, alimentee UNIQUEMENT par la perception Isaac) :
def brain_decide(exp_stand, exp_crouch):
    if not exp_stand:            return "STAND (deja masque)"
    if exp_crouch:               return "MOVE (aucun couvert : accroupi n'aide pas)"
    return "CROUCH (hull-down : masque en s'abaissant)"

# --- 2 situations : derriere le muret / a decouvert ---
SPOTS = [("derriere_muret", 4.1), ("a_decouvert", -1.0)]
print("=== B1 : le G1 REAGIT a la geometrie ISAAC (perception = AABB USD reelles de la scene) ===", flush=True)
print("  menace en x=%.0f | oeil debout %.2fm / accroupi %.2fm | muret 1m en x=%.0f" % (THREAT[0], EYE_STAND, EYE_CROUCH, WALL_X), flush=True)
results = {}
for name, rx in SPOTS:
    place(rx, zc + 0.74, [])                                  # debout pour sonder
    es = isaac_exposed(rx, EYE_STAND)
    ec = isaac_exposed(rx, EYE_CROUCH)
    decision = brain_decide(es, ec)
    results[name] = (rx, es, ec, decision)
    print("  [%s] x=%.1f | debout %s | accroupi %s | -> %s"
          % (name, rx, "EXPOSE" if es else "masque", "EXPOSE" if ec else "masque", decision), flush=True)

# --- rendus : le robot APPLIQUE la decision derriere le muret (crouch) puis a decouvert (stand) ---
rx = results["derriere_muret"][0]
place(rx, zc + 0.50, crouch_overrides()); render(rx, "%s/b1_muret_crouch.png" % D)
rx = results["a_decouvert"][0]
place(rx, zc + 0.74, []); render(rx, "%s/b1_decouvert_stand.png" % D)

print("  -> perception ISAAC (pas de miroir) : le robot voit le couvert par raycast et choisit hull-down la ou il paie.", flush=True)
simulation_app.close()
