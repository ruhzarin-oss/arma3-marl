"""
Banc de perception, version 3 ( nuit du 18 au 19/09 ) : POSTURE, BALAYAGE et CIBLE REELLEMENT VISIBLE. Vise bancs/chacalvue seulement.
S applique apres patch_banc_vue_fine, patch_banc_journal et patch_banc_regard ( il reecrit le bloc du banc en entier, d un seul tenant ).

  modes ( CHACAL_CONTROLE_PERCEPTION ) :
    1  controle POSITIF de la mission ( inchange : cible debout, dans le secteur balaye )
    5  banc REGARD CENTRE : tous les hommes sont tournes vers la cible des la premiere seconde
    7  banc BALAYAGE DE LA MISSION : la cible est posee a CHACAL_CONTROLE_AZ degres de l axe de la phase ; les hommes balaient
       comme dans la mission ( trois azimuts -45 / 0 / +45, doWatch toutes les 10 s ). Mesure ce que la fenetre de la mission vaut.
    8  banc BALAYAGE REPARE : meme pose, mais chaque changement d azimut TOURNE les hommes ( setDir ) avant le doWatch.
  deux leviers neufs : CHACAL_CONTROLE_AZ ( ecart d azimut entre la cible et l axe, en degres ) et CHACAL_CONTROLE_POSTURE
    ( 0 debout, 1 accroupie comme les vraies menaces de 35_menaces.sqf ).
  cible REELLEMENT visible : apres la pose, si aucun homme n a une checkVisibility >= 0,10 vers la cible reelle, on la retire et on
    essaie le candidat suivant ( six au plus ). Le 18/09 au soir, 4 episodes sur 33 etaient des cibles masquees par la pose a 3 m pres.
Usage : python3 patch_banc_modes.py [depot]   ( --racine <dossier du banc> pour une copie )
"""
import sys
if "--racine" in sys.argv: B = sys.argv[sys.argv.index("--racine") + 1]
else: B = f"{sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/hmt/depot'}/bancs/chacalvue"
PH, EXT, SOC, LAN = f"{B}/mission.Altis/chacal/60_phases.sqf", f"{B}/mission.Altis/description.ext", f"{B}/mission.Altis/chacal/00_socle.sqf", f"{B}/lancer.sh"


def lire(p): return open(p, encoding="utf-8").read()
def ecrire(p, s): open(p, "w", encoding="utf-8").write(s)
def remplacer(s, a, b, quoi, n=1):
    assert s.count(a) == n, f"ancre « {quoi} » trouvee {s.count(a)} fois, attendu {n}"
    return s.replace(a, b)


s = lire(PH)
assert "TOURNE vers la cible" in s and "BANC_TERMINE" in s and "RECHERCHE FINE" in s, "les trois patchs precedents doivent etre appliques"
assert "BANC, VERSION 3" not in s, "patch deja applique"

# 1. l axe de la phase doit survivre au bloc ou il est calcule
s = remplacer(s, '''    if (count _secteur > 0) then {
        private _chefF = leader (group (_hommes select 0));
        private _axe = _chefF getDir _secteur;
''', '''    private _axePhase = -1;
    if (count _secteur > 0) then {
        private _chefF = leader (group (_hommes select 0));
        private _axe = _chefF getDir _secteur; _axePhase = _axe;
''', "axe de la phase")

