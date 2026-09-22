// =====================================================================
// CHACAL - LES DIX. Un detachement, trois elements, dix roles nommes.
//
// Les roles ne sont pas decoratifs : le corpus les porte. Un imitateur qui les
// ignore apprend la moyenne de dix hommes qui ne font pas la meme chose, et
// cette moyenne n est le comportement de personne.
//
// Ils sont crees en UN SEUL groupe puis repartis : la scission est une PHASE,
// pas un etat initial. Ce que le corpus doit montrer, c est le moment ou le
// detachement se coupe en trois.
// =====================================================================

MC7_gFS = ([west, 7] call MULTI_fnc_groupe);
MC7_FS = [];

MC7_fnc_kitOuest = {
    params ["_u", "_role"];
    _u setVariable ["chacal_role", _role, true];
    _u setSkill ["spotDistance", 0.75];
    _u setSkill ["spotTime", 0.8];
    _u setSkill ["aimingAccuracy", 0.7];
    _u setSkill ["aimingSpeed", 0.8];
    _u setSkill ["courage", 1];
    _u setSkill ["commanding", 1];
    // La nuit est l avantage. Il est materiel, pas scenaristique.
    if ((hmd _u) == "") then { _u linkItem "NVGoggles" };
    // Silencieux quand l arme en accepte un : une infiltration qui claque n en
    // est plus une, et le corpus doit contenir des tirs qui ne reveillent pas
    // tout le site.
    private _w = primaryWeapon _u;
    if (_w != "") then {
        {
            if (_x in ((configFile >> "CfgWeapons" >> _w >> "WeaponSlotsInfo" >> "MuzzleSlot" >> "compatibleItems") call BIS_fnc_getCfgDataArray))
                exitWith { _u addPrimaryWeaponItem _x };
        } forEach ["muzzle_snds_H", "muzzle_snds_B", "muzzle_snds_M", "muzzle_snds_H_MG"];
    };
    _u allowFleeing 0;
    _u
};

// ! CHEF et ADJOINT etaient tues a TROIS SECONDES d intervalle par la meme
// rafale : crees l un derriere l autre, ils marchaient cote a cote en tete de
// file. L ADJOINT est donc cree EN DERNIER - il ferme la file, et le
// detachement ne perd pas ses deux chefs d un coup.
// La liste est construite AVANT la boucle pour pouvoir etre repetee. L ADJOINT reste cree en
// dernier a chaque passe : c est lui qui ferme la file, et le detachement ne perd pas ses deux
// chefs sur la meme rafale.
private _rolesBase = [
    ["B_recon_TL_F",    "CHEF"],
    ["B_recon_M_F",     "TIREUR_1"],
    ["B_recon_M_F",     "TIREUR_2"],
    ["B_recon_exp_F",   "DEMO_1"],
    ["B_recon_exp_F",   "DEMO_2"],
    ["B_recon_medic_F", "MEDECIN"],
    ["B_recon_LAT_F",   "AT"],
    ["B_recon_F",       "FUSILIER_1"],
    ["B_recon_F",       "FUSILIER_2"],
    ["B_recon_TL_F",    "ADJOINT"]
];

// Repetee autant de fois que l effectif le demande : 10 -> une passe, 20 -> deux.
private _rolesTous = [];
for "_p" from 1 to (round (MC7_EFFECTIF / 10)) do { _rolesTous append _rolesBase };

{
    _x params ["_cls", "_role"];
    private _u = MC7_gFS createUnit [_cls, MC7_LZ getPos [12 call MC7_fnc_al, 360 call MC7_fnc_al], [], 0, "NONE"];
    [_u, _role] call MC7_fnc_kitOuest;
    MC7_FS pushBack _u;
} forEach _rolesTous;if (count MC7_FS < MC7_EFFECTIF) exitWith {
    MC7_ISSUE = "VOID"; MC7_CAUSE = "DETACHEMENT_INCOMPLET";
    (format ["CHACAL|VOID|blufor|%1", count MC7_FS]) call MC7_LOG;
};

MC7_gFS selectLeader (MC7_FS select 0);
MC7_gFS setBehaviour "STEALTH";
MC7_gFS setCombatMode "GREEN";      // ne tire que si on lui tire dessus
MC7_gFS setSpeedMode "LIMITED";
MC7_gFS setFormation "FILE";        // la formation de nuit hors piste
MC7_gFS allowFleeing 0;

