// blufor_coquille_lambs.sqf — EXECUTEUR corrige, facon LAMBS taskRush.
// On ne coupe QUE AUTOCOMBAT+FSM -> le moteur garde visee/tir/path/anim (fini le 0 kill).
// Mouvement = doMove (piloté par le driver). Regles reactives de taskRush : tire->ralentis, supprime->posture.
if (isNil "HMT_EMIT") then { HMT_EMIT = { diag_log _this }; };
HMT_WAGENT_MODE = false;
if (isNil "HMT_WPILOT") then { HMT_WPILOT = []; };

// lecture : positions coquilles + total EAST vivants (pour voir les kills) + ennemis EAST connus
HMT_WREAD = {
    private _s = "";
    { private _u=_x; if (!isNull _u) then { private _p=getPosATL _u;
        private _ok=[0,1] select (alive _u && !(_u getVariable ["ACE_isUnconscious", false]));
        _s=_s+format ["%1,%2,%3,%4;", round (_p#0), round (_p#1), round ((damage _u)*100), _ok];
      } else { _s=_s+"0,0,100,0;"; }; } forEach HMT_WPILOT;
    private _en = (allUnits select { side _x==east && alive _x && (west knowsAbout _x > 1) }) apply { [round ((getPosATL _x)#0), round ((getPosATL _x)#1)] };
    private _east = {alive _x && side _x==east} count allUnits;
    (format ["HARMATTAN_WRX n=%1 mode=%2 east=%3 en=%4 | %5", count HMT_WPILOT, HMT_WAGENT_MODE, _east, _en, _s]) call HMT_EMIT;
};

// armement LAMBS-style : on garde le tir moteur, on ne pilote que la DESTINATION + regles reactives
HMT_WARM = {
    removeAllMissionEventHandlers "EachFrame"; HMT_WEF = nil;     // <-- TUE l'ancien pilotage velocite (sinon il fige tout)
    HMT_WPILOT = HMT_WPILOT select { !isNull _x && { alive _x } };
    { _x enableAI "ALL"; _x setBehaviour "AWARE"; _x setCombatMode "RED"; _x setSkill 0.7; _x setVariable ["HMT_WSHELL", true]; } forEach HMT_WPILOT;
    // corps LAMBS pret ; le RUN assigne les comportements LAMBS par element (taskRush/suppression/flanc/tenir)
    private _grps = []; { _grps pushBackUnique (group _x) } forEach HMT_WPILOT;
    HMT_WGRPS = _grps;
    HMT_WAGENT_MODE = true;
    (format ["HARMATTAN_WARM pilots=%1 grps=%2 mode=LAMBS-pret", count HMT_WPILOT, count _grps]) call HMT_EMIT;
};

HMT_WDISARM = {
    { if (!isNull _x) then { _x enableAI "AUTOCOMBAT"; _x enableAI "FSM"; _x forceSpeed -1; _x setVariable ["HMT_WSHELL", nil] } } forEach HMT_WPILOT;
    HMT_WAGENT_MODE = false; (format ["HARMATTAN_WDISARM ok"]) call HMT_EMIT;
};

(format ["HARMATTAN_WBRIDGE ok warm=%1 read=%2", !(isNil "HMT_WARM"), !(isNil "HMT_WREAD")]) call HMT_EMIT;
