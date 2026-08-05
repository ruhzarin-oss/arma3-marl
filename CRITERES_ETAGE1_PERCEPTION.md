# Étage 1 — le CHAMP DE RISQUE : critères déposés AVANT toute mesure

*6 août 2026, 00h10. Aucun entraînement lancé. La 3090 est libre, Arma tourne en CPU.*

## D abord, une prémisse corrigée

Le plan disait « ajouter deux nombres : l arc de tir ». **C est déjà fait, et déjà payé.**
`agent_complet.py:191` calcule `ec_lui` — mon écart à la face du défenseur — et la ligne 194
le donne à l observation, avec sa saturation `sigmoid((CHAMP - ec_lui) * 1,2)`. Le −28 %
d exposition du 27/07 est un acquis **encaissé**, pas une piste à ouvrir.

⟨lu dans le code, pas dans mes souvenirs. La règle du projet : demander « QUE VOIT-IL ? »
en ouvrant le fichier, jamais en se rappelant.⟩

Ce que l agent voit aujourd hui, exhaustivement : sa position, la position / distance /
azimut de chaque défenseur vivant, s il est dans le cône de chacun, leur suppression et leur
posture, et **un scalaire de risque appris pour SA case à lui**.

Ce qu il ne voit pas : **le prix d un pas qu il n a pas encore fait.** Il connaît le coût
d où il est. Il ignore le coût d où il irait. C est le trou réel.

## Ce qui se teste

Le **champ de risque** : le danger qu il subirait **à 35 m dans chacune des 8 directions**,
huit nombres, calculés avec le risque **APPRIS** (`risque_geo.pt`, AUC 0,714 sur corpus Arma).

C est le dispositif conçu le 27/07 — mais il reposait alors sur `expo`, dont on a mesuré
depuis qu elle **vaut le hasard** (AUC 0,5005). Un champ bâti sur une fonction qui n ordonne
rien ne pouvait rien dire. La fondation existe maintenant ; le dispositif redevient sensé.

Trois choix, repris sans retouche du 27/07 :
- **à 35 m, pas au pas suivant** — c est l échelle de la MANŒUVRE, pas du réflexe ;
- **le PRIX, jamais la réponse** — le moins cher est toujours de fuir, l arbitrage reste
  entier. Pas de booléen « peut-il me tirer dessus » : ce serait souffler la réponse ;
- **géométrie générique** — qui voit quoi d où, même principe que la coque à 12 rayons.

## Le verrou d entrée : l instrument doit prouver qu il discrimine

**Rien ne se juge sur un banc qui a échoué à ses propres portes.** État constaté du banc 150
avec risque appris (`RESULTAT_BANC150_RISQUE.txt`) : **P2 (contrôle nul) et P3 (l agent bat la
droite) ont CÉDÉ**, et l oracle libre fait 7/20 quand la droite fait 2,0 — l information
parfaite ne s y détache pas.

Donc, **avant** de lire quoi que ce soit sur le champ de risque :

> **PORTE 0.** Sur le banc retenu, le **crochet scripté** doit battre l **assaut frontal
> scripté** sur la métrique primaire. Si les deux doctrines ne se séparent pas, le banc ne
> peut pas juger un agent, et **l étage 1 n est pas lancé** — on répare le banc, point.

C est le contrôle qui a manqué quatre nuits durant : cinq « refus » de l agent jugeaient en
réalité le banc.

## La métrique primaire : l ARRIVÉE, pas l exposition

L exposition est le moyen ; l objectif est la fin. Un agent moins exposé qui n arrive pas
n a rien gagné.

**PRIMAIRE — le palier de rayon tenu.** La distance de départ la plus grande à laquelle
l agent arrive encore, curriculum identique, 3 graines. Référence sans champ : **125 m**
(`RESULTAT_CHAMP_RISQUE.log`, graine 1 : tenu à 110 m, divergence à 125 m).

> **Succès : +1 palier au moins (≥ 140 m) sur 2 graines sur 3.**

**TÉMOIN DE MÉCANISME — la distance du détour.** Choisi **dans les données**, pas dans
l intuition : c est la grandeur qui a ordonné correctement les trois doctrines le 27/07
(crochet 184 m · appris voyant 132 m · frontal 118 m). Seuil **repris sans retouche du
27/07 : ≥ 155 m**, la mi-chemin entre l appris et le crochet.

> Le témoin dit si l explication est **la bonne** ou seulement compatible. Il ne sauve pas
> un échec de la primaire et ne le remplace pas.

⟨rappel de la faute du 27/07 : mon témoin d alors — « temps passé dans l angle mort » — est
monté de 18,9 à 20,2 % pendant que l exposition chutait de 28 %. Je savais QUE ça marchait,
pas COMMENT. Un témoin se choisit dans les données.⟩

## Les contrôles qui savent échouer

**C1 — NUL (placebo).** Même agent, même architecture, huit nombres **de bruit** à la place
du champ. **Doit ne rien gagner.** S il gagne, ce n est pas l information qui paie, c est la
capacité ajoutée au réseau — et tout le résultat tombe.

**C2 — PRÉSENCE.** Le champ doit **discriminer** : écart-type entre les 8 directions
supérieur à la moyenne du champ. S il est plat, on donne huit copies du même nombre.

**C3 — SMOKE-TEST, avant les heures de GPU.** Un run de 2 itérations doit imprimer la
dimension d entrée passée de 8 à 16 canaux par entité **et** un champ non constant sur un
lot. Tant que ça n est pas à l écran, rien de long ne part.
⟨la règle maison : prouver que le changement est ACTIF avant de payer la nuit.⟩

## Ce qui la ferait échouer — écrit maintenant

- **La primaire ne bouge pas** (palier < 140 m sur 2 graines / 3) : le champ est du confort,
  pas de la capacité. **On ferme le chantier perception ce soir-là.** Pas de deuxième réglage,
  pas de « il manquait un tarif » — c est ainsi qu on perd quatre nuits.
- **La primaire monte mais C1 monte aussi** : c est la taille du réseau, pas l information.
  Résultat nul, versé tel quel.
- **La primaire monte et le témoin ne suit pas** (détour < 155 m) : on garde le gain et on
  écrit **« ça marche, on ne sait pas pourquoi »**. On ne raconte pas d histoire.
- **PORTE 0 cède** : rien n est lancé, et la nuit passe à réparer le banc.

## Coût

Une nuit. Le champ coûtait **×1,4** en temps de calcul au 27/07, indépendamment du nombre
d environnements — le GPU est sous-employé, la 3090 est libre, Arma occupe le CPU.

Si l étage 1 échoue, **l étage 2 n existe pas** et un trimestre est économisé.
C est à ça que sert un chantier qui porte son propre couteau.
