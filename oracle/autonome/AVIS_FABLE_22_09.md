# Avis de Fable sur la moitié Architecte — 22/09/2026

*Saisi à la demande de Younes (« soumets à Fable ton raisonnement pour réussir »). Question posée : mon diagnostic
(« les candidats prédisent la compromission au lieu d'apprendre l'effet de l'option ») et mon plan (candidat EvoGP
sur la pseudo-issue ψ par IPW) suffisent-ils à faire réussir l'Architecte ?*

## Verdict : GO AVEC CHANGEMENTS

Le candidat ψ/EvoGP seul ne changera rien : à ce rapport signal/bruit (τ ≈ 0,08, écart-type de ψ ≈ 1) il convergera
vers une constante ou sur-ajustera. Le diagnostic est vrai mais secondaire. **Ce qui bloque, c'est l'instrument**
(estimateur, critère d'adoption, protocole) **et le fait que le vrai concurrent n'est pas « toujours traverser ».**

## Les cinq raisons, dans l'ordre

1. **Le vrai concurrent est « toujours attendre ».** Une règle personnalisée ne bat cette constante que s'il existe
   des situations où traverser gagne — la moitié « patrouille » du 19/09, qui n'a pas répliqué. Si attendre ne nuit
   jamais, la meilleure équation lisible EST une constante.
2. **Malédiction du vainqueur sur le motif** : 17 points à la confirmation, 13 en cumulé, 8 après (p = 0,27).
   Estimation honnête : ~5-10 points sur les postes.
3. **Deux populations mélangées** : réserve de l'Architecte à 0,257 de compromission, épisodes de l'Oracle à
   0,45-0,50. L'effet vit dans les situations adverses et se dilue.
4. **L'estimateur jette de la variance** : les épisodes de l'Oracle sont des PAIRES (même situation, deux options),
   traitées comme indépendantes.
5. **La porte est sous-dimensionnée** : pour 3,4 points à base 0,25, ~4 000 épisodes à α 0,05, ~6 000 avec
   Bonferroni k = 4. On en a 1 134. Le 5/5 synthétique a été obtenu à un effet irréaliste.

## Recommandations, par importance

1. Changer le concurrent : **la meilleure constante**, réévaluée.
2. **Test apparié par situation (sign-flip)** sur les paires de l'Oracle — exact sous le nul.
3. **Coupure temporelle et un seul regard** : exploration = tout ce qui existe au commit ; confirmation = uniquement
   les épisodes futurs.
4. **Arbre de politique de profondeur ≤ 2** optimisé sur la valeur de décision comme candidat appris principal ;
   EvoGP-ψ seulement contraint à ≤ 2 comparaisons.
5. **L'Oracle nourrit la confirmation** : moitié postes proches, moitié patrouilles proches, paires entrelacées.
6. Redimensionner les contrôles (positif à −0,08 sur 40 %, négatif de bout en bout par permutation dans la paire).
7. Score du duel = **regret de la règle contre la meilleure constante**, par itération, sur les paires.

## Pièges signalés

- **Fuite post-décision dans la perception** : si une fenêtre de comptage dépasse l'instant de décision, attendre
  donne plus de temps pour voir et entendre, et la perception encode l'option. À auditer.
- Le motif est en vérité (`menace_p2 = 5`), la règle en perception — il faut dire d'avance ce que fait la règle
  face aux autres types de menace.
- Bootstrap percentile à 20 grappes : sous-couvre.
- Propensions [0,1 ; 0,9] : poids jusqu'à 10 ; tronquer à [0,3 ; 0,7].
- Le « 1 fausse adoption sur 20 » ne tient pas compte des regards répétés de la boucle en service.
- **Attendre sans coût** : si le monde ne facture pas l'attente, l'équation est une constante par construction —
  la réponse est alors une horloge, pas une équation.

## Plan proposé

- **Étape 0, gratuite** : plafond en vérité (« attendre ssi poste proche ») ; signes par monde dans et hors « poste
  perçu » ; corrélation intra-paire ; audit des fenêtres de perception (bloquant) ; contrôle positif réaliste de la
  porte actuelle.
- **Étape 1** : pré-enregistrer C1 = toujours attendre, C2 = attendre ssi menace vue et aucun moteur ; H1 (τ < 0 sur
  les paires « poste perçu », N = 480 paires) puis H2 conditionnelle (traverser gagne hors poste) ; décision écrite
  d'avance ; un seul regard.
- **Étape 2** : campagne de confirmation nourrie par l'Oracle (~2-3 jours de ferme).
- **Étape 3** : l'Oracle prend pour cible la règle adoptée ; s'il ne fait pas perdre « attendre » en 10 itérations,
  verdict de monde : ajouter un coût à l'attente.
- **Étape 4** : contrôles de l'instrument avant de lire l'étape 2.

> « L'Oracle a fait sa part. La moitié Architecte échoue parce que sa porte d'adoption est plus aveugle que l'effet
> qu'elle cherche, et parce qu'elle se compare au mauvais adversaire. »
