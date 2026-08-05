# A/B instrumenté — critères écrits AVANT toute donnée

*5 août 2026, 6 h. Le générateur n'est pas encore modifié.*

## Pourquoi on refait un fait déjà établi

Le **+12,3 points** de l'attaque à deux axes (1324 engagements, p < 0,0001) est le seul fait
fort du projet et le seul mécanisme inconnu. Il date du **2 août**, donc **d'avant toutes les
corrections** de ces trois jours.

> **Règle 1 du labo : avant d'ajouter quoi que ce soit pour corriger un défaut, mesurer que
> le défaut existe encore.** Appliquée ici au fait lui-même.

Et ses journaux bruts sont **perdus** : seul le résultat agrégé subsiste. On ne peut donc ni
le vérifier, ni en chercher le mécanisme. Ce run fait les deux d'un coup.

## Ce qu'on instrumente, et pourquoi chaque champ

| journal | cadence | ce qu'il permet |
|---|---|---|
| **positions** de chaque homme | 1 Hz | reconstruire les trajectoires, mesurer qui arrive et quand |
| **tirs avec cible** (`assignedTarget`) | à l'événement | qui tire sur qui — validé à **+17 points** de mortalité sur le corpus |
| **`knowsAbout`** par paire vivante | 0,2 Hz | qui sait quoi, et à quel instant |
| **arrivée par axe** | au franchissement | **la lecture non testée** : le flanc fait-il *arriver* plutôt que *survivre* ? |
| **verdict** détaillé | à la clôture | prise, cause, pertes de chaque camp |

Le quatrième est le cœur : le A/B mesurait la **prise d'objectif**, pas la survie, et j'ai
cherché son mécanisme dans la mortalité pendant toute une nuit.

## Les critères

**A0 — LES JOURNAUX SONT COMPLETS.** Vérifié par un **smoke de 3 engagements** avant le run
long. Chaque engagement doit produire : ≥ 1 ligne de position par homme et par seconde, ≥ 1
tir avec cible identifiée, ≥ 1 relevé de `knowsAbout`, un verdict. Si un seul champ manque,
**on ne lance pas les 8 heures**.

**A1 — LE FAIT TIENT-IL ?** `deux_axes` contre `frontal`, effectif total égal, configurations
brassées. Écart **≥ +6 points** de taux de prise, **p < 0,05**.

⟨le seuil est à la moitié du +12,3 mesuré le 2/08 : on demande que l'effet tienne, pas qu'il
soit identique. Un effet qui s'effondre sous 6 points serait un fait fragile.⟩

**A2 — CONTRÔLE POSITIF INTÉGRÉ.** Quelques configurations où les défenseurs sont **figés
face à un seul axe**. Là, le deux-axes **doit écraser**. S'il n'écrase pas, **c'est
l'instrument qui est cassé, pas le fait** — et rien d'autre n'est lisible.

**A3 — PLAFOND SCRIPTÉ.** Une doctrine écrite à la main — crochet plus base de feu — sert de
référence haute. **Si elle ne passe pas le critère, le banc ferme avant d'avoir jugé
quiconque.** C'est la règle 2 transposée : sur un banc à objectif il n'y a pas de chemin
optimal calculable, donc le plafond est une doctrine, pas une géométrie.

**A4 — CONTRÔLE NUL.** Le même bras rejoué doit donner un taux de prise voisin. Si la
variance entre répétitions dépasse l'écart entre bras, on ne conclut rien.

## Ce qui ferait échouer ce run, dit d'avance

- si **A0** cède, on n'a pas de mécanisme, seulement un chiffre — et on aura refait l'erreur
  du 2 août ;
- si **A2** cède, l'instrument est cassé et **A1 n'est pas lisible**, quel que soit son p ;
- si **A1** cède alors que A2 et A3 passent, alors **le +12,3 ne tient pas** — le fait
  fondateur du projet devient suspect, et c'est un résultat majeur, pas un échec.

## Ce que ce run ne dira pas

Il ne dira pas si l'agent est bon. Aucun agent n'y participe. **Aucun entraînement GPU tant
que A2 et A3 ne sont pas passés** — c'est la consigne explicite.

## Interdits en vigueur pendant ce chantier

Banc à 150 m et toute variante d'approche solitaire · bancs d'escouade · étape 5 comme
fonction de coût · tout raffinement d'`expo` · champ de risque · émetteur d'arêtes v9 ·
**tout ajout d'observation à l'agent**, y compris « être visé », tant qu'aucun défaut n'est
mesuré sur la version courante.
