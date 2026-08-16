#!/usr/bin/env python3
"""banc_executant — LE 4,7x VIENT-IL DE L EXECUTANT ?

Acquis : A3C repare tue 4,20/6 contre 0,90 pour un doMove vers les MEMES positions
interieures. Refute le 15/08 : ce n est pas le tir force (retirer doTarget/reveal/doFire/
forgetTarget donne 5,00, ca ne s effondre pas). Ce n est pas non plus "combien entrent"
(3,30 contre 2,00, p=0,108). Reste l EXECUTANT.

`fnc_actionExecuteUnitPlot.sqf` fait 1 511 lignes et se decrit lui-meme comme LA fonction
de mouvement d A3C — postures, synchronisation entre binomes, mode de combat, vitesse,
rayon, reprise. Le temoin `doMove` envoie les hommes aux memes points et obtient 0,90.
L hypothese est donc que TOUT l ecart tient dans la maniere de conduire l homme.

L EXPERIENCE : meme plan, meme feu, meme tout — on remplace seulement l executant.
  REF    : l executant d origine (controle d instrument, doit refaire ~4,20)
  DOMOVE : un executant minimal AU MEME CONTRAT — il consomme A3C_PLOT point par point,
           pose A3C_PLOT_ACTIVE, mais ne fait qu un `doMove` et attendre. Pas de posture,
           pas de synchronisation, pas de reprise.

CE QUI FERAIT ECHOUER : tailles de fonction identiques (substitution non prise) ; REF loin
de 4,20 (instrument infidele) ; erreurs SQF non nulles.
ET SI L ECART NE S EFFONDRE PAS, LE MECANISME EST DIFFUS ET ON ARRETE CE FIL — declare
d avance pour ne pas en faire un puits sans fond.

Ancien entete :
banc_feu — LE 4,7x VIENT-IL DE LA DISCIPLINE DE FEU ?

Mesure du 15/08 : A3C repare tue 4,20 defenseurs sur 6 contre 0,90 pour un doMove
(p=0,00010) SANS faire entrer plus d hommes (3,30 contre 2,00, p=0,108). L avantage n est
donc ni dans le deplacement ni dans la repartition. `fnc_actionClearBuilding.sqf` lignes
249-286 revele le mecanisme candidat : pour chaque homme et chaque cible, A3C calcule la
ligne de vue REELLE (`lineIntersectsWith` contre le batiment), puis force `doTarget`,
`reveal [_target,4]` et `doFire` — et `forgetTarget` sur ce qu on ne voit pas, pour que
l homme cesse de fixer un mur. Un registre partage `A3C_ENGAGEDTARGETS` evite que ce
"forget" efface une cible qu un camarade voit encore.

L EXPERIENCE : on recompile la routine depuis sa source extraite, en deux variantes.
  REF     : source inchangee (l include du script_component, inutile ici, est retiree)
  SANSFEU : MEME source, MEMES calculs, on retire seulement les QUATRE appels qui AGISSENT
            — doTarget, reveal, doFire, forgetTarget. La decision de tir est toujours
            calculee, elle n est plus executee.

REF EST LE CONTROLE DE L INSTRUMENT : s il ne reproduit pas les 4,20 de l original, ma
recompilation est infidele et la comparaison SANSFEU ne vaut rien. On le verifie AVANT
de lire quoi que ce soit.

CE QUI FERAIT ECHOUER : taille de fonction identique entre les deux bras (la substitution
n a pas pris) ; REF loin de 4,20 (recompilation infidele) ; erreurs SQF non nulles.

Ancien entete :
usine_saine — REPRISE SUR UN A3C REPARE, AVEC GARDE DE SANTE DU MONDE.

Ancien entete :
usine_bis — ON DOUBLE L ECHANTILLON. Suite de usine_corpus.py, meme monde, meme protocole.

POURQUOI. Le verdict "la geometrie d A3C est indistinguable d un doMove" reposait sur
AUC=0,889 avec p=0,065 et n=6 par bras. Un AUC de 0,889 est une separation FORTE avec un
test SOUS-PUISSANT : lire ce p comme une egalite, c est prendre un accord obtenu sur trop
peu pour un accord. Toute la lecture de la soiree reposait dessus. On passe a 16 par bras.

RIEN NE CHANGE D AUTRE : meme batiment, meme cap, meme duree, meme tick, meme ordre. Les
manches s AJOUTENT au corpus existant (rid a partir de 19), elles ne le remplacent pas.
Seul le bras LAMBS est retire : A3C contre LAMBS etait deja tranche (AUC 1,000, p=0,005).

CE QUI FERAIT ECHOUER : des rid en double, ou des ticks par manche differents de 120 —
signe que le protocole a bouge et que les 6 anciennes manches ne sont plus comparables.

--- entete d origine ---
usine_corpus — A3C et LAMBS recoivent LA MEME intention, on enregistre la GEOMETRIE.

LA QUESTION : l usine a corpus A3C produit-elle quelque chose que LAMBS ne produisait
deja ? Si les deux profs ecrivent la meme geometrie, il n y a pas d usine.

INTENTION COMMUNE : nettoyer ce batiment.
  bras A3C   : [_units, _bld] call A3C_ai_shared_fnc_actionClearBuilding
  bras LAMBS : [_grp, _pos, 30] spawn lambs_wp_fnc_taskCQB      (Public, meme intention)

CE QUI EST DECLARE AVANT LE PREMIER PAS :
  · LAMBS EST CHARGE DANS LES DEUX BRAS. Son etage « danger » modifie la reaction de
    TOUTE IA ; le laisser d un cote seulement changerait deux choses a la fois. Le
    contraste porte donc sur LA ROUTINE DE TACHE, pas sur le mod. C est une limite
    assumee, pas un oubli.
  · LE MONDE FORCE L ENTREE, ET C EST MESURE. Batiment Land_i_House_Big_01_V1_F : ses
    9 positions interieures sont TOUTES hors de vue des 8 points de depart (test
    lineIntersects, 9/9 bloquees). La garnison ne peut donc PAS etre tuee depuis
    l exterieur : entrer est le seul chemin. Un premier essai filtrait par « z modele
    > 3 m » — ce filtre ne matchait RIEN (hautes=0 partout, meme sur une tour de 25 m)
    et retombait en silence sur toutes les positions. La vue se mesure, elle ne se
    suppose pas.
  · METRIQUE « DEDANS » : boite englobante reelle du batiment en repere MODELE, plus un
    toit au-dessus de la tete (lineIntersects vers le ciel). Premiere version rejetee :
    « a moins de 2,5 m d une des 9 positions cataloguees » donnait dedans=0 alors que les
    hommes etaient A 0,9 m DU CENTRE ET A 2,9 m DE HAUT, donc a l etage. La metrique
    ratait ce qu elle etait censee compter.
  · CONTROLE POSITIF : un troisieme bras `SCRIPT` envoie chaque homme a une position
    interieure par doMove. Si LUI n entre pas non plus, ce n est pas les profs qui
    echouent, c est le monde ou la metrique. Il manquait au banc precedent.
  · SEPARABILITE = CONDITION NECESSAIRE, PAS SUFFISANTE. Deux corpus distinguables
    peuvent etre egalement pauvres. Mais s ils ne le sont pas, l usine est vide et on
    s arrete la, sans entrainer quoi que ce soit.
  · FUITE DE GROUPES : le juge doit decouper PAR MANCHE, jamais par tick. Un tick de la
    manche 7 en apprentissage et un autre en test rendrait n importe quoi separable.

SORTIE : logs_train/corpus_a3c_lambs.jsonl — une ligne par tick, geometrie en repere
MODELE du batiment (invariante en translation/rotation).
"""
import sys, os, time, re, json, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SB = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5851, 6083
LOG = SB + "/logs/serverSAIN.out"
NDEF, NATT, DIST = 6, 8, 70.0
T_RUN, TICK = 240.0, 2.0
BRAS = ["REF", "DOMOVE"]
PAR_BLOC, BLOCS = 2, 9
RID0 = 3
SORTIE = os.environ.get("SORTIE", "/home/younes/arma3-marl/logs_train/banc_executant.jsonl")
SEUIL_ERREURS = 200        # au-dela, la manche est VOID sans intervention humaine
INIT = "/home/younes/arma3-marl/a3c_init_serveur.sqf"


