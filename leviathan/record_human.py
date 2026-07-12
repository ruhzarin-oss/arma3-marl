#!/usr/bin/env python3
"""record_human.py — enregistre le JOUEUR (slot WEST attaquant) tick par tick en demonstrations.
Pont FICHIER (leviathan001_live garde le pont natif). Logge pos + vitesse(=action) + cap + posture +
ennemis east vus -> human_demos.jsonl. Sert a l'apprentissage par imitation des agents (obs->action)."""
import sys, time, json, re, ast
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from arma_bridge import ArmaBridge

MIS = "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanFOB.Stratis"
LOG = "/mnt/data/harmattan-sandbox/logs/server_fob.out"
OUT = "/home/younes/arma3-marl/leviathan/human_demos.jsonl"
PAT = re.compile(r'x=(-?\d+) y=(-?\d+) vx=(-?[\d.]+) vy=(-?[\d.]+) dir=(-?\d+) st=(-?\d+) alive=(\d) side=(\w+) en=(\[.*\])')


def main():
    b = ArmaBridge(mission=MIS, log=LOG)
    b.send('call compile preprocessFileLineNumbers "human_state.sqf";', timeout=15); time.sleep(1)
    f = open(OUT, "a"); n = 0
    print("[record] joueur WEST -> %s" % OUT, flush=True)
    while True:
        r = b.query("call HMT_HUMAN;", r'HARMATTAN_HUM (.+)', want=1, timeout=8)
        if r:
            m = PAT.search(r[-1].group(1).rstrip('"').strip())
            if m:
                rec = {"t": round(time.time(), 1),
                       "x": int(m.group(1)), "y": int(m.group(2)),
                       "vx": float(m.group(3)), "vy": float(m.group(4)),
                       "dir": int(m.group(5)), "stance": int(m.group(6)),
                       "alive": int(m.group(7)), "side": m.group(8),
                       "enemies": ast.literal_eval(m.group(9))}
                if rec["side"] == "WEST" and rec["alive"] == 1:                  # ne garde que le joueur attaquant vivant
                    f.write(json.dumps(rec) + "\n"); f.flush(); n += 1
                    if n % 20 == 0:
                        print("[record] %d frames | pos=(%d,%d) v=(%.1f,%.1f) ennemis_vus=%d"
                              % (n, rec["x"], rec["y"], rec["vx"], rec["vy"], len(rec["enemies"])), flush=True)
        time.sleep(0.4)


if __name__ == "__main__":
    main()
