#!/usr/bin/env python3
"""Charge les 2 checkpoints suppression et compare voyant vs aveugle (pas de re-entrainement)."""
import torch
from suppression_train import SupNet, evaluate
from suppression_env import SuppressionEnv
DEV = "cuda:0"
O = SuppressionEnv(2, DEV).obs_dim
def load(tag):
    net = SupNet(O).to(DEV)
    net.load_state_dict(torch.load("/home/younes/arma3-marl/leviathan/%s.pt" % tag, map_location=DEV))
    net.eval(); return net
v = load("suppression_voyant"); a = load("suppression_aveugle")
sv = evaluate(v, blind=False); bv = evaluate(a, blind=True)
print("=== BRIQUE SUPPRESSION (eval, n=4096) ===")
print("VOYANT (voit expo ami) ami arrive %.0f%%" % sv)
print("AVEUGLE (tir mal time)  ami arrive %.0f%%" % bv)
print("ECART = +%.0f pts  => %s" % (sv - bv, "la perception paie (loi +97)" if sv - bv > 10 else "gain faible"))
