// ═══ GESTE N°3 — PRISE DE COUVERT SOUS LE FEU : LA PORTE 0 DU LIEU ═══
// Criteres : CRITERES_GESTE3_COUVERT.md (08/08) et PROTOCOLE_GESTE3_LIEUX.md (10/08, redepose).
//   professeur : l equipe se jette a couvert au premier tir proche, se couche, repart apres 10 s
//   temoin     : elle continue debout, meme axe, meme lieu, meme effectif
//   grandeur   : LES PERTES — la survie de l equipe a la traversee
//   porte      : 10 POINTS — c est un LIEU qu on certifie
//   lecture    : SUR LA BORNE de l intervalle ⟨regle 14 : une porte se depose avec sa lecture⟩
// Sept lieux certifies le 10/08 sous protocole redepose, trois chemins de mesure concordants.
if (isServer) then {
    HMT_LOG = { diag_log _this };
    (format ["HMT|G|EMPREINTE|%1|%2", "9365bf13a86d9d74", str (getMissionConfigValue "")]) call HMT_LOG;
    HMT_A2PUR = false; HMT_BOND = false; HMT_APPUI = false;
    HMT_COUVERT3 = true;
    // ---- SON PROPRE BALAYAGE. LA CALIBRATION DU 10/08 NE VAUT PAS ICI.
    // On a cru qu un seul balayage servirait deux gestes : "chaque geste y lit SA bande sur SA
    // grandeur". C est faux, et la raison est dans le generateur, pas dans la statistique.
    // Le balayage a tourne sous HMT_APPUI, qui FIXE l effectif attaquant a 8 ET impose la
    // distance certifiee. Ce banc-ci ne fait ni l un ni l autre : il a rendu 16 attaquants et
    // une distance tiree entre 200 et 400 m des son premier accrochage. La colonne SURVIE que
    // j ai lue decrit donc le monde du geste n2, pas celui-ci.
    // R15 : la calibration heritee est NULLE. Ce geste balaie son propre monde.
    // Un seul bras pendant le balayage : on regle le monde, on ne compare rien.
    HMT_CALIBRE = true;
    HMT_C3_CE = false;
    // LE CANAL PROPRE DU GESTE N3, dans SON fichier. Une copie du generateur ne peut
    // plus l emporter — c est exactement ce qui l a detruit le 10/08.
    [] spawn { sleep 10; execVM "couvert_c3.sqf"; };
    [] spawn { sleep 8; [6, 420, 2, false, false, 1.5, 3.0] execVM "generateur_engagements_v12.sqf"; };
};
