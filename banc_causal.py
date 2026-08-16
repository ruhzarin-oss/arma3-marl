#!/usr/bin/env python3
"""banc_causal — la QUALITE DU DECOUPAGE change-t-elle l issue du combat ?

Tout ce qui precede mesurait un indice de Rand : une metrique INTERMEDIAIRE, sans lien
etabli avec l issue. Ici on mesure des MORTS.

LE PRINCIPE : la machinerie d execution d A3C est IDENTIQUE dans les trois bras. On
remplace seulement la valeur de retour de `A3C_main_fnc_buildingCreateRooms` — donc le
PLAN DE PIECES qu on lui donne. Une seule variable bouge.

  A3C          : son propre decoupage (reference)
  HYDRA+ETAGE  : l approximation mesuree a 0,438 d indice de Rand
  ETAGE        : la regle bete, 0,325

MEME ENSEMBLE DE CANDIDATS DANS LES TROIS BRAS. L original part des indices 1..bpc filtres
par `isPositionInsideBuilding` (l indice 0 est le point d entree, il est exclu). Mes
substituts partent EXACTEMENT du meme ensemble et se contentent de le grouper autrement,
puis appliquent le meme tri intra-piece et calculent les portes avec la meme fonction
`buildingFindRoomDoors`. Sinon je changerais deux choses a la fois.

LE DEGAGEMENT EST MESURE EN JEU, sur le batiment du terrain, pas repris du corpus des
modeles poses : pas d hypothese de transfert dans un banc qui doit trancher.

CE QUI FERAIT ECHOUER CE BANC :
  · pieces identiques dans les trois bras -> la substitution ne prend pas, tout est nul.
    C est le JOUET qui doit l attraper avant les 30 manches.
  · def tues identiques a la variance pres -> le decoupage ne compte pas. Resultat NEGATIF
    et il compte : le fil meurt avec une preuve de combat, pas un proxy.
  · ordre_ok faux -> le substitut casse la routine, resultat inexploitable.
"""
import sys, os, time, re, json, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SB = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5850, 6082
LOG = SB + "/logs/serverCAU.out"
MODS = "@CBA_A3;@A3C"
NDEF, NATT, DIST = 6, 8, 70.0
T_RUN, PERIODE = 240.0, 10.0
BRAS = ["A3C", "HYDRA", "ETAGE"]
PAR_BLOC, BLOCS = 3, 10
TAU = 1.2
SORTIE = os.environ.get("SORTIE", "/home/younes/arma3-marl/logs_train/banc_causal.jsonl")


def sh(c):
    subprocess.run(["bash", "-lc", c], check=False)


def nc(s):
    return "\n".join(l.split("//")[0] for l in s.splitlines() if l.split("//")[0].strip())


SUBST = '''
if (isNil "A3C_ORIG_rooms") then { A3C_ORIG_rooms = A3C_main_fnc_buildingCreateRooms };
HMT_BRAS = "A3C";
HMT_DEG = {
    params ["_p"];
    private _d = 8;
    for "_k" from 0 to 7 do {
        private _ang = _k * 45;
        private _a = AGLToASL [_p select 0, _p select 1, (_p select 2) + 1];
        private _e = _a vectorAdd [8 * sin _ang, 8 * cos _ang, 0];
        private _r = lineIntersectsSurfaces [_a, _e, objNull, objNull, true, 1, "GEOM", "NONE"];
        if (count _r > 0) then { private _dd = _a distance ((_r select 0) select 0); if (_dd < _d) then { _d = _dd } };
    };
    _d
};
HMT_PASSAGE = {
    params ["_pi", "_pj"];
    private _mn = 8;
    for "_s" from 1 to 3 do {
        private _t = _s / 4;
        private _m = _pi vectorAdd ((_pj vectorDiff _pi) vectorMultiply _t);
        private _v = [_m] call HMT_DEG;
        if (_v < _mn) then { _mn = _v };
    };
    _mn
};
A3C_main_fnc_buildingCreateRooms = {
    params ["_b", "_bpc", "_rs"];
    if (HMT_BRAS == "A3C") exitWith {
        private _r = _this call A3C_ORIG_rooms;
        diag_log format ["HMT_PIECES bras=A3C n=%1", count _r];
        _r
    };
    private _cand = [];
    for "_i" from 1 to _bpc do {
        private _p = _b buildingPos _i;
        if (_rs || {[_p, _b] call A3C_main_fnc_isPositionInsideBuilding}) then { _cand pushBack _i };
    };
    private _pere = [];
    { _pere pushBack _forEachIndex } forEach _cand;
    HMT_TROUVE = {
        params ["_pere", "_x"];
        private _r = _x;
        while {(_pere select _r) != _r} do { _r = _pere select _r };
        _r
    };
    for "_a" from 0 to (count _cand - 2) do {
        for "_c" from (_a + 1) to (count _cand - 1) do {
            private _pa = _b buildingPos (_cand select _a);
            private _pc = _b buildingPos (_cand select _c);
            private _ok = (abs ((_pa select 2) - (_pc select 2)) < 1.5);
            if (_ok && {HMT_BRAS == "HYDRA"}) then {
                if ((_pa distance _pc) >= 8) then { _ok = false }
                else { _ok = ([_pa, _pc] call HMT_PASSAGE) >= TAU_ };
            };
            if (_ok) then {
                private _ra = [_pere, _a] call HMT_TROUVE;
                private _rc = [_pere, _c] call HMT_TROUVE;
                if (_ra != _rc) then { _pere set [_ra, _rc] };
            };
        };
    };
    private _grp = createHashMap;
    for "_k" from 0 to (count _cand - 1) do {
        private _r = [_pere, _k] call HMT_TROUVE;
        private _l = _grp getOrDefault [str _r, []];
        _l pushBack (_cand select _k);
        _grp set [str _r, _l];
    };
    private _rooms = [];
    {
        private _idx = _y;
        private _tri = [_idx, [], { (_b buildingPos _x) distance2D (position _b) }, "DESCEND"] call BIS_fnc_sortBy;
        private _dp = [_b, _tri] call A3C_main_fnc_buildingFindRoomDoors;
        _rooms pushBack [_tri, _dp];
    } forEach _grp;
    diag_log format ["HMT_PIECES bras=%1 n=%2", HMT_BRAS, count _rooms];
    _rooms
};
diag_log "HMT_SUBST pose";
'''

