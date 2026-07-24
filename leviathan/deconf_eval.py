#!/usr/bin/env python3
"""deconf_eval — dé-confusion : le BC 60% restauré (prof plain) évalué dans les 2 physiques (sans/avec hull)."""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from corps import evaluate
from train_koth_gpu import Net
BASE = "/home/younes/arma3-marl"
net = Net(17, 13, 256, 3); net.load_state_dict(torch.load(BASE + "/corps_bc_60.pt", map_location="cuda:0")); net = net.to("cuda:0").eval()
e1 = evaluate(net, hull=False); e2 = evaluate(net, hull=True)
print("=== DE-CONFUSION (BC plain restaure) ===")
print("  SANS hull (monde du 60 pct)  : FOB pris %.0f pct | pertes %.1f/18" % (100 * e1[0], e1[2]))
print("  AVEC hull (nouveau monde)    : FOB pris %.0f pct | pertes %.1f/18" % (100 * e2[0], e2[2]))
print("  >>> %s" % ("PHYSIQUE coupable (le plain s'effondre aussi sous hull)" if e1[0] > 0 and e2[0] < e1[0] * 0.6 else "PHYSIQUE INNOCENTE -> le prof cover-aware etait le coupable du 3 pct"))
print("DECONF_EVAL_DONE")
