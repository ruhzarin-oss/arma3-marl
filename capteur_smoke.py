#!/usr/bin/env python3
"""capteur_decisions — on capte ce qu A3C DECIDE, pas ou ses hommes vont.

Mesure du 14/08 : la geometrie d A3C est indistinguable d un doMove naif (AUC 0,889,
p=0,065) alors qu il tue 3,2x plus (p=0,011). L avantage n est donc pas dans les
positions. Il est ici.

CE QU A3C DECIDE, ET QUI EST INSPECTABLE :
  1. TOPOLOGIE — `A3C_main_fnc_buildingCreateRooms` infere les PIECES du batiment en
     groupant les positions qui se voient entre elles, puis `buildingFindRoomDoors`
     trouve les PORTES. Le batiment n est pas une liste de points, c est un graphe.
  2. AFFECTATION — les hommes sont apparies en BINOMES, chaque binome recoit la piece
     non encore prise la plus proche de l entree.
  3. PLAN PAR HOMME — ecrit dans la variable `A3C_PLOT` : positions a tenir, marqueur de
     piece, posture, rayon. Les DEUX DERNIERES positions d une piece partagent le meme
     marqueur pour que les binomes s attendent.
LAMBS expose son equivalent : `lambs_main_currentTarget` et `currentTask` par homme.

TROISIEME BRAS, ET C EST UNE TROUVAILLE DU JOUR :
  `fnc_actionClearBuilding.sqf` ligne 100 : `if !(isDedicated) then { _units = [...]
  BIS_fnc_sortBy ...; {_x setVariable ["A3C_PLOT",[],true]} forEach _units };`
  SUR UN SERVEUR DEDIE, LE TRI DES HOMMES PAR DISTANCE A L ENTREE EST SAUTE, et les plots
  ne sont pas remis a zero. Le bras `A3C_TRIE` refait ces deux lignes a la main avant
  d appeler. Si le tri compte, A3C tourne degrade sur TOUS les serveurs dedies.

CE QUI FERAIT ECHOUER CE CAPTEUR :
  · pieces=0 ou 1 -> la topologie ne se lit pas, il n y a rien a capter.
  · plans vides -> `A3C_PLOT` n est pas le bon canal. ARRIVE AU PREMIER ESSAI : sonder la
    variable toutes les 4 s ne rend JAMAIS rien, parce qu elle est ecrite puis consommee en
    quelques millisecondes (`actionExecuteUnitPlot` la vide, ligne 501). Corrige non pas en
    sondant plus vite mais en INTERCEPTANT : les fonctions A3C sont de simples variables
    globales, on les remplace par une enveloppe qui journalise ses arguments puis appelle
    l originale. Le plan est alors capte AU MOMENT OU IL EST REMIS A L EXECUTANT.
  · A3C_TRIE identique a A3C -> le trou de la ligne 100 est sans effet, resultat negatif
    qui compte et qu il faudra dire.
"""
import sys, os, time, re, json, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SB = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5842, 6074
LOG = SB + "/logs/serverDEC.out"
NDEF, NATT, DIST = 6, 8, 70.0
T_RUN, TICK = 60.0, 4.0
BRAS = ["A3C", "A3C_TRIE", "LAMBS"]
PAR_BLOC, BLOCS = 3, 1
SORTIE = "/home/younes/arma3-marl/logs_train/decisions_a3c.jsonl"


def sh(c):
    subprocess.run(["bash", "-lc", c], check=False)


def sc(s):
    return "\n".join(l.split("//")[0] for l in s.splitlines() if l.split("//")[0].strip())


SCENE = '''
HMT_REC = false;
sleep 0.3;
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
HMT_CACHEES = count HMT_HAUT;
if (count HMT_HAUT < 3) then { HMT_HAUT = HMT_BPOS };
private _bb = boundingBoxReal HMT_BLD;
HMT_BBX = ((_bb select 1) select 0) - 0.5;
HMT_BBY = ((_bb select 1) select 1) - 0.5;
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
diag_log format ["HMT_SCENE bat=%1 pos=%2 cachees=%3 def=%4 att=%5", typeOf HMT_BLD, count HMT_BPOS, HMT_CACHEES, count HMT_DEF, count HMT_ATT];
'''

TOPO = '''
private _bpc = [HMT_BLD] call MCSS_fnc_getLastBuildingPosIndex;
private _rooms = [HMT_BLD, _bpc, false] call A3C_main_fnc_buildingCreateRooms;
private _s = "";
private _i = 0;
{
    _s = _s + format ["R%1=%2/portes%3~", _i, (_x select 0), count (_x select 1)];
    _i = _i + 1;
} forEach _rooms;
diag_log format ["HMT_TOPO bpc=%1 pieces=%2 %3", _bpc, count _rooms, _s];
'''

