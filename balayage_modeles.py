#!/usr/bin/env python3
"""balayage_modeles — un exemple par MODELE de batiment, pas par exemplaire.

CE QUE LE BALAYAGE STRATIS A MONTRE : 145 batiments captes, mais 26 types distincts et
50 couples (type, decision) seulement. 28 exemplaires du meme petit pavillon ne font pas
28 exemples, ils en font un, recopie. LE PLAFOND N EST PAS LE NOMBRE DE BATIMENTS, C EST
LE NOMBRE DE MODELES.

D OU CE CHANGEMENT : on ne parcourt plus des cartes, on FAIT APPARAITRE les batiments.
`createVehicle` sur un terrain plat donne acces a TOUTE la bibliotheque d assets chargee,
sans dependre de ce qu un terrain contient. Charger CUP Terrains ajoute l architecture
d Europe de l Est et d Asie centrale a l architecture grecque de vanilla.

DEUX PHASES.
  A. criblage : chaque classe derivee de House est posee, on compte ses positions
     interieures, on garde celles a >= 4. Rapide, quelques dixiemes de seconde par classe.
  B. capture : sur les retenues, on pose le batiment, 8 hommes en couronne, on appelle
     A3C et on intercepte le plan. ~8 s par modele.

CE QUI FERAIT ECHOUER :
  · moins de 150 modeles retenus -> CUP n apporte pas ce qu on croit, il faudra d autres
    bibliotheques (RHS, IFA3) ou renoncer.
  · les modeles poses se comportent autrement que ceux du terrain -> controle : les 26
    types deja vus sur Stratis DOIVENT redonner la meme decision une fois poses. Si non,
    le corpus pose est un artefact et tout ce balayage est a jeter.
"""
import sys, os, time, re, json, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SB = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5845, 6077
LOG = SB + "/logs/serverMOD.out"
MODS = "@CBA_A3;@A3C;@cup_terrains_core;@cup_terrains_maps"
PAR_BLOC = 60
ATTENTE = 6.5
POSE = "[1720, 5580, 0]"          # piste de Stratis, plat
SORTIE = "/home/younes/arma3-marl/logs_train/corpus_modeles.jsonl"


def sh(c):
    subprocess.run(["bash", "-lc", c], check=False)


def nc(s):
    return "\n".join(l.split("//")[0] for l in s.splitlines() if l.split("//")[0].strip())


INSTRUMENT = '''
HMT_RID = -1;
if (isNil "A3C_ORIG_exec") then { A3C_ORIG_exec = A3C_ai_shared_fnc_actionExecuteUnitPlot };
A3C_ai_shared_fnc_actionExecuteUnitPlot = {
    params ["_u", "_plot"];
    private _w = "";
    {
        private _p = (_x select 0) select 0;
        private _mk = (_x select 1) select 0;
        private _m = HMT_BLD worldToModel _p;
        _w = _w + format ["%1@%2@%3@%4^", round ((_m select 0) * 10) / 10, round ((_m select 1) * 10) / 10, round ((_m select 2) * 10) / 10, _mk];
    } forEach _plot;
    diag_log format ["HMT_PLAN %1 %2 %3 %4", HMT_RID, HMT_ATT find _u, count _plot, _w];
    _this call A3C_ORIG_exec;
};
if (isNil "A3C_ORIG_rooms") then { A3C_ORIG_rooms = A3C_main_fnc_buildingCreateRooms };
A3C_main_fnc_buildingCreateRooms = {
    private _r = _this call A3C_ORIG_rooms;
    private _s = ""; private _i = 0;
    { _s = _s + format ["R%1=%2/p%3~", _i, (_x select 0), count (_x select 1)]; _i = _i + 1 } forEach _r;
    diag_log format ["HMT_ROOMS %1 n=%2 %3", HMT_RID, count _r, _s];
    _r
};
diag_log "HMT_INSTRUMENT pose";
'''

CRIBLE = '''
HMT_LISTE = [];
[] spawn {
    private _cand = [];
    {
        private _n = configName _x;
        if ((getNumber (_x >> "scope") > 0) && {_n isKindOf ["House", configFile >> "CfgVehicles"]}) then { _cand pushBack _n };
    } forEach ("true" configClasses (configFile >> "CfgVehicles"));
    diag_log format ["HMT_CAND n=%1", count _cand];
    private _k = 0;
    {
        private _b = _x createVehicleLocal POSE_;
        private _np = count (_b buildingPos -1);
        deleteVehicle _b;
        if (_np >= 4) then { HMT_LISTE pushBack _x };
        _k = _k + 1;
        if (_k % 400 == 0) then { diag_log format ["HMT_CRIBLE %1/%2 retenus=%3", _k, count _cand, count HMT_LISTE]; sleep 0.01 };
    } forEach _cand;
    diag_log format ["HMT_LISTE n=%1", count HMT_LISTE];
};
'''

