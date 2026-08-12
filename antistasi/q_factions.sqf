// Demande au serveur quelles factions il accepte, et l'etat du demarrage.
diag_log format ["Q_ETAT startup=%1 saveData=%2 setupPlayer=%3",
    missionNamespace getVariable ["A3A_startupState", "?"],
    !isNil "A3A_saveData",
    !isNull (missionNamespace getVariable ["A3A_setupPlayer", objNull])];

private _t = "true" configClasses (configFile/"A3A"/"Templates");
diag_log format ["Q_NB_TEMPLATES %1", count _t];

// on ne garde que celles dont les addons requis sont presents
private _ok = _t select { (getArray (_x/"requiredAddons") findIf { !(isClass (configFile/"CfgPatches"/_x)) }) == -1 };
diag_log format ["Q_TEMPLATES_OK %1", count _ok];
{
    diag_log format ["Q_TPL|%1|%2|%3", configName _x, getText (_x/"name"), getNumber (_x/"side")];
} forEach _ok;

diag_log format ["Q_HQ_MARKER %1", markerPos "Synd_HQ"];
