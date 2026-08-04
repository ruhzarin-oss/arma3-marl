# Critères du champ de risque — écrits AVANT le ré-entraînement

*4 août 2026, minuit passé. Aucune donnée de ce run n'existe au moment où ce fichier est
écrit. Les seuils sont traduits d'un dispositif déposé le 27 juillet et jamais conclu.*

## Le diagnostic qui justifie ce pas

Mesuré le 27/07, jamais invalidé : **même manœuvre, même quantité, mauvais moment.**

| | distance moyenne du détour |
|---|---|
| crochet scripté | **184 m** |
| appris voyant | **132 m** |
| appris aveugle | 123 m |
| assaut frontal | 118 m |

L'exposition n'a pas le même prix partout — **0,07 par pas à 200 m, 0,20 à 25 m**. Le crochet
achète tout son écart au tarif du long puis rentre en ligne droite ; l'appris achète le même
écart au milieu du terrain, au tarif fort.

**L'agent ne peut pas apprendre que l'exposition lointaine est bon marché : rien dans son
observation ne lui donne le prix avant de le payer.**

## Ce qu'on branche

Huit nombres dans `moi` : **l'exposition qu'il subirait à 35 mètres** dans chacune des huit
directions cardinales et intercardinales.

Trois choix, repris tels quels du 27/07 :

- **à 35 m, pas au pas suivant** — c'est l'échelle de la MANŒUVRE, pas du réflexe ;
- **le PRIX, jamais la réponse** — on donne l'exposition, pas « va par là ». Le moins cher
  est toujours de fuir ; l'arbitrage reste entier ;
- **géométrie générique** — même principe que la coque à 12 rayons.

## Les seuils, et la traduction que j'assume

Le 27/07 avait figé : **expo ≤ 0,0180 et détour repoussé à ≥ 155 m**, sur un départ à 250 m.
Le banc actuel part de **150 m** : un détour à 155 m y est géométriquement impossible.

**Je traduis donc le seuil en fraction du rayon de départ, et je le fais maintenant, avant
toute donnée :**

```
155 m sur un départ de 250 m  =  62 % du rayon
appris voyant : 132 / 250     =  53 %
crochet       : 184 / 250     =  74 %
```

> **Seuil de signature : la distance moyenne du détour doit atteindre 62 % du rayon de
> départ.** Sur un banc à 150 m, cela fait **93 m**.

C'est une traduction d'échelle, pas un assouplissement : la fraction est identique.

## Les deux critères, tous deux exigés

**C1 — LE BANC.** L'agent bat strictement la ligne droite sur **≥ 15 configurations sur 20**
au banc 150 m. Critère intouché depuis sa première rédaction.

**C2 — LA SIGNATURE.** La distance moyenne du détour atteint **≥ 62 % du rayon de départ**.

⟨Fable, 04/08 : « le 27/07 avait pour critère *un gain*, et un gain de −28 % n'a pas suffi.
Cette fois le critère est double et mécaniste. **Un gain sans la signature = le canal
perception est clos.** »⟩

## La mesure de la signature

Pour chaque pas de la trajectoire : la composante du déplacement **perpendiculaire** à la
direction de l'objectif, pondérée par la distance à l'objectif à cet instant. La moyenne
pondérée donne la distance à laquelle le détour a réellement été acheté.

C'est la définition du 27/07, recalculée hors ligne depuis les trajectoires exportées.

## Condition d'échec, déposée d'avance

Si **C1 échoue** (moins de 15/20) **ou** si **C2 échoue** (détour sous 62 % du rayon) :

> **Plus aucun ajout d'observation n'est recevable.** Le canal « il lui manque quelque chose
> à percevoir » est clos. Le suspect devient celui que le programme désignait déjà :
> **l'étape 5 — apprendre dans le rejeu au lieu d'apprendre en mourant.**

C'est le troisième essai sur ce levier depuis le 27/07 ; il n'y en aura pas de quatrième.

## Contrôle de coût

Le surcoût mesuré le 27/07 était de **×1,4** seulement, le GPU étant sous-employé. Si le
surcoût dépasse ×2,5 ici, le champ est recalculé moins souvent — mais jamais supprimé
sans le dire.
