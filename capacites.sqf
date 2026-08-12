// capacites.sqf — DEMANDER SI UN HOMME PEUT, AVANT DE LUI ORDONNER.
//
// ⟨Younes, 09/08 : « reprends canFight canMove unitReady dans nos bancs »⟩
//
// ═══ POURQUOI, ET CE QUE ÇA A COÛTÉ DE NE PAS L'AVOIR ═══
//
// Antistasi vérifie systématiquement qu'un homme PEUT faire ce qu'on lui demande avant de le
// lui demander : `canFight` 21 fois, `canMove` 71 fois, `unitReady` 32 fois dans leur code.
// Chez nous : zéro. On ordonne, et on suppose.
//
// La nuit du 08 au 09/08 a payé cette absence trois fois, et toujours de la même façon —
// UN BANC QUI PRODUIT DES ZÉROS CRÉDIBLES AU LIEU DE DIRE QU'IL EST EN PANNE :
//   · trois essais francs puis dix-huit à zéro : les fusils étaient vides, personne ne le
//     disait. Mon premier contrôle demandait `someAmmo`, qui répond « oui » pour une grenade.
//   · 480 tirs refusés sur 480 : l'arme pointait à 55° de la cible, parce que j'avais coupé
//     `MOVE` — un homme qui ne peut pas bouger ne peut pas tourner. Rien ne me l'a dit.
//   · un professeur qui piétinait : `doStop` jamais relâché, deux équipes qui alternaient sans
//     avancer pendant quatre-vingt-dix accrochages.
//
// Dans les trois cas, la question « cet homme peut-il faire ce que je lui demande ? » avait une
// réponse dans le moteur, et personne ne la posait.
//
// ═══ CE QUE CE FICHIER AJOUTE ═══
// Non pas des garde-fous qui corrigent en silence — ça masquerait la panne au lieu de la dire —
// mais un RECENSEMENT journalisé à chaque essai : combien d'hommes pouvaient se battre, tirer,
// bouger, et étaient prêts à recevoir un ordre. Un banc doit savoir dire « je me suis éteint ».
//
// ⚠️ AUCUN DE CES COMPTEURS NE CORRIGE QUOI QUE CE SOIT. Ils constatent. Le dépouillement
// refuse le verdict si le recensement montre que les hommes ne pouvaient pas obéir — de la
// même façon qu'il le refuse quand un contrôle tombe. Une panne constatée vaut mieux qu'un
// zéro plausible.
//
// ⟨repris de A3A_fnc_canFight · MIT · Copyright (c) 2023 Antistasi Ultimate Team⟩

// ─────────────────────────────────────────── cet homme est-il encore dans le combat ?
HMT_PEUT_COMBATTRE = {
    params ["_u"];
    if (isNull _u) exitWith { false };
    if (!alive _u) exitWith { false };
    if (captive _u) exitWith { false };
    if ((lifeState _u) isEqualTo "INCAPACITATED") exitWith { false };
    true
};

// ─────────────────────────────────────────── peut-il tirer, MAINTENANT, avec son arme ?
// `canFire` dit que l arme n est pas detruite. Il ne dit RIEN des munitions : c est la
// distinction qui m a echappe toute la nuit. On demande les deux.
HMT_PEUT_TIRER = {
    params ["_u"];
    if !([_u] call HMT_PEUT_COMBATTRE) exitWith { false };
    if (!(canFire _u)) exitWith { false };
    if ((_u ammo (primaryWeapon _u)) <= 0) exitWith { false };
    true
};

// ─────────────────────────────────────────── peut-il se deplacer, ET tourner ?
// `canMove` couvre le vehicule detruit. Mais un fantassin a qui l on a coupe l IA « MOVE » ne
// peut pas PIVOTER non plus, et `canMove` l ignore — c est ce qui a produit 55° d ecart de
// visee. On teste donc aussi l automatisme, qui est de notre fait.
HMT_PEUT_BOUGER = {
    params ["_u"];
    if !([_u] call HMT_PEUT_COMBATTRE) exitWith { false };
    if (!(canMove _u)) exitWith { false };
    if (_u checkAIFeature "MOVE" isEqualTo false) exitWith { false };
    true
};

// ─────────────────────────────────────────── a-t-il fini son ordre precedent ?
// `unitReady` est faux tant qu un ordre est en cours. Un homme jamais pret est un homme qui
// n arrive jamais — le motif exact du professeur qui pietinait.
HMT_EST_PRET = {
    params ["_u"];
    if !([_u] call HMT_PEUT_COMBATTRE) exitWith { false };
    unitReady _u
};

// ─────────────────────────────────────────── le recensement, a journaliser par essai
// Rend [combattants, tireurs, mobiles, prets] sur la liste donnee.
HMT_RECENSER = {
    params ["_liste"];
    private _c = 0; private _t = 0; private _m = 0; private _p = 0;
    {
        if ([_x] call HMT_PEUT_COMBATTRE) then { _c = _c + 1 };
        if ([_x] call HMT_PEUT_TIRER)     then { _t = _t + 1 };
        if ([_x] call HMT_PEUT_BOUGER)    then { _m = _m + 1 };
        if ([_x] call HMT_EST_PRET)       then { _p = _p + 1 };
    } forEach _liste;
    [_c, _t, _m, _p]
};

"HMT|CAP|capacites_chargees|1" call HMT_LOG;
