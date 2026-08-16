#!/usr/bin/env python3
"""recolte_pieces — positions interieures BRUTES -> decoupage en PIECES, par modele.

POURQUOI UNE SECONDE RECOLTE. Le balayage a enregistre le NOMBRE de pieces et le nombre de
portes, mais pas QUELLE position appartient a QUELLE piece. Or c est exactement la cible
qu on veut apprendre. Ma faute : le parseur extrayait `/p(\\d+)~` et jetait le `R0=[1,2,3]`.

MAIS CELLE-CI EST BIEN PLUS RAPIDE : on n a besoin ni d assaillants, ni de combat, ni
d attendre les plans. `A3C_main_fnc_buildingCreateRooms` se laisse appeler directement.
Une a deux secondes par modele au lieu de vingt.

CIBLE : la partition des positions interieures en pieces. C est ce que le controle a
certifie a 98 % entre pose et terrain, et c est ce qui varie vraiment avec la geometrie
(2 a 34 pieces), contrairement a la repartition des hommes qui ne prend que 5 valeurs.

LIMITE STRUCTURELLE, ECRITE AVANT LA MESURE : A3C decoupe par LIGNE DE VUE MUTUELLE entre
positions — donc par les MURS. Or les murs ne sont PAS dans ce que j enregistre : je n ai
que les positions ou un homme peut se tenir. Deux positions a 3 m avec une cloison entre
elles sont dans deux pieces ; deux positions a 10 m dans un hall sont dans la meme. Un
modele nourri des seules positions pourrait donc etre incapable de retrouver le decoupage
autrement que par correlation avec la distance. Si c est le cas, la mesure le dira, et la
conclusion ne sera pas "A3C est trivial" mais "mon entree est incomplete".
"""
import sys, os, time, re, json, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SB = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5847, 6079
LOG = SB + "/logs/serverREC.out"
MODS = "@CBA_A3;@A3C;@cup_terrains_core;@cup_terrains_maps"
POSE = "[1720, 5580, 0]"
PAR_BLOC = 150
SORTIE = "/home/younes/arma3-marl/logs_train/corpus_decoupage.jsonl"


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
private _cls = HMT_LISTE select IDX_;
private _b = _cls createVehicleLocal POSE_;
_b setVectorUp [0, 0, 1];
private _bp = _b buildingPos -1;
private _bpc = [_b] call MCSS_fnc_getLastBuildingPosIndex;
private _rooms = [_b, _bpc, false] call A3C_main_fnc_buildingCreateRooms;
private _g = "";
{ private _m = _b worldToModel _x; _g = _g + format ["%1@%2@%3^", round ((_m select 0) * 10) / 10, round ((_m select 1) * 10) / 10, round ((_m select 2) * 10) / 10] } forEach _bp;
private _r = "";
{
    private _idx = _x select 0;
    private _portes = "";
    { private _m = _b worldToModel _x; _portes = _portes + format ["%1@%2@%3+", round ((_m select 0) * 10) / 10, round ((_m select 1) * 10) / 10, round ((_m select 2) * 10) / 10] } forEach (_x select 1);
    _r = _r + format ["%1=%2~", _idx, _portes];
} forEach _rooms;
private _bb = boundingBoxReal _b;
deleteVehicle _b;
diag_log format ["HMT_D %1|%2|%3|%4|%5|%6|%7", IDX_, _cls, count _bp, _g, _r, round (((_bb select 1) select 0) * 10) / 10, round (((_bb select 1) select 1) * 10) / 10];
'''


def lance():
    sh("pkill -9 -f serverREC.cfg; sleep 2")
    sh("cp %s/staging/serverBAL.cfg %s/staging/serverREC.cfg" % (SB, SB))
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverREC.cfg' -profiles='%s/profilesREC' "
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
        time.sleep(0.15)
    return None


def pts(t, sep="^"):
    o = []
    for e in t.split(sep):
        q = e.split("@")
        if len(q) < 3:
            continue
        try:
            o.append([float(q[0]), float(q[1]), float(q[2])])
        except ValueError:
            continue
    return o


if __name__ == "__main__":
    b = lance()
    b.send(nc(CRIBLE.replace("POSE_", POSE)), wait=False)
    L = att(b, "HMT_LISTE n=", 900)
    total = int(re.search(r"n=(\d+)", L).group(1))
    print("modeles : %d" % total, flush=True)
    ok = ko = 0
    with open(SORTIE, "w") as fh:
        i = 0
        while i < total:
            if i > 0 and i % PAR_BLOC == 0:
                b.sock.close(); sh("pkill -9 -f serverREC.cfg; sleep 3")
                b = lance()
                b.send(nc(CRIBLE.replace("POSE_", POSE)), wait=False); att(b, "HMT_LISTE n=", 900)
                print("  [relance a %d]" % i, flush=True)
            b.send(nc(UN.replace("IDX_", str(i)).replace("POSE_", POSE)), wait=False)
            ligne = att(b, "HMT_D %d|" % i, 25)
            if not ligne:
                ko += 1; i += 1; continue
            ch = ligne.split("HMT_D ", 1)[1].split("|")
            if len(ch) < 7:
                ko += 1; i += 1; continue
            pieces = []
            for bloc in ch[4].split("~"):
                if "=" not in bloc:
                    continue
                g, p = bloc.split("=", 1)
                try:
                    idx = json.loads(g.replace(" ", ""))
                except Exception:
                    continue
                if not isinstance(idx, list):
                    continue
                pieces.append({"positions": [int(x) for x in idx], "portes": pts(p, "+")})
            fh.write(json.dumps({"i": i, "type": ch[1], "npos": int(ch[2]),
                                 "geom": pts(ch[3]), "pieces": pieces,
                                 "bbox": [float(ch[5]), float(ch[6].split()[0])]}) + "\n")
            ok += 1
            if i % 100 == 0:
                print("  %d/%d  ok=%d ko=%d" % (i, total, ok, ko), flush=True)
            i += 1
    fh_ok = ok
    b.sock.close(); sh("pkill -9 -f serverREC.cfg")
    print("\ncorpus decoupage : %s  (%d modeles, %d muets)" % (SORTIE, fh_ok, ko), flush=True)
