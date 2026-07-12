#!/usr/bin/env python3
"""gear_test.py — verifie qu'on peut equiper un FS avec du gear RHS/ACE sur le serveur modde."""
import sys, time, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge

SB = "/mnt/data/harmattan-sandbox"
b = ArmaBridge(mission=SB + "/arma3server/mpmissions/HarmattanBridge14.Stratis", log=SB + "/logs/server14.out")
time.sleep(2)
cmd = ('private _u = (createGroup west) createUnit ["B_recon_F", [5300,3300,0], [], 0, "FORM"]; '
       'removeAllWeapons _u; _u addWeapon "rhs_weap_m4a1"; _u addPrimaryWeaponItem "rhsusf_acc_eotech"; '
       '_u linkItem "rhsusf_ANPVS_15"; _u addItem "ACE_fieldDressing"; '
       'diag_log format ["HARMATTAN_GEAR arme=%1 | nvg=%2 | ace=%3", primaryWeapon _u, hmd _u, "ACE_fieldDressing" in (items _u)];')
b.send(cmd)
time.sleep(1.5)
out = None
for ln in reversed(b._log_lines(200)):
    m = re.search(r"HARMATTAN_GEAR (.+)", ln)
    if m:
        out = m.group(1).strip().rstrip('"'); break
print("RESULTAT GEAR:", out if out else "pas de reponse")
