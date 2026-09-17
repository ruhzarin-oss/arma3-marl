"""Branche une formule EvoGP sur le delai du porteur ( phase 5 ). A appliquer quand AUCUN run CHACAL ne tourne.
Mode 0 ( defaut ) : comportement d'origine, octet pour octet sur le delai joue. Mode 1 : la formule decide 45 ou 180."""
import sys
D = "/mnt/data/hmt/depot/bancs/chacal"
O = "/mnt/data/hmt/depot/outils"

def remplacer(chemin, ancre, nouveau, n=1):
    s = open(chemin, encoding="utf-8").read()
    assert s.count(ancre) == n, f"{chemin} : ancre trouvee {s.count(ancre)} fois, {n} attendue(s) : {ancre[:60]!r}"
    open(chemin, "w", encoding="utf-8").write(s.replace(ancre, nouveau))

# ---------------------------------------------------------------- 00_socle.sqf
remplacer(f"{D}/mission.Altis/chacal/00_socle.sqf",
 'CHACAL_DELAI_PORTEUR = ["CHACAL_DELAI_PORTEUR", 45] call BIS_fnc_getParamValue;\n',
 'CHACAL_DELAI_PORTEUR = ["CHACAL_DELAI_PORTEUR", 45] call BIS_fnc_getParamValue;\n'
 '// ! BOUCLE EVOGP ( equation/PROTOCOLE_BOUCLE_EVOGP_P5.md, 17/09 ) : le delai du porteur peut etre decide par une formule\n'
 '// apprise par EvoGP, passee en codes entiers ( CHACAL_F0..F31, ordre prefixe, equation/formule.py ). Mode 0 = impose par\n'
 '// le job ( origine ). CHACAL_DELAI_PORTEUR reste la valeur du job ( ligne FINI ) ; CHACAL_DELAI_JOUE est le delai joue.\n'
 'CHACAL_DELAI_MODE = ["CHACAL_DELAI_MODE", 0] call BIS_fnc_getParamValue;\n'
 'CHACAL_F_LEN = ["CHACAL_F_LEN", 0] call BIS_fnc_getParamValue;\n'
 'CHACAL_F = [];\n'
 'for "_k" from 0 to 31 do { CHACAL_F pushBack (["CHACAL_F" + str _k, 0] call BIS_fnc_getParamValue) };\n'
 'CHACAL_F resize CHACAL_F_LEN;\n'
 'CHACAL_DELAI_JOUE = CHACAL_DELAI_PORTEUR;\n')

# ---------------------------------------------------------------- 60_phases.sqf
P = f"{D}/mission.Altis/chacal/60_phases.sqf"
remplacer(P, 'CHACAL_fnc_finPhase = {\n',
 '// Interprete des formules EvoGP ( codes prefixes ). ">" vaut +1 si a > b, sinon -1, comme dans EvoGP ( mesure le 17/09 ).\n'
 'CHACAL_F_CONST = [-1, -0.5, -0.25, 0, 0.25, 0.5, 1];\n'
 'CHACAL_fnc_evalNoeud = {\n'
 '    params ["_i", "_obs"];\n'
 '    private _c = CHACAL_F select _i;\n'
 '    if (_c >= 301) exitWith { [CHACAL_F_CONST select (_c - 301), _i + 1] };\n'
 '    if (_c >= 201) exitWith { [_obs select (_c - 201), _i + 1] };\n'
 '    if (_c == 106) exitWith { private _m = [_i + 1, _obs] call CHACAL_fnc_evalNoeud; [-(_m select 0), _m select 1] };\n'
 '    private _g = [_i + 1, _obs] call CHACAL_fnc_evalNoeud;\n'
 '    private _d = [_g select 1, _obs] call CHACAL_fnc_evalNoeud;\n'
 '    private _u = _g select 0; private _v = _d select 0;\n'
 '    private _r = switch (_c) do {\n'
 '        case 101: { _u + _v };\n'
 '        case 102: { _u - _v };\n'
 '        case 103: { _u * _v };\n'
 '        case 104: { _u min _v };\n'
 '        case 105: { _u max _v };\n'
 '        case 107: { if (_u > _v) then {1} else {-1} };\n'
 '        default { (format ["CHACAL|ERREUR|formule|code_inconnu|%1", _c]) call CHACAL_LOG; 0 };\n'
 '    };\n'
 '    [_r, _d select 1]\n'
 '};\n'
 'CHACAL_fnc_finPhase = {\n')
