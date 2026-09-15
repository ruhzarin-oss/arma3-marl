// =====================================================================
// HMT_fnc_drapeau - leve (ou baisse) un drapeau et le rend persistant.
//   ["prisonnier_relache"]        call HMT_fnc_drapeau;   // vrai
//   ["prisonnier_relache", false] call HMT_fnc_drapeau;   // faux
// =====================================================================
params [["_nom", "", [""]], ["_valeur", true, [true]]];
if (_nom isEqualTo "") exitWith { false };

private _cle = format ["HMT_%1", _nom];

// tout de suite, et sur tous les clients
missionNamespace setVariable [_cle, _valeur, true];

// et apres la fin de mission : c'est ca qui fait la campagne
profileNamespace setVariable [_cle, _valeur];
saveProfileNamespace;

diag_log format ["[ARBRE] %1 = %2", _cle, _valeur];
_valeur
