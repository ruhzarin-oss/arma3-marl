#!/usr/bin/env python3
"""controle_cap — un batiment POSE vaut-il un batiment DU TERRAIN ?

POURQUOI CE SCRIPT EXISTE : le premier controle changeait DEUX choses a la fois — le
batiment etait pose au lieu d etre sur le terrain, ET le cap d approche differait (les
deux balayages font cap = indice*37 mais l indice n est pas le meme). Or le cap change
l affectation : 11 types sur 26 variaient deja d un exemplaire a l autre sur le terrain.
Le 59 % d accord obtenu ne pouvait donc rien dire. Ici le cap est APPARIE : chaque type
est pose au cap exact de son exemplaire de terrain. Une seule variable bouge.

LECTURE DU RESULTAT, ecrite avant :
  · accord >= 90 % sur les batiments FERMES -> le corpus pose est valide, on entraine.
  · accord < 70 %                            -> le sol plat change la decision, les 707
    modeles sont un artefact et le balayage est a jeter.
  · entre les deux                           -> il faudra comprendre quoi diffère avant
    de payer un entrainement.
Les structures OUVERTES (jetees, radars) sont comptees a part : sans murs, leur decoupage
depend de ce qu il y a autour, un desaccord y est attendu et n accuse pas le procede.
"""
import sys, os, time, re, json, subprocess, collections
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SB = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5846, 6078
LOG = SB + "/logs/serverCTL.out"
MODS = "@CBA_A3;@A3C;@cup_terrains_core;@cup_terrains_maps"
POSE = "[1720, 5580, 0]"
ATTENTE = 6.5
PAR_TYPE = 3
OUVERT = ("Pier", "Radar", "Cargo_Patrol", "Net_", "Wall")

sys.path.insert(0, "/home/younes/arma3-marl")
from balayage_modeles import INSTRUMENT, wp, xy, nc, att   # meme instrument, meme parseurs


def sh(c):
    subprocess.run(["bash", "-lc", c], check=False)


CAPTURE = '''
HMT_RID = IDX_;
{ deleteVehicle _x } forEach (allUnits - allPlayers);
{ if (count (units _x) == 0) then { deleteGroup _x } } forEach allGroups;
if (!isNil "HMT_BLD") then { deleteVehicle HMT_BLD };
HMT_BLD = "CLS_" createVehicle POSE_;
HMT_BLD setVectorUp [0, 0, 1];
HMT_BPOS = HMT_BLD buildingPos -1;
private _cap = CAP_;
HMT_GA = createGroup west;
HMT_ATT = [];
for "_i" from 0 to 7 do {
    private _p = HMT_BLD getPos [70, _cap + _i * 5];
    private _u = HMT_GA createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL [_p select 0, _p select 1, 0];
    HMT_ATT pushBack _u;
};
diag_log format ["HMT_BAT %1|%2|%3|%4", IDX_, typeOf HMT_BLD, count HMT_BPOS, _cap];
[HMT_ATT, HMT_BLD] call A3C_ai_shared_fnc_actionClearBuilding;
'''


def lance():
    sh("pkill -9 -f serverCTL.cfg; sleep 2")
    sh("cp %s/staging/serverBAL.cfg %s/staging/serverCTL.cfg" % (SB, SB))
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverCTL.cfg' -profiles='%s/profilesCTL' "
       "-port=%d -world=Stratis -autoInit -mod='%s' >> '%s' 2>&1 < /dev/null & disown"
       % (SB, EXT, SB, SB, PORT, MODS, LOG))
    time.sleep(75)
    return SocketBridge(EXT)


def capte(b, i, cls, cap):
    marque = len(b.lines)
    b.send(nc(CAPTURE.replace("IDX_", str(i)).replace("CLS_", cls).replace("CAP_", str(cap)).replace("POSE_", POSE)), wait=False)
    if not att(b, "HMT_BAT %d|" % i, 30):
        return None
    time.sleep(ATTENTE)
    plans, pieces = [], None
    for L in list(b.lines)[marque:]:
        m = re.search(r"HMT_PLAN (-?\d+) (-?\d+) (\d+) (.*)", L)
        if m and m.group(1) == str(i):
            plans.append({"unite": int(m.group(2)), "wp": wp(m.group(4))})
        m2 = re.search(r"HMT_ROOMS (-?\d+) n=(\d+)", L)
        if m2 and m2.group(1) == str(i):
            pieces = int(m2.group(2))
    aff = {}
    for p in plans:
        for w in p["wp"]:
            if w.get("piece"):
                aff[p["unite"]] = w["piece"]
    return {"pieces": pieces, "affectation": aff}


if __name__ == "__main__":
    S = [json.loads(l) for l in open("/home/younes/arma3-marl/logs_train/corpus_pieces_Stratis.jsonl")]
    par = collections.defaultdict(list)
    for d in S:
        if len(par[d["type"]]) < PAR_TYPE:
            par[d["type"]].append(d)
    cas = [d for v in par.values() for d in v]
    print("cas a rejouer au cap apparie : %d (%d types)" % (len(cas), len(par)), flush=True)

    b = lance()
    b.send(nc(INSTRUMENT)); att(b, "HMT_INSTRUMENT", 25)
    res = []
    for i, d in enumerate(cas):
        r = capte(b, i, d["type"], d["cap"])
        if r is None:
            print("  %-38s cap=%3d  MUET" % (d["type"], d["cap"]), flush=True); continue
        mp = (r["pieces"] == d["pieces"])
        ma = (sorted(r["affectation"].items()) == sorted(d["affectation"].items()))
        ouvert = any(o.lower() in d["type"].lower() for o in OUVERT)
        res.append({"type": d["type"], "cap": d["cap"], "ouvert": ouvert,
                    "pieces_terrain": d["pieces"], "pieces_pose": r["pieces"],
                    "aff_terrain": d["affectation"], "aff_pose": r["affectation"],
                    "meme_pieces": mp, "meme_aff": ma})
        if i % 10 == 0:
            print("  %d/%d" % (i, len(cas)), flush=True)
    b.sock.close(); sh("pkill -9 -f serverCTL.cfg")

    json.dump(res, open("/home/younes/arma3-marl/logs_train/controle_cap.json", "w"), indent=1)
    for etiq, sel in (("FERMES", [r for r in res if not r["ouvert"]]),
                      ("ouverts (attendu discordant)", [r for r in res if r["ouvert"]])):
        if not sel:
            continue
        p = sum(1 for r in sel if r["meme_pieces"]); a = sum(1 for r in sel if r["meme_aff"])
        print("\n%s — %d cas" % (etiq, len(sel)))
        print("   memes PIECES      : %d/%d (%.0f%%)" % (p, len(sel), 100 * p / len(sel)))
        print("   meme AFFECTATION  : %d/%d (%.0f%%)" % (a, len(sel), 100 * a / len(sel)))
    ferm = [r for r in res if not r["ouvert"]]
    if ferm:
        t = 100 * sum(1 for r in ferm if r["meme_aff"]) / len(ferm)
        print("\nVERDICT : %s" % ("corpus pose VALIDE, on entraine" if t >= 90 else
                                  ("ARTEFACT du sol plat, balayage a jeter" if t < 70 else
                                   "ZONE GRISE — comprendre l ecart avant de payer un entrainement")))
        for r in ferm:
            if not r["meme_aff"]:
                print("   ecart: %-34s cap=%3d terrain=%s pose=%s" % (r["type"], r["cap"], r["aff_terrain"], r["aff_pose"]))
