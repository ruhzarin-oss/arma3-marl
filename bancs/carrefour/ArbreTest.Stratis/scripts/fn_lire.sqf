// =====================================================================
// HMT_fnc_lire - relit un drapeau, mission en cours d'abord, profil ensuite.
//   ["prisonnier_relache"] call HMT_fnc_lire;   // -> true / false
// =====================================================================
params [["_nom", "", [""]]];
if (_nom isEqualTo "") exitWith { false };

private _cle = format ["HMT_%1", _nom];
private _v = missionNamespace getVariable _cle;
if (isNil "_v") then { _v = profileNamespace getVariable [_cle, false] };

_v isEqualTo true
