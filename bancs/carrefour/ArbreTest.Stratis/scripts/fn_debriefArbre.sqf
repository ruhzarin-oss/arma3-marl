// =====================================================================
// HMT_fnc_debriefArbre - affiche l'arbre du chapitre.
// Chemin pris en clair, branches ratees en gris : c'est le gris qui donne
// envie de rejouer.
//
//   ["CHAPITRE 2 - LE VILLAGE", HMT_ARBRE] call HMT_fnc_debriefArbre;
//
// HMT_ARBRE = liste de noeuds [profondeur, libelle, drapeau]
//   profondeur 0 = un point de decision (titre)
//   profondeur 1 = une branche possible
// =====================================================================
params [["_titre", "CHAPITRE", [""]], ["_noeuds", [], [[]]]];
if (_noeuds isEqualTo []) exitWith { diag_log "[ARBRE] arbre vide, rien a afficher"; false };

#define C_TITRE "#FFFFFF"
#define C_PRIS  "#FFD25A"
#define C_RATE  "#4A4A4A"
#define C_NOTE  "#8A8A8A"

private _txt = "";
{
    _x params [["_prof", 0], ["_libelle", "?"], ["_drapeau", ""]];

    if (_prof == 0) then {
        // un point de decision
        _txt = _txt + format [
            "<br/><t color='%1' size='1.15'>%2</t><br/>",
            C_TITRE, toUpper _libelle
        ];
    } else {
        // une branche. Le guide "|--" remplace l'indentation : les espaces
        // de tete sont rabotes par le rendu de certaines polices.
        private _pris = [_drapeau] call HMT_fnc_lire;
        _txt = _txt + format [
            "<t color='%1'>   |-- [%2] %3</t><br/>",
            [C_RATE, C_PRIS] select _pris,
            ["  ", "x"]      select _pris,
            _libelle
        ];
    };
} forEach _noeuds;

// Le compteur. C'est lui qui transforme un debrief en rejouabilite.
private _total = { (_x select 0) > 0 } count _noeuds;
private _vus   = { ((_x select 0) > 0) && { [_x select 2] call HMT_fnc_lire } } count _noeuds;
_txt = _txt + format [
    "<br/><t color='%1' size='0.9'>Branches empruntees : %2 / %3</t>",
    C_NOTE, _vus, _total
];

// --- affichage -------------------------------------------------------
disableSerialization;
if (!createDialog "HMT_Debrief") exitWith { diag_log "[ARBRE] createDialog a echoue"; false };

private _dlg = findDisplay 9000;
(_dlg displayCtrl 9001) ctrlSetText _titre;

private _ctrl = _dlg displayCtrl 9002;
_ctrl ctrlSetStructuredText parseText _txt;

// On etire le texte a sa vraie hauteur : c'est ce qui arme le defilement
// du groupe qui le contient, sinon un arbre long est coupe en silence.
private _h = ctrlTextHeight _ctrl;
_ctrl ctrlSetPosition [0, 0, 0.47 * safezoneW, _h];
_ctrl ctrlCommit 0;

true