def sh(c):
    subprocess.run(["bash", "-lc", c], check=False)


def sans_commentaires(s):
    return "\n".join(l.split("//")[0] for l in s.splitlines() if l.split("//")[0].strip())


SCENE = '''
HMT_REC = false;
sleep 0.3;
{ deleteVehicle _x } forEach (allUnits - allPlayers);
{ if (count (units _x) == 0) then { deleteGroup _x } } forEach allGroups;
HMT_C = [4000, 4000, 0];
{ if (toLower (text _x) == "agia marina") exitWith { HMT_C = locationPosition _x } } forEach (nearestLocations [[4000,4000,0], ["NameVillage","NameCity","NameCityCapital"], 12000]);
private _cands = nearestObjects [HMT_C, ["Land_i_House_Big_01_V1_F"], 800];
HMT_BLD = _cands select 0;
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
private _bb = boundingBoxReal HMT_BLD;
HMT_BBX = ((_bb select 1) select 0) - 0.5;
HMT_BBY = ((_bb select 1) select 1) - 0.5;
if (count HMT_HAUT < 3) then { HMT_HAUT = HMT_BPOS };
HMT_GD = createGroup east;
HMT_DEF = [];
for "_i" from 0 to (NDEF_ - 1) do {
    private _p = HMT_HAUT select (_i % (count HMT_HAUT));
    private _u = HMT_GD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL _p;
    _u disableAI "PATH";
    _u setSkill 0.6;
    HMT_DEF pushBack _u;
};
HMT_GD setBehaviour "COMBAT"; HMT_GD setCombatMode "RED";
HMT_GA = createGroup west;
HMT_ATT = [];
for "_i" from 0 to (NATT_ - 1) do {
    private _p = HMT_BLD getPos [DIST_, 200 + _i * 5];
    private _u = HMT_GA createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL [_p select 0, _p select 1, 0];
    _u setSkill 0.6;
    HMT_ATT pushBack _u;
};
HMT_GA setBehaviour "AWARE"; HMT_GA setCombatMode "RED";
diag_log format ["HMT_SCENE bat=%1 pos=%2 cachees=%3 bbox=%4x%5 def=%6 att=%7", typeOf HMT_BLD, count HMT_BPOS, HMT_CACHEES, round HMT_BBX, round HMT_BBY, count HMT_DEF, count HMT_ATT];
'''

