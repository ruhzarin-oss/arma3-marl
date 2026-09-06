// freshness_bench.sqf — sonde de fraicheur proposee par Fable le 25/08 (memoire
// pixels-arma-verdict-fable-nogo) : "monte le banc de fraicheur si tu veux une preuve
// a un jour". A charger sur le CLIENT RENDU (le meme qui fait tourner capture_bridge.py
// cote Windows), PAS sur le dedie headless — il n'y a pas de camera a filmer sans rendu.
//
// Principe : un panneau BLANC attache a la camera de l'unite observee bascule
// visible/invisible a un instant connu, logue par HARMATTAN_ACTUATOR (meme canal TCP natif
// que les observations, donc meme retard reseau que le vrai flux — pas une mesure optimiste
// sur un canal a part). Le detecteur cote Python (freshness_detect.py) mesure quand le
// flash apparait REELLEMENT dans les cadres captures et calcule le retard.
//
// Critere ecrit AVANT la mesure (Fable, 25/08) :
//   - controle positif : 20/20 flashes detectes, sinon le banc lui-meme est en panne.
//   - echec de fraicheur : p95 > 500 ms, ou l'unite se deplace de plus de 2 m dans l'image
//     pendant l'intervalle (pas mesure ici, a instrumenter separement si le p95 passe).

params [["_unit", objNull], ["_period", 2]];
if (isNull _unit) exitWith { diag_log "FRESH_BENCH: _unit nulle, sonde non demarree" };

private _panel = "Sign_Sphere100cm_F" createVehicleLocal (getPosATL _unit);
_panel setObjectTexture [0, "#(argb,8,8,3)color(1,1,1,1,co)"];
_panel attachTo [_unit, [0, 1.2, 0]];   // 1,2 m devant les yeux : remplit le champ, quelle que soit l'orientation
_panel hideObjectGlobal true;

diag_log format ["FRESH_BENCH demarree unit=%1 period=%2", _unit, _period];

[_panel, _period] spawn {
    params ["_panel", "_period"];
    private _on = false;
    while {!isNull _panel} do {
        sleep _period;
        _on = !_on;
        _panel hideObjectGlobal (!_on);
        // meme format que HARMATTAN_OBS18 : une ligne, parsable, sur le canal deja mesure
        // en production (native TCP si dispo, sinon diag_log/RPT comme le reste du pont).
        if (!isNil "HARMATTAN_NATIVE_OUT") then {
            "hmt_native" callExtension ("o|FRESH_FLASH on=" + str _on);
        } else {
            diag_log format ["FRESH_FLASH on=%1", _on];
        };
    };
};
