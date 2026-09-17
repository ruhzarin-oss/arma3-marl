"""Rendre la menace visible au moment de choisir ( plans/plan-menace-visible.md ). A appliquer quand AUCUN run CHACAL ne tourne.
S'applique avant ou apres le patch EvoGP ( ancres distinctes ). CHACAL_OBSERVATION = 0 : aucune fenetre, aucun comportement change ;
seules des colonnes de perception s'ajoutent en fin de ligne de decision ( marqueur version 3 )."""
import sys
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/hmt/depot"
B, O = f"{D}/bancs/chacal", f"{D}/outils"


def remplacer(chemin, ancre, nouveau, n=1):
    s = open(chemin, encoding="utf-8").read()
    assert s.count(ancre) == n, f"{chemin} : ancre trouvee {s.count(ancre)} fois, {n} attendue(s) : {ancre[:70]!r}"
    open(chemin, "w", encoding="utf-8").write(s.replace(ancre, nouveau))


# ---------------------------------------------------------------- 00_socle.sqf : leviers
remplacer(f"{B}/mission.Altis/chacal/00_socle.sqf",
 'CHACAL_ITINERAIRE = ["CHACAL_ITINERAIRE", 0] call BIS_fnc_getParamValue;',
 'CHACAL_ITINERAIRE = ["CHACAL_ITINERAIRE", 0] call BIS_fnc_getParamValue;\n'
 '// ! LA MENACE VISIBLE ( plans/plan-menace-visible.md, 17/09 ) : fenetre d observation avant les choix des phases 1, 2 et 4,\n'
 '// en secondes ( 90 fixe par Younes ). 0 = origine. CONTROLE_PERCEPTION : 1 groupe inerte a 150 m devant, 2 a 1500 m derriere.\n'
 'CHACAL_OBSERVATION = ["CHACAL_OBSERVATION", 0] call BIS_fnc_getParamValue;\n'
 'CHACAL_CONTROLE_PERCEPTION = ["CHACAL_CONTROLE_PERCEPTION", 0] call BIS_fnc_getParamValue;')