SCENE = '''
{ deleteVehicle _x } forEach (allUnits - allPlayers);
{ if (count (units _x) == 0) then { deleteGroup _x } } forEach allGroups;
HMT_C = [4000, 4000, 0];
{ if (toLower (text _x) == "agia marina") exitWith { HMT_C = locationPosition _x } } forEach (nearestLocations [[4000,4000,0], ["NameVillage","NameCity","NameCityCapital"], 12000]);
HMT_BLD = (nearestObjects [HMT_C, ["Land_i_House_Big_01_V1_F"], 800]) select 0;
HMT_BPOS = HMT_BLD buildingPos -1;
HMT_TIRS = [];
for "_i" from 0 to (NATT_ - 1) do { HMT_TIRS pushBack (HMT_BLD getPos [DIST_, 200 + _i * 5]) };
HMT_HAUT = [];
{
    private _p = _x; private _bl = 0;
    {
        private _a = AGLToASL [_p select 0, _p select 1, (_p select 2) + 1.4];
        private _c = AGLToASL [_x select 0, _x select 1, (_x select 2) + 1.4];
        if (lineIntersects [_a, _c]) then { _bl = _bl + 1 };
    } forEach HMT_TIRS;
    if (_bl == count HMT_TIRS) then { HMT_HAUT pushBack _p };
} forEach HMT_BPOS;
if (count HMT_HAUT < 3) then { HMT_HAUT = HMT_BPOS };
HMT_GD = createGroup east;
HMT_DEF = [];
for "_i" from 0 to (NDEF_ - 1) do {
    private _p = HMT_HAUT select (_i % (count HMT_HAUT));
    private _u = HMT_GD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL _p; _u disableAI "PATH"; _u setSkill 0.6;
    HMT_DEF pushBack _u;
};
HMT_GD setBehaviour "COMBAT"; HMT_GD setCombatMode "RED";
HMT_GA = createGroup west;
HMT_ATT = [];
for "_i" from 0 to (NATT_ - 1) do {
    private _p = HMT_BLD getPos [DIST_, 200 + _i * 5];
    private _u = HMT_GA createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL [_p select 0, _p select 1, 0]; _u setSkill 0.6;
    HMT_ATT pushBack _u;
};
HMT_GA setBehaviour "AWARE"; HMT_GA setCombatMode "RED";
diag_log format ["HMT_SCENE cachees=%1 def=%2 att=%3", count HMT_HAUT, count HMT_DEF, count HMT_ATT];
'''

LANCE = '''
HMT_BRAS = "BRAS_";
HMT_OK = 0;
[HMT_ATT, HMT_BLD] call A3C_ai_shared_fnc_actionClearBuilding;
HMT_OK = 1;
diag_log format ["HMT_ORDRE rid=RID_ ok=%1", HMT_OK];
'''

