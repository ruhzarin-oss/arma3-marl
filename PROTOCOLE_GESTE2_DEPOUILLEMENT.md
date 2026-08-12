# GESTE N°2 — LE DÉPOUILLEMENT, DÉPOSÉ AVANT LA CALIBRATION

*10 août 2026, 18 h 15. **Écrit pendant que le balayage est encore muet** — aucun de ses chiffres
n'a été vu. C'est le seul moment où ce dépôt est gratuit.*

**Fiches relues ⟨règle 10⟩** : `porte-a2-tient-instrument-valide`, `cout-exposition-par-metre`,
`accord-sur-zero-nest-pas-accord`, `mesure-doit-savoir-echouer`.

## LA RÈGLE QUI GOUVERNE CE DÉPÔT

⟨Fable, 10/08⟩ *« Fige à l'aveugle ce que le point de fonctionnement ne décide pas : grandeur,
appariement, niveau, et la lecture selon R14 — c'est le prix de l'erreur qui choisit borne ou
estimation, pas la calibration. Mais la taille dépend de la variance, donc de la bande, et un
seuil en points à taux de base inconnu n'est pas un seuil. **Dépose des formules, pas des
chiffres** ; la calibration les remplira mécaniquement, sans discrétion. »*

**Tout ce qui suit en toutes lettres est figé. Tout ce qui suit en formule sera rempli par la
calibration, mécaniquement — je n'aurai aucune main à y mettre.**

## CE QUI EST FIGÉ MAINTENANT, ET NE BOUGERA PLUS

**Grandeur** : la **PRISE** — l'objectif est-il tenu à la fin de l'accrochage. Lue par
accrochage, en oui/non, sur le champ `pris` du générateur. Pas la durée tenue, pas les pertes,
pas la distance minimale : **la prise**, parce que c'est ce que la mission prétend acheter.

**Appariement** : **par lieu** ⟨règle 12⟩. Le bras professeur et le bras témoin sont comparés
*à l'intérieur* de chaque lieu, jamais entre lieux. Aucune comparaison ne traverse jamais deux
lieux — c'est une propriété du plan, pas un compromis.

**Niveau** : **95 %**. Pas 99 : le durcissement du geste n°1 était le **péage d'une seconde
vue**, et cette campagne-ci n'a pas encore été regardée. Si elle l'est une fois et rejugée, le
même péage s'appliquera.

**Lecture ⟨règle 14⟩** : **sur la BORNE inférieure**, jamais sur l'estimation. Le prix de
l'erreur ici est cher et asymétrique — certifier un geste qui n'appuie rien envoie tout l'étage
au-dessus construire sur du vide, tandis que rater un geste réel coûte une campagne de plus.
⟨Fable : *« c'est le prix de l'erreur qui choisit la lecture. Cher et asymétrique → la borne. »*⟩

**Seuil** : **10 points de prise**, inchangé, celui de la porte 0 du lieu. Le retoucher en voyant
un chiffre serait l'amendement interdit ⟨règle 13⟩.

**Nombre de lieux** : **L ≥ 8**, les lieux déjà chassés en jeu.

## CE QUI EST DÉPOSÉ EN FORMULE, ET QUE LA CALIBRATION REMPLIRA

Soit `p` le taux de prise au point de fonctionnement — **rendu par le balayage, pas choisi**.
Soit `n` le nombre d'accrochages par bras et par lieu, `L` le nombre de lieux.

1. **Bruit d'accrochage, par lieu** — c'est la leçon chèrement payée du geste n°1, où les trois
   quarts de « l'éventail entre couloirs » étaient ceci et non de l'hétérogénéité :

   `σ²_binom = 2 · p · (1 − p) / n`

2. **Hétérogénéité vraie entre lieux**, obtenue par soustraction et jamais autrement :

   `σ²_lieux = max(0 ; s²_observé − σ²_binom)`

3. **Erreur-type de l'écart moyen apparié** :

   `SE = √( (σ²_lieux + σ²_binom) / L )`

4. **LA PORTE** :

   `écart_moyen − 1,96 · SE ≥ 10 points`

5. **LA TAILLE** — c'est elle qui manquait au geste n°1, et son absence a coûté la campagne
   ⟨*« un raté d'un dixième sur une porte non dimensionnée n'est pas un verdict, c'est une
   mesure inachevée »*⟩ :

   `n` est le plus petit entier tel que, si l'effet vrai valait `Δ`, la borne atteindrait
   10 points avec probabilité **0,8** :

   `Δ − 1,96 · √((σ²_lieux + 2p(1−p)/n) / L) ≥ 10`  avec une marge de puissance de 0,84 SE

   soit `n ≥ 2p(1−p) / ( L·((Δ − 10)/2,80)² − σ²_lieux )`

   **`Δ` est figé à 20 points** — le double du seuil. Ce n'est pas une prédiction du résultat :
   c'est la déclaration de ce qui vaut la peine d'être détecté, et elle s'écrit sans connaître
   `p`. Si le dénominateur est négatif, **aucun `n` ne suffit** : l'hétérogénéité entre lieux
   dépasse à elle seule le budget, et il faut alors **plus de lieux, pas plus d'accrochages**.

## CE QUI FERAIT ÉCHOUER LA CAMPAGNE — écrit avant

- **La borne à 95 % n'atteint pas 10** → le geste n°2 ne certifie pas, et on le dit.
- **Le dénominateur de la taille est négatif** → on ne lance pas la campagne ainsi ; on chasse
  des lieux supplémentaires. Lancer quand même serait payer un serveur pour une porte qu'aucune
  quantité d'accrochages ne peut ouvrir.
- **Le balayage ne rend aucune bande sur les trois axes** → le générateur se redépose, et ce
  dépouillement attend le nouveau ⟨butoir de campagne du 10/08⟩.
- **Un lieu rend moins de `n` accrochages par bras** → il n'entre pas dans la moyenne appariée,
  et son absence est **écrite**, pas compensée.
- **Un contrôle tombe** — fuite de groupes, erreurs de script, bras déséquilibrés → aucun
  verdict ce jour-là.

⚠️ **Ce dépôt ne contient volontairement aucun chiffre issu du monde.** `p` viendra du balayage,
`s²_observé` de la campagne. Si l'un des deux se retrouvait ici en dur, c'est que quelqu'un —
moi — aura regardé avant l'heure.
