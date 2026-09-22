# Avis de Fable sur la fusion Architecte–Oracle — 22/09/2026

*Saisi à la demande de Younes (« il faut fusionner Architecte et Oracle » ; « rédige le plan et soumets-le à Fable »).
Plan soumis : `PLAN_FUSION_22_09.md`. Texte de Fable reproduit tel quel.*

## Verdict

**NO-GO sur la fusion en jeu fictif / double oracle telle qu'elle est posée. GO AVEC CHANGEMENTS sur une fusion plus modeste** : un seul corpus apparié, un panneau juge gelé, l'Oracle en proposeur, l'Architecte hors ligne — et seulement après avoir tranché la question de l'horloge. La machine proposée est bonne ; le jeu qu'elle résoudrait n'a pas d'enjeu mesurable aujourd'hui.

## Les raisons, dans l'ordre d'importance

1. **La marge à gagner est de 1 à 3 points.** Le plafond en vérité « attendre ssi poste proche » bat « toujours attendre » de −0,013 [−0,032 ; +0,003]. C'est tout ce que la perception peut apporter en phase 2 avec ce monde. Le double oracle est une machine à trouver l'exploitabilité ; ici l'exploitabilité maximale vaut au plus 3 points. On construit un chalut pour pêcher un point.

2. **La ferme ne voit pas de tels effets à ce débit.** Avec ρ intra-paire = 0,38 et des taux de 0,22 et 0,26, l'écart-type d'une différence appariée vaut ≈ 0,475. Il faut, à 80 % de puissance et α 0,05 unilatéral : 3 points → ~1 550 paires ; 5 points → ~560 ; 7 points → ~285 ; 10 points → ~140. À 12 paires par heure : 130 h, 47 h, 24 h, 12 h. Bonferroni sur 6 candidats multiplie par 1,4. Une porte de promotion à 12 paires par itération a un SE de 0,137 : elle ne détecte que des effets ≥ 0,34. À 32 paires, ≥ 0,21. C'est la cécité que j'ai chiffrée ce matin (3 adoptions sur 20), transformée en règle d'itération.

3. **ε_t = « regret max trouvé » institutionnalise la malédiction du vainqueur.** Un maximum sur 31 candidats estimés chacun sur ~12 paires vaut, sous bruit pur, environ 2 SE ≈ 0,27. Sur 31 confirmations à α 0,05, on attend 1,5 faux positif ; on en a confirmé 1. Le motif poste-proche a fondu de 17 à 8 points après confirmation. Honnêtement : l'Oracle n'a encore rien trouvé qui se distingue du bruit, et le progrès mesuré par ε_t descendrait tout seul, par régression vers la moyenne, sans que rien ne s'apprenne.

4. **Le jeu est dégénéré.** Action binaire, attente gratuite (« le monde de CHACAL n'a pas d'horloge »), équation plate (0,10 de variance). L'équilibre est « toujours attendre », ce que la confirmation à 480 paires teste déjà. De plus, un minimax sur les situations choisies par l'Oracle n'est pas la valeur dans la mission : le terrain choisit les situations, pas un adversaire. Un Architecte qui répond au mélange des attaques apprend à se défendre contre l'instrument. Enfin, en jeu à somme nulle la réponse d'équilibre peut être mixte : une règle qui tire à pile ou face n'est ni lisible ni transmissible à un chef.

