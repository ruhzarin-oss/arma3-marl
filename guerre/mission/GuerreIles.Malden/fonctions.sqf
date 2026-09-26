// =====================================================================
// fonctions.sqf — GUERREILES.MALDEN : la guerre des iles sur le Warlords officiel de Malden.
//
// Warlords garde ce qu il sait faire : le graphe des zones, le vote de la cible, la capture jugee
// par le moteur d Arma (declencheurs SEIZED), les garnisons neutres. On lui retire son argent :
// StartCP 0, CPMultiplier 0, MaxCP 0 (description.ext). Plus aucun point ne nait dans Arma.
//
// L argent vient du moteur du monde, par le pont : guerre/horloge.py verse chaque minute d horloge
// murale la bourse de guerre de chaque ile (guerre/bourse.py) par GUERRE_fnc_tour. Le commandant
// ci-dessous la depense en escouades posees a la base de son camp (pas de parachutage : les
// hommes sortent du pays), et donne a chaque groupe UN ordre de groupe : la cible de son camp, ou
// sa base si l ennemi la vise. Jamais un soldat pilote un par un.
//
// Nos groupes ne sont pas ceux des « warlords » (unites jouables) : la regle de Warlords qui tue
// toute IA entree dans une zone ni tenue ni visee (fn_WLSectorsSetup) ne les voit pas.
//
// ⚠️ TOUT CE QUI REMONTE VERS PYTHON PASSE PAR LABO_R : une cle ecrite ici, puis des NOMBRES.
// ⚠️ LABO_R ne s appelle que dans la portee d une commande du pont (_labo_nonce), jamais d un spawn.
// Camps : 0 east (l envahisseur, Stratis), 1 west (le defenseur, Malden), 2 independant (neutres).
// =====================================================================

LABO_R = {
	params ["_cle", "_vals"];
	private _s = format ["[LABO] R %1 %2", _labo_nonce, _cle];
	{ _s = _s + " " + (str _x); } forEach _vals;
	diag_log _s;
	_labo_k = _labo_k + 1;
};

GUERRE_CAMPS = [east, west, independent];
GUERRE_PLAFOND = 100;
GUERRE_PLAFOND_HOMMES = GUERRE_PLAFOND;
GUERRE_caisse = [0, 0];
GUERRE_verse = [0, 0];
GUERRE_depense = [0, 0];
GUERRE_pertes = [0, 0];
GUERRE_achats = [0, 0];
GUERRE_groupes = [[], []];

// l escouade : 8 hommes de la liste d achat de Warlords (A3DefaultAll), chef en tete
GUERRE_ESCOUADE = [
	["O_Soldier_F", "O_soldier_AR_F", "O_Soldier_GL_F", "O_soldier_LAT_F", "O_medic_F", "O_Soldier_F", "O_Soldier_A_F", "O_soldier_M_F"],
	["B_Soldier_F", "B_soldier_AR_F", "B_Soldier_GL_F", "B_soldier_LAT_F", "B_medic_F", "B_Soldier_F", "B_Soldier_A_F", "B_soldier_M_F"]
];
GUERRE_VEHICULE = ["O_LSV_02_armed_F", "B_LSV_01_armed_F"];
GUERRE_VEHICULE_TOUTES = 3;

// le prix d une classe dans la liste de Warlords ; 100 si elle n y est pas
GUERRE_fnc_prix = {
	params ["_i", "_classe", "_type"];
	private _c = getNumber (configFile >> "CfgWLRequisitionPresets" >> "A3DefaultAll" >> (["EAST", "WEST"] select _i) >> _type >> _classe >> "cost");
	if (_c <= 0) then { _c = 100; };
	_c
};

GUERRE_COUT_ESCOUADE = [0, 0];
GUERRE_COUT_VEHICULE = [0, 0];
{
	private _i = _x;
	private _t = 0;
	{ _t = _t + ([_i, _x, "Infantry"] call GUERRE_fnc_prix); } forEach (GUERRE_ESCOUADE select _i);
	GUERRE_COUT_ESCOUADE set [_i, _t];
	GUERRE_COUT_VEHICULE set [_i, [_i, GUERRE_VEHICULE select _i, "Vehicles"] call GUERRE_fnc_prix];
} forEach [0, 1];

GUERRE_fnc_base = {
	params ["_i"];
	missionNamespace getVariable [["BIS_WL_base_EAST", "BIS_WL_base_WEST"] select _i, objNull]
};

GUERRE_fnc_cible = {
	params ["_i"];
	missionNamespace getVariable [["BIS_WL_currentSector_EAST", "BIS_WL_currentSector_WEST"] select _i, objNull]
};

