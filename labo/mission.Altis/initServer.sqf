// =====================================================================
// LABO.ALTIS — la mission du LABO (instance 9). Elle ne mesure rien.
//
// Elle n'exécute que ce que labo/arma_labo.py écrit dans C:\hmt_bridge\i9\cmd_<N>.sqf, lu par
// la DLL hmt_ext au niveau OS (pas de gel d'index). Retour par diag_log vers le RPT.
//
// DEUX DIFFÉRENCES AVEC L'ACTUATEUR DE PONTTEST, toutes deux payées :
//   1. Chaque commande tourne dans SON fil (spawn). Une commande qui boucle ou qui dort ne fige
//      plus l'actuateur, et `sleep` y est permis (nettoyer en a besoin).
//   2. HMT_n avance AVANT l'exécution : une commande qui ne compile pas ne bloque pas la suite.
//      Python le voit au battement (n avancé, pas de reçu) et le dit : SansRecu.
//
// Le battement répète le compteur toutes les 2 s : Python ouvre le RPT à la fin et doit pouvoir
// se caler sans avoir vu ce qui précède.
// =====================================================================
diag_log format ["[LABO] extension : %1", ("hmt_ext" callExtension "version")];
call compile preprocessFileLineNumbers "fonctions.sqf";
diag_log format ["[LABO] fonctions version %1", (if (isNil "LABO_VERSION") then {0} else {LABO_VERSION})];

HMT_n = 0;
[] spawn {
	diag_log "[LABO] actuateur demarre";
	while { true } do {
		private _next = HMT_n + 1;
		private _code = "hmt_ext" callExtension (str _next);
		if !(_code isEqualTo "") then {
			HMT_n = _next;
			[_code] spawn { call compile (_this select 0); };
		};
		sleep 0.1;
	};
};

[] spawn {
	private _k = 0;
	while { true } do {
		_k = _k + 1;
		diag_log format ["[LABO] HMT_SYNC %1 coeur %2", HMT_n, _k];
		sleep 2;
	};
};