CAPTURE = '''
HMT_RID = IDX_;
{ deleteVehicle _x } forEach (allUnits - allPlayers);
{ if (count (units _x) == 0) then { deleteGroup _x } } forEach allGroups;
if (!isNil "HMT_BLD") then { deleteVehicle HMT_BLD };
private _cls = HMT_LISTE select IDX_;
HMT_BLD = _cls createVehicle POSE_;
HMT_BLD setVectorUp [0, 0, 1];
HMT_BPOS = HMT_BLD buildingPos -1;
private _cap = (IDX_ * 37) % 360;
private _bb = boundingBoxReal HMT_BLD;
private _g = "";
{ private _m = HMT_BLD worldToModel _x; _g = _g + format ["%1@%2@%3^", round ((_m select 0) * 10) / 10, round ((_m select 1) * 10) / 10, round ((_m select 2) * 10) / 10] } forEach HMT_BPOS;
HMT_GA = createGroup west;
HMT_ATT = [];
private _st = "";
for "_i" from 0 to 7 do {
    private _p = HMT_BLD getPos [70, _cap + _i * 5];
    private _u = HMT_GA createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL [_p select 0, _p select 1, 0];
    HMT_ATT pushBack _u;
    private _m = HMT_BLD worldToModel (getPosATL _u);
    _st = _st + format ["%1@%2^", round ((_m select 0) * 10) / 10, round ((_m select 1) * 10) / 10];
};
diag_log format ["HMT_BAT %1|%2|%3|%4|%5|%6|%7|%8", IDX_, _cls, count HMT_BPOS, _cap, _g, _st, round (((_bb select 1) select 0) * 10) / 10, round (((_bb select 1) select 1) * 10) / 10];
[HMT_ATT, HMT_BLD] call A3C_ai_shared_fnc_actionClearBuilding;
'''


def lance():
    sh("pkill -9 -f serverMOD.cfg; sleep 2")
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverMOD.cfg' -profiles='%s/profilesMOD' "
       "-port=%d -world=Stratis -autoInit -mod='%s' >> '%s' 2>&1 < /dev/null & disown"
       % (SB, EXT, SB, SB, PORT, MODS, LOG))
    time.sleep(75)
    return SocketBridge(EXT)


def att(b, motif, sec=30):
    t0 = time.time()
    while time.time() - t0 < sec:
        h = [L for L in b._log_lines(3000) if motif in L]
        if h:
            return h[-1]
        time.sleep(0.25)
    return None


def wp(t):
    o = []
    for e in t.split("^"):
        q = e.split("@")
        if len(q) < 3:
            continue
        try:
            p = {"x": float(q[0]), "y": float(q[1]), "z": float(q[2])}
        except ValueError:
            continue
        if len(q) >= 4:
            p["piece"] = q[3].split("_Room_")[-1] if "_Room_" in q[3] else ""
        o.append(p)
    return o


def xy(t):
    o = []
    for e in t.split("^"):
        q = e.split("@")
        if len(q) < 2:
            continue
        try:
            o.append([float(q[0]), float(q[1])])
        except ValueError:
            continue
    return o


def prepare(b):
    b.send(nc(INSTRUMENT)); att(b, "HMT_INSTRUMENT", 25)
    b.send(nc(CRIBLE.replace("POSE_", POSE)), wait=False)
    L = att(b, "HMT_LISTE n=", 900)
    return int(re.search(r"n=(\d+)", L).group(1)) if L else 0


def un(b, i, fh):
    marque = len(b.lines)
    b.send(nc(CAPTURE.replace("IDX_", str(i)).replace("POSE_", POSE)), wait=False)
    ligne = att(b, "HMT_BAT %d|" % i, 30)
    if not ligne:
        return False
    ch = ligne.split("HMT_BAT ", 1)[1].split("|")
    if len(ch) < 8:
        return False
    time.sleep(ATTENTE)
    plans, pieces, portes = [], None, None
    for L in list(b.lines)[marque:]:
        m = re.search(r"HMT_PLAN (-?\d+) (-?\d+) (\d+) (.*)", L)
        if m and m.group(1) == str(i):
            plans.append({"unite": int(m.group(2)), "wp": wp(m.group(4))})
        m2 = re.search(r"HMT_ROOMS (-?\d+) n=(\d+) (.*)", L)
        if m2 and m2.group(1) == str(i):
            pieces = int(m2.group(2)); portes = [int(x) for x in re.findall(r"/p(\d+)~", m2.group(3))]
    aff = {}
    for p in plans:
        for w in p["wp"]:
            if w.get("piece"):
                aff[p["unite"]] = w["piece"]
    fh.write(json.dumps({"i": i, "type": ch[1], "npos": int(ch[2]), "cap": int(ch[3]),
                         "positions": wp(ch[4]), "depart": xy(ch[5]),
                         "bbox": [float(ch[6]), float(ch[7].split()[0])],
                         "pieces": pieces, "portes": portes,
                         "plans": plans, "affectation": aff}) + "\n")
    fh.flush()
    return True


if __name__ == "__main__":
    b = lance()
    total = prepare(b)
    print("modeles retenus (>= 4 positions interieures) : %d" % total, flush=True)
    if total < 150:
        print("MOINS DE 150 MODELES -> CUP n apporte pas ce qu on croyait. Note.", flush=True)
    ok = ko = 0
    with open(SORTIE, "w") as fh:
        i = 0
        while i < total:
            if i > 0 and i % PAR_BLOC == 0:
                b.sock.close(); sh("pkill -9 -f serverMOD.cfg; sleep 3")
                b = lance(); prepare(b)
                print("  [serveur relance a %d/%d]" % (i, total), flush=True)
            if un(b, i, fh):
                ok += 1
            else:
                ko += 1
            if i % 25 == 0:
                print("  %d/%d  captures=%d  muets=%d" % (i, total, ok, ko), flush=True)
            i += 1
    b.sock.close(); sh("pkill -9 -f serverMOD.cfg")
    print("\ncorpus : %s  (%d modeles, %d muets)" % (SORTIE, ok, ko), flush=True)
