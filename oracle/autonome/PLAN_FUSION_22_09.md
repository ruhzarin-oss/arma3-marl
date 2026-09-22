# Plan — fusionner l'Architecte et l'Oracle en un seul duel qui apprend (22/09/2026)

*Demande de Younes, 22/09 16 h 20 : « il ne faut pas faire comme ça, il faut fusionner Architecte et Oracle » ; puis
« rédige le plan et soumets-le à Fable ». Rien n'est codé ni lancé avant l'avis.*

## 1. Où on en est (faits mesurés)

**La boucle** (`depot/oracle/autonome/`, en service depuis le 21/09) :
- **Oracle** : imagination = 10 modèles logistiques L2 bootstrap (armes × option), 20 000 situations imaginées par
  itération, propose 8 exploitations (regret imaginé de la règle courante), 4 explorations, 2 confirmations ; chaque
  situation est jouée sous les deux options (paires) sur deux mondes. Sur l'itération 12 : Brier 0,22 contre 0,30 pour la
  constante (il voit mieux que le hasard) ; 3 313 pièges jouables imaginés, 31 à confirmer, 1 confirmé (Fisher).
  Motif prospectif confirmé : « poste proche (`menace_p2` = 5) → attendre sauve », 51 % contre 38 % sur 283 épisodes
  (cumul ; il fondait de 17 à 8 points après confirmation).
- **Architecte** : une règle perception → option (`constante`, `lineaire`, `formule` EvoGP), réapprise toutes les 2
  itérations, adoptée si elle bat la courante sur des mondes neufs (IC bootstrap par monde, Bonferroni). Règle en place :
  « toujours traverser ». Équation plate (EvoGP à fond : P = 0,10). **Gelé depuis le 22/09 11 h 55** par la confirmation.
- **Avis de Fable du 22/09 (étape 0)** : la vraie concurrente est « toujours attendre » (−0,069 apparié sur 304 paires) ;
  plafond en vérité « attendre ssi poste proche » −0,013 [−0,032 ; +0,003] → la perception n'est pas le goulot ; porte
  d'adoption aveugle (effet réaliste adopté 3 fois sur 20) ; corrélation intra-paire 0,38 (test apparié adopté).
- **Confirmation de « toujours attendre »** (`CONFIRMATION_ATTENDRE.md`) : 480 paires futures, un seul regard,
  sign-flip unilatéral α 0,05, contrôles négatif et positif avant lecture ; **22 / 480** à 16 h (≈ 12 paires par
  itération, ≈ 1 itération par heure → ~38 h de ferme restantes).
- 1 725 épisodes utilisables, compromission 0,248 ; « toujours traverser » 0,257, « toujours attendre » 0,223.

**Le banc** : épisode multiple `chacalmulti` en service derrière la boucle depuis 14 h 05 (multiplexeur) : 12 serveurs,
jusqu'à 3 cellules de l'Oracle + 1 témoin négatif par serveur, pouls 2,01 s (100 %), 0 erreur, 0 fuite entre cellules.
Limites : 3 mondes A au plus à 3 km les uns des autres ; l'Oracle concentre ses pièges sur un monde (le 14 dans 9
candidats sur 14 à l'itération 13), et un monde ne peut pas occuper deux cellules d'un même serveur → 1 à 2 cellules
par serveur en pratique ; 2 cellules sur 25 ont tiré un autre monde que le banc seul (bloquées depuis v4).