ORDRES = {
    "REF": ('if (isNil "A3C_VRAI_exec") then { A3C_VRAI_exec = A3C_ai_shared_fnc_actionExecuteUnitPlot };'
            'A3C_ai_shared_fnc_actionExecuteUnitPlot = A3C_VRAI_exec;'
            'diag_log format ["HMT_VARIANTE REF taille=%1", count (str A3C_ai_shared_fnc_actionExecuteUnitPlot)];'
            '[HMT_ATT, HMT_BLD] call A3C_ai_shared_fnc_actionClearBuilding;'),
    "DOMOVE": ('if (isNil "A3C_VRAI_exec") then { A3C_VRAI_exec = A3C_ai_shared_fnc_actionExecuteUnitPlot };'
               'A3C_ai_shared_fnc_actionExecuteUnitPlot = { params ["_unit","_data"]; _unit setVariable ["A3C_PLOT_ACTIVE", true, true]; while { alive _unit && {count (_unit getVariable ["A3C_PLOT",[]]) > 0} } do { private _d = _unit getVariable ["A3C_PLOT",[]]; private _p = ((_d select 0) select 0) select 0; _unit doMove _p; private _t0 = time; waitUntil { sleep 0.5; !alive _unit || {(_unit distance _p) < 2.5} || {(time - _t0) > 30} }; _d = _unit getVariable ["A3C_PLOT",[]]; if (count _d > 0) then { _d deleteAt 0; _unit setVariable ["A3C_PLOT", _d, true] }; }; _unit setVariable ["A3C_PLOT_ACTIVE", false, true]; _unit setVariable ["A3C_PLOT", [], true]; };'
               'diag_log format ["HMT_VARIANTE DOMOVE taille=%1", count (str A3C_ai_shared_fnc_actionExecuteUnitPlot)];'
               '[HMT_ATT, HMT_BLD] call A3C_ai_shared_fnc_actionClearBuilding;'),
}

