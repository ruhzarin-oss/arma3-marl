#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-BANC-APPUI-2
#
# 1. LA FUITE DE JOURNAL. Mes boucles ( tactique, chien de garde, relance ) dorment 5 a 10 s ; quand l episode se
#    ferme pendant ce sommeil, elles ecrivent APRES la ligne FINI. La porte `rien_apres_fini` a refuse 17 episodes
#    sur 96 dans l ablation, dont 10 qui avaient pose leurs trois charges : la censure allait dans un seul sens.
#    Remede : apres chaque sommeil, on teste de nouveau CHACAL_FIN avant d ecrire quoi que ce soit.
#
# 2. LE CONTROLE POSITIF DE L APPUI, refait apres la revue adversariale ( quatre defauts bloquants sur la V1 ) :
#    . on ne DEPLACE PAS l appui : il reste a la position que la mission lui a donnee, celle du tournoi, sinon on
#      changerait deux choses a la fois et ni 0 ni 200 coups ne voudraient dire quelque chose ;
#    . on teste la vue vers les DEFENSEURS eux-memes, pas vers le centre du site ( qui est dans un batiment ) ;
#    . on oriente les tireurs vers leur cible ( setDir ) : un homme teleporte ou pose garde son cap ;
#    . deux bras : 1 = cloue comme dans le socle ( RED, PATH et LAMBS coupes ), 2 = NON cloue ( RED seul ),
#      pour que le contraste designe le coupable si l appui est muet ;
#    . l episode se ferme par exitWith EN TETE de phase 5 : rien ne s ecrit apres FINI ;
#    . on journalise par tireur : coups, cible vue ou non, distance, et le cap avant et apres.
#    Critere ecrit d avance ( Fable ) : l appui tire dans au moins 18 episodes sur 20. Sous 10 sur 20, le socle n a
#    que trois pieces et tout le tournoi des tactiques d appui est a refaire.
import sys

M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"
D = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis"
L = "/mnt/data/hmt/depot/bancs/chacal/lancer.sh"


def bilan(s): return (s.count("{") - s.count("}"), s.count("[") - s.count("]"), s.count("(") - s.count(")"))


