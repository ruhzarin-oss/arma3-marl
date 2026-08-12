import sys, time, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
import arma_couture as C
import torch
from porter_boucle import charger, COLS

C.CX, C.CY, C.SCALE, C.FIRE_RANGE = 1734.0, 5391.0, 200.0, 110.0
b = SocketBridge(5830)
time.sleep(1)
b.send(re.sub(r"//.*$", "", C.perc_sqf(), flags=re.M), wait=False)
time.sleep(3)
obs = C.parse_obs(b._log_lines(900))
NOMS = ["apx/S", "apy/S", "dgx", "dgy", "alive", "slope", "dcover", "los", "nd",
        "dmgin", "ntf", "adx", "ady", "asup", "tff", "p0", "p1", "p2"]
print(f"\n  {len(obs)} hommes vus par la couture")
if obs:
    print("  " + "".join(f"{n:>8}" for n in NOMS))
    for i in sorted(obs)[:4]:
        print("  " + "".join(f"{v:>8.2f}" for v in obs[i]))
    o = torch.tensor([obs[i] for i in sorted(obs)], dtype=torch.float32)
    pol = charger()
    with torch.no_grad():
        lo, _ = pol(o[:, COLS])
    print(f"\n  actions rendues : {lo.argmax(-1).tolist()}")
    print(f"  logits du 1er homme : {[round(x,2) for x in lo[0].tolist()]}")
    print("\n  ---- ce que le gymnase donnait, pour comparaison ----")
    from assault_terrain import AssaultTerrain
    from monde_fidele import MONDE_ARMA
    e = AssaultTerrain(num_envs=4, seed=3, device="cpu", max_steps=60, **MONDE_ARMA)
    og = e.reset()
    print("  " + "".join(f"{n:>8}" for n in
          ["apx/S", "apy/S", "dgx", "dgy", "alive", "slope", "dcover", "los", "nd", "p0", "p1", "p2"]))
    for k in range(3):
        print("  " + "".join(f"{v:>8.2f}" for v in og[0, k].tolist()))
b.sock.close()
