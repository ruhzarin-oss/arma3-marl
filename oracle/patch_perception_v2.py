"""
PERCEPTION v2 ( 19/09 ) : journaliser de quoi repondre AUX QUESTIONS SUIVANTES sans rejouer la grille.
Demande de Younes : « anticipe les questions futures pour les tester maintenant ».

Ajoute a la ligne de decision, et a une sonde toutes les 10 s pendant la fenetre d observation :
  distance_moteur  : distance au vehicule de menace dont le moteur tourne ( -1 si aucun ) -> la portee se rechoisit apres coup ;
  moteur_allume    : un moteur de menace tourne-t-il, OU QU IL SOIT -> distingue un rate par distance d un rate par moteur eteint ;
  vue_vehicule     : ligne de vue geometrique vers ce vehicule -> on pourra exiger la vue, ou une attenuation, sans rejouer ;
  n_vues_menace    : combien de fois l oeil a vu la menace dans les 40 s -> explique les -1 de menace_mobile_vue.
La sonde ( CHACAL_SONDE_PERCEPTION = 1 ) ecrit ces memes champs toutes les 10 s pendant la fenetre : n importe quelle duree de
fenetre se relit apres coup.
"""
import sys
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/hmt/depot"
B = f"{D}/bancs/chacaloracle"
M = f"{B}/mission.Altis/chacal/60_phases.sqf"


def remplacer(chemin, ancre, nouveau, n=1):
    t = open(chemin, encoding="utf-8").read()
    assert t.count(ancre) == n, f"{chemin} : ancre {ancre[:60]!r} trouvee {t.count(ancre)} fois"
    open(chemin, "w", encoding="utf-8").write(t.replace(ancre, nouveau))


# 1. compter les regards de l oeil, pour expliquer les -1
remplacer(M,
 '''    private _mobileVue = -1;
    {
        private _hv = (_x getVariable ["chacal_vue", []]) select { (time - (_x select 0)) <= 40 };
        if (count _hv >= 2) then {''',
 '''    private _mobileVue = -1;
    private _nVues = 0;
    {
        private _hv = (_x getVariable ["chacal_vue", []]) select { (time - (_x select 0)) <= 40 };
        _nVues = _nVues max (count _hv);
        if (count _hv >= 2) then {''')

# 2. le moteur : distance, etat, ligne de vue - et non plus seulement un drapeau
remplacer(M,
 '''    private _moteur = 0;
    {
        private _v = vehicle _x;
        if ((_v != _x) && { isEngineOn _v }) then {
            { if ((_x distance2D _v) < CHACAL_PORTEE_SON) exitWith { _moteur = 1 } } forEach _hommes;
        };
    } forEach _menaces;''',
 '''    private _moteur = 0; private _dMoteur = -1; private _moteurAllume = 0; private _vueVeh = 0;
    {
        private _v = vehicle _x;
        if ((_v != _x) && { isEngineOn _v }) then {
            _moteurAllume = 1;
            { private _d = _x distance2D _v; if ((_dMoteur < 0) || { _d < _dMoteur }) then { _dMoteur = _d } } forEach _hommes;
            if ((_dMoteur >= 0) && { _dMoteur < CHACAL_PORTEE_SON }) then { _moteur = 1 };
            if (({ [_x, _v, 1200, 70] call CHACAL_fnc_voit } count _hommes) > 0) then { _vueVeh = 1 };
        };
    } forEach _menaces;''')

# 3. les quatre champs dans la ligne de decision
remplacer(M,
 '''|menace_mobile_vue|%11|moteur_entendu|%12|verite_menaces|%13|verite_distance_menace|%14|azimut_chef|%15",
        _percue, _vues, _connues, _camp, _homme, round _dMin, (round (_err * 10)) / 10, _mobile, _vueDepuis, _veh,
        _mobileVue, _moteur,''',
 '''|menace_mobile_vue|%11|moteur_entendu|%12|distance_moteur|%13|moteur_allume|%14|vue_vehicule|%15|n_vues_menace|%16|verite_menaces|%17|verite_distance_menace|%18|azimut_chef|%19",
        _percue, _vues, _connues, _camp, _homme, round _dMin, (round (_err * 10)) / 10, _mobile, _vueDepuis, _veh,
        _mobileVue, _moteur, round _dMoteur, _moteurAllume, _vueVeh, _nVues,''')

# 4. la sonde : les memes champs toutes les 10 s pendant la fenetre d observation
remplacer(f"{B}/mission.Altis/chacal/00_socle.sqf",
 'CHACAL_PORTEE_SON = ["CHACAL_PORTEE_SON", 600] call BIS_fnc_getParamValue;',
 'CHACAL_PORTEE_SON = ["CHACAL_PORTEE_SON", 600] call BIS_fnc_getParamValue;   // portee du moteur entendu, en metres\n'
 '// ! 1 = une ligne sonde_decision toutes les 10 s pendant la fenetre : n importe quelle duree de fenetre se relit apres coup\n'
 'CHACAL_SONDE_PERCEPTION = ["CHACAL_SONDE_PERCEPTION", 0] call BIS_fnc_getParamValue;')

remplacer(M,
 '''    (format ["CHACAL|E|reglage_observation|%1|phase|%2|avant|%3|balayage|%4|distance_secteur|%5|azimuts|%6", round (time * 100) / 100, _phase,''',
 '''    if (CHACAL_SONDE_PERCEPTION == 1) then {
        [_phase] spawn {
            params ["_ph"];
            private _t0 = time;
            while { !CHACAL_FIN && { (time - _t0) < (600 * CHACAL_ECHELLE) } } do {
                (format ["CHACAL|E|sonde_decision|%1|phase|%2|depuis|%3%4", round (time * 100) / 100, _ph,
                    round (time - _t0), call CHACAL_fnc_perceptionMenace]) call CHACAL_LOG;
                sleep (10 * CHACAL_ECHELLE);
            };
        };
    };
    (format ["CHACAL|E|reglage_observation|%1|phase|%2|avant|%3|balayage|%4|distance_secteur|%5|azimuts|%6", round (time * 100) / 100, _phase,''')

remplacer(f"{B}/mission.Altis/description.ext",
 '    class CHACAL_PORTEE_SON\n',
 '    class CHACAL_SONDE_PERCEPTION\n    {\n        title = "Sonde de decision : 1 = une ligne toutes les 10 s pendant la fenetre";\n'
 '        values[] = {0,1}; texts[] = {"0","1"}; default = 0;\n    };\n'
 '    class CHACAL_PORTEE_SON\n')
remplacer(f"{B}/lancer.sh", 'ecrire_param PORTEE_SON "$(lit portee_son 600)"',
 'ecrire_param PORTEE_SON "$(lit portee_son 600)"; ecrire_param SONDE_PERCEPTION "$(lit sonde_perception 0)"')
print("patch perception v2 applique : distance_moteur, moteur_allume, vue_vehicule, n_vues_menace, sonde a 10 s")
