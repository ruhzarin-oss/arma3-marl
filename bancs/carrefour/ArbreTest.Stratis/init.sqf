// =====================================================================
// ArbreTest.Stratis - le banc.
// Aucun combat : on leve les drapeaux a la main (molette souris) et on
// regarde l'arbre reagir. Le controle positif, c'est "tout effacer" :
// si l'arbre affiche encore des branches en clair apres ca, il ment.
// =====================================================================
if (!hasInterface) exitWith {};
waitUntil { sleep 0.2; !isNull player && { time > 0 } };
waitUntil { sleep 0.2; !isNil "HMT_fnc_debriefArbre" };   // CfgFunctions compile

// --- L'arbre du chapitre : [profondeur, libelle, drapeau] ------------
// profondeur 0 = point de decision, profondeur 1 = branche.
HMT_ARBRE = [
    [0, "Entree dans le village", ""],
    [1, "Infiltration de nuit",          "inf_nuit"],
    [1, "Assaut frontal",                "assaut"],

    [0, "Le prisonnier", ""],
    [1, "Relache",                       "prisonnier_relache"],
    [1, "Execute",                       "prisonnier_execute"],
    [1, "Laisse au chef de village",     "prisonnier_abandonne"],

    [0, "Le village", ""],
    [1, "Aucun civil touche",            "civils_epargnes"],
    [1, "Des civils sont tombes",        "civils_tues"],

    [0, "Exfiltration", ""],
    [1, "Par la riviere",                "exfil_riviere"],
    [1, "Heliportee sous le feu",        "exfil_helo"],
    [1, "Personne n'est ressorti",       "exfil_echec"]
];

// --- Une action par branche : c'est le banc, pas la mission ----------
{
    _x params ["_prof", "_libelle", ["_drapeau", ""]];
    if (_prof > 0) then {
        player addAction [
            format ["<t color='#7FD4FF'>Lever :</t> %1", _libelle],
            {
                params ["", "", "", "_arg"];
                _arg call HMT_fnc_drapeau;
                hint parseText format ["<t color='#FFD25A'>%1</t><br/>drapeau leve", _arg select 0];
            },
            [_drapeau, true],
            1.5, false, true
        ];
    };
} forEach HMT_ARBRE;

// --- Voir l'arbre ----------------------------------------------------
player addAction [
    "<t color='#FFD25A'>=== Voir le debrief ===</t>",
    { ["CHAPITRE 2 - LE VILLAGE", HMT_ARBRE] call HMT_fnc_debriefArbre },
    [], 3, false, true
];

// --- Controle positif : tout a zero, l'arbre doit afficher 0 / 9 -----
player addAction [
    "<t color='#FF7F7F'>=== Effacer tous les drapeaux ===</t>",
    {
        {
            if ((_x select 0) > 0) then { [(_x select 2), false] call HMT_fnc_drapeau };
        } forEach HMT_ARBRE;
        hint "drapeaux effaces - le debrief doit maintenant etre entierement gris";
    },
    [], 2, false, true
];

// --- Quelle fin serait choisie, la, tout de suite ? -------------------
player addAction [
    "<t color='#9FE89F'>=== Quel epilogue ? ===</t>",
    { hint format ["Epilogue retenu : %1", call HMT_fnc_epilogue] },
    [], 2.5, false, true
];

diag_log "[ARBRE] banc pret";
hint parseText "<t size='1.2'>Banc de l'arbre</t><br/><br/>Molette souris : lever les drapeaux,<br/>puis <t color='#FFD25A'>Voir le debrief</t>.";
