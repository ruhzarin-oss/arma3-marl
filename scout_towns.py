"""scout_towns — etape 1 : trouver un VRAI objectif sur Altis (ville/village sur relief, du bati, du couvert)
pour quitter la plage. Liste les localites + densite de batiments + altitude -> on choisit le nouveau theatre."""
import re
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
sqf = (
    'private _locs = nearestLocations [[15000,15000,0], ["NameCityCapital","NameCity","NameVillage","NameLocal"], 30000];\n'
    '{ private _p = locationPosition _x;\n'
    '  private _nb = ({_x isKindOf "House"} count (_p nearObjects ["House", 140]));\n'
    '  private _hi = 0; { private _hh = getTerrainHeightASL [(_p#0)+(_x#0), (_p#1)+(_x#1)]; if (_hh > _hi) then {_hi=_hh}; } forEach [[0,0],[150,0],[-150,0],[0,150],[0,-150],[120,120],[-120,-120]];\n'
    '  diag_log format ["HARMATTAN_TOWN nom=%1 x=%2 y=%3 h=%4 hmax=%5 bati=%6", text _x, round (_p#0), round (_p#1), round (getTerrainHeightASL _p), round _hi, _nb];\n'
    '} forEach _locs;\n'
    'diag_log "HARMATTAN_SCOUTDONE";\n'
)
ls = env._query(sqf, settle=2.5)
towns = []
for l in ls:
    m = re.search(r"HARMATTAN_TOWN nom=(.+?) x=(\d+) y=(\d+) h=(-?\d+) hmax=(-?\d+) bati=(\d+)", l)
    if m:
        towns.append((int(m.group(6)), m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))))
towns.sort(reverse=True)  # densite de bati decroissante
print("=== localites Altis (par densite de batiments, top 14) ===")
print("  %-22s %12s  alt   relief(150m)  batiments" % ("nom", "(x,y)"))
for bati, nom, x, y, h, hmax in towns[:14]:
    print("  %-22s (%5d,%5d)  %3dm     +%3dm        %3d" % (nom[:22], x, y, h, hmax - h, bati))