# 2. le bloc du banc, reecrit d un seul tenant
debut = "    if ((CHACAL_CONTROLE_PERCEPTION in [1, 5]) && { count _hommes > 0 }) then {\n"
fin = "    if ((CHACAL_CONTROLE_PERCEPTION in [2, 3]) && { count _hommes > 0 }) then {\n"
assert s.count(debut) == 1 and s.count(fin) == 1
i, j = s.index(debut), s.index(fin)
bloc = '''    if ((CHACAL_CONTROLE_PERCEPTION in [1, 5, 7, 8]) && { count _hommes > 0 }) then {
        // ! BANC, VERSION 3 ( nuit du 18/09 ). 5 = regard centre ; 7 = balayage de la mission ; 8 = balayage repare ; 1 = controle positif.
        private _banc = CHACAL_CONTROLE_PERCEPTION in [5, 7, 8];
        private _balaie = CHACAL_CONTROLE_PERCEPTION in [7, 8];
        private _chef = leader (group (_hommes select 0));
        private _oeil = (getPosASL _chef) vectorAdd [0, 0, 1.5];
        private _nH = count _hommes; private _haut = if (CHACAL_CONTROLE_POSTURE == 1) then {1.0} else {1.6};
        if (_axePhase < 0) then { _axePhase = getDir _chef };
        // les azimuts a essayer : tout le tour ( 72 ) en regard centre ; l axe + l ecart demande, a +-10 deg, en balayage
        private _azs = [];
        if (_balaie) then { { _azs pushBack ((_axePhase + CHACAL_CONTROLE_AZ + _x + 720) % 360) } forEach [0, -5, 5, -10, 10] }
        else { for "_a" from 0 to 355 step 5 do { _azs pushBack _a } };
        // ! RECHERCHE FINE : on compte les HOMMES qui voient chaque point, et on range les candidats du meilleur au moins bon ;
        // a egalite l ordre d essai gagne ( distance demandee d abord ).
        private _cands = []; private _rang = 0;
        {
            private _d = CHACAL_CONTROLE_DIST * _x;
            {
                _rang = _rang + 1;
                private _pC = _chef getPos [_d, _x];
                private _cible = (ATLToASL _pC) vectorAdd [0, 0, _haut];
                if (!(surfaceIsWater _pC) && { !(terrainIntersectASL [_oeil, _cible]) }) then {
                    private _n = { (count (lineIntersectsSurfaces [eyePos _x, _cible, _x, objNull, true, 1, "VIEW", "VIEW"])) == 0 } count _hommes;
                    if ((_n * 2) >= _nH) then { _cands pushBack [_n, -_rang, _x, _d] };
                };
            } forEach _azs;
        } forEach [1, 0.97, 1.03, 0.94, 1.06];
        _cands sort false;
        if (count _cands == 0) exitWith {
            // ! AUCUNE LIGNE DE VUE : poser la cible mesurerait le relief, pas la perception. En mode banc on rend l episode tout de suite.
            (format ["CHACAL|E|banc_refuse|%1|phase|%2|distance|%3|cause|AUCUNE_LIGNE_DE_VUE|hommes_avec_vue|0|hommes|%4|mode|%5|az_consigne|%6",
                round (time * 100) / 100, _phase, CHACAL_CONTROLE_DIST, _nH, CHACAL_CONTROLE_PERCEPTION, CHACAL_CONTROLE_AZ]) call CHACAL_LOG;
            if (_banc) then { CHACAL_ISSUE = "VOID"; CHACAL_CAUSE = "BANC_SANS_LIGNE_DE_VUE"; CHACAL_FIN = true };
        };
        // ! LA CIBLE REELLE DOIT ETRE VISIBLE : createUnit la pose a 3 m pres du point teste, et elle peut tomber derriere un buisson
        // ( 4 episodes sur 33 le 18/09 au soir ). On pose, on mesure checkVisibility vers la cible REELLE, et si personne ne la voit
        // on la retire et on essaie le candidat suivant, six au plus. Si aucun ne passe, on garde le premier et on l ECRIT ( vis_pose ).
        private _g = grpNull; private _az = 0; private _dPose = 0; private _nVue = 0; private _visPose = -1; private _essais = 0;
        private _poser = {
            params ["_c"];
            private _gg = createGroup east;
            private _pp = _chef getPos [_c select 3, _c select 2];
            {
                private _u = _gg createUnit [_x, _pp, [], 3, "NONE"]; _u disableAI "AUTOTARGET"; _u disableAI "TARGET"; _u disableAI "MOVE";
                _u setUnitPos (if (CHACAL_CONTROLE_POSTURE == 1) then {"MIDDLE"} else {"UP"});
            } forEach ["O_Soldier_TL_F", "O_Soldier_F", "O_Soldier_F"];
            _gg setCombatMode "BLUE"; _gg setBehaviour "SAFE";
            _gg
        };
        {
            if (isNull _g && { _essais < 6 }) then {
                _essais = _essais + 1;
                private _gg = [_x] call _poser;
                private _cB = leader _gg;
                private _v = selectMax (_hommes apply { [_x, "VIEW", _cB] checkVisibility [eyePos _x, aimPos _cB] });
                if (_v >= 0.1) then { _g = _gg; _az = _x select 2; _dPose = _x select 3; _nVue = _x select 0; _visPose = _v }
                else { { deleteVehicle _x } forEach (units _gg); deleteGroup _gg };
            };
        } forEach _cands;
        if (isNull _g) then {
            private _c = _cands select 0;
            _g = [_c] call _poser; _az = _c select 2; _dPose = _c select 3; _nVue = _c select 0;
            private _cB = leader _g;
            _visPose = selectMax (_hommes apply { [_x, "VIEW", _cB] checkVisibility [eyePos _x, aimPos _cB] });
        };
        private _vueReelle = { ([_x, "VIEW", leader _g] checkVisibility [eyePos _x, aimPos (leader _g)]) > 0.5 } count _hommes;
        CHACAL_MENACES pushBack [_phase, "BANC_PERCEPTION", _g];
        _gBanc = _g;
        if (CHACAL_CONTROLE_PERCEPTION == 5) then {
            private _cibleU = leader _g;
            // ! « REGARDEE » DES LA PREMIERE SECONDE : doWatch seul met jusqu a 90 s a pivoter de 24 deg ( fumee du 18/09, monde 5 ),
            // et le banc mesurait ce pivot. Chaque homme est TOURNE vers la cible, puis la fixe.
            { _x setDir (_x getDir _cibleU); _x doWatch _cibleU } forEach _hommes;
            _regards = [];                            // le banc a regard centre ne balaie pas
        };
        if (CHACAL_CONTROLE_PERCEPTION == 1) then { _regards = [getPosATL (leader _g)] };   // controle POSITIF : la cible est dans le secteur balaye
        // modes 7 et 8 : _regards garde les trois azimuts de la mission ; la cible n est PAS designee aux hommes
        (format ["CHACAL|E|banc_perception|%1|phase|%2|distance|%3|azimut|%4|ligne_de_vue|1|heure|%5|lune|%6|jumelles|%7|hommes|%8|hommes_avec_vue|%9|vue_reelle|%10|distance_posee|%11|mode|%12|posture|%13|az_consigne|%14|axe|%15|essais|%16|vis_pose|%17|candidats|%18",
            round (time * 100) / 100, _phase, CHACAL_CONTROLE_DIST, round _az,
            (date select 3) + ((date select 4) / 60), moonIntensity,
            ((_hommes apply { hmd _x }) joinString ","), _nH, _nVue, _vueReelle, round _dPose,
            CHACAL_CONTROLE_PERCEPTION, CHACAL_CONTROLE_POSTURE, CHACAL_CONTROLE_AZ, round _axePhase, _essais, (round (_visPose * 100)) / 100, count _cands]) call CHACAL_LOG;
    };
'''
s = s[:i] + bloc + s[j:]