**La mission** : six phases ; seule la phase 2 (traverser ou attendre la patrouille) a un Architecte et un Oracle. Le
plan SCRIPTÉ réussit la mission de bout en bout 17 fois sur 36 (goulot : l'exfiltration). Mesure du 17/09 : les six
choix de phase étaient tous indifférents ou dominés — aucun ne dépendait de la situation.

## 2. La fusion proposée : un jeu à somme nulle, résolu par jeu fictif (« double oracle »)

- **Les joueurs.** L'Architecte choisit une règle π (perception à la décision → option). L'Oracle choisit une
  distribution de situations q (ses armes : menace, distances, patrouille, heure, palier, réserve, Oracle de commande…),
  sous la contrainte de jouabilité (la meilleure option réussit au moins une fois sur deux). Gain de l'Oracle :
  compromission de π sur q, moins celle de la meilleure réponse (le regret).
- **Une itération = un lot d'épisodes multiples** contenant : (a) les attaques de l'Oracle contre π_t, en paires ;
  (b) des explorations ; (c) un **panneau juge fixe** : situations tirées de la distribution naturelle, sur des mondes
  que ni l'Oracle ni l'Architecte ne choisissent, identique d'une itération à l'autre ; (d) les témoins.
- **Les deux apprennent à chaque itération, sur les mêmes données.**
  - L'Architecte fait une **meilleure réponse au MÉLANGE de toutes les attaques passées** (pas seulement la dernière,
    pour ne pas courir après l'Oracle), dans une classe contrainte : constantes, arbres de profondeur ≤ 2 sur la
    perception, EvoGP à ≤ 2 comparaisons. Estimateur : valeur appariée par situation (sign-flip).
  - L'Oracle fait une **meilleure réponse à π_(t+1)** : son imagination apprend sur tout, et vise le regret de la
    nouvelle règle.
- **Promotion de la règle** (anti-poursuite) : π_(t+1) remplace π_t seulement si elle réduit le regret sur le mélange
  historique des attaques (test apparié, Bonferroni sur les candidats) ET n'est pas pire sur le panneau juge (marge de
  non-infériorité) ; hystérésis (deux itérations de suite).
- **Mesures de progrès** : l'exploitabilité ε_t = regret confirmé maximal que l'Oracle trouve contre π_t (doit
  baisser) ; la compromission de π_t sur le panneau juge (doit baisser, comparée à « toujours traverser » 0,257 et
  « toujours attendre » 0,223) ; le nombre de pièges confirmés pour 100 paires.
- **Arrêt** : ε_t sous un seuil pendant N itérations → π est inexploitable dans l'espace des armes de l'Oracle ; ou
  aucune règle ne bat la meilleure constante après M itérations → verdict de monde : il faut une horloge (un coût à
  l'attente), sinon l'équation est une constante par construction.
- **Le monde comme nuisance** : l'Oracle choisit la situation, le multiplexeur tire les mondes parmi les mondes A
  compatibles (strate de visibilité si besoin) → 3 cellules par serveur ; le monde reste une covariable de
  l'imagination, pas une arme.

## 3. La confirmation des 480 paires

Trois options :
- **A** — la finir d'abord, en campagne dédiée sur le banc multiple (paires seulement), puis fusionner.
- **B** — la clore maintenant (déclarée « suivi », sans décision), ses paires deviennent le premier mélange d'attaques.
- **C** — la garder, **isolée** : les paires de confirmation (candidats « confirmation » des itérations ≥ 12) sont
  exclues de l'apprentissage de l'Architecte jusqu'au regard unique ; l'Architecte se dégèle sur tout le reste.
Ma préférence : C.

## 4. Plus tard : toute la mission

Phase par phase, chacune avec un choix, des armes pour l'Oracle et un panneau juge ; à condition que le choix compte
(sinon six constantes). Puis la mission complète avec les six règles contre le plan scripté (17/36).

## 5. Les questions posées à Fable

1. Le jeu fictif / double oracle est-il le bon concept de solution ici (action binaire, classe de règles contrainte,
   Oracle qui apprend un modèle du monde) ? Faut-il plutôt une meilleure réponse régularisée, ou autre chose ?
2. Comment empêcher l'Architecte de courir après le dernier Oracle, et l'Oracle de chasser une cible mouvante avec une
   imagination apprise sur des règles passées ?
3. Confirmation : A, B ou C — laquelle garde la rigueur sans bloquer la fusion ?
4. Le panneau juge : quels mondes (A mis de côté ? graines neuves ?), quelle taille, quelle distribution ? Les mondes B
   (tenus hors de tout pour la poche) restent intouchés.
5. La porte de promotion : test apparié sur le mélange historique + non-infériorité sur le juge — puissance réaliste
   à ~12 paires par itération et un effet de 3 à 7 points ?
6. Le monde : nuisance tirée par le multiplexeur, ou arme de l'Oracle ?
7. Est-ce prématuré tant que l'équation est plate et que l'attente ne coûte rien — faut-il d'abord une horloge ?
8. Budget, falsificateurs, règles d'arrêt, et ce qui doit être écrit avant la première itération fusionnée.
