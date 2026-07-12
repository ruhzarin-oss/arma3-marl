import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from train_koth_gpu import Net
DEV = "cuda:0"; SCALE = 140.0
brain = Net(14, 4, 512, 3).to(DEV)
brain.load_state_dict(torch.load("/home/younes/arma3-marl/koth_lambs_cloned14.pt", map_location=DEV))
brain.eval()
ACT = ["TENIR", "AVANCE", "SUPPR.", "COUVERT"]
def obs(dist_obj, en_dx, en_dy, visible, sup, stance):
    # agent au sud de l objectif a dist_obj ; objectif droit nord
    px, py = 0.0, -dist_obj; gx, gy = 0.0, 0.0
    o = [(px-gx)/SCALE, (py-gy)/SCALE, (gx-px)/SCALE, (gy-py)/SCALE, 1.0, 0.0, 0.0]
    vdx = en_dx/SCALE if visible else 0.0; vdy = en_dy/SCALE if visible else 0.0
    o += [vdx, vdy, sup, 0.0, stance, en_dx/SCALE, en_dy/SCALE]   # ennemi TOUJOURS connu (kdx,kdy)
    return o
def decide(*args):
    with torch.no_grad():
        return int(brain.a_logits(torch.tensor([obs(*args)], dtype=torch.float32, device=DEV)).argmax(1).item())
P = print
P("=== surface de decision du cerveau distille (obj a 40m) ===")
P("ennemi a ~25m, VISIBLE, debout (stance 0) :")
for sup in [0.0, 0.2, 0.4, 0.6, 0.9]:
    P("  suppression %.1f -> %s" % (sup, ACT[decide(40, 22, 14, True, sup, 0.0)]))
P("ennemi a ~25m, sup 0.9, on fait varier la POSTURE :")
for st, nm in [(0.0,"DEBOUT"), (0.5,"ACCROUPI"), (1.0,"COUCHE")]:
    P("  %-8s -> %s" % (nm, ACT[decide(40, 22, 14, True, 0.9, st)]))
P("ennemi sup 0.9 couche, on fait varier la VISIBILITE (couvert = non visible mais connu) :")
P("  VISIBLE   -> %s" % ACT[decide(40, 22, 14, True, 0.9, 1.0)])
P("  NON VISIBLE (a couvert) -> %s" % ACT[decide(40, 22, 14, False, 0.9, 1.0)])
P("on baisse la suppression a couvert (sup 0.2, non visible, couche) :")
P("  -> %s" % ACT[decide(40, 22, 14, False, 0.2, 1.0)])
P("aucun ennemi du tout (sup 0, rien) a 40m :")
P("  -> %s" % ACT[decide(40, 0, 0, False, 0.0, 0.0)])
P("=== distance ennemi (visible, sup 0.6, debout) ===")
for d in [15, 30, 60, 100, 130]:
    P("  ennemi a %3dm -> %s" % (d, ACT[decide(40, d*0.85, d*0.5, d<=110, 0.6, 0.0)]))
P("PROBE FINI")
