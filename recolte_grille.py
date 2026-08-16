#!/usr/bin/env python3
"""recolte_grille — l OCCUPATION DU VOLUME, pour faire Hydra sans le transposer.

CE QUI MANQUAIT. Le degagement mesure aux points de station a donne +0,102 (0,325 -> 0,438)
mais plafonne : ce sont des points colles aux murs, alors que Hydra echantillonne l espace
libre sur l AXE MEDIAN, la ou le degagement est maximal. Pour faire Hydra pour de vrai il
faut la grille d occupation, puis le champ de distance, puis l elagage.

COMMENT ON OBTIENT L OCCUPATION DANS ARMA. Il n existe pas de requete "ce point est-il dans
la matiere". Mais un rayon rend ses intersections avec les surfaces. On balaie donc le
volume selon les TROIS AXES : un rayon vertical ne voit jamais un mur vertical, un rayon
horizontal ne voit jamais un plancher. Les trois ensemble donnent la coque.

RESOLUTION 0,6 m, boite englobante reelle elargie de 1 m. Environ 2 400 rayons par modele.

CE QUI FERAIT ECHOUER :
  · taux d occupation > 60 % ou < 2 % -> le balayage marque n importe quoi, grille inutile.
  · les positions interieures d A3C tombent dans du plein -> le repere ou la quantification
    sont faux, tout le reste serait du bruit. C est LE controle : une position ou un homme
    se tient DOIT etre dans du vide.
"""
import sys, os, time, re, json, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SB = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5849, 6081
LOG = SB + "/logs/serverGRI.out"
MODS = "@CBA_A3;@A3C;@cup_terrains_core;@cup_terrains_maps"
POSE = "[1720, 5580, 0]"
RES = 0.6
PAR_BLOC = 120
SORTIE = "/home/younes/arma3-marl/logs_train/corpus_grille.jsonl"


def sh(c):
    subprocess.run(["bash", "-lc", c], check=False)


def nc(s):
    return "\n".join(l.split("//")[0] for l in s.splitlines() if l.split("//")[0].strip())


CRIBLE = '''
HMT_LISTE = [];
[] spawn {
    private _cand = [];
    { private _n = configName _x;
      if ((getNumber (_x >> "scope") > 0) && {_n isKindOf ["House", configFile >> "CfgVehicles"]}) then { _cand pushBack _n };
    } forEach ("true" configClasses (configFile >> "CfgVehicles"));
    { private _b = _x createVehicleLocal POSE_; if (count (_b buildingPos -1) >= 4) then { HMT_LISTE pushBack _x }; deleteVehicle _b } forEach _cand;
    diag_log format ["HMT_LISTE n=%1", count HMT_LISTE];
};
'''

UN = '''
[] spawn {
    private _cls = HMT_LISTE select IDX_;
    private _b = _cls createVehicleLocal POSE_;
    _b setVectorUp [0, 0, 1];
    private _bb = boundingBoxReal _b;
    private _mn = _bb select 0; private _mx = _bb select 1;
    private _x0 = (_mn select 0) - 1; private _y0 = (_mn select 1) - 1; private _z0 = (_mn select 2) - 1;
    private _x1 = (_mx select 0) + 1; private _y1 = (_mx select 1) + 1; private _z1 = (_mx select 2) + 1;
    private _nx = ceil ((_x1 - _x0) / RES_); private _ny = ceil ((_y1 - _y0) / RES_); private _nz = ceil ((_z1 - _z0) / RES_);
    if (_nx * _ny * _nz > 400000) exitWith { deleteVehicle _b; diag_log format ["HMT_GR %1|%2|TROPGROS|%3|%4|%5|0|0|0", IDX_, _cls, _nx, _ny, _nz] };
    HMT_G = [];
    HMT_G resize (_nx * _ny * _nz);
    HMT_G = HMT_G apply { false };
    HMT_MARQUE = {
        params ["_b", "_pASL", "_x0", "_y0", "_z0", "_nx", "_ny", "_nz"];
        private _m = _b worldToModel (ASLToAGL _pASL);
        private _ix = floor (((_m select 0) - _x0) / RES_);
        private _iy = floor (((_m select 1) - _y0) / RES_);
        private _iz = floor (((_m select 2) - _z0) / RES_);
        if (_ix >= 0 && {_ix < _nx} && {_iy >= 0} && {_iy < _ny} && {_iz >= 0} && {_iz < _nz}) then {
            HMT_G set [_ix + _nx * (_iy + _ny * _iz), true];
        };
    };
    HMT_RAI = {
        params ["_b", "_ma", "_mb", "_x0", "_y0", "_z0", "_nx", "_ny", "_nz"];
        private _a = AGLToASL (_b modelToWorld _ma);
        private _e = AGLToASL (_b modelToWorld _mb);
        private _r = lineIntersectsSurfaces [_a, _e, objNull, objNull, true, 24, "GEOM", "NONE"];
        { [_b, (_x select 0), _x0, _y0, _z0, _nx, _ny, _nz] call HMT_MARQUE } forEach _r;
    };
    for "_iz" from 0 to (_nz - 1) do {
        private _zz = _z0 + (_iz + 0.5) * RES_;
        for "_iy" from 0 to (_ny - 1) do {
            private _yy = _y0 + (_iy + 0.5) * RES_;
            [_b, [_x0 - 1, _yy, _zz], [_x1 + 1, _yy, _zz], _x0, _y0, _z0, _nx, _ny, _nz] call HMT_RAI;
        };
        for "_ix" from 0 to (_nx - 1) do {
            private _xx = _x0 + (_ix + 0.5) * RES_;
            [_b, [_xx, _y0 - 1, _zz], [_xx, _y1 + 1, _zz], _x0, _y0, _z0, _nx, _ny, _nz] call HMT_RAI;
        };
        sleep 0.001;
    };
    for "_ix" from 0 to (_nx - 1) do {
        private _xx = _x0 + (_ix + 0.5) * RES_;
        for "_iy" from 0 to (_ny - 1) do {
            private _yy = _y0 + (_iy + 0.5) * RES_;
            [_b, [_xx, _yy, _z1 + 1], [_xx, _yy, _z0 - 1], _x0, _y0, _z0, _nx, _ny, _nz] call HMT_RAI;
        };
        sleep 0.001;
    };
    private _occ = 0;
    for "_iz" from 0 to (_nz - 1) do {
        private _s = "";
        for "_k" from 0 to (_nx * _ny - 1) do {
            if (HMT_G select (_k + _nx * _ny * _iz)) then { _s = _s + str _k + ","; _occ = _occ + 1 };
        };
        diag_log format ["HMT_GZ %1 %2 %3", IDX_, _iz, _s];
    };
    private _bp = _b buildingPos -1;
    private _pp = "";
    { private _m = _b worldToModel _x; _pp = _pp + format ["%1@%2@%3^", round ((_m select 0) * 100) / 100, round ((_m select 1) * 100) / 100, round ((_m select 2) * 100) / 100] } forEach _bp;
    deleteVehicle _b;
    diag_log format ["HMT_GR %1|%2|OK|%3|%4|%5|%6|%7|%8|%9", IDX_, _cls, _nx, _ny, _nz, _occ, format ["%1,%2,%3", round (_x0 * 100) / 100, round (_y0 * 100) / 100, round (_z0 * 100) / 100], RES_, _pp];
};
'''


