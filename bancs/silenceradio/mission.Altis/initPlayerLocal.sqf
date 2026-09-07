// =====================================================================
// SILENCE RADIO - equipe, equipement, briefing, exfiltration
// =====================================================================

waitUntil { sleep 0.5; !isNull player && { !isNil "HMT_ready" } && { HMT_ready } };

// ---------------------------------------------------------------------
// 1. Equipement furtif (classes de base uniquement, aucun DLC)
// ---------------------------------------------------------------------
HMT_fnc_kitBlufor = {
	params ["_u", ["_leader", false]];
	removeAllWeapons _u;
	removeAllItems _u;
	removeAllAssignedItems _u;
	removeUniform _u;
	removeVest _u;
	removeBackpack _u;
	removeHeadgear _u;

	_u forceAddUniform "U_B_CombatUniform_mcam";
	_u addVest "V_PlateCarrier1_rgr";
	_u addHeadgear "H_Booniehat_khk";
	_u addBackpack "B_AssaultPack_blk";

	// les chargeurs AVANT l'arme : sinon elle sort vide
	for "_i" from 1 to 8 do { _u addItemToVest "30Rnd_65x39_caseless_mag" };
	_u addWeapon "arifle_MXC_F";
	_u addPrimaryWeaponItem "muzzle_snds_H";
	_u addPrimaryWeaponItem "optic_Holosight";
	_u addPrimaryWeaponItem "acc_pointer_IR";

	for "_i" from 1 to 3 do { _u addItemToUniform "16Rnd_9x21_Mag" };
	_u addWeapon "hgun_P07_snds_F";

	for "_i" from 1 to 2 do { _u addItemToVest "SmokeShell" };
	for "_i" from 1 to 2 do { _u addItemToUniform "FirstAidKit" };

	_u linkItem "ItemMap";
	_u linkItem "ItemCompass";
	_u linkItem "ItemWatch";
	_u linkItem "ItemRadio";
	_u linkItem "NVGoggles";
	_u addWeapon "Rangefinder";   // jumelles : addWeapon, pas linkItem

	if (_leader) then {
		_u addItemToBackpack "DemoCharge_Remote_Mag";
		_u addItemToBackpack "DemoCharge_Remote_Mag";
	};

	_u setUnitTrait ["camouflageCoef", 0.7];
	_u setUnitTrait ["audibleCoef",   0.7];
};

[player, true] call HMT_fnc_kitBlufor;
player setPosATL HMT_insert;
player setDir (HMT_insert getDir HMT_camp);

// ---------------------------------------------------------------------
// 2. Les trois autres
// ---------------------------------------------------------------------
private _grp = group player;
{
	private _u = _grp createUnit [_x, HMT_insert getPos [4 + random 8, random 360], [], 0, "FORM"];
	[_u, false] call HMT_fnc_kitBlufor;
	_u setSkill ["courage", 1];
	_u setSkill ["aimingAccuracy", 0.5];
	if (_forEachIndex == 0) then { _u addItemToBackpack "DemoCharge_Remote_Mag" };
} forEach ["B_soldier_exp_F", "B_soldier_M_F", "B_medic_F"];

_grp selectLeader player;
_grp setFormation "WEDGE";
_grp setBehaviour "STEALTH";
_grp setCombatMode "GREEN";
_grp setSpeedMode "LIMITED";

// un zodiac echoue : c'est par la que vous etes arrives
private _boat = createVehicle ["B_Boat_Transport_01_F", HMT_insert getPos [60, HMT_bearing], [], 0, "CAN_COLLIDE"];
_boat setDir (random 360);

// ---------------------------------------------------------------------
// 3. Prendre les donnees
// ---------------------------------------------------------------------
HMT_intelDone = false;
if (!isNull HMT_laptop) then {
	HMT_laptop addAction [
		"<t color='#66ff66'>Copier les donnees du terminal</t>",
		{
			if (HMT_intelDone) exitWith {};
			HMT_intelDone = true;
			(_this select 0) removeAction (_this select 2);
			["tIntel", "SUCCEEDED"] call BIS_fnc_taskSetState;
			hint "Donnees copiees. L'antenne, maintenant.";
		},
		[], 10, true, true, "", "_this distance _target < 3.5"
	];
} else {
	HMT_intelDone = true;
	["tIntel", "SUCCEEDED"] call BIS_fnc_taskSetState;
};

// ---------------------------------------------------------------------
// 4. Exfiltration : elle n'apparait qu'une fois le travail fait
// ---------------------------------------------------------------------
[] spawn {
	waitUntil { sleep 2; HMT_intelDone && { !isNil "HMT_radarDown" } };

	[west, "tExfil", ["Le travail est fait. Redescendez au point de recuperation sur la cote.", "Exfiltrer", "mrk_exfil"], HMT_exfil, "CREATED", 8, true, "move"] call BIS_fnc_taskCreate;
	"mrk_exfil" setMarkerAlpha 1;
	hint "Point d'exfiltration marque sur la carte.";

	waitUntil { sleep 1; (player distance2D HMT_exfil) < 30 || !alive player };
	if (!alive player) exitWith {};

	["tExfil", "SUCCEEDED"] call BIS_fnc_taskSetState;
	sleep 2;
	if (HMT_detected) then { endMission "End2" } else { endMission "End1" };
};

// echec : le chef tombe
player addEventHandler ["Killed", {
	[] spawn { sleep 4; endMission "End3" };
}];

// ---------------------------------------------------------------------
// 5. Briefing
// ---------------------------------------------------------------------
private _gridObj = mapGridPosition HMT_camp;
private _gridExf = mapGridPosition HMT_exfil;
private _gridIns = mapGridPosition HMT_insert;
private _dist    = round (HMT_insert distance2D HMT_camp);

player createDiaryRecord ["Diary", ["Regles d'engagement",
"Aucun appui, aucune evacuation, aucune couverture aerienne. Silencieux sur toutes les armes.<br/><br/>
Le camp appelle une reaction des qu'il vous voit. Une fois l'alerte donnee, elle ne retombe pas.<br/><br/>
Deux fins possibles selon que vous ayez ete vus ou non. Le contrat, c'est la seconde."]];

player createDiaryRecord ["Diary", ["Plan",
format ["1. Depuis la plage en %1, remonter %2 m jusqu'au relais en %3.<br/>
2. Copier le terminal, pose sur une table a l'interieur du perimetre.<br/>
3. Poser une charge sur l'antenne radar et la detruire.<br/>
4. Redescendre au point d'exfiltration en %4.<br/><br/>
Le mur de HESCO est incomplet : il y a des trouees. Trois projecteurs eclairent le camp.",
_gridIns, _dist, _gridObj, _gridExf]]];

player createDiaryRecord ["Diary", ["Situation",
format ["Altis, 02h45, nuit claire, pas de vent.<br/><br/>
Le CSAT a installe un relais d'ecoute sur la hauteur en %1. Il couvre tout le sud de l'ile et sert de relais aux patrouilles du secteur. Nos communications ne passent plus.<br/><br/>
Effectif estime : une dizaine d'hommes dans le camp, deux mitrailleuses lourdes en poste, une patrouille exterieure d'environ quatre hommes. Une reserve mobile stationne a un kilometre au nord.<br/><br/>
Vous etes quatre. Vous etes arrives par la mer.", _gridObj]]];

sleep 1;
["SILENCE RADIO", format ["Relais CSAT en %1 - %2 m de montee depuis la plage.", _gridObj, _dist]] spawn BIS_fnc_infoText;
