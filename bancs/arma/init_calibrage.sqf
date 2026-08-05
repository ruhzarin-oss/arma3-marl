// CALIBRAGE AVEUGLE du rapport de force.
// UN SEUL BRAS (frontal) : la comparaison entre bras est IMPOSSIBLE, pas seulement interdite.
// Journaux lourds coupes — on ne mesure QUE le taux de resolution.
// Plage de ratio LARGE (0,7 a 3,0) : un seul passage balaye tout, au lieu de trois reglages.
// Cible deposee dans l en-tete du generateur AVANT cette nuit : 40 a 60 % de resolus.
if (isServer) then {
    HMT_LOG = { diag_log _this };
    [] spawn { sleep 8; [6, 420, 1, false, true, 0.7, 3.0] execVM "generateur_engagements_v12.sqf"; };
};
