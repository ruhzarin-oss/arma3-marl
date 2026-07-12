#!/usr/bin/env python3
import sys, time, re, ast
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge
import torch, torch.nn as nn
LOG = "/mnt/data/harmattan-sandbox/logs/server_fob.out"
b = ArmaBridge(mission="/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanFOB.Stratis", log=LOG)
FN = ["dist", "vis", "behnd", "entr", "expo", "openg", "fire", "gren", "smoke", "alli"]
TAC = ["TIR", "GRENADE", "FLANC", "FUMI", "SUPPR"]


class Net(nn.Module):
    def __init__(s):
        super().__init__()
        s.b = nn.Sequential(nn.Linear(10, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        s.a = nn.Linear(128, 5); s.v = nn.Linear(128, 1)
    def forward(s, x):
        h = s.b(x); return s.a(h), s.v(h)


r = b.query('call compile preprocessFileLineNumbers "parity_test2.sqf";', r"HARMATTAN_PAR DONE", want=1, timeout=30)
print("trigger:", "DONE recu" if r else "PAS de DONE (voir erreurs)")
time.sleep(1)
txt = open(LOG, errors="ignore").read().splitlines()
rows = []
for ln in txt:
    m = re.search(r"HARMATTAN_PAR (\w+) known=(\S+) v=(\[[^\]]*\])", ln)
    if m and m.group(1) not in ("DONE", "nodefender"):
        rows.append((m.group(1), m.group(2), ast.literal_eval(m.group(3))))
rows = rows[-3:]
if not rows:
    errs = [l for l in txt if ("Error" in l and "reveal: Type Side" not in l)][-5:]
    print("Aucune ligne PAR. Erreurs recentes:")
    for e in errs:
        print("  ", e)
    sys.exit(0)
net = Net(); net.load_state_dict(torch.load("/home/younes/arma3-marl/leviathan/orchestration_arma_voyant.pt", map_location="cpu")); net.eval()
print("        " + " ".join("%-5s" % f for f in FN) + "  known -> tactique")
cols = [[] for _ in range(10)]
with torch.no_grad():
    for lab, known, v in rows:
        lg, _ = net(torch.tensor([v], dtype=torch.float32)); am = int(lg.argmax())
        for i in range(10):
            cols[i].append(v[i])
        print("%-12s " % lab + " ".join("%-5.2f" % x for x in v) + "  k=%-4s -> %s" % (known, TAC[am]))
print("\n=== plage par feature (dans [0,1] et varie ?) ===")
for i in range(10):
    if cols[i]:
        print("  %-6s %.2f .. %.2f" % (FN[i], min(cols[i]), max(cols[i])))