remplacer(P, '[5, "DELAI_PORTEUR", [45, 180], CHACAL_DELAI_PORTEUR, "IMPOSE"] call CHACAL_fnc_decision;\n',
 'if ((CHACAL_DELAI_MODE == 1) && { CHACAL_F_LEN > 0 }) then {\n'
 '    // memes perceptions, memes calculs et meme instant que la ligne de decision ecrite juste apres\n'
 '    private _defF = (if (isNil "CHACAL_EST_SITE") then {[]} else {CHACAL_EST_SITE}) select { alive _x };\n'
 '    private _obsF = [\n'
 '        (if (CHACAL_ALARME) then {1} else {0}),\n'
 '        (if (CHACAL_T_ALARME >= 0) then { round (time - CHACAL_T_ALARME) } else { -1 }),\n'
 '        (if (CHACAL_COMPROMIS) then {1} else {0}),\n'
 '        count (CHACAL_FS select { alive _x }),\n'
 '        { (west knowsAbout _x) > 1.4 } count _defF\n'
 '    ];\n'
 '    private _res = [0, _obsF] call CHACAL_fnc_evalNoeud;\n'
 '    private _valF = _res select 0;\n'
 '    CHACAL_DELAI_JOUE = if (_valF > 0) then {180} else {45};\n'
 '    [5, "DELAI_PORTEUR", [45, 180], CHACAL_DELAI_JOUE, "FORMULE", format ["|valeur_formule|%1|codes_lus|%2|codes_attendus|%3", _valF, _res select 1, CHACAL_F_LEN]] call CHACAL_fnc_decision;\n'
 '} else {\n'
 '    [5, "DELAI_PORTEUR", [45, 180], CHACAL_DELAI_PORTEUR, "IMPOSE"] call CHACAL_fnc_decision;\n'
 '};\n')
remplacer(P, '(time - _t > CHACAL_DELAI_PORTEUR * CHACAL_ECHELLE)', '(time - _t > CHACAL_DELAI_JOUE * CHACAL_ECHELLE)')
remplacer(P, 'round (time - _t), _dH, CHACAL_DELAI_PORTEUR]) call CHACAL_LOG;', 'round (time - _t), _dH, CHACAL_DELAI_JOUE]) call CHACAL_LOG;')

# ---------------------------------------------------------------- description.ext
codes = [0] + list(range(101, 108)) + list(range(201, 206)) + list(range(301, 308))
classes = ('    class CHACAL_DELAI_MODE\n    {\n        title = "Delai du porteur : 0 impose par le job, 1 decide par la formule EvoGP";\n'
           '        values[] = {0,1}; texts[] = {"IMPOSE","FORMULE"}; default = 0;\n    };\n'
           '    class CHACAL_F_LEN\n    {\n        title = "Formule EvoGP : nombre de codes";\n'
           f'        values[] = {{{",".join(str(v) for v in range(33))}}}; texts[] = {{{",".join(chr(34) + str(v) + chr(34) for v in range(33))}}}; default = 0;\n    }};\n')
for k in range(32):
    classes += (f'    class CHACAL_F{k}\n    {{\n        title = "Formule EvoGP : code {k}";\n'
                f'        values[] = {{{",".join(str(v) for v in codes)}}}; texts[] = {{{",".join(chr(34) + str(v) + chr(34) for v in codes)}}}; default = 0;\n    }};\n')
remplacer(f"{D}/mission.Altis/description.ext",
 '        values[] = {45,60,90,120,180};\n        texts[]  = {"45","60","90","120","180"};\n        default = 45;\n    };\n',
 '        values[] = {45,60,90,120,180};\n        texts[]  = {"45","60","90","120","180"};\n        default = 45;\n    };\n' + classes)

# ---------------------------------------------------------------- lancer.sh
L = f"{D}/lancer.sh"
remplacer(L, 'ITINERAIRE=$(lit itineraire 0)   #', 'ITINERAIRE=$(lit itineraire 0); DELAI_MODE=$(lit delai_mode 0); F_LEN=$(lit f_len 0)   #')
remplacer(L, 'ecrire_param ITINERAIRE "$ITINERAIRE"\n',
 'ecrire_param ITINERAIRE "$ITINERAIRE"\n'
 '# boucle EvoGP ( 17/09 ) : mode du delai et formule en codes ; ecrits a CHAQUE lancement, 0 par defaut\n'
 'ecrire_param DELAI_MODE "$DELAI_MODE"; ecrire_param F_LEN "$F_LEN"\n'
 'for k in $(seq 0 31); do ecrire_param F$k "$(lit f$k 0)"; done\n')

# ---------------------------------------------------------------- verifier_valeurs.py
remplacer(f"{O}/verifier_valeurs.py", '"exfil": "CHACAL_EXFIL",\n', '"exfil": "CHACAL_EXFIL", "delai_mode": "CHACAL_DELAI_MODE", "f_len": "CHACAL_F_LEN",\n')
print("patch applique")
