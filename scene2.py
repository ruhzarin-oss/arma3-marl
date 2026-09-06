#!/usr/bin/env python3
"""scene2 — LE COMBAT A COMMENCE (16 -> 14). On le laisse se derouler et on le MESURE.

⚠️ LECON DU PASSAGE PRECEDENT : `currentCommand` peut rendre une CHAINE VIDE, le motif ne
   matche pas, et le compteur du pont DESYNCHRONISE — « ordre 35 non acquitte ». On n emet
   plus que des NOMBRES : jamais de champ qui puisse etre vide.
"""
import sys, time
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
B = NativeBridge(port=5801, timeout=25)
E = lambda t, *a: 'format ["%s"%s] call HMT_EMIT;' % (t, "".join("," + x for x in a))
def q(sqf, pat, t=25):
    try: return B.query(sqf, pat, want=1, timeout=t)
    except Exception as e: print("    (pont : %s)" % str(e)[:60]); return None

print("=" * 90); print(" LA SCENE COMBAT — on mesure le deroulement"); print("=" * 90)
r = q(E("HMTS n=%1 b=%2 o=%3 d=%4", "count allUnits",
        "{alive _x && side _x == west} count allUnits",
        "{alive _x && side _x == east} count allUnits",
        "round ((getPos leader HMT_GB) distance (getPos leader HMT_GO))"),
      r"HMTS n=(\d+) b=(\d+) o=(\d+) d=(\d+)")
if not r: print("  ⛔ le pont ne repond pas"); sys.exit(1)
n0, b0, o0, d0 = (int(g) for g in r[0].groups())
print("  depart : %d unites  (bleus %d, rouges %d)  distance %d m" % (n0, b0, o0, d0))

print("\n─── ORDRES EXPLICITES : se chercher et engager ───")
q('HMT_GB setBehaviour "COMBAT"; HMT_GO setBehaviour "COMBAT";'
  'HMT_GB setSpeedMode "FULL"; HMT_GO setSpeedMode "FULL";'
  'HMT_GB setCombatMode "RED"; HMT_GO setCombatMode "RED";'
  '{ _x doMove (getPos leader HMT_GO); _x reveal [leader HMT_GO, 1.5] } forEach units HMT_GB;'
  '{ _x doMove (getPos leader HMT_GB); _x reveal [leader HMT_GB, 1.5] } forEach units HMT_GO;'
  + E("HMTOK %1", "count allUnits"), r"HMTOK (\d+)")
print("  ordres passes (COMBAT, FULL, RED, doMove + reveal mutuel)")

print("\n  %-5s %8s %8s %8s %10s %10s" % ("t(s)", "bleus", "rouges", "dist", "vus par E", "vus par W"))
t0 = time.time(); hist = []
for k in range(10):
    time.sleep(20)
    r = q(E("HMTP b=%1 o=%2 d=%3 ve=%4 vw=%5",
            "{alive _x && side _x == west} count allUnits",
            "{alive _x && side _x == east} count allUnits",
            "round ((getPos leader HMT_GB) distance (getPos leader HMT_GO))",
            "{ alive _x && side _x == west && {(east knowsAbout _x) > 1} } count allUnits",
            "{ alive _x && side _x == east && {(west knowsAbout _x) > 1} } count allUnits"),
          r"HMTP b=(\d+) o=(\d+) d=(\d+) ve=(\d+) vw=(\d+)")
    if not r: continue
    b, o, d, ve, vw = (int(g) for g in r[0].groups())
    hist.append((b, o, d))
    print("  %-5.0f %8d %8d %8d %10d %10d" % (time.time() - t0, b, o, d, ve, vw), flush=True)
    if b == 0 or o == 0:
        print("  -> un camp est aneanti, le combat est termine."); break

print("\n─── VERDICT ───")
if hist:
    b, o, d = hist[-1]
    morts = (b0 + o0) - (b + o)
    print("  morts pendant l observation : %d   distance %d m -> %d m" % (morts, d0, d))
    if morts >= 3 and d < d0:
        print("  ✅ LA SCENE EST MESURABLE : ils se cherchent, se trouvent, et meurent.")
        print("     Arma peut desormais servir de banc — c est ce que le gymnase ne pouvait pas donner.")
    elif morts > 0:
        print("  ~ des morts, mais peu : le contact est lent. Rapprocher les camps au prochain montage.")
    else:
        print("  ⛔ aucun mort : ils ne s engagent pas malgre COMBAT/RED/reveal. A instruire.")
B.close()
