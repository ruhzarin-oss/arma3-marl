// =====================================================================
// PREVOL DU HARNAIS — CONTROLE N.0 : LA LATENCE ALLER-RETOUR
//
// Fable : « la voie se choisit sur ce nombre, pas sur un avis ». Critere pre-inscrit :
// mediane < 1 s, p99 < 3 s sur 100 allers-retours. Sous ce seuil, un cycle de decision
// de 4 s tient. Au-dessus, le harnais est a repenser AVANT d'ecrire quoi que ce soit.
//
// ENTREE  : la DLL hmt_ext_x64 lit C:\hmt_bridge\cmd_<N>.sqf au niveau OS. Pas de
//           -filePatching, pas de gel d'index.
// SORTIE  : diag_log vers le RPT, que Python suit depuis WSL par /mnt/c/...
// =====================================================================
diag_log format ["[PONT] extension : %1", ("hmt_ext" callExtension "version")];

HMT_n = 0;
[] spawn {
	diag_log "[PONT] actuateur demarre";
	while { true } do {
		private _next = HMT_n + 1;
		private _code = "hmt_ext" callExtension (str _next);
		if !(_code isEqualTo "") then {
			HMT_n = _next;
			call compile _code;
		};
		sleep 0.1;
	};
};

// battement de coeur : prouve que la mission vit meme si aucune commande n'arrive
[] spawn {
	private _k = 0;
	while { true } do { _k = _k + 1; diag_log format ["[PONT] HMT_SYNC %1 coeur %2", HMT_n, _k]; sleep 3; };
};