# 3. le balayage : en mode 8 chaque changement d azimut TOURNE les hommes
s = remplacer(s, '''            { _x doWatch (_regards select _iRegard) } forEach (CHACAL_FS select { alive _x });
''', '''            // ! mode 8 : le balayage REPARE tourne les hommes ( setDir ) ; doWatch seul pivote trop lentement pour tenir 10 s par azimut
            {
                if (CHACAL_CONTROLE_PERCEPTION == 8) then { _x setDir (_x getDir (_regards select _iRegard)) };
                _x doWatch (_regards select _iRegard);
            } forEach (CHACAL_FS select { alive _x });
''', "balayage de la fenetre")

# 4. fermeture anticipee et fin d episode : tous les modes de banc
s = remplacer(s, "        if ((CHACAL_CONTROLE_PERCEPTION == 5) && { !isNull _gBanc } && { _tConnue < 0 }) then {",
              "        if ((CHACAL_CONTROLE_PERCEPTION in [5, 7, 8]) && { !isNull _gBanc } && { _tConnue < 0 }) then {", "fermeture anticipee")
s = remplacer(s, '    if ((CHACAL_CONTROLE_PERCEPTION == 5) && { !CHACAL_FIN }) then { CHACAL_ISSUE = "VOID"; CHACAL_CAUSE = "BANC_TERMINE"; CHACAL_FIN = true };',
              '    if ((CHACAL_CONTROLE_PERCEPTION in [5, 7, 8]) && { !CHACAL_FIN }) then { CHACAL_ISSUE = "VOID"; CHACAL_CAUSE = "BANC_TERMINE"; CHACAL_FIN = true };', "fin d episode")
ecrire(PH, s)

# 5. les deux leviers : description.ext, 00_socle.sqf, lancer.sh
e = lire(EXT)
assert "CHACAL_CONTROLE_AZ" not in e
ancre = '''    class CHACAL_CONTROLE_DIST
    {'''
e = remplacer(e, ancre, '''    class CHACAL_CONTROLE_AZ
    {
        title = "Banc de perception, modes 7 et 8 : ecart d azimut entre la cible et l axe de la phase, en degres";
        values[] = {0,30,60,90,135,180}; texts[] = {"0","30","60","90","135","180"}; default = 0;
    };
    class CHACAL_CONTROLE_POSTURE
    {
        title = "Banc de perception : posture de la cible, 0 debout, 1 accroupie";
        values[] = {0,1}; texts[] = {"0","1"}; default = 0;
    };
''' + ancre, "parametre CONTROLE_DIST de description.ext")
ecrire(EXT, e)
c = lire(SOC)
assert "CHACAL_CONTROLE_AZ" not in c
a = 'CHACAL_CONTROLE_DIST = ["CHACAL_CONTROLE_DIST", 150] call BIS_fnc_getParamValue;'
c = remplacer(c, a, 'CHACAL_CONTROLE_AZ = ["CHACAL_CONTROLE_AZ", 0] call BIS_fnc_getParamValue;   // banc, modes 7 et 8 : ecart d azimut cible / axe de la phase\n'
              'CHACAL_CONTROLE_POSTURE = ["CHACAL_CONTROLE_POSTURE", 0] call BIS_fnc_getParamValue;   // banc : 0 debout, 1 accroupie\n' + a, "lecture de CONTROLE_DIST")
ecrire(SOC, c)
l = lire(LAN)
assert "CONTROLE_AZ" not in l
a = 'ecrire_param OBSERVATION "$OBSERVATION";'
assert l.count(a) == 1
l = l.replace(a, '# banc de perception, version 3 : ecart d azimut ( modes 7 et 8 ) et posture de la cible, ecrits a CHAQUE lancement, 0 par defaut\n'
              'ecrire_param CONTROLE_AZ "$(lit controle_az 0)"; ecrire_param CONTROLE_POSTURE "$(lit controle_posture 0)"\n' + a)
ecrire(LAN, l)
print("patch banc_modes applique :", B)