ORDRES = {
    "A3C": '[HMT_ATT, HMT_BLD] call A3C_ai_shared_fnc_actionClearBuilding;',
    "A3C_TRIE": ('HMT_ATT = [HMT_ATT, [], {vehicle _x distance2D (HMT_BLD buildingPos 0)}, "ASCEND"] call BIS_fnc_sortBy;'
                 '{ _x setVariable ["A3C_PLOT", [], true] } forEach HMT_ATT;'
                 '[HMT_ATT, HMT_BLD] call A3C_ai_shared_fnc_actionClearBuilding;'),
    "LAMBS": '[HMT_GA, getPosATL HMT_BLD, 30, 15] spawn lambs_wp_fnc_taskCQB;',
}

LANCE = '''
HMT_RID = RID_;
HMT_T = 0;
ORDRE_
diag_log format ["HMT_ORDRE rid=%1 ok=1", HMT_RID];
HMT_REC = true;
[] spawn {
    while {HMT_REC} do {
        private _s = "";
        private _i = 0;
        {
            private _u = _x;
            private _pl = _u getVariable ["A3C_PLOT", []];
            private _cl = if (_u getVariable ["A3C_CLEARING", false]) then {1} else {0};
            private _lt = _u getVariable ["lambs_main_currentTarget", []];
            private _lk = _u getVariable ["lambs_main_currentTask", ""];
            private _w = "";
            {
                private _p = (_x select 0) select 0;
                private _mk = (_x select 1) select 0;
                _w = _w + format ["%1@%2@%3^", round ((_p select 0) * 10) / 10, round ((_p select 1) * 10) / 10, _mk];
            } forEach _pl;
            private _m = HMT_BLD worldToModel (getPosATL _u);
            private _e = eyePos _u;
            private _dd = if ((abs (_m select 0) < HMT_BBX) && {abs (_m select 1) < HMT_BBY} && {lineIntersects [_e, _e vectorAdd [0, 0, 40]]}) then {1} else {0};
            _s = _s + format ["%1!%2!%3!%4!%5!%6!%7#", _i, _cl, _w, _lt, _lk, _dd, (if (alive _u) then {1} else {0})];
            _i = _i + 1;
        } forEach HMT_ATT;
        diag_log format ["HMT_DEC %1 %2 %3 %4", HMT_RID, HMT_T, ({ alive _x } count HMT_DEF), _s];
        HMT_T = HMT_T + 1;
        sleep TICK_;
    };
};
'''


