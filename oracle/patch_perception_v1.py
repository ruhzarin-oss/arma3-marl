"""
DEUX PERCEPTIONS QUI MANQUAIENT ( 19/09, apres le verdict 843118c ).

Le verdict etablit que la meilleure option depend du TYPE de menace : contre une patrouille qui roule on traverse,
contre un poste fixe on attend. Mais la regle n est pas jouable : au moment du choix, le vehicule n est percu que
dans 7 episodes sur 58, et les champs qui devraient distinguer les deux - menace_mobile, distance_menace, vue_depuis -
valent -1 PARTOUT, parce qu ils ne sont remplis que si la menace est CONNUE du groupe, ce qui n arrive jamais
( 0 sur 118 ).

On ajoute donc deux canaux qui ne dependent pas de la connaissance du groupe :
  1. menace_mobile_vue : la menace a-t-elle BOUGE entre deux regards de l oeil ? C est la difference physique entre
     une patrouille et un poste. On suit les positions vues par le canal geometrique, comme on suivait deja les
     positions crues par le canal connaissance.
  2. moteur_entendu : un moteur en marche a moins de CHACAL_PORTEE_SON metres. De nuit un blinde s entend bien plus
     loin qu un homme ne se voit, et seul le bras PATROUILLE en a un. Approximation ASSUMEE : Arma ne modelise pas
     la propagation du son pour la connaissance de l IA ; on definit ici une perception, et le controle dira si elle
     separe les deux bras sans jamais s allumer sur un poste.
"""
import sys
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/hmt/depot"
B = f"{D}/bancs/chacaloracle"
M = f"{B}/mission.Altis/chacal/60_phases.sqf"


def remplacer(chemin, ancre, nouveau, n=1):
    t = open(chemin, encoding="utf-8").read()
    assert t.count(ancre) == n, f"{chemin} : ancre {ancre[:60]!r} trouvee {t.count(ancre)} fois"
    open(chemin, "w", encoding="utf-8").write(t.replace(ancre, nouveau))


# 1. suivre aussi ce que l OEIL voit, pas seulement ce que le groupe croit
remplacer(M,
 '''        private _chefs = call CHACAL_fnc_chefsDetachement;
        {
            private _t = _x; private _crue = [];
            { private _k = _x targetKnowledge _t; if (_k select 0) exitWith { _crue = _k select 6 } } forEach _chefs;
            if (count _crue > 0) then {
                private _h = _t getVariable ["chacal_crue", []];
                _h pushBack [time, _crue];
                if (count _h > 6) then { _h deleteAt 0 };
                _t setVariable ["chacal_crue", _h];
            };
        } forEach (call CHACAL_fnc_unitesMenace);''',
 '''        private _chefs = call CHACAL_fnc_chefsDetachement;
        private _hommesS = CHACAL_FS select { alive _x };
        {
            private _t = _x; private _crue = [];
            { private _k = _x targetKnowledge _t; if (_k select 0) exitWith { _crue = _k select 6 } } forEach _chefs;
            if (count _crue > 0) then {
                private _h = _t getVariable ["chacal_crue", []];
                _h pushBack [time, _crue];
                if (count _h > 6) then { _h deleteAt 0 };
                _t setVariable ["chacal_crue", _h];
            };
            // ! LE MEME SUIVI, MAIS PAR L OEIL. Le canal connaissance est mort ( 0 sur 118 ) : sans ce second
            // suivi, menace_mobile vaut -1 partout et la regle etablie le 19/09 reste injouable.
            if (({ [_x, _t, 800, 70] call CHACAL_fnc_voit } count _hommesS) > 0) then {
                private _hv = _t getVariable ["chacal_vue", []];
                _hv pushBack [time, getPosATL _t];
                if (count _hv > 6) then { _hv deleteAt 0 };
                _t setVariable ["chacal_vue", _hv];
            };
        } forEach (call CHACAL_fnc_unitesMenace);''')

