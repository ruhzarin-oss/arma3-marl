"""
Menace visible, version 2 ( plans/plan-menace-visible.md, bc35b07 / b8e8509 ) :
  1. la fenetre rend la main ( doFollow ) et remet la posture a AUTO : le figeage de P4 est repare ;
  2. pendant la fenetre, les hommes SCRUTENT le secteur ( doWatch sur le point de reference de la phase ) ;
  3. quatre canaux ecrits ( oeil, groupe, camp, homme ) et un niveau conjugue menace_percue = 0, 1 ou 2 ;
  4. mode sonde : une ligne toutes les 5 s pendant la fenetre, pour mesurer quand la connaissance arrive ;
  5. CHACAL_CONTROLE_PERCEPTION : 1 = 150 m devant accroupi, 2 = 1500 m derriere, 3 = 150 m devant DEBOUT.
A appliquer quand aucun run ne tourne.
"""
import sys
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/hmt/depot"
B, O = f"{D}/bancs/chacal", f"{D}/outils"
P = f"{B}/mission.Altis/chacal/60_phases.sqf"

s = open(P, encoding="utf-8").read()
debut, fin = s.index("CHACAL_fnc_perceptionMenace = {"), s.index("CHACAL_fnc_decision = {")
assert debut < fin and (fin - debut) > 2000, "bloc des fonctions de perception introuvable"

