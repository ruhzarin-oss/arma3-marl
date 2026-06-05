import time
from arma_bridge import ArmaBridge
b = ArmaBridge()
print(">>> spawn d'une squad BLUFOR de 4")
b.send('HMT_GRP = createGroup west; for "_i" from 0 to 3 do { HMT_GRP createUnit ["B_Soldier_F", [1000 + _i*4, 1000, 0], [], 0, "FORM"]; }; diag_log format ["HARMATTAN_SPAWN total=%1", count allUnits];')
time.sleep(2)
print(">>> observation initiale")
for u in b.read_obs(): print("   ", u)
print(">>> ordre : tout le monde vers (1120,1120)")
b.send('{ _x doMove [1120,1120,0]; } forEach allUnits;')
print(">>> on attend 9 s puis on relit")
time.sleep(9)
for u in b.read_obs(): print("   ", u)
print("OK pont S3")
