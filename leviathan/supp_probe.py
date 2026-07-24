#!/usr/bin/env python3
"""supp_probe.py — SONDE DE SUPPRESSION (réflexion Fable, étape 1). Mesure si la base de feu WEST dégrade
le TIR des défenseurs. Défenseurs déjà spawnés (spawn_hard_east). Ici : ligne de feu WEST au standoff,
les deux camps immortels, puis 2 phases — WEST TIENT LE FEU (baseline) vs WEST SUPPRIME — en comptant les
tirs EAST par soldat vivant. Verdict : si le taux de tir EAST ne baisse pas -> la base de feu ne supprime rien."""
import sys, time, argparse, statistics
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

ap = argparse.ArgumentParser()
ap.add_argument("--fob", default="3253,2984"); ap.add_argument("--standoff", type=int, default=65)
ap.add_argument("--nwest", type=int, default=12); ap.add_argument("--ticks", type=int, default=22)
ap.add_argument("--wclass", default="B_soldier_F")   # B_soldier_F = fusilier ; B_soldier_AR_F = mitrailleur (VOLUME)
a = ap.parse_args(); fx, fy = [int(v) for v in a.fob.split(",")]
b = NativeBridge(port=5816)


def spawn_west_line(n, standoff, wclass):
    sqf = ('[] spawn { if (!isNil "HMT_WPILOT") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_WPILOT }; HMT_WPILOT=[]; HMT_FOB=[%d,%d]; '
           'private _g = createGroup west; for "_i" from 0 to %d do { if (_i mod 8 == 0) then { _g = createGroup west }; '
           'private _px=%d+(_i-%d)*5; private _py=%d; '
           'private _u = _g createUnit ["%s",[_px,_py,0],[],0,"NONE"]; '
           'if (!isNull _u) then { _u setPosATL [_px,_py,0]; HMT_WPILOT pushBack _u }; }; '
           'call HMT_SHAMAL_ARM; (format ["HARMATTAN_SHL west=%%1", count HMT_WPILOT]) call HMT_EMIT; }') % (
               fx, fy, n - 1, fx, n // 2, fy + standoff, wclass)
    return b.query(sqf, r"HARMATTAN_SHL west=(\d+)", want=1, timeout=60)


def rearm():
    b.send('{ if (alive _x) then { _x setVehicleAmmo 1 } } forEach HMT_EAST;')


def measure(phase_fn, K, warm=3):
    samples = []   # (eshots_cumul, alive_east, alive_west)
    for t in range(K + warm):
        b.send("call %s;" % phase_fn)
        r = b.query("call HMT_SUPP_SENSE;", r"HARMATTAN_SUPP (\d+) (\d+) (\d+)", want=1, timeout=10)
        if r:
            samples.append((int(r[-1].group(1)), int(r[-1].group(2)), int(r[-1].group(3))))
        time.sleep(1.0)
    # taux de tir EAST par défenseur vivant, en ignorant le warm-up
    rates = []
    for i in range(warm + 1, len(samples)):
        d = samples[i][0] - samples[i - 1][0]; alive = max(samples[i][1], 1)
        rates.append(d / alive)
    return rates, samples[-1][1]


print("=== SONDE DE SUPPRESSION (Fable étape 1) : la base de feu WEST supprime-t-elle les défenseurs ? ===", flush=True)
b.send('call compile preprocessFileLineNumbers "shamal_obs.sqf";'); time.sleep(0.4)
b.send('call compile preprocessFileLineNumbers "supp_probe.sqf";'); time.sleep(0.4)
r = spawn_west_line(a.nwest, a.standoff, a.wclass)
print("ligne de feu WEST : %s x %s au standoff %dm" % (r[-1].group(1) if r else "?", a.wclass, a.standoff), flush=True)
s = b.query("call HMT_SUPP_SETUP;", r"HARMATTAN_SUPPSET east=(\d+) west=(\d+)", want=1, timeout=20)
print("sonde armée : EAST=%s WEST=%s (immortels, event-handler Fired sur EAST)" % (s[-1].group(1) if s else "?", s[-1].group(2) if s else "?"), flush=True)

print("--- MESURE ENTRELACÉE : HOLD/FIRE alternés par blocs de 3 (dé-confond le temps) ---", flush=True)
BLOCK = 3
hold_rates = []; fire_rates = []; prev = None
for t in range(a.ticks * 2):
    mode_fire = (t // BLOCK) % 2 == 1
    b.send("call %s;" % ("HMT_SUPP_FIRE" if mode_fire else "HMT_SUPP_HOLD"))
    r = b.query("call HMT_SUPP_SENSE;", r"HARMATTAN_SUPP (\d+) (\d+) (\d+)", want=1, timeout=10)
    if r:
        es = int(r[-1].group(1)); ea = max(int(r[-1].group(2)), 1)
        if prev is not None and (t % BLOCK) != 0:        # ignore le 1er tick de chaque bloc (latence de bascule)
            (fire_rates if mode_fire else hold_rates).append((es - prev) / ea)
        prev = es
    if t % 6 == 0: rearm()
    time.sleep(1.0)
mA = statistics.mean(hold_rates) if hold_rates else 0.0; mB = statistics.mean(fire_rates) if fire_rates else 0.0
red = 100 * (mA - mB) / mA if mA > 0 else 0.0
print("", flush=True)
print("=== RÉSULTAT (entrelacé, %d échantillons HOLD / %d FIRE) ===" % (len(hold_rates), len(fire_rates)), flush=True)
print("  tir EAST / défenseur vivant / tick :  WEST tient=%.2f   WEST supprime=%.2f" % (mA, mB), flush=True)
print("  RÉDUCTION du feu défenseur sous suppression : %.0f%%" % red, flush=True)
if red >= 30:
    print("  >>> la base de feu SUPPRIME (réduction nette) -> le bounding a une chance ; on peut construire le feu-et-mouvement.", flush=True)
elif red >= 10:
    print("  >>> suppression FAIBLE -> il faut du VOLUME (mitrailleuses côté WEST) avant tout bounding.", flush=True)
else:
    print("  >>> la base de feu ne supprime RIEN de mesurable (hypothèse Fable confirmée) -> aucune manœuvre ne marchera sans volume de feu.", flush=True)
print("SUPP_DONE", flush=True)