// ! LES CHARGES VONT A L ELEMENT D ASSAUT ENTIER ( Fable, 05/09 ).
// Deux hommes detaches qui traversent un site en alerte meurent - mesure du
// 05/09, DEMO_1 et DEMO_2 tues a 80 s d intervalle, aucune charge posee.
// Trois charges par demolisseur, une au chef et a l adjoint en secours : la
// pose reste faite par un DEMO quand il est la, et le role est ecrit dans la
// ligne, donc le corpus continue de porter les roles.
{ for "_i" from 1 to 3 do { _x addMagazine "DemoCharge_Remote_Mag" }; }
    forEach (MC7_FS select { (_x getVariable ["chacal_role",""]) in ["DEMO_1","DEMO_2"] });
{ _x addMagazine "DemoCharge_Remote_Mag"; }
    forEach (MC7_FS select { (_x getVariable ["chacal_role",""]) in ["CHEF","ADJOINT"] });

MC7_fnc_role = {
    private _r = _this;
    MC7_FS select { alive _x && { (_x getVariable ["chacal_role",""]) in _r } }
};
// ! FUSILIER_1 ETAIT DANS DEUX ELEMENTS ( Fable, 05/09 ). Il partait sur la
// crete avec la reco, puis le bouchon le recuperait alors que ses deux
// camarades etaient a la cache : le centre du groupe s etirait sur six cents
// metres et `fnc_enPlace` ne pouvait JAMAIS le trouver en place - mesure
// `BOUCHON|reste|287 -> 280 -> 281`, qui ne fermait pas.
// Les deux tireurs montent, observent, et RESTENT : c est deja l appui.
MC7_RECO    = ["TIREUR_1","TIREUR_2"];
MC7_APPUI   = ["TIREUR_1","TIREUR_2"];
MC7_ASSAUT  = ["CHEF","ADJOINT","DEMO_1","DEMO_2","MEDECIN"];
MC7_BOUCHON = ["AT","FUSILIER_1","FUSILIER_2"];
// ! PARTAGE 7/1 ( 16/09 ). Les deux FUSILIERS passent du bouchon a l assaut.
// L AT RESTE SEUL SUR LA ROUTE, et c est delibere : c est lui qui porte l arme antichar,
// la seule qui detruise un MRAP de reserve. Le deplacer confondrait " moins d hommes au
// bouchon " avec " plus d arme antichar a l assaut ", et le bras ne mesurerait plus
// l effectif mais l armement. L effectif total reste dix dans les deux bras.
if (MC7_PARTAGE == 1) then {
    MC7_ASSAUT  = ["CHEF","ADJOINT","DEMO_1","DEMO_2","MEDECIN","FUSILIER_1","FUSILIER_2"];
    MC7_BOUCHON = ["AT"];
};

MC7_gAppui = grpNull; MC7_gAssaut = grpNull;
MC7_gBouchon = grpNull; MC7_gReco = grpNull; MC7_gDemo = grpNull;

// Les elements sont des GROUPES a part entiere : un element qui reste dans le
// groupe du chef obeit encore a sa formation, donc ne se separe pas vraiment.
MC7_fnc_detacher = {
    params ["_roles", "_nom"];
    private _u = _roles call MC7_fnc_role;
    if (count _u == 0) exitWith { grpNull };
    private _g = ([west, 7] call MULTI_fnc_groupe);
    _u joinSilent _g;
    _g selectLeader (_u select 0);
    _g setVariable ["chacal_element", _nom, true];
    _g allowFleeing 0;
    (format ["CHACAL|E|scission|%1|%2|%3", round (time * 100) / 100, _nom, count _u]) call MC7_LOG;
    _g
};

if (MC7_IMMORTEL == 1) then {
    { _x allowDamage false } forEach MC7_FS;
    "CHACAL|AVERT|hors_corpus|immortel|1|couture_sous_le_feu" call MC7_LOG;
};

(format ["CHACAL|OK|blufor|%1|roles|%2", count MC7_FS,
    (MC7_FS apply { _x getVariable ["chacal_role", "?"] })]) call MC7_LOG;
