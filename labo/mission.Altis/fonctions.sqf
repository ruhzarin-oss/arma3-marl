// =====================================================================
// fonctions.sqf — les exécutants du LABO. Chargé une fois par initServer.sqf, par
// preprocessFileLineNumbers : les commentaires y sont permis et une erreur y porte son numéro de
// ligne. C'est pour ça que tout ce qui boucle vit ICI, jamais dans une commande envoyée.
//
// ⚠️ TOUT CE QUI REMONTE VERS PYTHON PASSE PAR LABO_R, qui n'émet que des NOMBRES derrière une
// clé écrite ici. Aucun texte du monde (nom, callsign, message) ne sort : le RPT est lu par un LLM.
//
// ⚠️ _labo_nonce et _labo_k sont des variables LOCALES de la commande en cours, posées par
// l'enveloppe de arma_labo.py. LABO_R les voit par la portée dynamique de `call`. Ne JAMAIS
// appeler LABO_R depuis un `spawn` : le nonce n'y existe pas et la ligne serait perdue.
//
// Indices de camp : 0 rouge (east), 1 bleu (west), 2 vert (independent), 3 civil.
// Codes REFUS : 1 eau, 2 pas de lieu sûr, 3 groupe inconnu, 4 groupe vide.
// =====================================================================

LABO_CAMPS = [east, west, independent, civilian];

LABO_R = {
	params ["_cle", "_vals"];
	private _s = format ["[LABO] R %1 %2", _labo_nonce, _cle];
	{ _s = _s + " " + (str _x); } forEach _vals;
	diag_log _s;
	_labo_k = _labo_k + 1;
};

// ---------------------------------------------------------------------
// ETAT : compte le monde à chaque appel. TOTAL, 4 × CAMP, un JOUEUR par joueur, et si _detail > 0
// jusqu'à _detail lignes U (un homme non joueur chacune).
// ---------------------------------------------------------------------
LABO_fnc_etat = {
	params [["_detail", 0]];
	private _nonJ = allUnits select { !isPlayer _x };
	private _joueurs = allPlayers select { !(_x isKindOf "HeadlessClient_F") };
	["TOTAL", [count allUnits, count _nonJ, count allDeadMen, count _joueurs, count allGroups]] call LABO_R;
	{
		private _cote = _x;
		private _u = allUnits select { (side group _x) isEqualTo _cote };
		private _g = allGroups select { ((side _x) isEqualTo _cote) && { (count units _x) > 0 } };
		["CAMP", [_forEachIndex, count _u, count _g]] call LABO_R;
	} forEach LABO_CAMPS;
	{
		private _p = getPosATL _x;
		["JOUEUR", [_p select 0, _p select 1, _p select 2, getDir _x]] call LABO_R;
	} forEach _joueurs;
	if (_detail > 0) then {
		{
			if (_forEachIndex < _detail) then {
				private _p = getPosATL _x;
				["U", [LABO_CAMPS find (side group _x), allGroups find (group _x),
				       _p select 0, _p select 1, _p select 2, damage _x]] call LABO_R;
			};
		} forEach _nonJ;
	};
};

// ---------------------------------------------------------------------
// POSER UN GROUPE à un point, sans ordre. On rend le nombre RÉELLEMENT posé.
// ---------------------------------------------------------------------
LABO_fnc_poser_groupe = {
	params ["_camp", "_nombre", "_px", "_py", "_skill"];
	private _classe = ["O_Soldier_F", "B_Soldier_F", "I_soldier_F"] select _camp;
	private _cote = [east, west, independent] select _camp;
	private _p = [_px, _py, 0];
	if (surfaceIsWater _p) exitWith { ["REFUS", [1]] call LABO_R; };
	private _g = createGroup [_cote, true];
	for "_i" from 1 to _nombre do { _g createUnit [_classe, _p, [], 8, "FORM"]; };
	{ _x setSkill _skill; _x allowFleeing 0; } forEach (units _g);
	private _l = getPosATL (leader _g);
	["GROUPE", [allGroups find _g, _camp, count (units _g), _l select 0, _l select 1]] call LABO_R;
};

