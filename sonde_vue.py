#!/usr/bin/env python3
"""sonde_vue — quelles positions interieures sont HORS VUE de l arc d approche ?
Sans position cachee, aucun banc ne peut forcer l entree : le feu exterieur suffit."""
import sys, time, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
SB = "/mnt/data/harmattan-sandbox"; EXT, PORT = 5841, 6073
def sh(c): subprocess.run(["bash", "-lc", c], check=False)

Q = '''
private _out = "";
{
    private _t = _x;
    private _cands = nearestObjects [[4000,4000,0], [_t], 6000];
    if (count _cands > 0) then {
        private _b = _cands select 0;
        private _bp = _b buildingPos -1;
        private _tirs = [];
        for "_i" from 0 to 7 do { _tirs pushBack (_b getPos [70, 200 + _i * 5]) };
        private _cache = 0; private _haut = 0;
        {
            private _p = _x;
            private _z = (_b worldToModel _p) select 2;
            if (_z > 3) then { _haut = _haut + 1 };
            private _bloque = 0;
            {
                private _a = AGLToASL [_p select 0, _p select 1, (_p select 2) + 1.4];
                private _c = AGLToASL [_x select 0, _x select 1, (_x select 2) + 1.4];
                if (lineIntersects [_a, _c]) then { _bloque = _bloque + 1 };
            } forEach _tirs;
            if (_bloque == 8) then { _cache = _cache + 1 };
        } forEach _bp;
        _out = _out + format ["%1 pos=%2 hautes=%3 CACHEES=%4 ;; ", _t, count _bp, _haut, _cache];
    } else {
        _out = _out + format ["%1 ABSENT ;; ", _t];
    };
} forEach ["Land_i_Shop_01_V1_F", "Land_Cargo_HQ_V1_F", "Land_i_House_Big_01_V1_F", "Land_i_House_Big_02_V1_F", "Land_Airport_Tower_F", "Land_i_Stone_HouseBig_V1_F", "Land_Offices_01_V1_F"];
diag_log format ["HMT_VUE %1", _out];
'''

if __name__ == "__main__":
    sh("pkill -9 -f serverUSINE.cfg; sleep 2")
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverUSINE.cfg' -profiles='%s/profilesUSINE' "
       "-port=%d -world=Stratis -autoInit -mod='@CBA_A3;@A3C;@LAMBS_Danger' >> '%s/logs/serverUSINE.out' 2>&1 < /dev/null & disown"
       % (SB, EXT, SB, SB, PORT, SB))
    time.sleep(50)
    b = SocketBridge(EXT); time.sleep(3)
    b.send("\n".join(l for l in Q.splitlines() if l.split("//")[0].strip()))
    L = None
    for _ in range(60):
        h = [x for x in b._log_lines(600) if "HMT_VUE" in x]
        if h: L = h[-1]; break
        time.sleep(0.5)
    if L:
        for e in L.split("HMT_VUE", 1)[1].split(";;"):
            if e.strip(): print("  " + e.strip())
    else:
        print("SONDE MUETTE")
    b.sock.close(); sh("pkill -9 -f serverUSINE.cfg")
