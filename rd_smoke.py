#!/usr/bin/env python3
"""recolte_degagement — l ingredient de Hydra : le DEGAGEMENT.

HYDRA (MIT-SPARK, arXiv 2201.13360) segmente en pieces ainsi : chaque noeud de l espace
libre porte sa distance au plus proche obstacle ; on ELAGUE les noeuds sous un seuil, ce qui
FERME LES PORTES (un goulot etroit a peu de degagement) ; les composantes connexes restantes
sont les pieces.

Ma mesure du soir a echoue faute de MURS dans l entree. Hydra montre qu il n en faut pas
tout : il suffit d UN SCALAIRE par endroit. On l ajoute et on remesure.

TRANSPOSITION, ET SES ECARTS ASSUMES :
  · Hydra echantillonne l espace libre sur l axe median (diagramme de Voronoi generalise),
    ou le degagement est LOCALEMENT MAXIMAL. Mes `buildingPos` sont des points de station
    arbitraires, souvent contre un mur. Ce n est PAS la meme quantite.
  · Je transpose donc l idee sur les ARETES et non sur les noeuds : pour chaque paire, on
    echantillonne 3 points le long du segment et on garde le degagement MINIMAL. C est la
    largeur du passage entre deux positions. Une arete qui traverse une porte a un minimum
    faible, elle tombe la premiere. C est l esprit de la dilatation.
  · Je NE teste PAS la visibilite entre positions : ce serait reimplementer la regle d A3C
    et le resultat serait circulaire. La seule information de mur est le degagement.
  · Je saute le raffinement par modularite : dilatation + composantes connexes d abord.

PLAFOND DECLARE : les batiments de plus de 80 positions sont tronques a 80 (mediane = 10,
maximum = 266). Ce n est pas silencieux, c est ecrit ici et compte dans la sortie.
"""
import sys, os, time, re, json, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SB = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5848, 6080
LOG = SB + "/logs/serverDEG.out"
MODS = "@CBA_A3;@A3C;@cup_terrains_core;@cup_terrains_maps"
POSE = "[1720, 5580, 0]"
PAR_BLOC = 150
NMAX = 80
SORTIE = "/home/younes/arma3-marl/logs_train/corpus_degagement.jsonl"


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
    private _bp = _b buildingPos -1;
    private _n = count _bp;
    private _tronque = 0;
    if (_n > NMAX_) then { _bp resize NMAX_; _tronque = 1 };
    HMT_DEG = {
        params ["_p"];
        private _d = 8;
        for "_k" from 0 to 7 do {
            private _ang = _k * 45;
            private _a = AGLToASL [_p select 0, _p select 1, (_p select 2) + 1];
            private _e = _a vectorAdd [8 * sin _ang, 8 * cos _ang, 0];
            private _r = lineIntersectsSurfaces [_a, _e, objNull, objNull, true, 1, "GEOM", "NONE"];
            if (count _r > 0) then {
                private _dd = _a distance ((_r select 0) select 0);
                if (_dd < _d) then { _d = _dd };
            };
        };
        _d
    };
    private _cl = "";
    { _cl = _cl + format ["%1^", round (([_x] call HMT_DEG) * 100) / 100] } forEach _bp;
    private _pa = "";
    for "_i" from 0 to (count _bp - 2) do {
        for "_j" from (_i + 1) to (count _bp - 1) do {
            private _pi = _bp select _i; private _pj = _bp select _j;
            if (_pi distance _pj < 8) then {
                private _mn = 8;
                for "_s" from 1 to 3 do {
                    private _t = _s / 4;
                    private _m = _pi vectorAdd ((_pj vectorDiff _pi) vectorMultiply _t);
                    private _dv = [_m] call HMT_DEG;
                    if (_dv < _mn) then { _mn = _dv };
                };
                _pa = _pa + format ["%1,%2,%3^", _i, _j, round (_mn * 100) / 100];
            };
        };
        sleep 0.001;
    };
    deleteVehicle _b;
    diag_log format ["HMT_G %1|%2|%3|%4|%5", IDX_, _cls, _tronque, _cl, _pa];
};
'''


def lance():
    sh("pkill -9 -f serverDEG.cfg; sleep 2")
    sh("cp %s/staging/serverBAL.cfg %s/staging/serverDEG.cfg" % (SB, SB))
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverDEG.cfg' -profiles='%s/profilesDEG' "
       "-port=%d -world=Stratis -autoInit -mod='%s' >> '%s' 2>&1 < /dev/null & disown"
       % (SB, EXT, SB, SB, PORT, MODS, LOG))
    time.sleep(75)
    return SocketBridge(EXT)


def att(b, motif, sec=60):
    t0 = time.time()
    while time.time() - t0 < sec:
        h = [L for L in b._log_lines(3000) if motif in L]
        if h:
            return h[-1]
        time.sleep(0.15)
    return None


if __name__ == "__main__":
    b = lance()
    b.send(nc(CRIBLE.replace("POSE_", POSE)), wait=False)
    L = att(b, "HMT_LISTE n=", 900)
    total = int(re.search(r"n=(\d+)", L).group(1))
    print("modeles : %d  (plafond %d positions)" % (total, NMAX), flush=True)
    total = min(total, int(os.environ.get("LIMITE", total)))
    ok = ko = tr = 0
    with open(SORTIE, "w") as fh:
        i = 0
        while i < total:
            if i > 0 and i % PAR_BLOC == 0:
                b.sock.close(); sh("pkill -9 -f serverDEG.cfg; sleep 3")
                b = lance()
                b.send(nc(CRIBLE.replace("POSE_", POSE)), wait=False); att(b, "HMT_LISTE n=", 900)
                print("  [relance a %d]" % i, flush=True)
            b.send(nc(UN.replace("IDX_", str(i)).replace("POSE_", POSE).replace("NMAX_", str(NMAX))), wait=False)
            ligne = att(b, "HMT_G %d|" % i, 90)
            if not ligne:
                ko += 1; i += 1; continue
            ch = ligne.split("HMT_G ", 1)[1].split("|")
            if len(ch) < 5:
                ko += 1; i += 1; continue
            deg = []
            for e in ch[3].split("^"):
                try:
                    deg.append(float(e))
                except ValueError:
                    pass
            aretes = []
            for e in ch[4].split("^"):
                q = e.split(",")
                if len(q) == 3:
                    try:
                        aretes.append([int(q[0]), int(q[1]), float(q[2])])
                    except ValueError:
                        pass
            tr += int(ch[2])
            fh.write(json.dumps({"i": i, "type": ch[1], "tronque": int(ch[2]),
                                 "degagement": deg, "aretes": aretes}) + "\n")
            fh.flush(); ok += 1
            if i % 100 == 0:
                print("  %d/%d  ok=%d ko=%d tronques=%d" % (i, total, ok, ko, tr), flush=True)
            i += 1
    b.sock.close(); sh("pkill -9 -f serverDEG.cfg")
    print("\ncorpus degagement : %s  (%d ok, %d muets, %d tronques a %d positions)"
          % (SORTIE, ok, ko, tr, NMAX), flush=True)
