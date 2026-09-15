// =====================================================================
// HMT_fnc_epilogue - lit les drapeaux et rend le nom de la fin.
// C'est l'arbre de Detroit reduit a sa vraie taille : une cascade de tests.
// En campagne, "end1" est route vers la mission suivante par Description.ext.
// =====================================================================
private _lu = { [_this] call HMT_fnc_lire };

private _discret  = ("inf_nuit" call _lu) && !("assaut" call _lu);
private _propre   = !("civils_tues" call _lu) && !("prisonnier_execute" call _lu);
private _rentre   = ("exfil_riviere" call _lu) || ("exfil_helo" call _lu);

// L'ORDRE COMPTE : le premier test qui passe gagne.
private _fin = switch (true) do {
    case (!_rentre):                   { "end3" };   // personne ne revient
    case (_discret && _propre):        { "end1" };   // la fin propre
    default                            { "end2" };   // objectif tenu, mais ca a coute
};

diag_log format ["[ARBRE] epilogue = %1 (discret=%2 propre=%3 rentre=%4)", _fin, _discret, _propre, _rentre];
_fin
