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


r = b.query('call compile preprocessFileLineNumbers "combat_parity.sqf";', r"HARMATTAN_CB DONE", want=1, timeout=80)
print("trigger:", ("DONE " + r[-1].group(0).split("DONE")[-1]) if r else "PAS de DONE")
time.sleep(1)
txt = open(LOG, errors="ignore").read().splitlines()
rows = []
for ln in txt:
    m = re.search(r"HARMATTAN_CB (DEF|ATK) supp=(\S+) kn=(\S+) v=(\[[^\]]*\])", ln)
    if m:
        rows.append((m.group(1), m.group(2), m.group(3), ast.literal_eval(m.group(4))))
# garder le dernier run (apres le dernier 'inject')
inj = max((i for i, l in enumerate(txt) if "HARMATTAN_CB inject" in l), default=0)
rows = []
for ln in txt[inj:]:
    m = re.search(r"HARMATTAN_CB (DEF|ATK) supp=(\S+) kn=(\S+) v=(\[[^\]]*\])", ln)
    if m:
        rows.append((m.group(1), m.group(2), m.group(3), ast.literal_eval(m.group(4))))
if not rows:
    print("Aucune ligne de combat. (unites pas encore au contact ?)")
    sys.exit(0)
net = Net(); net.load_state_dict(torch.load("/home/younes/arma3-marl/leviathan/orchestration_arma_voyant.pt", map_location="cpu")); net.eval()
print("        " + " ".join("%-5s" % f for f in FN) + "  -> tactique")
cols = [[] for _ in range(10)]; tac = {}
with torch.no_grad():
    for lab, supp, kn, v in rows:
        lg, _ = net(torch.tensor([v], dtype=torch.float32)); am = int(lg.argmax())
        tac[TAC[am]] = tac.get(TAC[am], 0) + 1
        for i in range(10):
            cols[i].append(v[i])
        print("%-4s " % lab + " ".join("%-5.2f" % x for x in v) + "  -> %s" % TAC[am])
print("\n=== plage par feature ===")
for i in range(10):
    if cols[i]:
        print("  %-6s %.2f .. %.2f" % (FN[i], min(cols[i]), max(cols[i])))
print("\n=== repartition tactiques:", tac)
