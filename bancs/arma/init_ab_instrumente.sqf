// A/B INSTRUMENTE — criteres dans CRITERES_AB_INSTRUMENTE.md, deposes avant toute donnee.
// Quatre bras tires au sort a chaque accrochage : frontal · deux axes · les deux en mode FIGE.
// Le mode FIGE est le CONTROLE POSITIF (A2) : defenseurs regardant l axe 1 et n en bougeant
// pas. Le deux-axes DOIT y ecraser le frontal, sinon l instrument est casse et A1 illisible.
if (isServer) then {
    HMT_LOG = { diag_log _this };
    [] spawn { sleep 8; [2, 600, 2, false] execVM "generateur_engagements_v12.sqf"; };
};