def patch(path, avant, apres, quoi):
    s = open(path, encoding="utf-8", errors="surrogateescape").read()
    if s.count(avant) != 1:
        print("  !! motif x%d : %s" % (s.count(avant), quoi)); sys.exit(1)
    s2 = s.replace(avant, apres, 1)
    if path.endswith(".sqf") and bilan(s) != bilan(s2):
        print("  !! equilibre %s -> %s : %s" % (bilan(s), bilan(s2), quoi)); sys.exit(1)
    open(path, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE :", quoi)


if "CHACAL_BANC_APPUI" in open(f"{M}/00_socle.sqf", encoding="utf-8", errors="surrogateescape").read():
    print("  deja present"); sys.exit(0)

# --- 1. la fuite de journal : on re-teste CHACAL_FIN apres chaque sommeil -------------------
patch(f"{M}/00_socle.sqf",
      """                    (format ["CHACAL|E|chien_de_garde|%1|relance|%2|reste|%3", round (time * 100) / 100,
                            _rates, round _d]) call CHACAL_LOG;""",
      """                        if (CHACAL_FIN) exitWith {};   // ! rien apres la ligne FINI : la porte de lecture refuse l episode
                        (format ["CHACAL|E|chien_de_garde|%1|relance|%2|reste|%3", round (time * 100) / 100,
                            _rates, round _d]) call CHACAL_LOG;""",
      "00_socle : le chien de garde n ecrit plus apres FINI")

patch(f"{M}/00_socle.sqf",
      """                    (format ["CHACAL|E|suppression|%1|%2|distance_assaut|%3", round (time * 100) / 100,
                        (_cible getVariable ["chacal_id", -1]), round _dmax]) call CHACAL_LOG;""",
      """                    if (!CHACAL_FIN) then {
                        (format ["CHACAL|E|suppression|%1|%2|distance_assaut|%3", round (time * 100) / 100,
                            (_cible getVariable ["chacal_id", -1]), round _dmax]) call CHACAL_LOG;
                    };""",
      "00_socle : la suppression n ecrit plus apres FINI")

patch(f"{M}/00_socle.sqf",
      """                    (format ["CHACAL|E|cible_designee|%1|%2|restants|%3", round (time * 100) / 100,
                        (_derniere getVariable ["chacal_id", -1]), count _viv]) call CHACAL_LOG;""",
      """                    if (!CHACAL_FIN) then {
                        (format ["CHACAL|E|cible_designee|%1|%2|restants|%3", round (time * 100) / 100,
                            (_derniere getVariable ["chacal_id", -1]), count _viv]) call CHACAL_LOG;
                    };""",
      "00_socle : la designation n ecrit plus apres FINI")

# --- 2. le banc : l appui a SA place, deux bras, vue mesuree vers les defenseurs -------------
patch(f"{M}/00_socle.sqf",
      'CHACAL_TACTIQUE = ["CHACAL_TACTIQUE", 0] call BIS_fnc_getParamValue;',
      'CHACAL_TACTIQUE = ["CHACAL_TACTIQUE", 0] call BIS_fnc_getParamValue;\n'
      '// ! CONTROLE POSITIF DE L APPUI ( Fable, regle 16 ) : 0 non, 1 appui CLOUE comme dans le socle, 2 appui NON CLOUE.\n'
      '// L appui reste a SA position : on ne change qu une chose a la fois.\n'
      'CHACAL_BANC_APPUI = ["CHACAL_BANC_APPUI", 0] call BIS_fnc_getParamValue;\n'
      'CHACAL_TIRS_BANC = 0;',
      "00_socle : parametre BANC_APPUI")

patch(f"{M}/00_socle.sqf", "CHACAL_fnc_plat = {",
      '''// ! LE CONTROLE POSITIF DE L APPUI. Quatre mesures depuis le 10/09 ( feu avant, oracle, tournoi, ablation ) ont
// constate le meme appui inerte sous quatre noms : 0 coup sur 17 episodes du socle complet. Avant d empiler une
// cinquieme mesure, on certifie le mecanisme lui-meme, comme le veut la regle 16.
// L appui NE BOUGE PAS : il est mesure la ou la mission l a mis. Deux bras : cloue ( 1 ) et non cloue ( 2 ).
CHACAL_fnc_bancAppui = {
    private _app = (units CHACAL_gAppui) select { alive _x };
    private _def = CHACAL_EST_SITE select { alive _x };
    if (count _app == 0 || { count _def == 0 }) exitWith {
        (format ["CHACAL|E|banc_appui_fin|%1|coups|0|tireurs|%2|defenseurs|%3|cause|RIEN_A_MESURER",
            round (time * 100) / 100, count _app, count _def]) call CHACAL_LOG;
    };
    "CHACAL|AVERT|hors_corpus|banc_appui|episode_de_certification" call CHACAL_LOG;
    // l assaut et le bouchon ne jouent pas : on ne mesure QUE l appui
    {
        if (!isNull _x) then {
            _x setBehaviour "CARELESS"; _x setCombatMode "BLUE";
            { if (alive _x) then { doStop _x; _x disableAI "PATH"; _x disableAI "AUTOCOMBAT"; _x setUnitPos "DOWN" } } forEach (units _x);
        };
    } forEach [CHACAL_gAssaut, CHACAL_gBouchon];
    // la cible : le defenseur le plus proche de l appui, et on mesure ce que chaque tireur VOIT vraiment
    private _c0 = _app call CHACAL_fnc_centre;
    private _tri = [_def, [_c0], { _x distance2D _input0 }, "ASCEND"] call BIS_fnc_sortBy;
    private _cible = _tri select 0;
    {
        private _u = _x;
        _u setDir (_u getDir _cible);
        _u setUnitPos "MIDDLE";
        if (CHACAL_BANC_APPUI == 1) then {
            _u disableAI "PATH";
            _u setVariable ["lambs_danger_disableAI", true, true];
        };
        { _u reveal [_x, 4] } forEach _def;
        _u addEventHandler ["Fired", { CHACAL_TIRS_BANC = CHACAL_TIRS_BANC + 1; (_this select 0) setVariable ["banc_tirs", ((_this select 0) getVariable ["banc_tirs", 0]) + 1] }];
        private _oeil = eyePos _u;
        private _vu = { count (lineIntersectsSurfaces [_oeil, aimPos _x, _u, _x, true, 1]) == 0 } count _def;
        (format ["CHACAL|E|banc_appui_poste|%1|%2|role|%3|distance_cible|%4|defenseurs_vus|%5|sur|%6|connait|%7",
            round (time * 100) / 100, (_u getVariable ["chacal_id", -1]), (_u getVariable ["chacal_role", ""]),
            round (_u distance _cible), _vu, count _def, round ((_u knowsAbout _cible) * 100) / 100]) call CHACAL_LOG;
    } forEach _app;
    CHACAL_gAppui setBehaviour "COMBAT"; CHACAL_gAppui setCombatMode "RED";
    if (CHACAL_BANC_APPUI == 1) then { CHACAL_gAppui setVariable ["lambs_danger_disableGroupAI", true, true] };
    { if (alive _x) then { _x doWatch _cible; _x doTarget _cible; _x doFire _cible } } forEach _app;
    private _t0 = time; private _morts0 = { !alive _x } count CHACAL_EST_SITE;
    while { (time - _t0) < (300 * CHACAL_ECHELLE) && { !CHACAL_FIN } } do {
        sleep 10;
        private _viv = CHACAL_EST_SITE select { alive _x };
        private _a = (units CHACAL_gAppui) select { alive _x };
        if (count _viv == 0 || { count _a == 0 }) exitWith {};
        private _c = _viv select 0;
        { _x reveal [_c, 4]; _x doWatch _c; _x doTarget _c; _x doFire _c } forEach _a;
    };
    private _detail = "";
    { _detail = _detail + format ["%1:%2 ", (_x getVariable ["chacal_role", ""]), (_x getVariable ["banc_tirs", 0])] } forEach _app;
    (format ["CHACAL|E|banc_appui_fin|%1|coups|%2|par_tireur|%3|defenseurs_tues|%4|duree|%5|appui_vivant|%6|cloue|%7",
        round (time * 100) / 100, CHACAL_TIRS_BANC, _detail,
        ({ !alive _x } count CHACAL_EST_SITE) - _morts0, round (time - _t0),
        count ((units CHACAL_gAppui) select { alive _x }), CHACAL_BANC_APPUI]) call CHACAL_LOG;
};

CHACAL_fnc_plat = {''', "00_socle : le banc d appui, l appui a sa place, deux bras")

# --- 3. branchement EN TETE de phase 5, avec exitWith ---------------------------------------
patch(f"{M}/60_phases.sqf",
      "// ! LE SOCLE ET LA TACTIQUE ( document du 11/09 ). Le socle repare l execution, la tactique conduit l appui.\nif (CHACAL_SOCLE == 1) then { call CHACAL_fnc_socleAssaut };",
      '''// ! CONTROLE POSITIF DE L APPUI : l episode ne mesure QUE l appui et se ferme ici. L exitWith est indispensable :
// sans lui, toute la suite de la phase 5 s ecrirait APRES la ligne FINI et la porte de lecture refuserait l episode.
if (CHACAL_BANC_APPUI > 0) exitWith {
    call CHACAL_fnc_bancAppui;
    [5, "ASSAUT", "BANC_APPUI"] call CHACAL_fnc_finPhase;
    CHACAL_FIN = true;
};
// ! LE SOCLE ET LA TACTIQUE ( document du 11/09 ). Le socle repare l execution, la tactique conduit l appui.
if (CHACAL_SOCLE == 1) then { call CHACAL_fnc_socleAssaut };''',
      "60_phases : le banc se branche et ferme l episode")

# --- 4. la ligne FINI ------------------------------------------------------------------------
patch(f"{M}/70_verdict.sqf", '|ablation|%41",', '|ablation|%41|banc_appui|%42|tirs_banc|%43",', "70_verdict : format FINI")
patch(f"{M}/70_verdict.sqf", "CHACAL_ZONES, CHACAL_ABLATION]) call CHACAL_LOG;",
      "CHACAL_ZONES, CHACAL_ABLATION, CHACAL_BANC_APPUI, CHACAL_TIRS_BANC]) call CHACAL_LOG;", "70_verdict : valeurs FINI")

patch(f"{D}/description.ext", '    class CHACAL_ABLATION\n', '''    // ! CONTROLE POSITIF DE L APPUI ( regle 16 ) : 1 cloue comme dans le socle, 2 non cloue. L appui reste a sa place.
    class CHACAL_BANC_APPUI
    {
        title = "Controle positif de l appui : 0 non, 1 cloue, 2 non cloue";
        values[] = {0,1,2};
        texts[]  = {"NON","CLOUE","NON CLOUE"};
        default = 0;
    };
    class CHACAL_ABLATION
''', "description.ext")
patch(L, 'ABLATION=$(lit ablation 0);', 'BANC_APPUI=$(lit banc_appui 0); ABLATION=$(lit ablation 0);', "lancer.sh : lecture")
patch(L, 'ecrire_param ABLATION "$ABLATION";', 'ecrire_param BANC_APPUI "$BANC_APPUI"; ecrire_param ABLATION "$ABLATION";', "lancer.sh : ecriture")
