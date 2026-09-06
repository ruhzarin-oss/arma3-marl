# PORTE D'ADOPTION — LA GREFFE, REJOUÉE DANS ARMA

**Déposée le 26/08/2026, avant la moindre donnée.** Elle remplace la porte d'adoption écrite
dans `DEPOT_BARREAU.md`, qui demandait d'entraîner une politique DANS le modèle.

## POURQUOI ELLE CHANGE DE FORME ⟨Fable⟩
> *« Ta porte d'adoption a été écrite quand "modèle du monde" voulait dire "simulateur où
> entraîner". Trois saturations plus tard, le livrable de l'étape 2 n'est pas un monde où
> apprendre : c'est un JUGE — un tarif appris. Et c'est exactement ce que `monde2` est déjà. »*

`monde2` est **discriminatif** : il rend un prix de mort, il ne déroule aucun état. Rebâtir un
RSSM pour satisfaire la lettre de l'ancienne porte serait un chantier entier au service d'une
ambition — entraîner DANS le modèle — qui hérite de **toutes les défaillances de crédit que ce
dossier vient de payer**. Ce que les étapes 3 et 5 consomment, c'est un **tarif** et un **juge
de gestes**. Le discriminatif les fournit.

## LA QUESTION, DANS SA FORME EXACTE
> **Un exécutant FIXE sur Arma — natif ou doctrine — filtré au moment de décider par le prix
> de mort de `monde2`, bat-il le même exécutant SANS filtre, sur scénarios jamais vus ?**

C'est **la greffe**, qui valait **+15,3 points sans un seul gradient** dans le gymnase,
rejouée dans le monde qui, lui, price l'information.

## LES QUATRE MANQUES DE MON PREMIER JET, CORRIGÉS

**1. ⭐ LE BUDGET COMPTE LE CORPUS.** *« Le bras-modèle a consommé des centaines de milliers de
transitions Arma pour s'entraîner ; si elles sont gratuites, il gagne en contrebande. »*
→ **Budget = transitions du monde réel consommées N'IMPORTE OÙ dans la chaîne, corpus inclus.**
Le bras greffé part donc avec une dette de 2,8 M de fenêtres d'étude, à déclarer dans le dépôt
du résultat. Ce n'est pas disqualifiant — c'est comptable, et ça se dit.

**2. MÊME INTERFACE POUR LES DEUX BRAS.** Même pont, même vocabulaire d'action, même exécutant.
Seul le **filtre** diffère. Sinon on juge l'interface.

**3. LE SENS DE « BAT », DÉPOSÉ ICI.** Critère principal = **survivants amis en fin de
scénario**. Secondaire, publié à côté sans pouvoir de décision : morts ennemis, distance
parcourue. ⚠️ **Pas la « prise »** : la scène d'hier n'a pas d'objectif à prendre, et inventer
un objectif après coup serait choisir la métrique qui arrange.

**4. DEUX GRAINES D'ENTRAÎNEMENT PAR BRAS, MINIMUM.** *« La loterie ne s'est jamais excusée. »*

## LES CONTRÔLES
· **plancher** : filtre à prix PERMUTÉ, retiré **à chaque décision** — ⚠️ une permutation figée
  m'a coûté 3,9 points le 25/08, dans le mauvais sens ;
· **barreau bas** : le natif Arma figé · **barreau haut** : LAMBS ;
· ⭐ **LE TUEUR** : si **aucun** des deux bras ne bat le natif, la comparaison est **vide** et
  on ne publie **pas de vainqueur**.

## LES SEUILS, ÉCRITS AVANT
· **succès** : `greffé − nu ≥ +1,0 survivant` (sur 8) **et** `greffé − permuté ≥ +0,5` ;
· **échec** sous +0,3 survivant ;
· entre les deux : deux graines de plus, **aucun verdict**.

## L'ÉCHEC PRÉ-INSCRIT, POUR NE PAS LE MÉLIRE
Le transfert est mesuré à **0/20** dans ce dossier. Si les deux bras s'effondrent également,
**le résultat porte sur le TRANSFERT, pas sur `monde2`** — et il ne se lira jamais comme un
verdict sur le modèle.

---

# LES DEUX RÈGLES DE PUBLICATION, À PARTIR DE MAINTENANT ⟨Fable⟩

## RÈGLE A — NE PUBLIER QUE DES GRANDEURS INVARIANTES
Invariantes au **ré-échantillonnage** et au **ré-échelonnage**.
· **rapports de cotes**, jamais de probabilités sous poids de classe — le poids 3 143 saturait
  mes probabilités près de 1, et la suppression sortait à ×1,97 au lieu de ×27,91 ;
· **jamais une AUC comparée à un rapport de taux** — « vu » rend AUC 0,5666 ET rapport ×2,45,
  les deux sont vrais et ne se contredisent pas ;
· **toute AUC porte son n de positifs**, et tout tarif porte son nombre d'ÉVÉNEMENTS.
> *Mes cinq erreurs du 26/08 sont toutes des confusions d'unités. Cette règle en tue la classe
> entière.*

## RÈGLE B — LA QUARANTAINE AU BORD DE L'ANNONCE
**Aucune « anomalie » ni « inversion » ne passe du brouillon au registre sans qu'un fait
indépendant DÉJÀ DÉPOSÉ ait été confronté d'abord.**
· J'ai annoncé « être vu ne prédit rien, contre la fiche des 563 000 observations » — la fiche
  disait ×2, j'ai mesuré ×2,45, **il n'y avait pas d'anomalie** ;
· J'ai annoncé « le modèle croit qu'être vu protège » — artefact de mon échelle.
> *Les deux seraient mortes en privé : le fait contradictoire existait avant mon cri.*
**Ce qu'on garde, c'est la frontière du dépôt — pas la vitesse.**

## AMENDEMENT AU BARREAU — `vu` EST NON MESURABLE ICI
Les tarifs reposent sur : suppression **193 morts** · knowsAbout **34** · **`vu` SIX**.
→ **`vu` se dépose « n = 6, NON MESURABLE dans ce corpus »**, et aucun estimateur ne sera
tenté. Ma réparation par encodage à trois états l'a prouvé de la meilleure façon : elle n'a pas
bougé `vu` (49 % → 47 %) et elle a **cassé la suppression** (×57,07, soit 191 % du vrai).
Le tarif de `vu` existe **ailleurs**, mesuré sur 563 000 observations. Le corpus n'a pas à le
re-dériver. **Si le modèle doit un jour le connaître, la réponse est une CAMPAGNE DE DONNÉES** —
le serveur tourne par tâche planifiée, on dessine des scénarios qui fabriquent des événements
vu-et-mort, et le n monte.
