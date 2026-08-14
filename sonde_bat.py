#!/usr/bin/env python3
"""sonde_bat — demander AU JEU quels batiments de Stratis ont un vrai interieur."""
import sys, os, time, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
SB = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5840, 6072
LOG = SB + "/logs/serverA3C.out"
def sh(c): subprocess.run(["bash", "-lc", c], check=False)

SONDE = '''
private _villes = [];
{ _villes pushBack [text _x, locationPosition _x] } forEach (nearestLocations [[4000,4000,0], ["NameCityCapital","NameCity","NameVillage"], 12000]);
private _res = [];
{
    private _nom = _x select 0; private _p = _x select 1;
    {
        private _b = _x;
        private _bp = _b buildingPos -1;
        if (count _bp >= 6) then {
            private _z = [];
            { _z pushBackUnique (round ((_x select 2) * 10)) } forEach (_bp apply { _b worldToModel _x });
            private _bb = boundingBoxReal _b;
            private _h = ((_bb select 1) select 2) - ((_bb select 0) select 2);
            _res pushBack [count _bp, count _z, round _h, typeOf _b, _nom, mapGridPosition _b];
        };
    } forEach (nearestObjects [_p, ["House"], 200]);
} forEach _villes;
_res sort false;
private _t = "";
{ _t = _t + format ["%1|%2|%3|%4|%5|%6 ;; ", _x select 0, _x select 1, _x select 2, _x select 3, _x select 4, _x select 5] } forEach (_res select [0, 14]);
diag_log format ["A3C_SONDE %1", _t];
'''

if __name__ == "__main__":
    sh("pkill -9 -f serverA3C.cfg; sleep 2")
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverA3C.cfg' -profiles='%s/profilesA3C' "
       "-port=%d -world=Stratis -autoInit -mod='@CBA_A3;@A3C' >> '%s' 2>&1 < /dev/null & disown"
       % (SB, EXT, SB, SB, PORT, LOG))
    time.sleep(50)
    b = SocketBridge(EXT); time.sleep(3)
    b.send("\n".join(l for l in SONDE.splitlines() if l.split("//")[0].strip()))
    L = None
    for _ in range(40):
        h = [x for x in b._log_lines(600) if "A3C_SONDE" in x]
        if h: L = h[-1]; break
        time.sleep(0.5)
    if L:
        print("nbPos | nbEtages | hauteur | type | ville | grille")
        for e in L.split("A3C_SONDE", 1)[1].split(";;"):
            if e.strip(): print("  " + e.strip())
    else:
        print("SONDE MUETTE")
    b.sock.close(); sh("pkill -9 -f serverA3C.cfg")
