# Témoin du FEU REÇU — critères redéposés avant tout comptage

*6 août 2026, 11h. ORDRE 5 de Fable. Corpus A2 figé (301 accrochages). **Attestation : aucune
décomposition par bras du tir n'a été calculée, affichée ni entrevue** — le dépouilleur
précédent s'est arrêté sur son contrôle de cohérence, avant la lecture des bras, et sa sortie
en fait foi.*

## Pourquoi ce fichier remplace le précédent

Le premier témoin visait l'**intention** : « qui le défenseur désigne-t-il comme cible ». Il
supposait un journal échantillonné en continu. **Le journal ne l'est pas** : `TIR` est émis sur
l'événement `Fired`, donc une ligne n'existe que si le défenseur **tire pour de bon**. Dans 26 %
des accrochages, aucun défenseur n'a tiré sur un assaillant.

> Corriger la description de l'instrument n'est pas assouplir la porte. La faute serait de
> retoucher le seuil **après avoir vu le verdict** — or aucun chiffre par bras n'existe.

Le témoin change donc d'objet, et il se rapproche de ce qu'on cherche : **le feu reçu**. Car le
sursis, c'est précisément *ne pas être pris à partie*.

## Les trois métriques

**A — FEU REÇU.** Part des assaillants pris pour cible au moins une fois par un défenseur
(`TIR` défenseur → assaillant), moyennée **par accrochage**. Un défenseur se reconnaît à son
axe : `-1` dans le journal de position.

**B — IMPACTS REÇUS.** Part des assaillants touchés au moins une fois (`HitPart`), même
moyenne. C'est la grandeur solide : un impact ne s'interprète pas.

**C — ACCROCHAGES MUETS.** Part des accrochages sans aucun tir défenseur, **par bras**. Un
accrochage muet est une **donnée**, pas un trou : zéro feu reçu, c'est le sursis joué à fond.
Rapporté séparément, accompagné de la **distribution des durées par bras** — pour vérifier que
les muets ne se concentrent pas dans un bras pour une raison parasite.

Lecture **au niveau de l'accrochage**, jamais de l'homme : les hommes d'un même accrochage ne
sont pas indépendants.

## La sensibilité, écrite avant de compter

Effectifs : **160 accrochages deux_axes, 140 frontal.**

Avec une dispersion des parts d'environ 0,30 d'un accrochage à l'autre — ordre de grandeur
attendu pour une proportion moyenne autour de 0,5 —

> **ce corpus voit un écart d'environ 10 points ou plus.** En dessous, un résultat non
> significatif ne veut rien dire, et il faudra l'écrire ainsi au lieu de conclure.

Le dépouilleur **imprimera la dispersion réellement observée** à côté de ce chiffre. Si elle
dépasse nettement 0,30, la porte est moins sensible que prévu et je le dirai avant de lire
les bras.

## Ce qui tranche

**ÉTABLI — le sursis.** Le deux_axes reçoit significativement **moins** de feu (A, p < 0,05,
écart ≥ 10 points), cohérent sur B — **alors qu'il est vu davantage** (+6,6 points, acquis).
→ Ils savent et ne peuvent pas tirer. L'étage 1 devra porter le risque d'**engagement**.

**MORT.** Feu reçu **égal ou supérieur** sur A **et** B.
→ L'hypothèse tombe, le mécanisme reste non établi, et on cesse de le chercher de ce côté.

**ZONE MIXTE.** A et B se contredisent, ou l'écart reste sous les 10 points.
→ On garde les chiffres, **on n'écrit pas d'histoire**, et l'étage 1 part sans réorientation.

Dans les trois cas : **le flanc reste fermé. Aucune nuit supplémentaire de ce côté.**

## Contrôles de cohérence — inchangés, et ils gardent le droit de tout arrêter

1. **Les morts doivent être touchés à ≥ 90 %.** Un mort se reconnaît à ce que le journal de
   position cesse de l'écrire — il ne logue que les vivants. *Passé au tour précédent : 94,3 %.*
2. **Le corpus doit contenir du feu défenseur.** Au moins 60 % des accrochages avec au moins un
   tir défenseur. *Seuil fixé ici à la couverture réelle de l'instrument, mesurée à 74,3 %, et
   non à une attente inventée — c'est précisément l'erreur qu'on corrige.*

## Ce que ce journal ne pourra JAMAIS dire

Si les défenseurs **suivent** le flanc sans tirer. Cette question a un prix connu : un re-run
avec `assignedTarget` échantillonné toutes les 2 secondes, indépendamment du tir.

> **Règle déposée par Fable, appliquée telle quelle** : si ce témoin sort ÉTABLI ou MORT, pas
> de re-run. S'il sort MIXTE, le re-run part la nuit prochaine sur le CPU, à condition que le
> battement de cœur de l'étage 1 ne montre pas d'écroulement de débit. Si les deux se gênent,
> l'étage 1 gagne.
