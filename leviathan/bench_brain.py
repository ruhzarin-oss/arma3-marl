#!/usr/bin/env python3
"""bench_brain.py — combien d'agents le CERVEAU tient-il ? (perceive+act+vitesse+tir, sans Arma)."""
import sys, time, torch
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from agent_swarm import AgentSwarm
from reflex_fight_train import FightNet

CKPT = "/home/younes/arma3-marl/leviathan/reflex_r23wh_voyant.pt"


def synth_hm(HN=400, hres=7.5):
    yy, xx = torch.meshgrid(torch.arange(HN), torch.arange(HN), indexing="ij")
    return (8 * torch.sin(xx.float() / 11) * torch.cos(yy.float() / 9)).float(), 0.0, 0.0, hres, HN


def bench(device, sizes):
    HM, hx0, hy0, hres, HN = synth_hm()
    body = FightNet(21, 8, 160)
    try: body.load_state_dict(torch.load(CKPT, map_location=device)); tag = "vrai reflex_r23wh"
    except Exception: tag = "net non charge (forme identique)"
    sw = AgentSwarm(body, HM, hx0, hy0, hres, HN, device=device)
    print("\n=== device=%s | %s ===" % (device, tag))
    print("   %8s | %10s | %12s | budget 10 Hz (100ms)" % ("agents", "ms/tick", "ms/agent"))
    for N in sizes:
        pos = torch.rand(N, 2, device=device) * 2800 + 100
        enemies = (torch.rand(40, 2) * 2800 + 100).tolist()
        prone = torch.zeros(N, device=device)
        goals = torch.rand(N, 2, device=device) * 2800 + 100
        for _ in range(3):                                            # warmup
            o, t, c = sw.perceive(pos, enemies, prone); m, s, f = sw.act(o); sw.decide_velocity(pos, m, t, c, goals); sw.bearings(f, t)
        if device.startswith("cuda"): torch.cuda.synchronize()
        R = 20 if N <= 5000 else 6
        t0 = time.time()
        for _ in range(R):
            o, t, c = sw.perceive(pos, enemies, prone); m, s, f = sw.act(o)
            vx, vy = sw.decide_velocity(pos, m, t, c, goals); idx, deg = sw.bearings(f, t)
        if device.startswith("cuda"): torch.cuda.synchronize()
        dt = (time.time() - t0) / R * 1000
        ok = "OK" if dt < 100 else "X"
        print("   %8d | %10.2f | %12.4f | %s" % (N, dt, dt / N, ok))


if __name__ == "__main__":
    sizes = [100, 500, 1000, 2000, 5000, 10000, 20000, 50000]
    bench("cpu", sizes)
    if torch.cuda.is_available():
        bench("cuda:0", sizes + [100000, 200000])                    # GPU = 3090
    else:
        print("\n(pas de CUDA)")
