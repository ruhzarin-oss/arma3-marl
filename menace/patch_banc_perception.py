"""
Banc de perception ( demande de Younes, 18/09 ) : de nuit, nos hommes REGARDENT une cible posee a distance connue,
avec ligne de vue verifiee, et on journalise ce qu ils voient et connaissent, plus les jumelles portees et l heure.
  CHACAL_CONTROLE_PERCEPTION = 5 : banc ; CHACAL_CONTROLE_DIST : distance en metres ( 50, 100, 150, 300 ).
A appliquer quand aucun run ne tourne.
"""
import sys
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/hmt/depot"
B, O = f"{D}/bancs/chacal", f"{D}/outils"


def remplacer(chemin, ancre, nouveau, n=1):
    t = open(chemin, encoding="utf-8").read()
    assert t.count(ancre) == n, f"{chemin} : ancre {ancre[:60]!r} trouvee {t.count(ancre)} fois"
    open(chemin, "w", encoding="utf-8").write(t.replace(ancre, nouveau))


remplacer(f"{B}/mission.Altis/chacal/00_socle.sqf",
 'CHACAL_SONDE = ["CHACAL_SONDE", 0] call BIS_fnc_getParamValue;',
 'CHACAL_SONDE = ["CHACAL_SONDE", 0] call BIS_fnc_getParamValue;\n'
 'CHACAL_CONTROLE_DIST = ["CHACAL_CONTROLE_DIST", 150] call BIS_fnc_getParamValue;   // banc de perception : distance de la cible')

# le banc : pose la cible dans une direction a ligne de vue libre, fait REGARDER tous les hommes, journalise jumelles et heure
remplacer(f"{B}/mission.Altis/chacal/60_phases.sqf",
 '''    if ((CHACAL_CONTROLE_PERCEPTION > 0) && { count _hommes > 0 }) then {
        private _chef = leader (group (_hommes select 0));''',
 '''    if ((CHACAL_CONTROLE_PERCEPTION == 5) && { count _hommes > 0 }) then {
        // ! BANC DE PERCEPTION ( 18/09 ) : la cible est posee LA OU ILS PEUVENT LA VOIR, et ils la regardent.
        private _chef = leader (group (_hommes select 0));
        private _oeil = (getPosASL _chef) vectorAdd [0, 0, 1.5];
        private _az = getDir _chef; private _trouve = false;
        {
            private _p = _chef getPos [CHACAL_CONTROLE_DIST, _x];
            private _cible = (ATLToASL _p) vectorAdd [0, 0, 1.6];
            if (!_trouve && { (count (lineIntersectsSurfaces [_oeil, _cible, _chef, objNull, true, 1, "VIEW", "VIEW"])) == 0 }) then { _az = _x; _trouve = true };
        } forEach [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340];
        private _p = _chef getPos [CHACAL_CONTROLE_DIST, _az];
        private _g = createGroup east;
        { private _u = _g createUnit [_x, _p, [], 3, "NONE"]; _u disableAI "AUTOTARGET"; _u disableAI "TARGET"; _u disableAI "MOVE"; _u setUnitPos "UP" } forEach ["O_Soldier_TL_F", "O_Soldier_F", "O_Soldier_F"];
        _g setCombatMode "BLUE"; _g setBehaviour "SAFE";
        CHACAL_MENACES pushBack [_phase, "BANC_PERCEPTION", _g];
        private _cibleU = leader _g;
        { _x doWatch _cibleU } forEach _hommes;   // ils REGARDENT la cible : plus d ambiguite de direction
        (format ["CHACAL|E|banc_perception|%1|phase|%2|distance|%3|azimut|%4|ligne_de_vue|%5|heure|%6|lune|%7|jumelles|%8|hommes|%9",
            round (time * 100) / 100, _phase, CHACAL_CONTROLE_DIST, round _az, (if (_trouve) then {1} else {0}),
            (date select 3) + ((date select 4) / 60), moonIntensity,
            ((_hommes apply { hmd _x }) joinString ","), count _hommes]) call CHACAL_LOG;
    };
    if ((CHACAL_CONTROLE_PERCEPTION > 0) && { CHACAL_CONTROLE_PERCEPTION != 5 } && { count _hommes > 0 }) then {
        private _chef = leader (group (_hommes select 0));''')

# l angle entre le regard et la cible, dans chaque ligne de sonde
remplacer(f"{B}/mission.Altis/chacal/60_phases.sqf",
 '''            (format ["CHACAL|E|sonde_perception|%1|phase|%2|depuis|%3%4", round (time * 100) / 100, _phase,
                round (time - _t0), call CHACAL_fnc_perceptionMenace]) call CHACAL_LOG;''',
 '''            private _angles = [];
            {
                private _t = _x;
                private _a = 999;
                { private _r = abs ((((_x getDir _t) - (getDir _x) + 540) % 360) - 180); if (_r < _a) then { _a = _r } } forEach (CHACAL_FS select { alive _x });
                _angles pushBack (round _a);
            } forEach (call CHACAL_fnc_unitesMenace);
            (format ["CHACAL|E|sonde_perception|%1|phase|%2|depuis|%3|angle_min|%4%5", round (time * 100) / 100, _phase,
                round (time - _t0), (if (count _angles > 0) then { _angles call BIS_fnc_lowest } else { -1 }),
                call CHACAL_fnc_perceptionMenace]) call CHACAL_LOG;''')

remplacer(f"{B}/mission.Altis/description.ext",
 '        title = "Controle de perception : 0 aucun, 1 groupe inerte a 150 m devant accroupi, 2 a 1500 m derriere, 3 a 150 m devant debout";\n        values[] = {0,1,2,3}; texts[] = {"0","1","2","3"}; default = 0;\n    };\n',
 '        title = "Controle de perception : 0 aucun, 1 a 150 m devant accroupi, 2 a 1500 m derriere, 3 a 150 m devant debout, 5 banc ( cible vue et regardee )";\n'
 '        values[] = {0,1,2,3,5}; texts[] = {"0","1","2","3","5"}; default = 0;\n    };\n'
 '    class CHACAL_CONTROLE_DIST\n    {\n        title = "Banc de perception : distance de la cible, en metres";\n'
 '        values[] = {50,100,150,300,600}; texts[] = {"50","100","150","300","600"}; default = 150;\n    };\n')
remplacer(f"{B}/lancer.sh", 'SONDE=$(lit sonde 0)', 'SONDE=$(lit sonde 0); CONTROLE_DIST=$(lit controle_dist 150)')
remplacer(f"{B}/lancer.sh", 'ecrire_param SONDE "$SONDE"', 'ecrire_param SONDE "$SONDE"; ecrire_param CONTROLE_DIST "$CONTROLE_DIST"')
remplacer(f"{O}/verifier_valeurs.py", '"sonde": "CHACAL_SONDE",', '"sonde": "CHACAL_SONDE", "controle_dist": "CHACAL_CONTROLE_DIST",')
print("patch banc de perception applique")
