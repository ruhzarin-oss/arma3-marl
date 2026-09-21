# L'espace du diable en phase 2 — ce que l'Oracle peut faire pour casser l'Architecte

*21/09/2026. Point 2 du plan du duel. Younes : « l'Oracle a tous les droits, il peut absolument tout faire, sans foi
ni loi, pour casser l'Architecte — c'est le diable ». Ce document dresse l'inventaire de ses armes, vérifiées une par
une dans le banc `chacaloracle` (96 paramètres de mission), et les deux seules règles qui gardent le duel utile.*

## Les deux règles — et pourquoi même le diable y a intérêt

1. **Chaque piège laisse au moins un choix gagnant.** Si toutes les options perdent, c'est un mur : l'Architecte
   n'apprend rien, son équation ne change pas, et le diable n'a plus rien à casser. Mesuré, pas décrété : un piège
   candidat est joué sous les deux options ; il n'est valide que si la meilleure option réussit assez souvent
   (seuil à écrire avant la première campagne de pièges).
2. **Le diable connaît la règle, pas le coup.** Il lit l'équation de l'Architecte, donc il **prédit** son choix, et
   il pose son piège en conséquence — mais **avant** que le choix soit fait. S'il pouvait réagir après, toutes les
   options perdraient (règle 1). C'est aussi ce qui rend la surprise mutuelle possible : l'Architecte qui change
   sa règle fait tomber le diable dans le vide.

Tout le reste est permis : tricher sur les positions, aveugler, assourdir, leurrer, choisir le monde.

## Ce qu'il peut régler dès aujourd'hui — sans une ligne de code

Paramètres exposés par la mission **et pilotables par un job** (vérifié dans `description.ext`, `00_socle.sqf`,
`lancer.sh`) :

| arme | réglage | valeurs | ce qu'elle lui donne |
|---|---|---|---|
| **le terrain** | `GRAINE` × `GRAINE_HAUT` | 32 × 32 = 1 024 mondes | les routes, le relief, les angles morts. Graines 13 à 24 : 12 valides sur 12 |
| **la mise en scène** | `SITUATION` | 0 à 31 | quelles menaces, où, indépendamment du monde |
| **la menace de la route** | `MENACE_P2` | 0 aucune · 1 patrouille motorisée · 2 poste · 3 les deux plus près · 4 patrouille seule près · 5 poste seul près | le type même du danger que l'équation doit reconnaître |
| **la menace d'avant** | `MENACE_P1` | 0 à 5 | user ou alerter le détachement avant la route |
| **l'heure** | `JOUR` | nuit · jour | jour : on voit et on est vu 2 à 3 fois plus loin |
| **les oreilles de l'Architecte** | `PORTEE_SON` | 0 · 300 · 600 · 900 m | à 0, il est **sourd** au moteur — la variable que son équation utilise le plus |
| **ses yeux** | `AVANT`, `BALAYAGE`, `OBSERVATION` | 260/180/120/80 m ; balayage cassé ou réparé ; 0 à 300 s de fenêtre | le placer trop loin, trop près, lui couper la fenêtre d'observation |
| **la force en face** | `PALIER`, `HMG`, `QRF_N`, `QRF_DELAI`, `QRF_DIST` | garnison 0-4 ; 0-2 mitrailleuses ; 0-2 véhicules de réserve partant de 45 s à jamais, de 1 à 7 km | la réaction qui suit une erreur |
| **le chasseur** | `ORACLE_CMD`, `_B`, `_NU`, `_EPS`, `_DELTA` | budget 0-12, doute, erreur, période 30-120 s | la patrouille qui cherche pendant l'épisode |
| **la taille de la proie** | `EFFECTIF` | 10 · 20 | un groupe plus gros se voit plus |

L'espace combiné dépasse **10⁹ situations**. Le diable ne peut pas les essayer dans Arma : il lui faut une
**imagination** (plus bas).

## Ce qu'il ne peut pas encore faire — les armes à forger

Ce sont précisément celles qui visent une équation **fondée sur la perception**, donc les plus diaboliques :

| arme | ce qu'elle casse | effort |
|---|---|---|
| **Omniscience** (`ORACLE_CMD = 2`) : le chasseur lit la **vraie** position du détachement | l'hypothèse « il ne sait que ce qu'il voit » ; le contrôle de non-triche devient sans objet pour ce mode | faible — une ligne |
| **Le leurre** : un véhicule moteur allumé, sans troupe, sur la route | la règle « moteur entendu, donc danger, donc attendre » | moyen |
| **La patrouille silencieuse** : moteur coupé, à pied ou roue libre | la règle « rien entendu, donc la voie est libre » | faible à moyen |
| **Le piège posé sur la traversée prédite** : menace placée à distance et azimut choisis du point où l'équation fait traverser | le lieu exact de la décision | moyen |
| **Le passage minuté** : la patrouille surgit juste après la fenêtre d'observation | la règle « j'ai regardé, rien, j'y vais » | moyen |

**Interdit, même au diable :** changer le piège après le choix (règle 2).

## Comment le diable cherche

- **Il lit l'équation** de l'Architecte (point 1) : il sait quelle option elle choisit dans chaque situation.
- **Il imagine avec le modèle du monde** : le réseau de neurones du jeu B (point 1, en calcul) prédit la
  compromission réelle d'une situation sous chaque option. Le diable cherche les situations où **l'option choisie
  par l'équation est la plus dangereuse selon le monde**, alors qu'**une autre option reste sûre** (règle 1).
- **Il ne joue dans Arma que ses meilleurs pièges** — et la mesure du duel est l'erreur de l'équation sur ces
  pièges, comparée à des situations tirées au hasard.
- **Limite honnête :** le réseau n'a appris que sur les situations déjà jouées. Il ne peut pas imaginer un leurre
  ou une patrouille silencieuse, qui n'ont jamais existé. Pour ces armes neuves, le diable doit **explorer dans
  Arma**, pas imaginer.

## Ordre de travail proposé

1. Attendre l'équation du point 1 — si elle est plate, le premier piège est trivial, et c'est déjà une information.
2. Forger les trois armes les moins chères : **omniscience, patrouille silencieuse, leurre** — fumée de 4 épisodes
   chacune, **ferme vide**, avant toute campagne.
3. Écrire le seuil de jouabilité et la mesure du duel **avant** la première campagne de pièges.
