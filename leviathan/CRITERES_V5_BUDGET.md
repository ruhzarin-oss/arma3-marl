# CRITÈRES v5 — L'ORDRE DEVIENT UN BUDGET (figés avant la première ligne)

Écrits le 2026-07-29. Architecte : Fable. Exécution : Opus 5. Arbitrage : Younes.

## LE DIAGNOSTIC QUI JUSTIFIE v5, MESURÉ
Sonde appariée sur `mission_v4.pt`, mêmes états, seul le verbe affiché change :
- écart de valeur entre les deux ordres : **0,049** → le critique se sert du verbe, il n'est
  pas aveugle. L'hypothèse du poison dans les avantages est **écartée**.
- divergence des actions (Jensen-Shannon) : **0,00148** sur une échelle qui monte à 0,693,
  soit deux millièmes du maximum → **le verbe a un levier quasi nul sur le comportement**.

Cause : le verbe est une **constante d'épisode dont la conséquence n'existe qu'au dernier pas**.
Rien ne bouge pendant l'épisode qui dépende de l'ordre. Même un apprenant parfait n'aurait
rien sur quoi se conditionner.

## LE CHANGEMENT DE v5 — UN SEUL
**L'ordre cesse d'être un verbe et devient un budget de dose.**

`B` : budget d'exposition, scalaire, tiré **log-uniformément** à chaque épisode.
`C_t` : dose consommée, somme des expositions instantanées jusqu'au pas t.

L'observation porte, **à chaque pas, dans l'acteur ET dans le critique** :
`[ B , C_t , (T−t)/T , (B−C_t)/B ]`.
Le verbe devient une grandeur vivante qui se consume.

## LA RÉCOMPENSE — quatre poids, aucun par verbe
```
u_t = max(0, C_t − B) / B
r_t = λ_prog·(Φ(s_{t−1}) − Φ(s_t))            progrès, forme potentielle
    − λ_pertes·pertes_t
    − λ_dep·[ min(u_t,1) − min(u_{t−1},1) ]   dépassement, forme télescopique
    + λ_succ·succès_terminal                  SANS branche de verbe
λ_dep = 0,5·λ_succ
```

**Le bonus terminal perd sa branche par verbe.** C'est le terme de dose qui fait le travail
de l'ordre, et il le fait densément.

## POURQUOI ELLE NE PEUT PAS RÉAPPRENDRE L'IMMOBILITÉ — à vérifier dans le code, pas à espérer
1. **Sous le budget, la dérivée du terme est nulle.** L'exposition est contingentée, pas taxée.
   Un quota, pas un prix. C'est ce que l'amendement 3 cherchait sans l'obtenir.
2. **Forme télescopique** : la somme sur l'épisode vaut exactement `−λ_dep·min(u_T,1)`,
   donc bornée par `−0,5·λ_succ`.
3. **Inégalité à asserter dans le code** : immobilité ⇒ R = 0 ; tout épisode réussi ⇒
   R ≥ λ_succ − λ_dep ≥ 0,5·λ_succ > 0. **Le succès domine strictement l'immobilité, quel que
   soit le budget dépensé.**
4. **Au-delà du budget saturé (u ≥ 1) le terme redevient plat** : un agent qui a brûlé son
   budget ne se couche pas, il continue à viser le succès.

## AVANT D'ENTRAÎNER — LA FRONTIÈRE PAR BUDGET
Mesurer, avec les six doctrines et **sans aucun entraînement**, le taux de réussite atteignable
par niveau de budget, 8 niveaux, 1024 épisodes chacun, instrument certifié.

**`B_min` est fixé au plus petit budget où une doctrine réussit encore.** En deçà, on
enseignerait l'immobilité — c'est la seule façon dont v5 peut échouer sur ce point, et elle est
bornée par une mesure préalable, pas par une intuition.

Le plafond global, lui, est déjà connu : l'étalon donne 87,5 % et 62,9 %, très au-dessus des
seuils du jalon. Le retard est dans la politique, pas dans le monde.

## JALON 3, SCINDÉ — obéissance et compétence ne se confondent plus
**3a — OBÉISSANCE.** Trois critères, tous appariés :
1. dose réalisée **monotone croissante en B** sur 8 niveaux, ρ de Spearman ≥ 0,80 ;
2. divergence d'actions appariée significativement ≠ 0 (référence v4 : 0,00148) ;
3. succès sous ordre vrai > succès sous ordre permuté, **test apparié**, ≥ 5 points, 5 graines.

**3b — COMPÉTENCE.** 40 % / 15 %, et seulement si 3a est franchi.
**Jalon 4.** 50 % / 20 %. Maintenu, non abaissé.

Ces seuils sont pré-enregistrés **maintenant, avant de lancer v5**. Un jalon fixé après avoir
vu le chiffre n'est plus un jalon.

## LE RUNNER — la liste exécutable
1. **Tous les points de contrôle conservés**, plus le meilleur-certifié à part. Jamais
   d'écrasement. v4 a perdu son meilleur agent (32 % à 300 itérations) parce qu'il écrasait.
2. Évaluation tous les 50, même graine de validation, **médiane glissante sur 3 points**.
3. **Règle de sélection déclarée d'avance** : modèle retenu = meilleur sur la graine de
   validation ; chiffre publié sur **5 autres** graines tenues à l'écart.
4. **Décroissance linéaire du pas d'apprentissage jusqu'à zéro** sur le budget déclaré. Un pas
   constant sur une politique durcie est la cause canonique de l'effondrement tardif (32 → 25,8).
5. **3 graines d'entraînement minimum** pour toute affirmation de jalon. Une exécution est une
   anecdote.
6. **Sonde de divergence-verbe en ligne à chaque évaluation.** Si elle reste ~0, l'agent est
   sourd et on le sait à l'itération 20 au lieu de 400.

## RAPPEL STATISTIQUE
`32 %` était un **maximum sur quatre tirages** : sa valeur non biaisée est plus basse, ~28 %.
Il ne se cite plus comme le résultat de v4.

## INTERDITS
Ceux des jalons 1 et 3 restent en vigueur. En plus :
- **Ne pas allonger le budget de pas avant que la porte d'obéissance soit franchie.** Tout
  travail sur le plafond est perdu tant que l'agent est sourd.
- **Réétiquetage a posteriori en réserve, PAS dans v5.** C'est le meilleur levier de compétence
  disponible ; il attend que 3a soit franchi.