NOUVEAU = r'''CHACAL_fnc_perceptionMenace = {
    // Quatre canaux, jamais la verite : l oeil ( geometrie ), le GROUPE, le CAMP, l HOMME.
    // menace_percue conjugue les deux premiers : 2 connue du groupe, 1 seulement visible, 0 rien ( decision de Younes, 17/09 ).
    private _menaces = call CHACAL_fnc_unitesMenace;
    private _hommes = CHACAL_FS select { alive _x };
    private _chefs = call CHACAL_fnc_chefsDetachement;
    private _vues = 0; private _connues = 0; private _camp = 0; private _homme = 0;
    private _dMin = -1; private _err = -1; private _vueDepuis = -1; private _mobile = -1; private _proche = objNull;
    {
        private _t = _x;
        private _vu = ({ [_x, _t, 800, 70] call CHACAL_fnc_voit } count _hommes) > 0;
        if (_vu) then { _vues = _vues + 1 };
        if ((west knowsAbout _t) > 1.4) then { _camp = _camp + 1 };
        if (({ ((_x targetKnowledge _t) select 1) } count _hommes) > 0) then { _homme = _homme + 1 };
        private _k = [];
        { private _kk = _x targetKnowledge _t; if (_kk select 0) exitWith { _k = _kk } } forEach _chefs;
        if (count _k > 0) then {
            _connues = _connues + 1;
            private _crue = _k select 6;
            private _d = 1e9;
            { _d = _d min (_x distance2D _crue) } forEach _hommes;
            if ((_dMin < 0) || { _d < _dMin }) then {
                _dMin = _d; _err = _k select 5; _proche = _t;
                _vueDepuis = if ((_k select 2) > 0) then { round (time - (_k select 2)) } else { -1 };
            };
        };
    } forEach _menaces;
    if (!isNull _proche) then {
        private _h = (_proche getVariable ["chacal_crue", []]) select { (time - (_x select 0)) <= 25 };
        _mobile = if (count _h >= 2) then { if ((((_h select 0) select 1) distance2D ((_h select ((count _h) - 1)) select 1)) > 10) then {1} else {0} } else {-1};
    };
    private _percue = if (_connues > 0) then {2} else { if (_vues > 0) then {1} else {0} };
    private _veh = 0;
    if ((!isNil "CHACAL_VEH_ROUTE") && { !isNull CHACAL_VEH_ROUTE } && { ({ (_x select 1) == "PATROUILLE_ROUTE" } count CHACAL_MENACES) > 0 }) then {
        if (({ (_x targetKnowledge CHACAL_VEH_ROUTE) select 0 } count _chefs) > 0) then { _veh = 1 };
    };
    private _vDist = -1;
    { private _t = _x; { private _dd = _x distance2D _t; if ((_vDist < 0) || { _dd < _vDist }) then { _vDist = _dd } } forEach _hommes } forEach _menaces;
    format ["|menace_percue|%1|menaces_vues|%2|menaces_connues|%3|menaces_camp|%4|menaces_homme|%5|distance_menace|%6|erreur_position|%7|menace_mobile|%8|vue_depuis|%9|vehicule_connu|%10|verite_menaces|%11|verite_distance_menace|%12|azimut_chef|%13",
        _percue, _vues, _connues, _camp, _homme, round _dMin, (round (_err * 10)) / 10, _mobile, _vueDepuis, _veh,
        count _menaces, round _vDist, (if (count _chefs > 0) then { round (getDir (_chefs select 0)) } else { -1 })]
};
CHACAL_fnc_secteurPhase = {
    params ["_phase"];
    switch (_phase) do {
        case 1: { if (isNil "CHACAL_LZ") then { [] } else { CHACAL_LZ } };
        case 2: { if (isNil "CHACAL_ROUTE") then { [] } else { CHACAL_ROUTE } };
        case 4: { if (isNil "CHACAL_SITE") then { [] } else { CHACAL_SITE } };
        default { [] };
    };
};
CHACAL_fnc_fenetreObservation = {
    params ["_phase"];
    if (CHACAL_OBSERVATION <= 0) exitWith {};
    private _t0 = time;
    private _hommes = CHACAL_FS select { alive _x };
    private _secteur = [_phase] call CHACAL_fnc_secteurPhase;
    // ! OBSERVER, C EST SCRUTER UN SECTEUR ( controles du 17/09 : la menace posee a 150 m devant n etait connue que
    // 2 fois sur 8 ; les hommes s arretaient mais gardaient leur cap ). On les fait regarder le point de la phase.
    { doStop _x; if (_phase == 1) then { _x setUnitPos "MIDDLE" }; if (count _secteur > 0) then { _x doWatch _secteur } } forEach _hommes;
    if ((CHACAL_CONTROLE_PERCEPTION > 0) && { count _hommes > 0 }) then {
        private _chef = leader (group (_hommes select 0));
        private _p = if (CHACAL_CONTROLE_PERCEPTION == 2) then { _chef getPos [1500, (getDir _chef) + 180] } else { _chef getPos [150, getDir _chef] };
        private _g = createGroup east;
        {
            private _u = _g createUnit [_x, _p, [], 5, "NONE"];
            _u disableAI "AUTOTARGET"; _u disableAI "TARGET"; _u disableAI "MOVE";
            _u setUnitPos (if (CHACAL_CONTROLE_PERCEPTION == 3) then {"UP"} else {"MIDDLE"});
        } forEach ["O_Soldier_TL_F", "O_Soldier_F", "O_Soldier_F"];
        _g setCombatMode "BLUE";
        CHACAL_MENACES pushBack [_phase, "CONTROLE_PERCEPTION", _g];
        (format ["CHACAL|E|controle_perception|%1|phase|%2|mode|%3|distance|%4|posture|%5", round (time * 100) / 100, _phase,
            CHACAL_CONTROLE_PERCEPTION, round (_chef distance2D _p), (if (CHACAL_CONTROLE_PERCEPTION == 3) then {"UP"} else {"MIDDLE"})]) call CHACAL_LOG;
    };
    (format ["CHACAL|E|observation|%1|phase|%2|debut|duree_prevue|%3%4", round (time * 100) / 100, _phase, CHACAL_OBSERVATION,
        call CHACAL_fnc_perceptionMenace]) call CHACAL_LOG;
    private _prochain = time;
    waitUntil {
        sleep 1;
        if ((CHACAL_SONDE > 0) && { time >= _prochain }) then {
            _prochain = time + 5;
            (format ["CHACAL|E|sonde_perception|%1|phase|%2|depuis|%3%4", round (time * 100) / 100, _phase,
                round (time - _t0), call CHACAL_fnc_perceptionMenace]) call CHACAL_LOG;
        };
        CHACAL_FIN || ((time - _t0) >= (CHACAL_OBSERVATION * CHACAL_ECHELLE))
    };
    // ! RENDRE LA MAIN ( faute du 17/09 : sans ceci, les trois elements de la phase 4 ne repartent jamais et les huit
    // episodes finissent au plafond, 55 min au lieu de 5 ).
    {
        if (alive _x) then { _x doWatch objNull; _x setUnitPos "AUTO"; _x doFollow (leader (group _x)) };
    } forEach _hommes;
    (format ["CHACAL|E|observation|%1|phase|%2|fin|duree|%3%4", round (time * 100) / 100, _phase, round (time - _t0),
        call CHACAL_fnc_perceptionMenace]) call CHACAL_LOG;
};
'''
open(P, "w", encoding="utf-8").write(s[:debut] + NOUVEAU + s[fin:])