GUERRE_fnc_vivants = {
	params ["_i"];
	private _n = 0;
	{ _n = _n + ({ alive _x } count (units _x)); } forEach (GUERRE_groupes select _i);
	_n
};

// ---------------------------------------------------------------------
// POSER : une escouade (ou un vehicule arme avec son equipage) sur un point sur de la base.
// ---------------------------------------------------------------------
GUERRE_fnc_lieu = {
	params ["_base"];
	[getPos _base, 20, 180, 6, 0, 0.3, 0] call BIS_fnc_findSafePos
};

// les deux fonctions de pose sont dans suivi.sqf : chaque homme pose porte le numero de front d un habitant du moteur

addMissionEventHandler ["EntityKilled", {
	params ["_mort"];
	if (_mort isKindOf "CAManBase") then {
		private _i = (group _mort) getVariable ["GUERRE_camp", -1];
		if (_i >= 0) then { GUERRE_pertes set [_i, (GUERRE_pertes select _i) + 1]; };
	};
}];

// ---------------------------------------------------------------------
// LES SOLDATS SUIVIS (v5, option 1 de Younes, 26/09) : suivi.sqf, SANS commentaire, car le meme texte est envoye tel
// quel par le pont pour brancher une bataille en cours (call compile ne retire pas les //). Chaque homme pose porte
// GUERRE_id, le numero de front d un habitant de son ile, pris dans GUERRE_reserve (versee par GUERRE_fnc_tour2).
// Sans numero, pas de soldat : la pose rend l argent. GUERRE_fnc_positions rend U camp numero x y degats pour chaque
// vivant et MORT camp numero pour chaque mort depuis le releve precedent. GUERRE_fnc_identifier numerote les hommes
// poses avant le branchement. v6 : chaque soldat suivi est un point sur la carte (bleu Malden, rouge Stratis),
// deplace a chaque releve ; un mort devient une croix noire la ou il est tombe. v7 : chaque joueur est un point jaune,
// deplace chaque seconde (demande de Younes).
// ---------------------------------------------------------------------
#include "suivi.sqf"

// ---------------------------------------------------------------------
// LA DOCTRINE (v8, demande de Younes le 26/09 : regler le blocage « de maniere realiste ») : doctrine.sqf, SANS
// commentaire, envoye tel quel par le pont pour la bataille en cours. Le commandant, un ordre par groupe, et le tour.
// - CONCENTRER : chaque camp a un point de RALLIEMENT a 800 m de sa cible, cote de sa base. Ses groupes offensifs s y
//   regroupent ; l ASSAUT ne part que si la force reunie vaut 3 fois les defenseurs REPERES (connaissance du camp,
//   knowsAbout > 1 ; au moins une escouade supposee). Si toute la force engagee (au ralliement et devant la cible)
//   tombe sous 1 contre 1, repli au ralliement. (v9 : la v8 comptait seulement les hommes a 700 m de la cible, et
//   annulait l assaut a l instant ou il partait : Stratis, 51 reunis contre 8, restait au ralliement.)
// - CHOISIR LA CIBLE (v10, 27/09 : Younes a du choisir lui-meme, le vote de l IA de Warlords ne partait pas) : quand un
//   camp n a plus de cible, son etat-major prend la zone attaquable de meilleure valeur rapportee aux defenseurs reperes
//   et a la distance de son territoire ; la base ennemie seulement a 3 contre 1. Tous les chefs IA du camp votent pour
//   elle (le vote d un joueur compte toujours, il n est plus necessaire).
//   (Trois contre un : la regle d ordre de grandeur des armees pour prendre une position tenue.)
// - DEFENDRE SELON LA MENACE : si l ennemi vise sa base, un camp y garde les groupes les plus proches, un defenseur
//   pour trois ennemis reperes a moins de 1 500 m, au moins une escouade ; les autres gardent l offensive.
// - ACHETER : une escouade si la caisse, la reserve de soldats et le plafond d hommes le permettent ; sinon un vehicule
//   arme (un toutes les 3 escouades, ou des que le plafond empeche une escouade de plus).
// - Les credits non depenses sont plafonnes a 3 escouades (GUERRE_annules compte ce qui est refuse) : l argent, lui,
//   ne quitte le Tresor de l ile qu a l achat (guerre/moteur.py, payer_la_guerre).
// - Les poses de suivi.sqf gardent une garde qui rend l argent sans soldat : elle ne sert qu a l ancienne boucle
//   d une bataille branchee en cours (v1), neutralisee au branchement (GUERRE_PLAFOND = 0).
// ---------------------------------------------------------------------
#include "doctrine.sqf"

GUERRE_VERSION = 10;
