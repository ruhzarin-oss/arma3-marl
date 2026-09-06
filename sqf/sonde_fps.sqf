// Sonde de FPS serveur — sert de cas d essai au deploiement.
// Ce commentaire DOIT disparaitre a la copie : `call compile` ne le retire pas.
private _u = "http://exemple//chemin";   /* une URL dans une chaine : elle doit SURVIVRE */
format ["HMTFPS %1 %2", round (diag_fps * 10), count allUnits] call HMT_EMIT;