# ---------------------------------------------------------------- 60_phases.sqf
P = f"{B}/mission.Altis/chacal/60_phases.sqf"
remplacer(P, '"CHACAL|OK|decision|version|2" call CHACAL_LOG;',
 '"CHACAL|OK|decision|version|3" call CHACAL_LOG;   // 3 : perceptions de la menace en fin de ligne ( plans/plan-menace-visible.md )\n'
 '// ! LA MENACE VISIBLE ( 17/09 ). Deux canaux : ce qu un homme du detachement VOIT maintenant ( CHACAL_fnc_voit, geometrie ) et\n'
 '// ce que le GROUPE du detachement CONNAIT ( targetKnowledge, champ 0 « known by group », position crue, erreur, derniere vue ).\n'
 '// Pas knowsAbout : connaissance de camp. La verite ( verite_* ) est ecrite a part, pour la lecture seulement.\n'
 'CHACAL_fnc_unitesMenace = {\n'
 '    private _t = [];\n'
 '    { private _g = _x select 2; if (!isNull _g) then { _t append ((units _g) select { alive _x }) } } forEach CHACAL_MENACES;\n'
 '    _t\n'
 '};\n'
 'CHACAL_fnc_chefsDetachement = {\n'
 '    private _g = [];\n'
 '    { if (alive _x) then { _g pushBackUnique (group _x) } } forEach CHACAL_FS;\n'
 '    (_g select { !isNull _x && { alive (leader _x) } }) apply { leader _x }\n'
 '};\n'
 'CHACAL_fnc_suiviMenaces = {\n'
 '    while { !CHACAL_FIN } do {\n'
 '        private _chefs = call CHACAL_fnc_chefsDetachement;\n'
 '        {\n'
 '            private _t = _x; private _crue = [];\n'
 '            { private _k = _x targetKnowledge _t; if (_k select 0) exitWith { _crue = _k select 6 } } forEach _chefs;\n'
 '            if (count _crue > 0) then {\n'
 '                private _h = _t getVariable ["chacal_crue", []];\n'
 '                _h pushBack [time, _crue];\n'
 '                if (count _h > 6) then { _h deleteAt 0 };\n'
 '                _t setVariable ["chacal_crue", _h];\n'
 '            };\n'
 '        } forEach (call CHACAL_fnc_unitesMenace);\n'
 '        sleep 5;\n'
 '    };\n'
 '};\n'
 '[] spawn CHACAL_fnc_suiviMenaces;\n'
 'CHACAL_fnc_perceptionMenace = {\n'
 '    private _menaces = call CHACAL_fnc_unitesMenace;\n'
 '    private _hommes = CHACAL_FS select { alive _x };\n'
 '    private _chefs = call CHACAL_fnc_chefsDetachement;\n'
 '    private _vues = { private _t = _x; ({ [_x, _t, 800, 70] call CHACAL_fnc_voit } count _hommes) > 0 } count _menaces;\n'
 '    private _connues = 0; private _dMin = -1; private _err = -1; private _vueDepuis = -1; private _mobile = -1; private _proche = objNull;\n'
 '    {\n'
 '        private _t = _x; private _k = [];\n'
 '        { private _kk = _x targetKnowledge _t; if (_kk select 0) exitWith { _k = _kk } } forEach _chefs;\n'
 '        if (count _k > 0) then {\n'
 '            _connues = _connues + 1;\n'
 '            private _crue = _k select 6;\n'
 '            private _d = 1e9;\n'
 '            { _d = _d min (_x distance2D _crue) } forEach _hommes;\n'
 '            if ((_dMin < 0) || { _d < _dMin }) then {\n'
 '                _dMin = _d; _err = _k select 5; _proche = _t;\n'
 '                _vueDepuis = if ((_k select 2) > 0) then { round (time - (_k select 2)) } else { -1 };\n'
 '            };\n'
 '        };\n'
 '    } forEach _menaces;\n'
 '    if (!isNull _proche) then {\n'
 '        private _h = (_proche getVariable ["chacal_crue", []]) select { (time - (_x select 0)) <= 25 };\n'
 '        _mobile = if (count _h >= 2) then { if ((((_h select 0) select 1) distance2D ((_h select ((count _h) - 1)) select 1)) > 10) then {1} else {0} } else {-1};\n'
 '    };\n'
 '    private _veh = 0;\n'
 '    if ((!isNil "CHACAL_VEH_ROUTE") && { !isNull CHACAL_VEH_ROUTE } && { ({ (_x select 1) == "PATROUILLE_ROUTE" } count CHACAL_MENACES) > 0 }) then {\n'
 '        if (({ (_x targetKnowledge CHACAL_VEH_ROUTE) select 0 } count _chefs) > 0) then { _veh = 1 };\n'
 '    };\n'
 '    private _vDist = -1;\n'
 '    { private _t = _x; { private _dd = _x distance2D _t; if ((_vDist < 0) || { _dd < _vDist }) then { _vDist = _dd } } forEach _hommes } forEach _menaces;\n'
 '    format ["|menaces_vues|%1|menaces_connues|%2|distance_menace|%3|erreur_position|%4|menace_mobile|%5|vue_depuis|%6|vehicule_connu|%7|verite_menaces|%8|verite_distance_menace|%9|azimut_chef|%10",\n'
 '        _vues, _connues, round _dMin, (round (_err * 10)) / 10, _mobile, _vueDepuis, _veh, count _menaces, round _vDist,\n'
 '        (if (count _chefs > 0) then { round (getDir (_chefs select 0)) } else { -1 })]\n'
 '};\n'
 'CHACAL_fnc_fenetreObservation = {\n'
 '    params ["_phase"];\n'
 '    if (CHACAL_OBSERVATION <= 0) exitWith {};\n'
 '    private _t0 = time;\n'
 '    private _hommes = CHACAL_FS select { alive _x };\n'
 '    { doStop _x; if (_phase == 1) then { _x setUnitPos "DOWN" } } forEach _hommes;\n'
 '    if ((CHACAL_CONTROLE_PERCEPTION > 0) && { count _hommes > 0 }) then {\n'
 '        private _chef = leader (group (_hommes select 0));\n'
 '        private _p = if (CHACAL_CONTROLE_PERCEPTION == 1) then { _chef getPos [150, getDir _chef] } else { _chef getPos [1500, (getDir _chef) + 180] };\n'
 '        private _g = createGroup east;\n'
 '        { private _u = _g createUnit [_x, _p, [], 5, "NONE"]; _u disableAI "AUTOTARGET"; _u disableAI "TARGET"; _u disableAI "MOVE" } forEach ["O_Soldier_TL_F", "O_Soldier_F", "O_Soldier_F"];\n'
 '        _g setCombatMode "BLUE";\n'
 '        CHACAL_MENACES pushBack [_phase, "CONTROLE_PERCEPTION", _g];\n'
 '        (format ["CHACAL|E|controle_perception|%1|phase|%2|mode|%3|distance|%4", round (time * 100) / 100, _phase,\n'
 '            CHACAL_CONTROLE_PERCEPTION, round (_chef distance2D _p)]) call CHACAL_LOG;\n'
 '    };\n'
 '    (format ["CHACAL|E|observation|%1|phase|%2|debut|duree_prevue|%3%4", round (time * 100) / 100, _phase, CHACAL_OBSERVATION,\n'
 '        call CHACAL_fnc_perceptionMenace]) call CHACAL_LOG;\n'
 '    waitUntil { sleep 1; CHACAL_FIN || ((time - _t0) >= (CHACAL_OBSERVATION * CHACAL_ECHELLE)) };\n'
 '    if (_phase == 1) then { { if (alive _x) then { _x setUnitPos "AUTO" } } forEach _hommes };\n'
 '    (format ["CHACAL|E|observation|%1|phase|%2|fin|duree|%3%4", round (time * 100) / 100, _phase, round (time - _t0),\n'
 '        call CHACAL_fnc_perceptionMenace]) call CHACAL_LOG;\n'
 '};')
