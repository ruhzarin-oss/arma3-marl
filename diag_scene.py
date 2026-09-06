#!/usr/bin/env python3
"""diag_scene — POURQUOI PERSONNE NE COMBAT ? On mesure, on ne suppose pas."""
import sys, time
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
B = NativeBridge(port=5801, timeout=20)
def q(sqf, pat, t=20):
    return B.query(sqf, pat, want=1, timeout=t)
E = lambda txt, *a: 'format ["%s"%s] call HMT_EMIT;' % (txt, "".join("," + x for x in a))

print("=" * 88); print(" POURQUOI PERSONNE NE COMBAT ?"); print("=" * 88)

r = q(E("HMTA n=%1 armes=%2 balles=%3 chef=%4",
        "count allUnits",
        "{ (primaryWeapon _x) != \"\"\"\" } count allUnits",
        "{ someAmmo _x } count allUnits",
        "{ _x == leader group _x } count allUnits"),
      r"HMTA n=(\d+) armes=(\d+) balles=(\d+) chef=(\d+)")
if r: print("  1. unites %s | avec arme %s | avec munitions %s | chefs %s" % r[0].groups())

r = q(E("HMTD d=%1 bleuIA=%2 rougeIA=%3",
        "round ((getPos leader HMT_GB) distance (getPos leader HMT_GO))",
        "{ !isNull _x && {simulationEnabled _x} } count units HMT_GB",
        "{ !isNull _x && {simulationEnabled _x} } count units HMT_GO"),
      r"HMTD d=(\d+) bleuIA=(\d+) rougeIA=(\d+)")
if r: print("  2. distance entre chefs %s m | simulation active bleu %s rouge %s" % r[0].groups())

r = q(E("HMTC bleu=%1 rouge=%2 vue=%3",
        "currentCommand (leader HMT_GB)", "currentCommand (leader HMT_GO)",
        "round ((leader HMT_GO) knowsAbout (leader HMT_GB) * 100) / 100"),
      r"HMTC bleu=(\S*) rouge=(\S*) vue=([\d.]+)")
if r: print("  3. ordre en cours — bleu '%s' rouge '%s' | knowsAbout %s" % r[0].groups())

r = q(E("HMTB comportement=%1 vitesse=%2 formation=%3",
        "behaviour (leader HMT_GB)", "speedMode HMT_GB", "formation HMT_GB"),
      r"HMTB comportement=(\S+) vitesse=(\S+) formation=(\S+)")
if r: print("  4. comportement %s | vitesse %s | formation %s" % r[0].groups())

print("\n─── ON DONNE UN ORDRE EXPLICITE, PUIS ON REGARDE S ILS BOUGENT ───")
q('HMT_GB setBehaviour "AWARE"; HMT_GO setBehaviour "AWARE";'
  'HMT_GB setSpeedMode "FULL"; HMT_GO setSpeedMode "FULL";'
  'HMT_GB setCombatMode "RED"; HMT_GO setCombatMode "RED";'
  'HMT_D0 = (getPos leader HMT_GB) distance (getPos leader HMT_GO);'
  '{ _x doMove (getPos leader HMT_GO) } forEach units HMT_GB;'
  '{ _x doMove (getPos leader HMT_GB) } forEach units HMT_GO;'
  + E("HMTORDRE d0=%1", "round HMT_D0"), r"HMTORDRE d0=(\d+)")
for k in range(5):
    time.sleep(15)
    r = q(E("HMTM t=%1 d=%2 vivants=%3 tir=%4",
            str(k), "round ((getPos leader HMT_GB) distance (getPos leader HMT_GO))",
            "{alive _x} count allUnits",
            "{ (currentCommand _x) in [\"\"FIRE\"\",\"\"ATTACK\"\"] } count allUnits"),
          r"HMTM t=(\d+) d=(\d+) vivants=(\d+) tir=(\d+)")
    if r: print("  t=%-2s  distance %-5s m  vivants %-3s  en tir/attaque %s" % r[0].groups(), flush=True)
B.close()
