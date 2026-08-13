// ETAGE 1 DU GESTE N2 - CAMPAGNE REDEPOSEE, SESSION 1.
// Les 48 essais des quatre sessions precedentes sont des PARTIELS : ils ont DIMENSIONNE les
// nouveaux seuils, ils ne certifient rien et ne se relisent pas sous ce protocole.
// Le protocole precedent est mort de ses controles : tous des MINIMA sur des essais
// individuels, donc affirmant une probabilite de defaut NULLE, quand la sonde radio du 10/08
// a MESURE ~8 % de rate silencieux. Un seul essai pathologique condamnait alors quatre
// sessions sans recours. Les controles vivent desormais en DEUX FAMILLES : accord
// d instrument (absolu par essai) et presence d un phenomene (en TAUX, au niveau du TERRAIN,
// qui est le niveau que la decision emploie).
// ⚠️ POURQUOI UNE QUATRIEME. La session 2 a rendu, sur le terrain 4, un couple ou LES DEUX
// bras delivrent ZERO impact : un rapport 0 sur 0, indefini. Le controle « le temoin delivre »
// est tombe, et aucun verdict n a ete prononce sur les trois sessions.
// On n EXCLUT PAS cet essai — l ecarter apres l avoir vu est exactement ce que la regle
// deposee interdit. On AJOUTE une repetition, et on l ajoute SUR LES SIX TERRAINS, pas sur le
// seul qui gene : une reparation qui ne viserait que le terrain fautif serait un tri deguise.
// ⟨R13 : n ajoute que de la donnee, s applique symetriquement, se registre⟩
// Chaque session joue UNE repetition par terrain et par bras. Trois sessions donnent les trois
// repetitions, et la stabilite inter-session se lit sur le RATIO qui decide — gratuitement.
// Plus d admission par ligne de base : ce test etait une porte a pile ou face.
// Six terrains ; le septieme (4648,6996) sort pour un motif legitime — son temoin delivre
// ZERO deux fois, ce qui rend le ratio indefini.
if (isServer) then {
    HMT_LOG = { diag_log _this };
    HMT_PHASE = 3;
    HMT_SESSION = 2;
    HMT_CANDIDATS = [
        [1734,5391,0], [3416,5931,0], [4601,4431,0],
        [4783,5298,0], [2172,4643,0], [3450,6750,0]
    ];
    [] spawn { sleep 5; execVM "banc_appui.sqf"; };
};
