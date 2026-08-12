# LE COÛT PAR MÈTRE GAGNÉ — protocole v2, déposé avant le premier accrochage

*11 août 2026, 11 h 30. Le banc du coût tourne sur le port 6042, monde calibré du 10/08.*

## CE QUE LA v1 A COÛTÉ, ET CE QU'ELLE A APPRIS

La v1 a rendu un verdict positif — rapport 2,17, borne 1,49, permutation p = 0,0010 — sur un
**dénominateur qui ne mesurait pas ce qu'il nommait**. `_dmin` est la distance minimale à un
défenseur **vivant** ; la boucle qui l'entretient ne parcourt que les vivants, donc elle cesse
de tourner quand la défense tombe. Résultat : 3935 m sur une prise réussie, et **168 accrochages
PRIS déclarés « à gain nul »**.

⚠️ **Le contrôle qui manquait, et qu'on ajoute ici** : aucun de mes quatre contrôles ne demandait
si un champ **mesure la chose qu'il nomme**. Ils vérifiaient des tailles et des séparations.

> **CONTRÔLE DE SENS, désormais obligatoire sur tout champ qui entre dans une grandeur** : le
> champ doit se comporter comme son nom l'exige sur un cas dont on connaît la réponse. Ici :
> **un accrochage PRIS doit avoir gagné des mètres.** Si un seul pris affiche un gain nul, le
> champ ne mesure pas la distance à l'objectif, et rien ne se lit ce jour-là.

## LA GRANDEUR, MAINTENANT JOURNALISÉE

Le banc échantillonne toutes les 2 s, **par homme** : `HMT|G|POS|<accrochage>|<temps>|<homme>|
<distance à l'objectif>`.

> **Coût d'un homme = suppression subie (s) / mètres gagnés.**
> - **Suppression subie** = nombre d'échantillons `VISE` où un défenseur l'a désigné, × 2 s.
> - **Mètres gagnés** = sa distance initiale à l'objectif moins sa distance minimale atteinte.
>
> Le coût d'un accrochage est la **moyenne sur ses hommes**. ⟨on lit par HOMME parce que c'est
> l'homme qui est désigné dans `VISE` — la grandeur et son étiquette vivent au même niveau⟩

## LA LECTURE ⟨règle 14⟩ — inchangée depuis la v1

> **L'acquis est rétabli si la borne inférieure de l'intervalle à 95 % du rapport
> `coût(non pris) / coût(pris)` dépasse 1.**

Bootstrap 4000 tirages — la distribution des coûts est très asymétrique, une approximation
normale mentirait. **Aucun seuil chiffré n'est repris de juillet** : le 1,86 portait sur une
autre grandeur. ⟨Fable : *« ce qui se transporte, c'est le SIGNE et l'ordre, jamais le
chiffre »*⟩ La valeur sera **rapportée, pas comparée**.

## LES CONTRÔLES — lus AVANT la grandeur

1. **SENS — un accrochage pris a gagné des mètres.** Zéro exception tolérée.
2. **SENS — la distance décroît en moyenne au fil du temps.** Un homme qui avance se rapproche.
3. **POSITIF — les non pris perdent plus d'hommes** que les pris.
4. **NUL — l'étiquette permutée 1000 fois ne reproduit pas le rapport observé.**
5. **TAILLE — au moins 30 accrochages par bras.** En deçà : insuffisant, jamais « pas d'effet ».
6. **DÉNOMINATEUR — les hommes à zéro mètre sont comptés et nommés**, jamais exclus en silence.

## CE QUI FERAIT ÉCHOUER — écrit avant

- **Un contrôle de sens tombe** → le champ ne mesure pas ce qu'il nomme, et **rien** ne se lit.
  C'est la leçon de la v1, écrite en dur.
- **La borne n'atteint pas 1** → l'acquis ne revient pas, il reste au registre des sursitaires.
- **Le contrôle nul passe** → c'est du bruit d'échantillonnage, pas une séparation.
- **Le rapport ne tient que grâce aux hommes à zéro mètre** → artefact de dénominateur, dit
  comme tel.