5. **Une économie majeure est oubliée : le corpus apparié évalue n'importe quelle règle hors ligne.** Avec deux options et chaque situation jouée sous les deux, la valeur d'une règle π est la moyenne des issues enregistrées sous π(s). Sans épisode neuf, sans biais (une tirage par bras suffit à l'espérance). Le juge ne coûte donc rien par itération ; il coûte une fois, à la constitution, puis il est gelé. La fusion n'a pas besoin d'une dynamique de jeu ; elle a besoin d'un corpus, de strates et de poids. C'est le « gymnase de décisions » du 16/09, remis à sa place.

6. **L'imagination n'est pas une cible mouvante.** L'issue sachant (situation, option) ne dépend pas de la règle — vous avez vérifié l'absence de fuite post-décision. Le modèle est donc valide hors politique. Le vrai problème est la couverture : monde 14 dans 9 candidats sur 14. L'Oracle apprend peut-être « le monde 14 est méchant » et non un motif de perception.

## Réponses aux 8 questions

1. **Jeu fictif / double oracle** : concept juste pour une classe contrainte et un adversaire à modèle, mais mal posé ici — l'objectif n'est pas minimax, c'est la valeur naturelle ; l'Oracle est un falsificateur (proposeur), pas un joueur. À la place : corpus apparié stratifié + évaluation hors ligne + juge gelé.
2. **Poursuite** : elle disparaît si l'Architecte apprend hors ligne sur la strate naturelle et n'est falsifié que par les attaques. L'Oracle ne chasse rien de mouvant (raison 6) ; il lui manque une contrainte de couverture par monde.
3. **Confirmation : A, en parallèle.** Ne pas amender un test pré-enregistré en cours. Mais noter dès maintenant sa portée : ses situations sont choisies par l'Oracle contre « traverser », donc l'estimation est une borne haute de l'effet naturel. Les cellules libres jouent le panneau juge pendant ce temps.
4. **Panneau juge** : mondes A tirés à l'aveugle, équilibrés (au moins 4 mondes, aucun > 30 %), situations tirées par le script de mission et non par l'Oracle, en paires. Deux tranches gelées de 300 situations (600 épisodes) : l'une pour choisir, l'autre pour juger — un seul regard sur la seconde.
5. **Porte par itération** : puissance nulle pour 3 à 7 points (raison 2). Une seule porte, à N fixé d'avance, sur la tranche juge gelée.
6. **Monde** : nuisance bloquée, pas arme. Un piège compte s'il tient sur ≥ 2 mondes ; l'imagination garde le monde en covariable mais on lui interdit un piège « monde seul ».
7. **Oui, prématuré.** Tant que l'attente ne coûte rien, le choix n'est pas un choix (17/09 : six choix indifférents ou dominés). L'horloge est la condition de tout le reste.
8. Voir le plan révisé et la dernière section.

## Recommandations par importance

1. **Trancher l'horloge d'abord.** Le goulot de la mission est l'exfiltration (17/36). Si le temps consommé en phase 2 pèse sur l'exfiltration, l'horloge existe déjà : elle est cachée par la mesure « compromission fin de phase 2 ». Si elle ne pèse pas, c'est une décision de conception de mission (fenêtre d'exfiltration, aube), qui appartient à Younes. On ne l'invente pas dans l'estimateur.
2. **Constituer un corpus apparié à strates et poids**, unique, avec pour chaque situation : strate (attaque / exploration / juge / témoin), probabilité de tirage, monde, les deux issues.
3. **Écrire l'évaluateur hors ligne** et le tester par contrôles avant tout usage.
4. **Faire de l'Oracle un proposeur contraint** : couverture par monde, pièges confirmés seulement sur réplication pré-enregistrée.
5. **Rendre l'Architecte hors ligne** : recherche dans la classe sur la tranche 1, verdict unique sur la tranche 2.

## Pièges

- La distribution des 480 paires est choisie par l'Oracle contre « traverser » ; une confirmation positive vaut sur cette distribution, pas dans la mission.
- Regards répétés sur le « mélange historique » = inflation d'α sans dépense prévue. Une porte, un N, un regard.
- Une règle sélectionnée puis évaluée sur le même corpus est optimiste. Séparer choisir et juger.
- Trois cellules à 3 km : l'indépendance à tolérance zéro doit être vérifiée par les témoins à chaque lot, pas supposée.
- « Jouabilité ≥ 1/2 » définie par l'imagination et non par la mesure : un piège imaginé non jouable n'est pas un piège.
- Le monde 14 comme motif déguisé.
- Un équilibre mixte serait une règle aléatoire : l'interdire dans la classe.

## Plan révisé en étapes

**Étape 0 — Corpus et évaluateur (0 h de ferme, un jour d'écriture).** Journal apparié à strates ; évaluateur hors ligne. Porte : « toujours traverser » et « toujours attendre » recalculés hors ligne retombent sur 0,257 et 0,223 ; dix règles placebo (relabel aléatoire) donnent 0/10 de faux effet à α 0,05. Falsificateur : un placebo passe → l'évaluateur est cassé, rien d'autre ne se lance.

**Étape 1 — Panneau juge, tranche 1 (600 épisodes ≈ 10 itérations ≈ 10 h ; 4-5 h à 2-3 cellules).** 300 situations naturelles appariées, mondes A équilibrés, jouées dans les cellules libres pendant les 480. Porte : témoins négatifs nuls, taux constants dans l'IC de l'étape 0, aucun monde > 30 %. Falsificateur : l'écart attendre−traverser sur cette strate a un signe opposé à celui des paires Oracle → le −0,069 était un artefact de sélection.

**Étape 2 — Regard unique sur les 480 (≈ 38 h déjà engagées, en parallèle).** Pré-enregistrement inchangé. Falsificateur écrit : IC contenant 0 → « toujours attendre » n'est pas adoptée et le verdict de monde s'écrit (« choix indifférent sans horloge »).

**Étape 3 — Architecte hors ligne (600 épisodes pour la tranche 2 ≈ 10 h).** Recherche dans la classe (constantes, arbres ≤ 2, EvoGP ≤ 2 comparaisons, pas de règle mixte) sur la tranche 1 ; un candidat unique jugé sur la tranche 2 avec un seul regard, contre la meilleure constante, non-infériorité sur les strates Oracle. Puissance : 300 paires détectent ~7 points ; le plafond mesuré est de 1,3. Falsificateur attendu : rien ne bat la constante → la perception ne compte pas en phase 2 dans ce monde, ce qui ferme proprement le sujet.

**Étape 4 — Horloge (décision de Younes, puis 2 × 36 missions de bout en bout si on mesure au lieu de décider).** Nouvelle issue de phase 2 = (compromission, minutes consommées) reliée au succès de mission. Porte : le coût de l'attente est non nul et mesurable (≥ 5 points de succès de mission pour 20 min).

**Étape 5 — Fusion réduite, si et seulement si l'étape 4 donne une marge ≥ 5 points.** Oracle proposeur, Architecte hors ligne, juge gelé, tout sur le corpus commun. Budget : 560 paires par verdict (~47 h à 12 paires/h, ~16-24 h en multiple plein). Règle d'arrêt : deux verdicts successifs sans règle battant la constante → on passe à la phase suivante.

## Ce qui doit être écrit AVANT la première itération fusionnée

- La décision d'horloge, signée par Younes, et l'issue de phase 2 qui en découle.
- Le schéma du corpus : strates, poids de tirage, mondes autorisés (B toujours exclus), format des deux issues.
- Les contrôles de l'évaluateur hors ligne (positifs, placebos) et leurs seuils.
- La classe de règles, fermée, sans règle mixte ; le nombre de candidats pour Bonferroni.
- La taille N de la tranche juge et l'effet minimal détectable qui en résulte, affichés côte à côte.
- La définition d'un piège confirmé : réplication pré-enregistrée, ≥ 2 mondes, jouabilité mesurée et non imaginée.
- Les falsificateurs de chaque étape et ce qu'on écrit dans le journal si l'un d'eux tombe.
- Le script de reprise après arrêt de la station et le contrôle d'indépendance des cellules à chaque lot.

*On ne fusionne pas deux apprentis autour d'un enjeu d'un point ; on donne d'abord un prix au temps, puis on laisse le corpus juger.*
