// roles.sqf — ETAPE 3 : assigne un ROLE a chaque homme de la garnison + applique son loadout.
// HMT_LOADOUTS = table role->loadout(setUnitLoadout), A REMPLIR avec les exports ACE Arsenal de Younes.
// Tant qu'un role n'a pas d'export, on pose une arme de role par defaut (le reste du kit reste).
if (isNil "HMT_LOADOUTS") then { HMT_LOADOUTS = createHashMap; };

HMT_APPLYROLE = {
    params ["_u", "_role"];
    _u setVariable ["HMT_ROLE", _role, true];
    private _lo = HMT_LOADOUTS getOrDefault [_role, []];
    if (count _lo > 0) exitWith { _u setUnitLoadout _lo; };          // export ACE de Younes -> loadout complet
    switch (_role) do {                                              // sinon : arme de role par defaut (RHS)
        case "mg":        { _u addWeapon "rhs_weap_pkp"; _u addMagazines ["rhs_100Rnd_762x54mmR", 4]; };
        case "grenadier": { _u addWeapon "rhs_weap_ak74m_gp25"; _u addMagazines ["rhs_30Rnd_545x39_7N10_AK", 6]; _u addMagazines ["rhs_VOG25", 8]; };
        case "marksman":  { _u addWeapon "rhs_weap_svds"; _u addMagazines ["rhs_10Rnd_762x54mmR_7N1", 6]; };
        case "at":        { _u addWeapon "rhs_weap_rpg7"; _u addMagazines ["rhs_rpg7_PG7VL_single", 3]; };
        case "medic":     { _u addItemToBackpack "ACE_fieldDressing"; { _u addItemToBackpack "ACE_morphine" } forEach [1,2]; _u addItemToBackpack "ACE_epinephrine"; _u addItemToBackpack "ACE_bloodIV"; };
        default {};                                                  // rifleman = kit par defaut (HMT_KIT)
    };
};

// distribution des roles sur la garnison (cyclique : ~1 specialiste/role par escouade de 8)
HMT_ROLE_CYCLE = ["mg", "grenadier", "medic", "at", "marksman", "rifleman", "rifleman", "rifleman"];
private _i = 0; private _tab = createHashMap;
{
    private _u = _x select 0;
    if (!isNull _u) then {
        private _role = HMT_ROLE_CYCLE select (_i mod (count HMT_ROLE_CYCLE));
        [_u, _role] call HMT_APPLYROLE;
        _tab set [_role, (_tab getOrDefault [_role, 0]) + 1];
        _i = _i + 1;
    };
} forEach HMT_FOB_MEN;
diag_log format ["HARMATTAN_ROLES %1 hommes tagges | repartition=%2 | loadouts_ACE_remplis=%3", _i, _tab, count HMT_LOADOUTS];
