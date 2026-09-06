// =====================================================================
// CHACAL - operation speciale entierement scriptee, LAMBS contre LAMBS.
// Dix forces speciales, un site de guerre electronique, six phases.
// Aucun joueur : la mission tourne sur serveur dedie et n existe que pour
// produire un CORPUS.
//
// L ordre de chargement n est pas negociable :
//   socle   -> le journal et le tirage existent avant tout le reste
//   monde   -> la geometrie, qui peut declarer l episode VOID
//   decor   -> les objectifs sont poses AVANT que la garnison s y garnisse
//   opfor   -> la garnison ; blufor -> les dix
//   capture -> l enregistreur, INSTALLE AVANT que quoi que ce soit bouge
//   verdict -> les canaris de l enregistreur, puis l issue
//   phases  -> et seulement alors, le temps commence
// =====================================================================
call compile preprocessFileLineNumbers "chacal\00_socle.sqf";
call compile preprocessFileLineNumbers "chacal\10_monde.sqf";
if (CHACAL_ISSUE == "VOID") exitWith {
    (format ["CHACAL|FINI|VOID|%1|graine|%2", CHACAL_CAUSE, CHACAL_GRAINE]) call CHACAL_LOG;
};
call compile preprocessFileLineNumbers "chacal\20_decor.sqf";
if (CHACAL_ISSUE == "VOID") exitWith {
    (format ["CHACAL|FINI|VOID|%1|graine|%2", CHACAL_CAUSE, CHACAL_GRAINE]) call CHACAL_LOG;
};
call compile preprocessFileLineNumbers "chacal\30_opfor.sqf";
call compile preprocessFileLineNumbers "chacal\40_blufor.sqf";
if (CHACAL_ISSUE == "VOID") exitWith {
    (format ["CHACAL|FINI|VOID|%1|graine|%2", CHACAL_CAUSE, CHACAL_GRAINE]) call CHACAL_LOG;
};
call compile preprocessFileLineNumbers "chacal\50_capture.sqf";
call compile preprocessFileLineNumbers "chacal\70_verdict.sqf";
call compile preprocessFileLineNumbers "chacal\60_phases.sqf";

(format ["CHACAL|OK|monte|%1|est|%2|ouest|%3|graine|%4|echelle|%5",
    CHACAL_VERSION, count CHACAL_EST_SITE, count CHACAL_FS,
    CHACAL_GRAINE, CHACAL_ECHELLE]) call CHACAL_LOG;
