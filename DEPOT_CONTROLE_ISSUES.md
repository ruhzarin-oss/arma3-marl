# LE CONTRÔLE-ISSUES DU CHAMP D'EXPOSITION — déposé avant de jouer, 27/08/2026

## POURQUOI L'ANCIEN CONTRÔLE EST REMPLACÉ — justification ÉNONÇABLE SANS SON RÉSULTAT
L'ancien demandait : le prix sépare-t-il **20 m vers l'ennemi** de **20 m à l'opposé** ?
Il est **mal conçu a priori**, et voici pourquoi, indépendamment de ce qu'il a rendu ⟨Fable⟩ :

> **Il PRÉSUPPOSAIT l'axe de variation au lieu de l'exiger certifié.** Un contrôle positif se
> construit sur un contraste dont la vérité est **établie par une mesure indépendante**.
> « Se rapprocher de l'ennemi est plus dangereux » **n'a jamais été un fait déposé de ce
> dossier** : c'est une intuition de distance, importée du gymnase. Et le dossier la
> contredisait déjà — **le danger d'Arma est structuré par l'OCCLUSION, pas par la distance**
> (couvert 11×, pente dans le sens de la marche).

J'avais une vérité-terrain mesurée — 8 directions, étendue 13,5, **0 % de directions
équivalentes**, déposée AVANT sur d'autres scènes — et j'ai testé un contraste **supposé**.

**L'ancien contrôle ne se jette pas, il se REQUALIFIE en hypothèse sur le monde** : *à 150 m,
le danger ne varie pas le long de l'axe, il varie latéralement.* Hypothèse, pas verdict — une
scène, comptes de 0,12 et 0,38 sur 20 ennemis, **et un signe INVERSÉ** (s'éloigner exposait
plus). ⛔ Elle ne devient pas une doctrine ; elle a un protocole de réplication (§ RÉPLICATION).

## ⛔ LE PIÈGE REFUSÉ D'AVANCE — LA CIRCULARITÉ
Comparer « meilleure contre pire direction **selon le prix** » au compte de voyants est
**circulaire** : le prix **EST** le compte de voyants multiplié par un tarif. Ce test vérifie
la plomberie, **jamais l'instrument**. Il est conservé sous le nom de **CONTRÔLE
D'ASSEMBLAGE** et ne pourra jamais valider le champ.

## LE CONTRÔLE-ISSUES — la vérité vient d'une AUTRE MODALITÉ que les entrées du champ
> **Le champ doit pricer plus cher les endroits où l'on ENCAISSE DU FEU, mesurés sur des
> événements qu'il n'a pas vus.**

Le feu encaissé (`getSuppression`, dégâts reçus) est l'ancrage intermédiaire : il rend le n
atteignable en heures là où les morts demanderaient des jours. Les issues sont **prospectives**
— on price d'abord, l'événement arrive ensuite.

**PROTOCOLE.** Scènes jouées au **natif seul**, aucun ordre de notre part. À chaque pas :
1. on price la position **actuelle** de chaque homme, par identifiant ;
2. au pas suivant, on relève s'il a **encaissé du feu** (suppression au-dessus de son niveau
   antérieur, ou perte de vie) ;
3. on mesure l'**AUC du prix sur l'événement « encaisse du feu au pas suivant »**.

**Témoins obligatoires**, sur les mêmes états :
· **plancher** : le hasard ;
· **témoin trivial** : la distance au plus proche ennemi — un champ qui ne bat pas une simple
  distance n'apporte rien ;
· **bras nul** : le même champ, valeurs **permutées entre les hommes** à chaque pas.

## LES SEUILS — DIMENSIONNÉS, PAS CHOISIS (règle 3)
Aucun seuil n'est fixé ici. **Le n requis se calcule AVANT le verdict**, depuis le nombre
d'événements récoltés : toute AUC sera publiée avec son **n d'événements** et son intervalle,
et le champ ne passe que s'il bat **le maximum des témoins** au-delà de cet intervalle.
Si le n récolté ne permet pas de séparer, **le verdict est SUSPENDU** — jamais « échec ».

## LA RECEVABILITÉ DE SCÈNE — déposée AVANT de choisir la scène
⟨Fable : « la scène est une pièce de l'instrument ; les instruments se dimensionnent »⟩
Précédent : le raster est passé au span 300 parce que 120 voyait **0,000** défenseur.
Chiffres pris dans la table du 27/08 (20 rouges à 150 m · 20 à 80 m · 12 à 60 m), **pas dans
le résultat du contrôle** :

