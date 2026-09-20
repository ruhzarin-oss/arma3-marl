// =====================================================================
// CHACAL - LES CONTROLES DE L ORACLE ( plan a139c63 § 7, regle 16 ).
//
// POURQUOI. Un adversaire qui chasse doit pouvoir ETRE PRIS EN DEFAUT, sinon sa mesure ne vaut rien :
//   - controle POSITIF ( 1 ) : si on lui amene le detachement a 100 m, de jour, il DOIT l intercepter.
//     Une interception < 90 % veut dire que le canal par lequel il punit est bouche, et que tout
//     resultat nul de la campagne est un plancher d instrument, pas une absence d effet.
//   - controle de NON-TRICHE ( 3 ) : on teleporte le detachement dans une case lointaine en cours
//     d episode. Sa croyance NE DOIT PAS suivre avant une detection legitime. C est le seul controle
//     qui prouve qu il ne lit pas nos positions vraies.
//
// Ce fichier ne touche PAS a la logique de l Oracle : il agit sur le monde, et journalise. Il est charge
// apres 45_oracle.sqf pour disposer de CHACAL_O_CASES et de CHACAL_O_B.
// =====================================================================
if (CHACAL_ORACLE_CTRL <= 0) exitWith {};

// --- 3 : NON-TRICHE. On deplace NOS hommes, sans rien dire a personne. ---
if (CHACAL_ORACLE_CTRL == 3) then {
    if (CHACAL_ORACLE_CMD <= 0) exitWith {
        (format ["CHACAL|O|ctrl|erreur|%1|cause|NON_TRICHE_SANS_ORACLE", round (time * 100) / 100]) call CHACAL_LOG;
    };
    [] spawn {
        waitUntil { sleep 2; CHACAL_FIN || { !isNil "CHACAL_TPHASE" } };
        sleep (150 * CHACAL_ECHELLE);
        if (CHACAL_FIN) exitWith {};
        private _vivants = CHACAL_FS select { alive _x };
        if (count _vivants == 0) exitWith {};
        private _chef = _vivants select 0;
        private _pA = getPosATL _chef;
        // la case d ou l on part, et la case la plus LOINTAINE : le saut doit etre gros pour etre lisible
        private _dep = [_pA] call CHACAL_O_fnc_caseLaPlusProche;
        // ! LA CASE D ARRIVEE EXCLUT LE SITE ET SES ABORDS. Fumee du 20/09 a 15 h 55 : la case la plus lointaine
        // etait TOUJOURS le SITE, c est a dire la garnison elle-meme. Nos hommes y etaient vus en quelques secondes,
        // la fenetre d observation du controle se fermait aussitot, et le controle ne pouvait plus echouer.
        // Un controle qui ne peut pas echouer ne mesure rien ( regle 16 ).
        private _d = CHACAL_O_CASES apply { (_x select 1) distance2D _pA };
        { if (_forEachIndex in [5, 6]) then { _d set [_forEachIndex, -1] } } forEach _d;
        private _arr = _d find (selectMax _d);
        private _pB = (CHACAL_O_CASES select _arr) select 1;
        private _saut = round (_pA distance2D _pB);
        (format ["CHACAL|O|ctrl|teleport_avant|%1|de|%2|vers|%3|i_arr|%4|saut|%5|p_arr|%6|croyance|%7",
            round (time * 100) / 100, (CHACAL_O_CASES select _dep) select 0,
            (CHACAL_O_CASES select _arr) select 0, _arr, _saut,
            round ((CHACAL_O_B select _arr) * 100),
            str (CHACAL_O_B apply { round (_x * 100) })]) call CHACAL_LOG;
        // on garde la formation : chacun conserve son ecart au chef
        {
            private _ec = (getPosATL _x) vectorDiff _pA;
            _x setPosATL [(_pB select 0) + (_ec select 0), (_pB select 1) + (_ec select 1), 0];
        } forEach _vivants;
        sleep 2;
        (format ["CHACAL|O|ctrl|teleport_apres|%1|case_reelle|%2|croyance|%3",
            round (time * 100) / 100,
            (CHACAL_O_CASES select ([getPosATL _chef] call CHACAL_O_fnc_caseLaPlusProche)) select 0,
            str (CHACAL_O_B apply { round (_x * 100) })]) call CHACAL_LOG;
    };
};

// --- 1 : POSITIF. On amene la patrouille sur eux, de jour, a decouvert. Elle doit les prendre. ---
if (CHACAL_ORACLE_CTRL == 1) then {
    [] spawn {
        waitUntil { sleep 2; CHACAL_FIN || { !isNil "CHACAL_TPHASE" } };
        sleep (30 * CHACAL_ECHELLE);
        if (CHACAL_FIN) exitWith {};
        private _vivants = CHACAL_FS select { alive _x };
        if (count _vivants == 0 || { isNull CHACAL_VEH_ROUTE }) exitWith {
            (format ["CHACAL|O|ctrl|erreur|%1|cause|POSITIF_SANS_PATROUILLE", round (time * 100) / 100]) call CHACAL_LOG;
        };
        private _chef = _vivants select 0;
        // la route goudronnee la plus proche d eux, a moins de 400 m : on y pose le vehicule
        private _rs = (getPosATL _chef) nearRoads 400;
        private _p = if (count _rs > 0) then { getPosATL (_rs select 0) } else { _chef getPos [100, random 360] };
        CHACAL_VEH_ROUTE setPosATL _p;
        private _dist = round ((getPosATL _chef) distance2D _p);
        { _x setUnitPos "UP" } forEach _vivants;
        (format ["CHACAL|O|ctrl|positif|%1|patrouille_a|%2|hommes|%3|route|%4",
            round (time * 100) / 100, _dist, count _vivants,
            (if (count _rs > 0) then {1} else {0})]) call CHACAL_LOG;
    };
};
