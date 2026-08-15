# VERDICT — le tarif n'explique RIEN. La piste est fermée, et elle en ouvre une autre.

Mesuré le 15/08/2026. Critères déposés avant dans `DEPOT_TARIF.md` (`513adf3`).
Même définition des deux côtés, sur la colonne `los` que la politique reçoit réellement.

## Les deux contrôles positifs passent

Tarif > 1 dans chaque monde (5,77 et 2,87), et bien plus de 30 morts de chaque côté
(251 et 63). La mesure rend un verdict.

## LE RÉSULTAT — et il est l'inverse de ce que j'attendais

| | pas exposés | morts | P(mort \| exposé) | pas non exposés | morts | P(mort \| abrité) | **tarif** |
|---|---|---|---|---|---|---|---|
| **GYMNASE** | 1324 | 154 | 0,1163 | 4811 | 97 | 0,0202 | **5,77** |
| **ARMA** | 713 | 49 | 0,0687 | 584 | 14 | 0,0240 | **2,87** |

**Rapport Arma / gymnase = 0,50.**

Ma bande déposée disait : **> 2** → Arma plus cher, piste ouverte ; **< 0,5** ou **0,5-2** →
piste fermée. **Le résultat tombe à la frontière exacte des deux bandes qui ferment — et
c'est sans conséquence, puisque les deux ferment.** Le dépôt avait été écrit exprès ainsi.

**Arma ne fait pas payer l'exposition plus cher. Il la fait payer DEUX FOIS MOINS CHER.**
S'exposer y multiplie le risque par 2,87 quand le gymnase le multiplie par 5,77.

**La piste du tarif est FERMÉE.**

## Ce que les mêmes chiffres montrent, et qui n'était pas la question posée

| | part des pas passés EXPOSÉ |
|---|---|
| gymnase | **21,6 %** |
| **Arma** | **55,0 %** |

**L'agent est exposé 2,5 fois plus souvent sur Arma.** Le prix unitaire y est deux fois plus
doux, la quantité consommée deux fois et demie plus grande — et la mortalité totale finit
par se ressembler (4,1 % par homme-pas au gymnase, 4,9 % sur Arma).

**Ce n'est pas le prix, c'est la quantité.**

⚠️ **Cette observation n'était PAS un critère déposé.** Elle sort des mêmes données que la
mesure du tarif, après coup. Elle ouvre une question, **elle ne rend aucun verdict** — et
la nommer maintenant, c'est choisir la question après avoir vu les chiffres. Elle se
déposera avant d'être mesurée.

## La piste qu'elle ouvre, et son lien avec ce qui est déjà mesuré

`dcover` : médiane **0,035 au gymnase contre 0,100 sur Arma** — le couvert est **trois fois
plus loin** sur Arma. Un agent qui a appris que l'abri est à une cellule le cherche là où
il n'est pas.

Il faudra vérifier que ce n'est pas le vieux défaut sous un nom neuf : la sandbox protège
**11× trop** derrière le couvert (`sandbox-fidelite-arma-mesuree`). Un couvert trop
protecteur ET trop proche produit exactement un agent qui s'expose sans compter.

## Ce que ça ne dit pas

Rien sur la façon de corriger. Et le rapport 0,50 étant à la frontière, je ne cite pas
« Arma est deux fois plus clément » comme un acquis — je cite que **le tarif n'explique pas
l'écart**, ce que les deux bandes affirment ensemble.