> **Une scène est recevable si le compte MÉDIAN d'ennemis qui voient un candidat est ≥ 1,0
> ET si l'étendue directionnelle médiane est ≥ 2,0.**

Table mesurée : 150 m → médiane **0,0** (⛔ recalée) · 80 m → médiane **13,0** ✅ ·
60 m → médiane **9,0** ✅. **La scène à 150 m est écartée par le critère, pas par le verdict.**

## RÉPLICATION DE L'HYPOTHÈSE LATÉRALE
Le contraste vers/opposé est rejoué **tel quel** sur les scènes à 60 et 80 m. Si l'écart axial
apparaît de près et reste nul de loin, la lecture « propriété du monde » devient déposable, et
elle est tactiquement précieuse : **la profondeur est gratuite à distance, le latéral jamais.**
Sinon, l'hypothèse tombe.

## CE QUI EST INTERDIT
1. Adopter le contrôle d'assemblage **parce qu'il passe**.
2. Lancer la greffe à 16 graines **avant** que le contrôle-issues ait passé.
3. Faire de « le danger est latéral » une doctrine avant sa réplication.

---

# AMENDEMENT — L'ORDRE DE LECTURE, déposé AVANT toute donnée (27/08)

## L'OBJECTION, ET ELLE PORTAIT SUR LE PROTOCOLE LUI-MÊME
Fable avait prescrit « le feu encaissé, vérité d'une **autre modalité** que les entrées du
champ ». **Mais le prix contient déjà la suppression (×29,81), et l'événement mesuré est
« la suppression augmente ».** Ce n'est pas une modalité indépendante : **c'est de
l'autocorrélation habillée.** Un homme déjà supprimé a un prix élevé ET de fortes chances de
le rester. Le champ passerait le contrôle sans rien prouver.
⟨Fable : *« tu as raison, c'est une faute dans MA prescription »*⟩

## L'ORDRE DE LECTURE, ET IL NE BOUGERA PAS
· **PRIMAIRE — le champ GÉOMÉTRIQUE SEUL (les voyants, sans le terme de suppression), sur les
  seuls hommes NON SUPPRIMÉS au pas k.** C'est la cellule propre : l'entrée ne contient pas
  l'événement, **et la population ne le contient pas non plus**. Ce qui reste — être vu en k,
  encaisser en k+1 — est exactement la chaîne causale que le champ prétend pricer.
· **SECONDAIRE — le champ géométrique sur TOUS**, lue seulement si le n de la primaire ne
  sépare pas (règle 3 : **suspendu**, jamais « échec »).
· ⛔ **LE PRIX COMPLET est DESCRIPTIF et ne pourra JAMAIS valider** — même statut que le
  contrôle d'assemblage, et pour la même raison : **il contient ce qu'il prédit.**

**Justification, énonçable sans les données :** la composante SOUS CONTRÔLE est la
**géométrie** — c'est elle qui est neuve et non validée. Le tarif de suppression a déjà ses
portes (`DEPOT_BARREAU.md`). **On ne valide que ce qui est en question.**

## CORRECTION D'INSTRUMENT, MÊME OCCASION
Le premier lancement a planté sur `getPlayerID`, qui **ne fonctionne pas sur des unités IA**.
Remplacé par un **identifiant persistant assigné à la création** (`setVariable ["hid", _i]`) —
c'est la vraie application de la règle « tout tableau indexé sur des hommes se suit par
IDENTIFIANT », et non par position dans une liste qui se réindexe à chaque mort.

## DOUBLE RÉCOLTE — un run, deux usages ⟨Fable⟩
Les mêmes déroulés portent **les deux marges du consommateur**, à mesurer hors ligne :
· **marge du VETO** = part des décisions où une alternative est ≥ X % moins chère que
  `expectedDestination` pricée au champ réel ;
· **marge de la POSTURE** = part des homme-pas où le prix est haut **et l'homme encore debout**.
⭐ **Si les DEUX marges sont nulles, c'est un résultat majeur, pas un échec** : le natif price
déjà ce que le champ price, et la classe greffe meurt sur Arma pour une raison noble.
⛔ **On ne prépare aucun consommateur avant d'avoir sa marge** — construire le collecteur avant
la marge est la faute exacte que ce dossier vient de désapprendre (D1, redondant à 88 %).
