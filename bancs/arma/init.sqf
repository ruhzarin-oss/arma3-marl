// A/B INSTRUMENTE — le run reel. Criteres : CRITERES_AB_INSTRUMENTE.md, deposes avant.
// Reglage retenu par le CALIBRAGE AVEUGLE (95 accrochages, un seul bras, journaux coupes) :
//   rapport de force 1,5 a 3,0 -> ~50 % de resolution, dans la fenetre deposee 40-60 %.
// Charge INCHANGEE depuis le calibrage (6 accrochages simultanes) : on ne peut pas separer
// l effet du ratio de celui de la charge, donc on ne change pas la charge.
// Deux bras pleins (40/40) + A2 en tranche de controle a 20 %.
if (isServer) then {
    HMT_LOG = { diag_log _this };
    // BANC A2 DEDIE — 100 % fige, deux bras. Voir CRITERES_BANC_A2_DEDIE.md.
    // Remettre a false pour retrouver l A/B 40/40/20.
    HMT_A2PUR = true;
    [] spawn { sleep 8; [6, 420, 2, false, false, 1.5, 3.0] execVM "generateur_engagements_v12.sqf"; };
};
