"""diag_sape — laquelle des deux conditions de sape bloque ?

La sape exige : (a) au moins un assaillant a moins de 25 m de la cible,
                (b) AUCUN defenseur est vivant a moins de 40 m.
On mesure les deux en direct pendant l'assaut. Si (a) ne se realise jamais, les sapeurs
n'arrivent pas — probleme d'approche. Si (a) se realise mais (b) jamais, c'est la garnison
qui protege, et c'est alors le RAYON qu'il faut revoir, pas la mecanique.
"""
import sys, time
sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

Q = '''private _t = objNull;
{ if ((_x getVariable ["HMT_TARGET",""]) == "INTEL" && {alive _x}) exitWith { _t = _x }; } forEach HMT_TARGET;
private _atk = HMT_PB_ATK select { !isNull _x && alive _x };
private _d = if (count _atk > 0 && !isNull _t) then { selectMin (_atk apply { _x distance2D _t }) } else { -1 };
private _p25 = if (isNull _t) then { -1 } else { count (_atk select { (_x distance2D _t) < 25 }) };
private _def40 = if (isNull _t) then { -1 } else { count (allUnits select { side _x == east && alive _x && (_x distance2D _t) < 40 }) };
private _dmg = if (isNull _t) then { -1 } else { damage _t };
(format ["SAPEDBG atk=%1 dmin=%2 a25=%3 def40=%4 dmg=%5 sapeon=%6", count _atk, round _d, _p25, _def40, _dmg, HMT_PB_SAPE_ON]) call HMT_EMIT;'''

b = NativeBridge(port=5816)
try:
    b.send('call compile preprocessFileLineNumbers "pressure_bench.sqf";')
    time.sleep(1.5)
    print("--- reset ---")
    b.send('[] spawn { call HMT_PB_RESET; };')
    b.query('', r'HARMATTAN_PB_RESET (.+)', want=1, timeout=200)
    time.sleep(8)
    b.send('HMT_PB_GEL = true;')
    b.query('call HMT_PB_COHORTE;', r'HARMATTAN_PB_COHORTE (.+)', want=1, timeout=30)

    print("--- attaque M4 + sape INTEL ---")
    b.send('[[3], 48, "INTEL"] spawn HMT_PB_ATTACK;')
    r = b.query('', r'HARMATTAN_PB_ATTACK (.+)', want=1, timeout=120)
    print("  ", r[-1].group(1).strip().rstrip('"') if r else "AUCUN EMIT")

    print("\n  %-8s %s" % ("t", "atk / distance_min / a_moins_de_25m / defenseurs_a_40m / degats / sape_active"))
    for i in range(8):
        time.sleep(45)
        r = b.query(Q, r'SAPEDBG (.+)', want=1, timeout=25)
        print("  t+%03ds  %s" % ((i + 1) * 45, r[-1].group(1).strip().rstrip('"') if r else "MUET"), flush=True)
finally:
    try:
        b.send('HMT_PB_GEL = false;'); b.send('HMT_PB_SAPE_ON = false;'); b.close()
    except Exception:
        pass
