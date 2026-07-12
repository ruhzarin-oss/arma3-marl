import sys, math, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from train_koth_gpu import Net
DEV = "cuda:0"; SCALE = 110.0; SIGHT = 110.0
brain = Net(14, 4, 512, 3).to(DEV)
brain.load_state_dict(torch.load("/home/younes/arma3-marl/koth_lambs_cloned14.pt", map_location=DEV))
brain.eval()
ACT = ["TENIR", "AVANCER", "SUPPRESSER", "COUVERT"]
OBJ = (0.0, 0.0); EN = (16.0, -28.0)
vpos = [0.0, -70.0]; sup = 0.0; stance = 0.0; enhp = 100.0
def obs():
    px, py = vpos; gx, gy = OBJ
    o = [(px-gx)/SCALE, (py-gy)/SCALE, (gx-px)/SCALE, (gy-py)/SCALE, 1.0, 0.0, 0.0]
    ex, ey = EN[0]-px, EN[1]-py; nd = math.hypot(ex, ey)
    seen = enhp > 0 and nd <= SIGHT
    o += [ex/SCALE if seen else 0.0, ey/SCALE if seen else 0.0, sup, 0.0, stance,
          ex/SCALE if enhp > 0 else 0.0, ey/SCALE if enhp > 0 else 0.0]
    return o
def decide():
    with torch.no_grad():
        return int(brain.a_logits(torch.tensor([obs()], dtype=torch.float32, device=DEV)).argmax(1).item())
print("=== combat incarne : la danse couvert <-> riposte ===")
prev = None
for t in range(200):
    vdo = math.hypot(OBJ[0]-vpos[0], OBJ[1]-vpos[1]); ed = math.hypot(EN[0]-vpos[0], EN[1]-vpos[1])
    if vdo < 6.0:
        print("t=%3d >>> OBJECTIF TENU (PV ennemi=%.0f)" % (t, enhp)); break
    incoming = (enhp / 100.0) * max(0.0, 1.4 - 1.9 * stance) if (enhp > 0 and ed <= SIGHT) else 0.0
    sup = max(0.0, min(0.95, sup + (0.26 * incoming - 0.12)))
    tgt = 1.0 if sup > 0.6 else (0.5 if sup > 0.3 else 0.0)
    stance += max(-0.34, min(0.34, tgt - stance))
    a = decide()
    if a == 2 and enhp > 0 and ed <= SIGHT:
        enhp = max(0.0, enhp - 7.0 * max(0.25, 1.0 - ed / 130.0))
    elif a == 1:
        n = vdo + 1e-6; vpos[0] += (OBJ[0]-vpos[0])/n * 3.5; vpos[1] += (OBJ[1]-vpos[1])/n * 3.5
    if a != prev:
        print("  t=%3d | dist_obj=%4.1f PV_en=%3.0f sup=%.2f stance=%.2f | -> %s" % (t, vdo, enhp, sup, stance, ACT[a]))
        prev = a
print("FINI (PV ennemi final=%.0f)" % enhp)
