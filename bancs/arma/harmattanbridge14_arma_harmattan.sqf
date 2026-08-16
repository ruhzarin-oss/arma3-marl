// arma_harmattan.sqf — côté IN-GAME de l'adaptateur Arma 3 -> Harmattan.
// À charger dans une mission (init.sqf), puis appeler HMT_emit sur tes événements scénarisés.
// Le watcher Python (arma_adapter.py ingest <RPT> --follow) lit ces lignes du log RPT.
//
// Le RPT se trouve (Linux/Proton) typiquement sous :
//   ~/.steam/steam/steamapps/compatdata/107410/pfx/.../Arma 3/*.rpt
//   (ou dossier "Arma 3" de l'utilisateur Windows simulé)
//
// ⚠️ Template de départ — l'échappement JSON en SQF est délicat, à valider in-game.

HMT_emit = {
    params ["_id", "_kind", "_t", "_grid", "_desc", "_actors", "_truth"];
    private _actorsJson = "[" + ((_actors apply {"""" + _x + """"}) joinString ",") + "]";
    private _json = format [
        "{""scenario"":""%1"",""id"":%2,""kind"":""%3"",""t"":""%4"",""grid"":""%5"",""desc"":""%6"",""actors"":%7,""truth"":""%8""}",
        missionName, _id, _kind, _t, _grid, _desc, _actorsJson, _truth
    ];
    diag_log format ["HARMATTAN %1", _json];
};

// --- exemples d'émission (à déclencher par triggers/scripts de scénario) ---
// Drone qui détecte un convoi :
// [1, "IMINT", "08:42", "034 097", "Drone : convoi de 4 vehicules", ["groupe arme inconnu"], "convoi_reel"] call HMT_emit;
// Source humaine fiable :
// [2, "HUMINT", "09:10", "041 088", "Reunion entre deux chefs de faction", ["faction A","faction B"], "reunion_reelle"] call HMT_emit;
// Source qui ment (pour tester la gestion d'une source peu fiable) :
// [3, "HUMINT", "09:15", "050 070", "Colonne blindee massive (non confirme)", ["armee"], "FAUX_rumeur"] call HMT_emit;
