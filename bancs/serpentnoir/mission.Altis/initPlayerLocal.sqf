// =====================================================================
// SERPENT NOIR — l'homme seul : equipement, renseignement, fins
// =====================================================================
waitUntil { sleep 0.5; !isNull player && { !isNil "HMT_ready" } && { HMT_ready } };

// ---------------------------------------------------------------------
// 1. L'equipement d'un homme qui n'a droit ni au bruit ni a l'erreur
// ---------------------------------------------------------------------
removeAllWeapons player; removeAllItems player; removeAllAssignedItems player;
removeUniform player; removeVest player; removeBackpack player; removeHeadgear player;
removeGoggles player;

player forceAddUniform "U_B_CombatUniform_mcam";
player addVest "V_Chestrig_khk";
player addHeadgear "H_Booniehat_khk";
player addBackpack "B_AssaultPack_blk";

// les chargeurs AVANT l'arme : sinon elle sort vide
for "_i" from 1 to 6 do { player addItemToVest "20Rnd_762x51_Mag" };
player addWeapon "srifle_EBR_F";
player addPrimaryWeaponItem "muzzle_snds_B";
player addPrimaryWeaponItem "optic_DMS";
player addPrimaryWeaponItem "acc_pointer_IR";
player addPrimaryWeaponItem "bipod_01_F_blk";

for "_i" from 1 to 3 do { player addItemToUniform "16Rnd_9x21_Mag" };
player addWeapon "hgun_P07_snds_F";

for "_i" from 1 to 2 do { player addItemToVest "SmokeShell" };
for "_i" from 1 to 3 do { player addItemToUniform "FirstAidKit" };
player addItemToBackpack "ToolKit";
for "_i" from 1 to 2 do { player addItemToBackpack "DemoCharge_Remote_Mag" };

player linkItem "ItemMap"; player linkItem "ItemCompass";
player linkItem "ItemWatch"; player linkItem "ItemRadio";
player linkItem "NVGoggles";
player addWeapon "Rangefinder";

player setUnitTrait ["camouflageCoef", 0.65];
player setUnitTrait ["audibleCoef", 0.65];
player setPosATL HMT_INSERT;
player setDir (HMT_INSERT getDir HMT_OP);

// ---------------------------------------------------------------------
// 2. LE RENSEIGNEMENT — sans lui, le camp n'est pas sur la carte
// ---------------------------------------------------------------------
HMT_fnc_prendreIntel = {
	if (HMT_intel) exitWith {};
	HMT_intel = true;
	["tIntel", "SUCCEEDED"] call BIS_fnc_taskSetState;
	"m_camp" setMarkerAlpha 1;
	"m_camp" setMarkerText "Camp — cible localisee";
	[west, "tHvt", ["Le colonel Karimi dort au camp. Il fait la navette entre le poste de commandement et la baraque nord. Deux gardes du corps ne le quittent pas.", "Neutraliser la cible", "m_camp"], HMT_CAMP, "CREATED", 9, true, "kill"] call BIS_fnc_taskCreate;
	hint "Terminal copie. Le camp est sur votre carte.\n\nColonel Vahid Karimi. Uniforme d'officier. Deux gardes du corps.";
};

if (!isNull HMT_LAPTOP_RELAIS) then {
	HMT_LAPTOP_RELAIS addAction ["<t color='#66ff66'>Copier le terminal</t>",
		{ call HMT_fnc_prendreIntel; (_this select 0) removeAction (_this select 2); },
		[], 10, true, true, "", "_this distance _target < 3.5"];
};
// le terminal du camp donne la meme chose, pour qui saute l'avant-poste
if (!isNull HMT_LAPTOP_CAMP) then {
	HMT_LAPTOP_CAMP addAction ["<t color='#66ff66'>Copier le terminal</t>",
		{ call HMT_fnc_prendreIntel; (_this select 0) removeAction (_this select 2); },
		[], 10, true, true, "", "_this distance _target < 3.5"];
};

// ---------------------------------------------------------------------
// 3. LE CHRONOMETRE — il tourne, et il se voit
// ---------------------------------------------------------------------
[] spawn {
	private _t0 = time;
	while { alive player && !HMT_hvtMort && !HMT_hvtFui } do {
		private _r = HMT_LIMITE - (time - _t0);
		if (_r < 0) exitWith {};
		if ((round _r) % 300 == 0 && { _r > 60 }) then {
			hint format ["Depart du convoi dans %1 minutes.", round (_r / 60)];
			sleep 2;
		};
		sleep 1;
	};
};