LANCE = '''
HMT_RID = RID_;
HMT_T = 0;
HMT_OK = 0;
ORDRE_
HMT_OK = 1;
diag_log format ["HMT_ORDRE rid=%1 ok=%2", HMT_RID, HMT_OK];
HMT_REC = true;
[] spawn {
    while {HMT_REC} do {
        private _s = "";
        {
            private _u = _x;
            private _m = HMT_BLD worldToModel (getPosATL _u);
            private _st = switch (stance _u) do { case "STAND": {0}; case "CROUCH": {1}; case "PRONE": {2}; default {3} };
            private _e = eyePos _u;
            private _toit = lineIntersects [_e, _e vectorAdd [0, 0, 40]];
            private _dd = if ((abs (_m select 0) < HMT_BBX) && {abs (_m select 1) < HMT_BBY} && {_toit}) then {1} else {0};
            _s = _s + format ["%1,%2,%3,%4,%5,%6;", round ((_m select 0) * 10) / 10, round ((_m select 1) * 10) / 10, round (((getPosATL _u) select 2) * 10) / 10, _st, (if (alive _u) then {1} else {0}), _dd];
        } forEach HMT_ATT;
        private _dv = { alive _x } count HMT_DEF;
        private _in = 0;
        {
            private _u = _x;
            if (alive _u) then {
                private _m2 = HMT_BLD worldToModel (getPosATL _u);
                private _e2 = eyePos _u;
                if ((abs (_m2 select 0) < HMT_BBX) && {abs (_m2 select 1) < HMT_BBY} && {lineIntersects [_e2, _e2 vectorAdd [0, 0, 40]]}) then { _in = _in + 1 };
            };
        } forEach HMT_ATT;
        diag_log format ["HMT_TRJ %1 %2 %3 %4 %5", HMT_RID, HMT_T, _dv, _in, _s];
        HMT_T = HMT_T + 1;
        sleep TICK_;
    };
};
'''


def sante(vider=False):
    """compte les erreurs SQF de variable A3C indefinie ; vide le journal si demande"""
    r = subprocess.run(["bash", "-lc",
        "grep -a -c 'Undefined variable in expression: a3c_' '%s' 2>/dev/null || echo 0" % LOG],
        capture_output=True, text=True)
    try:
        n = int(r.stdout.strip().split()[0])
    except Exception:
        n = -1
    vivant = subprocess.run(["bash", "-lc", "pgrep -f serverSAIN.cfg >/dev/null && echo 1 || echo 0"],
                            capture_output=True, text=True).stdout.strip() == "1"
    if vider:
        sh(": > '%s'" % LOG)
    return n, vivant


def pose_init(b):
    with open(INIT) as f:
        corps = f.read()
    corps += '\nif (isNil "A3C_OPACITY") then { A3C_OPACITY = 1 };\n'
    corps += 'diag_log format ["HMT_INIT posees=%1", count (allVariables missionNamespace select {_x find "a3c_" == 0})];\n'
    b.send(nc_(corps))
    return attendre(b, "HMT_INIT", 25)


def nc_(s):
    return "\n".join(l.split("//")[0] for l in s.splitlines() if l.split("//")[0].strip())


def _port_libre():
    r = subprocess.run(["bash", "-lc", "ss -lnt 2>/dev/null | grep -c ':%d '" % PORT],
                       capture_output=True, text=True)
    return r.stdout.strip() in ("0", "")


def lance_serveur():
    """resilient : on attend que le port se libere, et on retente jusqu a 3 fois.
    Panne observee le 15/08 : le serveur du bloc precedent tenait encore le port 6083,
    le nouveau n a pas pu s y lier et est mort en silence -> ConnectionRefused au pont."""
    for essai in range(3):
        sh("pkill -9 -f serverSAIN.cfg")
        for _ in range(20):
            if _port_libre():
                break
            time.sleep(1)
        _lance_une_fois()
        try:
            return SocketBridge(EXT, connect_timeout=60)
        except OSError:
            print("  [serveur non joignable, essai %d/3]" % (essai + 1), flush=True)
    raise RuntimeError("serveur injoignable apres 3 essais")


def _lance_une_fois():
    sh("pkill -9 -f serverSAIN.cfg; sleep 2")
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverSAIN.cfg' -profiles='%s/profilesSAIN' "
       "-port=%d -world=Stratis -autoInit -mod='@CBA_A3;@A3C;@LAMBS_Danger' "
       ">> '%s' 2>&1 < /dev/null & disown" % (SB, EXT, SB, SB, PORT, LOG))
    time.sleep(50)


def attendre(b, motif, sec=20):
    t0 = time.time()
    while time.time() - t0 < sec:
        h = [L for L in b._log_lines(800) if motif in L]
        if h:
            return h[-1]
        time.sleep(0.3)
    return None