# 2. les deux nouveaux canaux dans la ligne de decision
remplacer(M,
 '''    private _vDist = -1;''',
 '''    // ! MOBILITE VUE : la menace a-t-elle bouge entre deux regards de l oeil ? -1 si l oeil ne l a pas vue deux fois.
    private _mobileVue = -1;
    {
        private _hv = (_x getVariable ["chacal_vue", []]) select { (time - (_x select 0)) <= 40 };
        if (count _hv >= 2) then {
            private _d = ((_hv select 0) select 1) distance2D ((_hv select ((count _hv) - 1)) select 1);
            if (_d > 10) exitWith { _mobileVue = 1 };
            if (_mobileVue < 0) then { _mobileVue = 0 };
        };
    } forEach _menaces;
    // ! LE MOTEUR : un blinde s entend de nuit bien plus loin qu un homme ne se voit, et seul le bras PATROUILLE
    // en a un. Approximation assumee, a valider par le controle : jamais 1 sur un poste a pied.
    private _moteur = 0;
    {
        private _v = vehicle _x;
        if ((_v != _x) && { isEngineOn _v }) then {
            { if ((_x distance2D _v) < CHACAL_PORTEE_SON) exitWith { _moteur = 1 } } forEach _hommes;
        };
    } forEach _menaces;
    private _vDist = -1;''')

remplacer(M,
 '''    format ["|menace_percue|%1|menaces_vues|%2|menaces_connues|%3|menaces_camp|%4|menaces_homme|%5|distance_menace|%6|erreur_position|%7|menace_mobile|%8|vue_depuis|%9|vehicule_connu|%10|verite_menaces|%11|verite_distance_menace|%12|azimut_chef|%13",
        _percue, _vues, _connues, _camp, _homme, round _dMin, (round (_err * 10)) / 10, _mobile, _vueDepuis, _veh,
        count _menaces, round _vDist, (if (count _chefs > 0) then { round (getDir (_chefs select 0)) } else { -1 })]''',
 '''    format ["|menace_percue|%1|menaces_vues|%2|menaces_connues|%3|menaces_camp|%4|menaces_homme|%5|distance_menace|%6|erreur_position|%7|menace_mobile|%8|vue_depuis|%9|vehicule_connu|%10|menace_mobile_vue|%11|moteur_entendu|%12|verite_menaces|%13|verite_distance_menace|%14|azimut_chef|%15",
        _percue, _vues, _connues, _camp, _homme, round _dMin, (round (_err * 10)) / 10, _mobile, _vueDepuis, _veh,
        _mobileVue, _moteur,
        count _menaces, round _vDist, (if (count _chefs > 0) then { round (getDir (_chefs select 0)) } else { -1 })]''')

remplacer(f"{B}/mission.Altis/chacal/00_socle.sqf",
 'CHACAL_ORACLE_CMD   = ["CHACAL_ORACLE_CMD", 0] call BIS_fnc_getParamValue;',
 'CHACAL_PORTEE_SON = ["CHACAL_PORTEE_SON", 600] call BIS_fnc_getParamValue;   // portee du moteur entendu, en metres\n'
 'CHACAL_ORACLE_CMD   = ["CHACAL_ORACLE_CMD", 0] call BIS_fnc_getParamValue;')
remplacer(f"{B}/mission.Altis/description.ext",
 '    class CHACAL_ORACLE_CMD\n',
 '    class CHACAL_PORTEE_SON\n    {\n        title = "Perception : portee du moteur entendu, en metres";\n'
 '        values[] = {0,300,600,900}; texts[] = {"0","300","600","900"}; default = 600;\n    };\n'
 '    class CHACAL_ORACLE_CMD\n')
remplacer(f"{B}/lancer.sh", 'ORACLE_CMD=$(lit oracle_cmd 0)', 'ORACLE_CMD=$(lit oracle_cmd 0); PORTEE_SON=$(lit portee_son 600)')
remplacer(f"{B}/lancer.sh", 'ecrire_param ORACLE_CMD "$ORACLE_CMD"', 'ecrire_param ORACLE_CMD "$ORACLE_CMD"; ecrire_param PORTEE_SON "$PORTEE_SON"')
print("patch perception v1 applique : menace_mobile_vue et moteur_entendu")