ETAT = '''
private _in = 0;
{
    private _u = _x;
    if (alive _u) then {
        private _c = 0;
        { if (_u distance _x < 2.5) then { _c = _c + 1 } } forEach HMT_BPOS;
        if (_c > 0) then { _in = _in + 1 };
    };
} forEach HMT_ATT;
diag_log format ["HMT_ETAT dedans=%1 att=%2 def=%3", _in, ({alive _x} count HMT_ATT), ({alive _x} count HMT_DEF)];
'''


def lance():
    sh("pkill -9 -f serverCAU.cfg; sleep 2")
    sh("cp %s/staging/serverBAL.cfg %s/staging/serverCAU.cfg" % (SB, SB))
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverCAU.cfg' -profiles='%s/profilesCAU' "
       "-port=%d -world=Stratis -autoInit -mod='%s' >> '%s' 2>&1 < /dev/null & disown"
       % (SB, EXT, SB, SB, PORT, MODS, LOG))
    time.sleep(50)
    return SocketBridge(EXT)


def att(b, motif, sec=30):
    t0 = time.time()
    while time.time() - t0 < sec:
        h = [L for L in b._log_lines(2000) if motif in L]
        if h:
            return h[-1]
        time.sleep(0.25)
    return None


def manche(b, bras, rid, fh):
    b.send(nc(SCENE.replace("NDEF_", str(NDEF)).replace("NATT_", str(NATT)).replace("DIST_", str(DIST))))
    if not att(b, "HMT_SCENE"):
        print("  r%d [%s] SCENE ABSENTE" % (rid, bras), flush=True); return None
    time.sleep(2)
    marque = len(b.lines)
    b.send(nc(LANCE.replace("BRAS_", bras).replace("RID_", str(rid))))
    od = att(b, "HMT_ORDRE rid=%d" % rid, 60)
    ok = bool(od and "ok=1" in od)
    npieces = -1
    for L in list(b.lines)[marque:]:
        m = re.search(r"HMT_PIECES bras=(\S+) n=(\d+)", L)
        if m: npieces = int(m.group(2))
    pic = 0
    t0 = time.time()
    while time.time() - t0 < T_RUN:
        time.sleep(PERIODE)
        b.send(ETAT)
        L = att(b, "HMT_ETAT", 10)
        if L:
            g = re.search(r"dedans=(\d+) att=(\d+) def=(\d+)", L)
            if g: pic = max(pic, int(g.group(1)))
    fin = re.search(r"dedans=(\d+) att=(\d+) def=(\d+)", att(b, "HMT_ETAT", 10) or "")
    r = {"rid": rid, "bras": bras, "ordre_ok": ok, "pieces": npieces, "dedans_pic": pic,
         "att_vivants": int(fin.group(2)) if fin else -1,
         "def_vivants": int(fin.group(3)) if fin else -1}
    r["def_tues"] = NDEF - r["def_vivants"] if r["def_vivants"] >= 0 else -1
    fh.write(json.dumps(r) + "\n"); fh.flush()
    print("  r%2d [%-5s] ok=%s pieces=%2d  def tues=%d/%d  att vivants=%d/%d  dedans pic=%d"
          % (rid, bras, ok, npieces, r["def_tues"], NDEF, r["att_vivants"], NATT, pic), flush=True)
    return r


if __name__ == "__main__":
    res = []
    rid = 0
    with open(SORTIE, os.environ.get("MODE", "w")) as fh:
        for bl in range(BLOCS):
            print("\n=== bloc %d/%d ===" % (bl + 1, BLOCS), flush=True)
            b = lance()
            b.send(nc(SUBST.replace("TAU_", str(TAU))))
            print("  %s" % (att(b, "HMT_SUBST", 20) or "SUBSTITUTION NON POSEE"), flush=True)
            for k in range(PAR_BLOC):
                bras = BRAS[rid % len(BRAS)]
                rid += 1
                r = manche(b, bras, rid, fh)
                if r: res.append(r)
            b.sock.close(); sh("pkill -9 -f serverCAU.cfg; sleep 3")
    print("\n================ RESULTAT ================", flush=True)
    for bras in BRAS:
        v = [r for r in res if r["bras"] == bras]
        if not v: continue
        n = len(v)
        print("%-6s n=%2d  pieces=%.1f  def tues=%.2f/%d  att vivants=%.2f/%d  dedans=%.2f  ordre_ok=%d/%d"
              % (bras, n, sum(r["pieces"] for r in v) / n, sum(r["def_tues"] for r in v) / n, NDEF,
                 sum(r["att_vivants"] for r in v) / n, NATT, sum(r["dedans_pic"] for r in v) / n,
                 sum(1 for r in v if r["ordre_ok"]), n))
