"""leviathan_live.py — MODE LIVE de LEVIATHAN.
La faction APPRISE (leviathan_e1_policy.pt) pilote UN seul monde qui tique en temps reel.
Chaque tick est HORODATE -> history_live.jsonl, avec les ORDRES par secteur (TENIR/RENFORCER/DEGARNIR).
Campagnes enchainees (a l'effondrement, nouvelle campagne) = monde persistant a regarder.
--ticks 0 = infini (Ctrl-C pour stopper) ; --cadence = secondes reelles par tick.
"""
import os, json, time, argparse
from datetime import datetime, timezone
import torch
from leviathan_env import LeviathanEnv, SECTORS
from train_leviathan import Net, act

HIST = "/home/younes/arma3-marl/leviathan/history_live.jsonl"
MAC = ["TENIR", "RENFORCER", "DEGARNIR"]


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main(threat=0.37, cadence=1.0, ticks=0, policy="leviathan_e1_policy.pt", fresh=True):
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    if fresh and os.path.exists(HIST):
        os.remove(HIST)
    e = LeviathanEnv(num_envs=1, device=dev, threat_rate=threat)
    net = Net(e.obs_dim, e.K, 256).to(dev)
    net.load_state_dict(torch.load(policy, map_location=dev)); net.eval()
    o = e.reset(); camp = 1; tick = 0; total = 0
    print("LEVIATHAN LIVE | politique=%s | menace=%.2f | cadence=%.2fs/tick" % (policy, threat, cadence))
    print("historique horodate -> %s\n" % HIST, flush=True)
    try:
        while ticks == 0 or total < ticks:
            owner_before = e.owner[0].clone()
            with torch.no_grad():
                a, _, _, _ = act(net, o, greedy=True)
            o, r, done, info = e.step(a, auto_reset=False)
            tick += 1; total += 1
            a0 = a[0].tolist()
            held = [i for i in range(e.K) if e.owner[0, i] > 0]
            lost = [SECTORS[i][0] for i in range(e.K) if owner_before[i] > 0 and e.owner[0, i] <= 0]
            rec = {"ts": now_iso(), "campagne": camp, "tick": tick, "secteurs_tenus": len(held),
                   "garnisons": {SECTORS[i][0]: round(float(e.garr[0, i]), 1) for i in held},
                   "muns": {SECTORS[i][0]: round(float(e.supply[0, i])) for i in held},
                   "menace": {SECTORS[i][0]: round(float(e.threat[0, i]), 1) for i in held},
                   "reserve": round(float(e.reserve[0]), 1),
                   "ordres": {SECTORS[i][0]: MAC[a0[i]] for i in held},
                   "renforts_actifs": bool(e.owner[0, e.hq] > 0), "depot_actif": bool(e.owner[0, e.depot] > 0),
                   "secteurs_perdus": lost, "reward": round(float(r[0]), 2)}
            with open(HIST, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            flags = "".join("#" if e.owner[0, i] > 0 else "." for i in range(e.K))
            ordres = " ".join("%s:%s" % (SECTORS[i][0][:4], MAC[a0[i]][:4]) for i in held)
            print("C%d t%03d [%s] tenus=%d res=%4.1f | %s%s" % (
                camp, tick, flags, len(held), float(e.reserve[0]), ordres,
                ("  >>PERDU " + ",".join(lost) if lost else "")), flush=True)
            if done[0] > 0:
                outcome = "EFFONDREE" if float(info["survived"][0]) < 0.5 else "a TENU (timeout)"
                print(">>> campagne %d : %s au tick %d -> nouvelle campagne\n" % (camp, outcome, tick), flush=True)
                e.reset(); o = e._obs(); camp += 1; tick = 0
            if cadence > 0:
                time.sleep(cadence)
    except KeyboardInterrupt:
        pass
    print("\n[stop] %d ticks, %d campagnes | historique -> %s" % (total, camp, HIST), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--threat", type=float, default=0.37)
    p.add_argument("--cadence", type=float, default=1.0)
    p.add_argument("--ticks", type=int, default=0)
    p.add_argument("--policy", type=str, default="leviathan_e1_policy.pt")
    a = p.parse_args()
    main(threat=a.threat, cadence=a.cadence, ticks=a.ticks, policy=a.policy)
