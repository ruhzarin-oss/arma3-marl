import json, math
s = json.load(open("/home/younes/arma3-marl/staff/state.json"))
en = [e for e in s["enemies"] if e[2]]
z = sum(1 for e in en if e[0] == 0 and e[1] == 0)
bx = [u for nm, sq in s["squads"].items() for u in sq["units"] if u[2]]
dmin = min(math.hypot(u[0]-e[0], u[1]-e[1]) for u in bx for e in en) if (en and bx) else -1
ex = sum(e[0] for e in en)/len(en); ey = sum(e[1] for e in en)/len(en)
print("pas", s["step"], "| OPFOR vivants", len(en), "| a[0,0]:", z,
      "| centre OPFOR ~", int(ex), int(ey), "| dist BLU-OPF min", int(dmin), "m")
