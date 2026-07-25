#!/usr/bin/env python3
"""canary.py — CANARI D'ACTIVATION (garde-fou Fable) : sans ce feu vert, tout run Arma est POUBELLE.
Vérifie : (1) un joueur connecté, (2) défenseurs vivants, (3) ils OUVRENT LE FEU sur un appât exposé.
Un appât BLUFOR est posé à ~45m du FOB (à découvert) ; s'il prend des dégâts / meurt / est bien connu en N s -> IA ACTIVE."""
import sys, time, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

ap = argparse.ArgumentParser(); ap.add_argument("--fob", default="3253,2984"); ap.add_argument("--wait", type=int, default=12)
a = ap.parse_args(); fx, fy = [int(v) for v in a.fob.split(",")]
b = NativeBridge(port=5816)

# état de départ : joueurs + défenseurs
r = b.query('(format ["HARMATTAN_C0 players=%1 east=%2 alive=%3", count allPlayers, count (allUnits select {side _x==east}), count (allUnits select {side _x==east && alive _x})]) call HMT_EMIT;',
            r"HARMATTAN_C0 (players=\d+ east=\d+ alive=\d+)", want=1, timeout=10)
print("état :", r[-1].group(1) if r else "PAS DE RETOUR")

# pose un appât BLUFOR exposé au nord du FOB (côté approche), allowDamage true
b.send('HMT_CANARY = (createGroup west) createUnit ["B_soldier_F", [%d,%d,0], [], 0, "NONE"]; '
       'HMT_CANARY setPosATL [%d,%d,0]; HMT_CANARY allowDamage true; HMT_CANARY setUnitPos "UP"; '
       '{ _x reveal [HMT_CANARY, 4] } forEach (allUnits select {side _x==east});' % (fx, fy + 45, fx, fy + 45))
print("appât posé à %dm nord du FOB, attente %ds..." % (45, a.wait), flush=True)
time.sleep(a.wait)

# l'appât a-t-il été engagé ? dégâts / mort / connu
q = ('private _c = HMT_CANARY; private _dmg = if (isNull _c) then {1} else {damage _c}; '
     'private _al = if (isNull _c) then {0} else {alive _c}; '
     'private _kn = 0; { private _k = _x knowsAbout _c; if (_k > _kn) then {_kn = _k} } forEach (allUnits select {side _x==east && alive _x}); '
     '(format ["HARMATTAN_C1 dmg=%1 alive=%2 known=%3", _dmg toFixed 2, _al, _kn toFixed 1]) call HMT_EMIT;')
r2 = b.query(q, r"HARMATTAN_C1 dmg=([\d.]+) alive=(\d) known=([\d.]+)", want=1, timeout=10)
b.send('if (!isNil "HMT_CANARY" && {!isNull HMT_CANARY}) then { deleteVehicle HMT_CANARY };')   # nettoie l'appât

if r2:
    dmg = float(r2[-1].group(1)); al = int(r2[-1].group(2)); known = float(r2[-1].group(3))
    active = (dmg > 0.02) or (al == 0) or (known > 2.0)
    print("appât : dégâts=%.2f vivant=%d connu=%.1f" % (dmg, al, known))
    print("=== CANARI %s ===" % ("VERT : IA ACTIVE, on peut compter les runs" if active else "ROUGE : IA INERTE (joueur connecté ? défenseurs actifs ?) -> NE PAS lancer l'A/B"))
    sys.exit(0 if active else 2)
else:
    print("=== CANARI INDÉTERMINÉ (pas de retour) ==="); sys.exit(3)
