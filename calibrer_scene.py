#!/usr/bin/env python3
"""calibrer_scene — LA SCENE SE DIMENSIONNE AVANT DE JUGER QUOI QUE CE SOIT.

Le banc precedent rendait 1 a 2 morts sur 16 en 22 pas : la metrique deposee (survivants amis)
ne prenait que DEUX valeurs, et les trois bras sortaient identiques au centieme. Ce n est pas
« ils se valent », c est UN BANC QUI NE SEPARE PAS.

On ne devine pas le reglage : on BALAIE distance x competence, et on garde la configuration
qui produit assez de morts pour que la mesure ait de la place. AUCUNE politique n est jugee
ici — on dimensionne l instrument, comme on avait dimensionne la fenetre du raster.

CRITERE DE RECEVABILITE, ecrit avant : une configuration est retenue si elle produit en
mediane >= 4 morts amis sur 8 ET laisse >= 1 survivant — sinon la metrique sature en haut
(personne ne meurt) ou en bas (tout le monde meurt) et ne discrimine pas davantage.
"""
import sys, time, json, itertools
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
E = lambda t, *a: 'format ["%s"%s] call HMT_EMIT;' % (t, "".join("," + x for x in a))

def essai(b, dist, skill, pas, graine, nrouge=8, retranche=False):
    b.query('HMT_POS = [] call BIS_fnc_randomPos;'
            'HMT_POS = [HMT_POS, 0, 800, 12, 0, 0.25, 0] call BIS_fnc_findSafePos;'
            '{ if (!isPlayer _x) then { deleteVehicle _x } } forEach allUnits;'
            'HMT_GB = createGroup west; HMT_GO = createGroup east;'
            'for "_i" from 0 to 7 do { HMT_GB createUnit ["B_Soldier_F", HMT_POS vectorAdd [(_i mod 4)*6-9, floor(_i/4)*6, 0], [], 0, "NONE"] };'
            'for "_i" from 0 to %d do { HMT_GO createUnit ["O_Soldier_F", HMT_POS vectorAdd [(_i mod 6)*8-20, %d + floor(_i/6)*8, 0], [], 0, "NONE"] };'
            '{ _x setSkill %.2f; _x allowFleeing 0 } forEach allUnits;'
            '%s'
            'HMT_GB setBehaviour "COMBAT"; HMT_GO setBehaviour "COMBAT";'
            'HMT_GB setCombatMode "RED"; HMT_GO setCombatMode "RED";'
            'HMT_GB setSpeedMode "FULL"; HMT_GO setSpeedMode "FULL";'
            '{ _x reveal [leader HMT_GO, 4]; _x doMove (getPos leader HMT_GO) } forEach units HMT_GB;'
            '{ _x reveal [leader HMT_GB, 4]; _x doMove (getPos leader HMT_GB) } forEach units HMT_GO;'
            % (nrouge - 1, dist, skill,
               '{ _x setUnitPos "DOWN"; _x disableAI "PATH" } forEach units HMT_GO;' if retranche else '')
            + E("HMTSC %1", "count allUnits"), r"HMTSC (\d+)", want=1, timeout=40)
    time.sleep(pas)
    r = b.query(E("HMTR b=%1 o=%2", "{alive _x} count units HMT_GB", "{alive _x} count units HMT_GO"),
                r"HMTR b=(\d+) o=(\d+)", want=1, timeout=30)
    return (int(r[0].group(1)), int(r[0].group(2))) if r else (None, None)

print("=" * 92); print(" CALIBRER LA SCENE — elle se dimensionne, elle ne se choisit pas"); print("=" * 92)
print("  recevable si : mediane des morts amis >= 4 sur 8  ET  >= 1 survivant", flush=True)
b = None; res = {}
try:
    b = NativeBridge(port=5801, timeout=40)
    print("\n  %-22s %10s %10s %12s" % ("configuration", "bleus", "rouges", "morts amis"))
    # ⚠️ LE PREMIER BALAYAGE A TROUVE LA VRAIE CAUSE : les bleus gagnent 8 a 0. Ce n est ni
    # la duree ni la distance — c est le RAPPORT DE FORCES. Le gymnase, lui, oppose des
    # attaquants a des defenseurs RETRANCHES que l attaquant doit venir chercher.
    for dist, nrouge, retr in itertools.product((150, 250), (12, 20), (False, True)):
        skill, pas = 0.7, 180
        vals = []
        for g in (1, 2):
            bl, ro = essai(b, dist, skill, pas, g, nrouge=nrouge, retranche=retr)
            if bl is not None: vals.append((bl, ro))
        if not vals: continue
        mb = sorted(v[0] for v in vals)[len(vals) // 2]
        mo = sorted(v[1] for v in vals)[len(vals) // 2]
        morts = 8 - mb
        ok = (morts >= 4) and (mb >= 1)
        nom = "d=%d rouges=%d %s" % (dist, nrouge, "RETRANCHES" if retr else "mobiles")
        print("  %-26s %10d %10d %12d   %s" % (nom, mb, mo, morts, "✅ RECEVABLE" if ok else ""), flush=True)
        res[nom] = dict(bleus=mb, rouges=mo, morts=morts, recevable=ok)
    bons = [k for k, v in res.items() if v["recevable"]]
    print("\n  configurations RECEVABLES : %s" % (", ".join(bons) if bons else "AUCUNE"))
    if not bons:
        print("  ⛔ aucune ne fabrique assez de combat — il faudra changer autre chose")
        print("     (armement, terrain, effectif) avant de rejuger une politique ici.")
    json.dump(res, open('/mnt/data/calibration_scene.json', 'w'), indent=1)
finally:
    if b:
        try: b.close()
        except Exception: pass