// ---------------------------------------------------------------------
// LA SCÈNE QUI COMBAT (recette mesurée le 26/08) : lieu par findSafePos puis VÉRIFIÉ, deux
// groupes face à face, COMBAT/RED/FULL, doMove par homme, reveal mutuel. Sans reveal, deux
// groupes à 220 m se tournent autour longtemps.
// ---------------------------------------------------------------------
LABO_fnc_poser_scene = {
	params ["_nb", "_nr", "_d", "_cx", "_cy", "_skill", "_combat"];
	private _p = [[_cx, _cy, 0], 0, 400, 5, 0, 0.3, 0] call BIS_fnc_findSafePos;
	if (((_p distance2D [_cx, _cy]) > 450) || { (getTerrainHeightASL [_p select 0, _p select 1]) <= 0 }) exitWith {
		["REFUS", [2]] call LABO_R;
	};
	private _az = random 360;
	private _pb = _p getPos [_d / 2, _az];
	private _pr = _p getPos [_d / 2, _az + 180];
	private _gb = grpNull;
	private _gr = grpNull;
	if (_nb > 0) then {
		_gb = createGroup [west, true];
		for "_i" from 1 to _nb do { _gb createUnit ["B_Soldier_F", _pb, [], 5, "FORM"]; };
	};
	if (_nr > 0) then {
		_gr = createGroup [east, true];
		for "_i" from 1 to _nr do { _gr createUnit ["O_Soldier_F", _pr, [], 5, "FORM"]; };
	};
	{ _x setSkill _skill; _x allowFleeing 0; } forEach ((units _gb) + (units _gr));
	if (_combat == 1) then {
		{
			if !(isNull _x) then { _x setBehaviour "COMBAT"; _x setSpeedMode "FULL"; _x setCombatMode "RED"; };
		} forEach [_gb, _gr];
		{ _x doMove _pr; } forEach (units _gb);
		{ _x doMove _pb; } forEach (units _gr);
		if (!(isNull _gb) && { !(isNull _gr) }) then {
			{ _gb reveal [_x, 4]; } forEach (units _gr);
			{ _gr reveal [_x, 4]; } forEach (units _gb);
		};
	};
	["BLEU", [allGroups find _gb, count (units _gb), _pb select 0, _pb select 1]] call LABO_R;
	["ROUGE", [allGroups find _gr, count (units _gr), _pr select 0, _pr select 1]] call LABO_R;
};

// ---------------------------------------------------------------------
// ORDONNER. _ordre : 0 aller, 1 arreter, 2 comportement, 3 combat, 4 vitesse, 5 posture, 6 reveler.
// _v indexe la liste de l'ordre ; les listes sont les mêmes que VALEURS dans arma_labo.py.
// ---------------------------------------------------------------------
LABO_fnc_ordonner = {
	params ["_gi", "_ordre", "_a", "_b", "_v"];
	if ((_gi < 0) || { _gi >= (count allGroups) }) exitWith { ["REFUS", [3]] call LABO_R; };
	private _g = allGroups select _gi;
	if ((count (units _g)) == 0) exitWith { ["REFUS", [4]] call LABO_R; };
	switch (_ordre) do {
		case 0: { { _x doMove [_a, _b, 0]; } forEach (units _g); };
		case 1: { doStop (units _g); };
		case 2: { _g setBehaviour (["CARELESS", "SAFE", "AWARE", "COMBAT", "STEALTH"] select _v); };
		case 3: { _g setCombatMode (["BLUE", "GREEN", "WHITE", "YELLOW", "RED"] select _v); };
		case 4: { _g setSpeedMode (["LIMITED", "NORMAL", "FULL"] select _v); };
		case 5: { { _x setUnitPos (["UP", "MIDDLE", "DOWN", "AUTO"] select _v); } forEach (units _g); };
		case 6: {
			private _cote = side _g;
			{
				if (((side group _x) != _cote) && { (side group _x) != civilian }) then { _g reveal [_x, 4]; };
			} forEach allUnits;
		};
	};
	private _l = getPosATL (leader _g);
	["ORDRE", [_gi, LABO_CAMPS find (side _g), count (units _g), _ordre, _l select 0, _l select 1]] call LABO_R;
};

// ---------------------------------------------------------------------
// NETTOYER : table rase. `sleep` est permis : la commande tourne dans son propre fil (spawn).
// La table rase se prouve : APRES doit dire 0 homme non joueur, sinon Python lève.
// ---------------------------------------------------------------------
LABO_fnc_nettoyer = {
	["AVANT", [count (allUnits select { !isPlayer _x }), count allDeadMen, count allGroups]] call LABO_R;
	{ if (!isPlayer _x) then { deleteVehicle _x; }; } forEach allUnits;
	{ deleteVehicle _x; } forEach allDeadMen;
	{ deleteVehicle _x; } forEach (allMissionObjects "WeaponHolderSimulated");
	{ deleteVehicle _x; } forEach (allMissionObjects "GroundWeaponHolder");
	sleep 1;
	{ if ((count (units _x)) == 0) then { deleteGroup _x; }; } forEach allGroups;
	sleep 0.5;
	["APRES", [count (allUnits select { !isPlayer _x }), count allDeadMen, count allGroups]] call LABO_R;
};

// Dernière ligne : si elle s'exécute, tout le fichier a compilé. Le canari la lit ; une valeur
// différente de VERSION_MISSION dans arma_labo.py = la mission jouée n'est pas celle du dépôt.
LABO_VERSION = 1;