def lance():
    sh("pkill -9 -f serverGRI.cfg; sleep 2")
    sh("cp %s/staging/serverBAL.cfg %s/staging/serverGRI.cfg" % (SB, SB))
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverGRI.cfg' -profiles='%s/profilesGRI' "
       "-port=%d -world=Stratis -autoInit -mod='%s' >> '%s' 2>&1 < /dev/null & disown"
       % (SB, EXT, SB, SB, PORT, MODS, LOG))
    time.sleep(75)
    return SocketBridge(EXT)


def att(b, motif, sec=180):
    t0 = time.time()
    while time.time() - t0 < sec:
        h = [L for L in b._log_lines(6000) if motif in L]
        if h:
            return h[-1]
        time.sleep(0.2)
    return None


if __name__ == "__main__":
    b = lance()
    b.send(nc(CRIBLE.replace("POSE_", POSE)), wait=False)
    L = att(b, "HMT_LISTE n=", 900)
    total = int(re.search(r"n=(\d+)", L).group(1))
    lim = int(os.environ.get("LIMITE", total))
    total = min(total, lim)
    print("modeles : %d  (resolution %.2f m)" % (total, RES), flush=True)
    ok = ko = gros = 0
    with open(SORTIE, "w") as fh:
        i = 0
        while i < total:
            if i > 0 and i % PAR_BLOC == 0:
                b.sock.close(); sh("pkill -9 -f serverGRI.cfg; sleep 3")
                b = lance()
                b.send(nc(CRIBLE.replace("POSE_", POSE)), wait=False); att(b, "HMT_LISTE n=", 900)
                print("  [relance a %d]" % i, flush=True)
            marque = len(b.lines)
            b.send(nc(UN.replace("IDX_", str(i)).replace("POSE_", POSE).replace("RES_", str(RES))), wait=False)
            fin = att(b, "HMT_GR %d|" % i, 240)
            if not fin:
                ko += 1; i += 1; continue
            ch = fin.split("HMT_GR ", 1)[1].split("|")
            if len(ch) < 3 or ch[2] != "OK":
                gros += 1; i += 1; continue
            nx, ny, nz = int(ch[3]), int(ch[4]), int(ch[5])
            occ = int(ch[6]); org = [float(x) for x in ch[7].split(",")]
            pos = []
            for e in ch[9].split("^"):
                q = e.split("@")
                if len(q) == 3:
                    try:
                        pos.append([float(q[0]), float(q[1]), float(q[2])])
                    except ValueError:
                        pass
            couches = {}
            for L2 in list(b.lines)[marque:]:
                m = re.match(r"HMT_GZ (\d+) (\d+) (.*)", L2.strip())
                if m and m.group(1) == str(i):
                    couches[int(m.group(2))] = [int(x) for x in m.group(3).split(",") if x.strip().isdigit()]
            fh.write(json.dumps({"i": i, "type": ch[1], "n": [nx, ny, nz], "res": RES,
                                 "origine": org, "occ": occ, "couches": couches,
                                 "positions": pos}) + "\n")
            fh.flush(); ok += 1
            if i % 25 == 0:
                tx = 100.0 * occ / max(nx * ny * nz, 1)
                print("  %d/%d ok=%d ko=%d tropgros=%d   dernier: %dx%dx%d occ=%.1f%%"
                      % (i, total, ok, ko, gros, nx, ny, nz, tx), flush=True)
            i += 1
    b.sock.close(); sh("pkill -9 -f serverGRI.cfg")
    print("\ncorpus grille : %s  (%d ok, %d muets, %d trop gros)" % (SORTIE, ok, ko, gros), flush=True)
