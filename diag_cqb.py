"""diag_cqb — MODULE CQB (test). Même scénario que diag_urban (8 assaut vs 20 défenseurs dans le bâti de Paros),
mais au lieu de viser une COORDONNÉE (qui tombe sous un toit, injoignable -> l'assaut se figeait à 47 m), on route
chaque assaillant vers une VRAIE position de bâtiment (`buildingPos`) du bâtiment qui abrite des défenseurs.
On mesure : l'assaut ENTRE-t-il enfin (dist mini chute, assaut au bâti monte) et NETTOIE-t-il (défenseurs tombent) ?"""
import time, re
import numpy as np
from op_arma import OpArma
import paros as M
SB = "/mnt/data/harmattan-sandbox"
CX, CY = M.COMPLEXE
env = OpArma(squads=(("ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge2.Altis",
             log=SB + "/logs/server2.out", move=30, acc=1.0, seed=5)
print("spawn : assaut(8) a 70m sud + 20 defenseurs dans le bati de Paros", flush=True)
env.spawn({"ASSAUT": (CX, CY - 70)}, [(CX, CY, 20, 12)])
env._query('{ private _g=_x; while {count waypoints _g > 0} do {deleteWaypoint [_g,0]}; { _x setBehaviour "COMBAT"; doStop _x } forEach units _g; } forEach (allGroups select {side _x == east});'
           '{ _x setBehaviour "COMBAT"; _x setUnitPos "UP"; _x enableAI "PATH"; } forEach ASSAUT; diag_log "HARMATTAN_OK";', settle=1.0)
env.read()

# routine CQB : router chaque assaillant vers une buildingPos d'un batiment qui abrite un defenseur vivant
CQB = ('private _ae = HMT_EN select {alive _x};\n'
       'private _blds = [];\n'
       '{ private _b = nearestBuilding _x; if (!isNull _b && {count (_b buildingPos -1) > 0}) then { _blds pushBackUnique _b }; } forEach _ae;\n'
       'private _pos = [];\n'
       '{ _pos append (_x buildingPos -1); } forEach _blds;\n'
       'if (count _pos == 0) then { if (count _ae > 0) then { _pos = [getPosATL (_ae select 0)] } else { _pos = [[%d,%d,0]] }; };\n'
       '{ private _u = ASSAUT select _forEachIndex; if (alive _u) then { _u doMove (_pos select (_forEachIndex mod (count _pos))); _u setUnitPos "UP"; }; } forEach ASSAUT;\n'
       '{ if (alive _x) then { doStop _x; } } forEach HMT_EN;\n'
       'diag_log "HARMATTAN_CQB";\n' % (CX, CY))

print("pas | dist_mini | def_vivants | assaut_au_bati | assaut_vivants", flush=True)
for step in range(1, 31):
    env.b.send(CQB, wait=True)
    time.sleep(1.3)
    env.read()
    al = env.alive(0); eal = env.en_alive()
    if al.any() and eal.any():
        d = np.sqrt((env.px[0][al][:, None] - env.epx[eal][None, :]) ** 2 + (env.py[0][al][:, None] - env.epy[eal][None, :]) ** 2)
        mind = int(d.min())
    else:
        mind = -1
    ls = env._query('private _ha = { (alive _x) && {(count (_x nearObjects ["House",10])) > 0} } count ASSAUT;'
                    'diag_log format ["HARMATTAN_B assbati=%1", _ha];', settle=0.6)
    assb = -1
    for l in ls:
        m = re.search(r"HARMATTAN_B assbati=(\d+)", l)
        if m:
            assb = int(m.group(1))
    if step % 2 == 0 or step <= 4:
        print("%3d | %8d | %10d | %13d | %d" % (step, mind, int(eal.sum()), assb, int(al.sum())), flush=True)
print("FINI", flush=True)