INSTRUMENT = '''
HMT_RID = 0;
if (isNil "A3C_ORIG_exec") then { A3C_ORIG_exec = A3C_ai_shared_fnc_actionExecuteUnitPlot };
A3C_ai_shared_fnc_actionExecuteUnitPlot = {
    params ["_u", "_plot"];
    private _w = "";
    {
        private _p = (_x select 0) select 0;
        private _mk = (_x select 1) select 0;
        private _po = (_x select 4) select 0;
        _w = _w + format ["%1@%2@%3@%4@%5^", round ((_p select 0) * 10) / 10, round ((_p select 1) * 10) / 10, round ((_p select 2) * 10) / 10, _mk, _po];
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


def lance():
    sh("pkill -9 -f serverDEC.cfg; sleep 2")
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverDEC.cfg' -profiles='%s/profilesDEC' "
       "-port=%d -world=Stratis -autoInit -mod='@CBA_A3;@A3C;@LAMBS_Danger' "
       ">> '%s' 2>&1 < /dev/null & disown" % (SB, EXT, SB, SB, PORT, LOG))
    time.sleep(50)
    return SocketBridge(EXT)


def att(b, motif, sec=25):
    t0 = time.time()
    while time.time() - t0 < sec:
        h = [L for L in b._log_lines(1200) if motif in L]
        if h:
            return h[-1]
        time.sleep(0.3)
    return None


def manche(b, bras, rid, fh):
    b.send(sc(SCENE.replace("NDEF_", str(NDEF)).replace("NATT_", str(NATT)).replace("DIST_", str(DIST))))
    s = att(b, "HMT_SCENE")
    if not s:
        print("  r%d [%s] SCENE ABSENTE" % (rid, bras), flush=True); return
    b.send(sc(TOPO))
    topo = att(b, "HMT_TOPO")
    npieces = int(re.search(r"pieces=(\d+)", topo).group(1)) if topo else -1
    time.sleep(2)
    marque = len(b.lines)
    b.send(sc(LANCE.replace("RID_", str(rid)).replace("ORDRE_", ORDRES[bras]).replace("TICK_", str(TICK))))
    att(b, "HMT_ORDRE rid=%d" % rid, 25)
    time.sleep(T_RUN)
    b.send("HMT_REC = false;")
    time.sleep(1.5)
    n = 0
    pic_plan = 0
    salles = set()
    plans = []
    for L in list(b.lines)[marque:]:
        m = re.search(r"HMT_PLAN (\d+) (-?\d+) (\d+) (.*)", L)
        if m and int(m.group(1)) == rid:
            wps = []
            for w in m.group(4).split("^"):
                q = w.split("@")
                if len(q) == 5:
                    wps.append({"x": float(q[0]), "y": float(q[1]), "z": float(q[2]),
                                "piece": q[3].split("_Room_")[-1] if "_Room_" in q[3] else "",
                                "posture": q[4]})
                    if wps[-1]["piece"]:
                        salles.add(wps[-1]["piece"])
            plans.append({"unite": int(m.group(2)), "n": int(m.group(3)), "wp": wps})
        m2 = re.search(r"HMT_ROOMS (\d+) n=(\d+) (.*)", L)
        if m2 and int(m2.group(1)) == rid:
            topo = "n=%s %s" % (m2.group(2), m2.group(3))
    if plans:
        fh.write(json.dumps({"rid": rid, "bras": bras, "type": "PLANS", "plans": plans}) + "\n")
    for L in list(b.lines)[marque:]:
        m = re.search(r"HMT_DEC (\d+) (\d+) (\d+) (.*)", L)
        if not m or int(m.group(1)) != rid:
            continue
        hommes = []
        for bloc in m.group(4).split("#"):
            if not bloc.strip():
                continue
            p = bloc.split("!")
            if len(p) < 7:
                continue
            wps = []
            for w in p[2].split("^"):
                if not w.strip():
                    continue
                q = w.split("@")
                if len(q) == 3:
                    r = q[2].split("_Room_")[-1] if "_Room_" in q[2] else ""
                    wps.append([float(q[0]), float(q[1]), r])
                    if r:
                        salles.add(r)
            hommes.append({"i": int(p[0]), "clearing": int(p[1]), "plan": wps,
                           "lambs_cible": p[3], "lambs_tache": p[4],
                           "dedans": int(p[5]), "vivant": int(p[6])})
        pic_plan = max(pic_plan, sum(1 for h in hommes if h["plan"]))
        fh.write(json.dumps({"rid": rid, "bras": bras, "t": int(m.group(2)),
                             "pieces": npieces, "def_vivants": int(m.group(3)),
                             "hommes": hommes}) + "\n")
        n += 1
    fh.flush()
    print("  r%2d [%-8s] pieces=%d ticks=%3d  PLANS interceptes=%d  hommes distincts=%d  salles=%d"
          % (rid, bras, npieces, n, len(plans), len(set(p["unite"] for p in plans)), len(salles)), flush=True)


if __name__ == "__main__":
    rid = 0
    with open(SORTIE, "w") as fh:
        for bl in range(BLOCS):
            print("\n=== bloc %d/%d ===" % (bl + 1, BLOCS), flush=True)
            b = lance()
            b.send('private _r = if (isNil "A3C_main_fnc_buildingCreateRooms") then {0} else {1}; private _l = if (isNil "lambs_wp_fnc_taskCQB") then {0} else {1}; diag_log format ["HMT_PORTE0 rooms=%1 lambs=%2", _r, _l];')
            g = att(b, "HMT_PORTE0")
            b.send(sc(INSTRUMENT))
            print("  %s" % (att(b, "HMT_INSTRUMENT", 15) or "INSTRUMENT NON POSE"), flush=True)
            print("  %s" % (g or "MUETTE"), flush=True)
            if not g or "rooms=1" not in g:
                print("  buildingCreateRooms absente -> arret", flush=True); b.sock.close(); break
            for k in range(PAR_BLOC):
                bras = BRAS[rid % len(BRAS)]
                rid += 1
                manche(b, bras, rid, fh)
            b.sock.close()
            sh("pkill -9 -f serverDEC.cfg; sleep 3")
    print("\ndecisions ecrites : %s" % SORTIE, flush=True)
    sh("wc -l %s" % SORTIE)