remplacer(P, 'count _def, CHACAL_SITUATION, _extra]) call CHACAL_LOG;',
             'count _def, CHACAL_SITUATION, _extra + (call CHACAL_fnc_perceptionMenace)]) call CHACAL_LOG;')
remplacer(P, 'if (CHACAL_P1_ATTENTE > 0) then {\n    [1, "INSERTION_ATTENTE", [1, 2], CHACAL_P1_ATTENTE, "IMPOSE"] call CHACAL_fnc_decision;',
             'if (CHACAL_P1_ATTENTE > 0) then {\n    [1] call CHACAL_fnc_fenetreObservation;   // menace visible : regarder avant de choisir ( 0 = origine )\n'
             '    [1, "INSERTION_ATTENTE", [1, 2], CHACAL_P1_ATTENTE, "IMPOSE"] call CHACAL_fnc_decision;')
remplacer(P, '    if (CHACAL_TRAVERSEE > 0) then {\n        private _vD = ',
             '    if (CHACAL_TRAVERSEE > 0) then {\n        [2] call CHACAL_fnc_fenetreObservation;   // menace visible : regarder avant de choisir ( 0 = origine )\n        private _vD = ')
remplacer(P, '        if (CHACAL_ITINERAIRE > 0) then { [4, "ITINERAIRE", [1, 2], CHACAL_ITINERAIRE, "IMPOSE"] call CHACAL_fnc_decision };',
             '        if (CHACAL_ITINERAIRE > 0) then { [4] call CHACAL_fnc_fenetreObservation; [4, "ITINERAIRE", [1, 2], CHACAL_ITINERAIRE, "IMPOSE"] call CHACAL_fnc_decision };')

# ---------------------------------------------------------------- description.ext
remplacer(f"{B}/mission.Altis/description.ext",
 '        title = "Choix de la phase 4 : 0 regle d origine, 1 itineraire direct, 2 detour de 350 m a mi-chemin";\n'
 '        values[] = {0,1,2}; texts[] = {"0","1","2"}; default = 0;\n    };\n',
 '        title = "Choix de la phase 4 : 0 regle d origine, 1 itineraire direct, 2 detour de 350 m a mi-chemin";\n'
 '        values[] = {0,1,2}; texts[] = {"0","1","2"}; default = 0;\n    };\n'
 '    class CHACAL_OBSERVATION\n    {\n        title = "Menace visible : fenetre d observation avant les choix des phases 1, 2, 4, en secondes (0 = origine)";\n'
 '        values[] = {0,30,45,60,90}; texts[] = {"0","30","45","60","90"}; default = 0;\n    };\n'
 '    class CHACAL_CONTROLE_PERCEPTION\n    {\n        title = "Controle de perception : 0 aucun, 1 groupe inerte a 150 m devant, 2 a 1500 m derriere";\n'
 '        values[] = {0,1,2}; texts[] = {"0","1","2"}; default = 0;\n    };\n')

# ---------------------------------------------------------------- lancer.sh et verifier_valeurs.py
remplacer(f"{B}/lancer.sh", 'ITINERAIRE=$(lit itineraire 0)',
          'ITINERAIRE=$(lit itineraire 0); OBSERVATION=$(lit observation 0); CONTROLE_PERCEPTION=$(lit controle_perception 0)')
remplacer(f"{B}/lancer.sh", 'ecrire_param ITINERAIRE "$ITINERAIRE"\n',
          'ecrire_param ITINERAIRE "$ITINERAIRE"\n# menace visible ( 17/09 ) : fenetre d observation et controle de perception, ecrits a chaque lancement\n'
          'ecrire_param OBSERVATION "$OBSERVATION"; ecrire_param CONTROLE_PERCEPTION "$CONTROLE_PERCEPTION"\n')
remplacer(f"{O}/verifier_valeurs.py", '"itineraire": "CHACAL_ITINERAIRE",',
          '"itineraire": "CHACAL_ITINERAIRE", "observation": "CHACAL_OBSERVATION", "controle_perception": "CHACAL_CONTROLE_PERCEPTION",')
print("patch menace applique")
