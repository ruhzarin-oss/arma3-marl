// ═══ GESTE N°2 — CALIBRAGE AVEUGLE DU MONDE ═══
// L aiguille etait au butoir : 84,4 % de prise au temoin, hors de la bande 20-80 %.
// On balaie l effectif defenseur (4 a 14) et on lira a quel reglage le taux de prise retombe
// dans la bande. UN SEUL BRAS — le temoin. On regle le monde, on ne compare rien, et aucun
// verdict ne sortira de ce run.
if (isServer) then {
    HMT_LOG = { diag_log _this };
    // ⚠️ UNE EMPREINTE, PAS UNE ETIQUETTE — somme de controle du monde, LUE et non tapee.
    // empreinte.sqf est ecrit par empreindre.py et EXCLU de son propre calcul.
    // Chemin relatif a la mission : lisible sans -filePatching.
    private _emp = "REPLI-NON-LU";
    if (fileExists "empreinte.sqf") then {
        _emp = call compile preprocessFileLineNumbers "empreinte.sqf";
    };
    (format ["HMT|G|EMPREINTE|%1|%2", _emp, str (getMissionConfigValue "")]) call HMT_LOG;
    HMT_A2PUR = false; HMT_BOND = false;
    HMT_APPUI = true;
    HMT_APPUI_CE = false;
    // ---- LE BALAYAGE EST TERMINE ET LU. 268 accrochages, onze reglages tous lisibles.
    // Le monde est desormais CALIBRE : 13 defenseurs, taux de prise 65 %, dans la bande 20-80.
    // Le banc repasse donc a DEUX BRAS - professeur contre temoin - ce que le calibrage
    // interdisait ("un seul bras : on regle le monde, on ne compare rien").
    HMT_CALIBRE = false;
    HMT_NDEF = 13;
    // BANC DU COUT : meme monde calibre que le n°2 (13 defenseurs, prise 65 %, aiguille dans
    // la bande), plus le temoin de PROGRESSION. Aucun verdict de mission ne sort d ici : ce
    // banc sert a refaire UN SURSITAIRE, le cout par metre gagne.
    [] spawn { sleep 8; [6, 420, 2, false, false, 1.5, 3.0] execVM "generateur_engagements_v12.sqf"; };
};
