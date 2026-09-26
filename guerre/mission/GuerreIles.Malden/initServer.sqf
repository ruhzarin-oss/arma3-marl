// =====================================================================
// GUERREILES.MALDEN — le serveur de la guerre des iles (instance 10).
//
// L actuateur et le battement sont ceux du LABO (labo/mission.Altis), a l identique : le module
// guerre/arma.py parle par la meme Liaison (labo/arma_labo.py), avec ses recus et ses pannes.
// Le commandant ne part qu une fois Warlords pret (secteurs et deux bases poses).
// =====================================================================
diag_log format ["[LABO] extension : %1", ("hmt_ext" callExtension "version")];
call compile preprocessFileLineNumbers "fonctions.sqf";
diag_log format ["[LABO] fonctions version %1", (if (isNil "GUERRE_VERSION") then {0} else {GUERRE_VERSION})];

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

[] spawn {
	waitUntil {
		sleep 1;
		(!isNil "BIS_WL_sectors")
		&& { !isNull (missionNamespace getVariable ["BIS_WL_base_WEST", objNull]) }
		&& { !isNull (missionNamespace getVariable ["BIS_WL_base_EAST", objNull]) }
	};
	diag_log format ["[LABO] guerre prete : %1 zones, escouade %2 points, vehicule %3 points", count BIS_WL_sectors, GUERRE_COUT_ESCOUADE, GUERRE_COUT_VEHICULE];
	[] call GUERRE_fnc_commandant;
};