def remplacer(chemin, ancre, nouveau, n=1):
    t = open(chemin, encoding="utf-8").read()
    assert t.count(ancre) == n, f"{chemin} : ancre {ancre[:60]!r} trouvee {t.count(ancre)} fois"
    open(chemin, "w", encoding="utf-8").write(t.replace(ancre, nouveau))


# levier de sonde
remplacer(f"{B}/mission.Altis/chacal/00_socle.sqf",
 'CHACAL_CONTROLE_PERCEPTION = ["CHACAL_CONTROLE_PERCEPTION", 0] call BIS_fnc_getParamValue;',
 'CHACAL_CONTROLE_PERCEPTION = ["CHACAL_CONTROLE_PERCEPTION", 0] call BIS_fnc_getParamValue;   // 3 = 150 m devant, DEBOUT\n'
 'CHACAL_SONDE = ["CHACAL_SONDE", 0] call BIS_fnc_getParamValue;   // 1 : une ligne sonde_perception toutes les 5 s pendant la fenetre')
remplacer(f"{B}/mission.Altis/description.ext",
 '        title = "Controle de perception : 0 aucun, 1 groupe inerte a 150 m devant, 2 a 1500 m derriere";\n        values[] = {0,1,2}; texts[] = {"0","1","2"}; default = 0;\n    };\n',
 '        title = "Controle de perception : 0 aucun, 1 groupe inerte a 150 m devant accroupi, 2 a 1500 m derriere, 3 a 150 m devant debout";\n'
 '        values[] = {0,1,2,3}; texts[] = {"0","1","2","3"}; default = 0;\n    };\n'
 '    class CHACAL_SONDE\n    {\n        title = "Sonde de perception : 1 = une ligne toutes les 5 s pendant la fenetre d observation";\n'
 '        values[] = {0,1}; texts[] = {"0","1"}; default = 0;\n    };\n')
remplacer(f"{B}/mission.Altis/description.ext",
 '        values[] = {0,30,45,60,90}; texts[] = {"0","30","45","60","90"}; default = 0;',
 '        values[] = {0,30,45,60,90,120,180,300}; texts[] = {"0","30","45","60","90","120","180","300"}; default = 0;')
remplacer(f"{B}/lancer.sh", 'CONTROLE_PERCEPTION=$(lit controle_perception 0)', 'CONTROLE_PERCEPTION=$(lit controle_perception 0); SONDE=$(lit sonde 0)')
remplacer(f"{B}/lancer.sh", 'ecrire_param OBSERVATION "$OBSERVATION"; ecrire_param CONTROLE_PERCEPTION "$CONTROLE_PERCEPTION"',
          'ecrire_param OBSERVATION "$OBSERVATION"; ecrire_param CONTROLE_PERCEPTION "$CONTROLE_PERCEPTION"; ecrire_param SONDE "$SONDE"')
remplacer(f"{O}/verifier_valeurs.py", '"controle_perception": "CHACAL_CONTROLE_PERCEPTION",',
          '"controle_perception": "CHACAL_CONTROLE_PERCEPTION", "sonde": "CHACAL_SONDE",')
print("patch menace v2 applique")
