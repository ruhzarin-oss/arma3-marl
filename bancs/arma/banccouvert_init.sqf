// GESTE N°3 — certification des lieux. Criteres : PROTOCOLE_GESTE3_LIEUX.md, depose avant.
if (isServer) then { HMT_LOG = { diag_log _this }; [] spawn { sleep 5; execVM "certif3.sqf"; }; };