def manche(b, bras, rid, fh):
    s = SCENE.replace("NDEF_", str(NDEF)).replace("NATT_", str(NATT)).replace("DIST_", str(DIST))
    b.send(sans_commentaires(s))
    sc = attendre(b, "HMT_SCENE", 25)
    if sc and "cachees=" in sc and int(sc.split("cachees=")[1].split()[0]) < 3:
        print("  MONDE NON FORCANT : %s" % sc.strip()[-60:], flush=True)
    if not sc:
        print("  manche %d [%s] SCENE ABSENTE" % (rid, bras), flush=True)
        return 0
    time.sleep(2)
    marque = len(b.lines)
    lanc = LANCE.replace("RID_", str(rid)).replace("ORDRE_", ORDRES[bras]).replace("TICK_", str(TICK))
    b.send(sans_commentaires(lanc))
    od = attendre(b, "HMT_ORDRE rid=%d" % rid, 20)
    ok = bool(od and "ok=1" in od)
    time.sleep(T_RUN)
    b.send("HMT_REC = false;")
    time.sleep(1.5)
    n = 0
    fin = None
    for L in list(b.lines)[marque:]:
        m = re.search(r"HMT_TRJ (\d+) (\d+) (\d+) (\d+) (.*)", L)
        if not m or int(m.group(1)) != rid:
            continue
        u = []
        for e in m.group(5).split(";"):
            if not e.strip():
                continue
            p = e.split(",")
            if len(p) == 6:
                u.append([float(p[0]), float(p[1]), float(p[2]), int(p[3]), int(p[4]), int(p[5])])
        if not u:
            continue
        fin = (int(m.group(3)), int(m.group(4)))
        fh.write(json.dumps({"rid": rid, "bras": bras, "t": int(m.group(2)),
                             "def_vivants": int(m.group(3)), "dedans": int(m.group(4)),
                             "u": u}) + "\n")
        n += 1
    fh.flush()
    taille = -1
    for L in list(b.lines)[marque:]:
        m = re.search(r"HMT_VARIANTE (\S+) taille=(\d+)", L)
        if m: taille = int(m.group(2))
    err, vivant = sante()
    void = (err > SEUIL_ERREURS) or (not vivant) or (n < 100)
    fh.write(json.dumps({"rid": rid, "bras": bras, "manifeste": True, "erreurs_sqf": err,
                         "serveur_vivant": vivant, "ticks": n, "taille_fnc": taille, "void": void}) + "\n")
    fh.flush()
    print("  manche %2d [%-6s] ordre_ok=%s ticks=%3d  fin: def=%s dedans=%s | erreurs SQF=%d vivant=%s%s"
          % (rid, bras, ok, n, fin[0] if fin else "?", fin[1] if fin else "?",
             err, vivant, "  <<< VOID" if void else "") + "  taille=%d" % taille, flush=True)
    return n


if __name__ == "__main__":
    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    rid = RID0
    with open(SORTIE, os.environ.get("MODE", "a")) as fh:
        for bloc in range(BLOCS):
            print("\n=== bloc %d/%d ===" % (bloc + 1, BLOCS), flush=True)
            b = lance_serveur()
            gi = pose_init(b)
            print("  %s" % (gi or "INIT SERVEUR NON POSEE"), flush=True)
            if not gi:
                b.sock.close(); continue
            p0 = attendre(b, "HARMATTAN", 10)
            b.send('private _a = count (allVariables missionNamespace select {_x find "a3c_ai_shared_fnc_" == 0}); private _l = if (isNil "lambs_wp_fnc_taskCQB") then {0} else {1}; diag_log format ["HMT_PORTE0 a3c=%1 lambsCQB=%2", _a, _l];')
            g = attendre(b, "HMT_PORTE0", 20)
            print("  %s" % (g or "PORTE0 MUETTE"), flush=True)
            if not g or "lambsCQB=1" not in g:
                print("  LAMBS taskCQB absente -> bras impossible, arret", flush=True)
                b.sock.close(); break
            for k in range(PAR_BLOC):
                bras = BRAS[(rid) % len(BRAS)]
                rid += 1
                try:
                    manche(b, bras, rid, fh)
                except OSError:
                    print("  [pont rompu en manche %d — relance et reprise]" % rid, flush=True)
                    try:
                        b.sock.close()
                    except Exception:
                        pass
                    b = lance_serveur()
                    pose_init(b)
                    try:
                        manche(b, bras, rid, fh)
                    except OSError:
                        print("  [manche %d perdue apres 2 essais]" % rid, flush=True)
            b.sock.close()
            sh("pkill -9 -f serverSAIN.cfg; sleep 3")
    print("\ncorpus ecrit : %s" % SORTIE, flush=True)
    sh("wc -l %s" % SORTIE)
