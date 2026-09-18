"""
Menace visible v3 ( banc de perception du 18/09 : de nuit, une cible REGARDEE est connue en 6 s jusqu a 150 m, jamais a
300 m ) :
  1. selectMin au lieu de BIS_fnc_lowest ( qui n existe pas : 114 erreurs par episode ) ;
  2. la fenetre BALAIE le secteur : trois azimuts ( gauche, centre, droite ), le regard tourne toutes les 10 s ;
  3. le controle POSITIF devient le montage du banc : cible a 150 m dans une direction a ligne de vue verifiee.
A appliquer quand aucun run ne tourne.
"""
import sys
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/hmt/depot"
B = f"{D}/bancs/chacal"
P = f"{B}/mission.Altis/chacal/60_phases.sqf"


def remplacer(chemin, ancre, nouveau, n=1):
    t = open(chemin, encoding="utf-8").read()
    assert t.count(ancre) == n, f"{chemin} : ancre {ancre[:70]!r} trouvee {t.count(ancre)} fois"
    open(chemin, "w", encoding="utf-8").write(t.replace(ancre, nouveau))


# 1. le bug
remplacer(P, '_angles call BIS_fnc_lowest', 'selectMin _angles')

# 2. le balayage : on prepare trois points de regard et on tourne
remplacer(P,
 '''    { doStop _x; if (_phase == 1) then { _x setUnitPos "MIDDLE" }; if (count _secteur > 0) then { _x doWatch _secteur } } forEach _hommes;''',
 '''    // ! OBSERVER, C EST BALAYER ( banc du 18/09 : une cible regardee est connue en 6 s jusqu a 150 m ; fixer un seul
    // point laisse la menace hors du champ ). Trois azimuts autour de l axe de la phase, le regard tourne toutes les 10 s.
    private _regards = [];
    if (count _secteur > 0) then {
        private _chefF = leader (group (_hommes select 0));
        private _axe = _chefF getDir _secteur;
        { _regards pushBack (_chefF getPos [(_chefF distance2D _secteur) max 200, _axe + _x]) } forEach [-45, 0, 45];
    };
    { doStop _x; if (_phase == 1) then { _x setUnitPos "MIDDLE" } } forEach _hommes;''')
remplacer(P,
 '''    private _prochain = time;
    waitUntil {
        sleep 1;''',
 '''    private _prochain = time; private _tRegard = 0; private _iRegard = -1;
    waitUntil {
        sleep 1;
        if ((count _regards > 0) && { time >= _tRegard }) then {
            _tRegard = time + 10; _iRegard = (_iRegard + 1) % (count _regards);
            { _x doWatch (_regards select _iRegard) } forEach (CHACAL_FS select { alive _x });
        };''')

# 3. le controle POSITIF prend le montage du banc ( cible a 150 m dans une direction a ligne de vue verifiee )
remplacer(P, '    if ((CHACAL_CONTROLE_PERCEPTION == 5) && { count _hommes > 0 }) then {',
             '    if ((CHACAL_CONTROLE_PERCEPTION in [1, 5]) && { count _hommes > 0 }) then {')
remplacer(P, '    if ((CHACAL_CONTROLE_PERCEPTION > 0) && { CHACAL_CONTROLE_PERCEPTION != 5 } && { count _hommes > 0 }) then {',
             '    if ((CHACAL_CONTROLE_PERCEPTION in [2, 3]) && { count _hommes > 0 }) then {')
# en mode 1, la cible reste a 150 m ( defaut du levier ) mais on NE force PAS le regard : ce sont les hommes qui balaient
remplacer(P, '        private _cibleU = leader _g;\n        { _x doWatch _cibleU } forEach _hommes;   // ils REGARDENT la cible : plus d ambiguite de direction',
             '        if (CHACAL_CONTROLE_PERCEPTION == 5) then {\n'
             '            private _cibleU = leader _g;\n'
             '            { _x doWatch _cibleU } forEach _hommes;   // banc : ils fixent la cible, aucune ambiguite de direction\n'
             '            _regards = [];                            // le banc ne balaie pas\n'
             '        } else {\n'
             '            _regards = [getPosATL (leader _g)];       // controle POSITIF : la cible est dans le secteur balaye\n'
             '        };')
print("patch menace v3 applique")