// ---------------------------------------------------------------------
// 4. LES FINS
// ---------------------------------------------------------------------
[] spawn {
	waitUntil { sleep 2; HMT_hvtMort || { !isNil "HMT_echappe" } || { !alive player } };
	if (!alive player) exitWith {};
	if (!isNil "HMT_echappe") exitWith { sleep 3; endMission "End3" };

	[west, "tExfil", ["La cible est neutralisee. Rejoignez le point de recuperation.", "Exfiltrer", "m_exfil"], HMT_EXFIL, "CREATED", 8, true, "move"] call BIS_fnc_taskCreate;
	"m_exfil" setMarkerAlpha 1;
	hint "Cible neutralisee.\n\nPoint d'exfiltration marque. Ne trainez pas.";

	waitUntil { sleep 1; (player distance2D HMT_EXFIL) < 30 || !alive player };
	if (!alive player) exitWith {};
	["tExfil", "SUCCEEDED"] call BIS_fnc_taskSetState;
	sleep 2;
	if (HMT_detecte) then { endMission "End2" } else { endMission "End1" };
};

player addEventHandler ["Killed", { [] spawn { sleep 4; endMission "End4" } }];

// ---------------------------------------------------------------------
// 5. BRIEFING
// ---------------------------------------------------------------------
private _gIns = mapGridPosition HMT_INSERT;
private _gOp  = mapGridPosition HMT_OP;
private _gRel = mapGridPosition HMT_RELAIS;
private _dOp  = round (HMT_INSERT distance2D HMT_OP);
private _gain = round HMT_OP_GAIN;
// le briefing DECRIT le terrain mesure, il ne le promet pas
private _quOp = if (_gain >= 10) then { format ["domine le camp de %1 m", _gain] }
           else { if (_gain >= -5) then { "est de plain-pied avec le camp" }
           else { format ["est %1 m sous le camp : c'est LUI qui domine", abs _gain] } };
if (!HMT_OP_VUE) then { _quOp = _quOp + ", et la vue n'y est pas franche — il faudra chercher votre angle" };

player createDiaryRecord ["Diary", ["Regles d'engagement",
"Vous etes SEUL. Aucun appui, aucune evacuation medicale, aucune reserve.<br/><br/>
L'alerte ne retombe jamais. Si le camp vous voit, la cible monte en voiture et part — et vous ne la rattraperez pas a pied.<br/><br/>
Le convoi part de lui-meme au bout de 35 minutes. Le temps est votre second adversaire."]];

player createDiaryRecord ["Diary", ["Plan",
format ["1. Mise a terre en %1. Aucun vehicule.<br/>
2. Le point d'observation en %2, a %3 m de la mise a terre : il %5. De la, vous verrez ce que vous affrontez.<br/>
3. L'avant-poste en %4 tient un terminal : il vous dira ou est la cible. Le camp n'est PAS sur votre carte avant ca.<br/>
4. Neutraliser le colonel. Uniforme d'officier, deux gardes du corps, il fait la navette entre deux batiments.<br/>
5. Exfiltrer. Le point n'apparait qu'une fois la cible a terre.<br/><br/>
L'enceinte du camp n'a que deux ouvertures. Les projecteurs sont allumes. Un guetteur tient la tour.",
_gIns, _gOp, _dOp, _gRel, _quOp]]];

player createDiaryRecord ["Diary", ["Situation",
"Altis, 01h20. Nuit claire, pas de vent.<br/><br/>
Le colonel Vahid Karimi commande le dispositif du centre de l'ile. Il embarque a l'aube et sera hors d'atteinte. C'est cette nuit ou jamais.<br/><br/>
Son camp est tenu par une vingtaine d'hommes : garde rapprochee, deux patrouilles a rayons differents, deux mitrailleuses lourdes en poste, un guetteur en tour, un blinde qui tourne. Un avant-poste couvre l'approche.<br/><br/>
Vous etes un homme, avec un fusil silencieux et des jumelles."]];

sleep 1;
["SERPENT NOIR", "Un homme. Trente-cinq minutes. Aucune sortie de secours."] spawn BIS_fnc_infoText;
