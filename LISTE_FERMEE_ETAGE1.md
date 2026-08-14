# LA LISTE FERMÉE DE L'ÉTAGE 1 — déposée avant la campagne 4

*14 août 2026. ⟨Fable⟩ « Trois chutes pour trois raisons, c'est la méthode qui attrape ET un
banc en série trop long : son verdict dépend d'une chaîne de canaux dont chacun peut le rendre
muet. Dépose la liste fermée des canaux dont le verdict dépend, chacun sous pré-vol. Si la 4
tombe sur un canal de la liste, tu répares ; si elle tombe HORS LISTE, le banc est
sous-spécifié et se redépose entier, plus court. »*

## POURQUOI CETTE LISTE

Trois campagnes complètes — 48 essais chacune, 144 en tout — **aucun verdict**. Chaque fois pour
une raison différente, chaque fois légitime :

| campagne | ce qui est tombé |
|---|---|
| 1 | « le témoin délivre », minimum sur essai — un seul zéro condamnait tout |
| 2 | « l'appui se tait au témoin » — un coup échappé sur 24 |
| 3 | « les murets encaissent » — 37,5 % d'essais natifs sans impact |

**Ce n'est pas trois malchances. C'est un banc dont le verdict traverse trop de choses qui
peuvent casser.** La liste ci-dessous est le nombre de choses qu'on accepte de traverser.

## LA LISTE FERMÉE — sept canaux, et rien d'autre

Le verdict de l'étage 1 est le **rapport apparié par terrain des impacts délivrés** entre le
bras natif et le témoin. Il dépend de ceci, et **de rien d'autre** :

| # | canal | ce qu'il doit garantir | pré-vol |
|---|---|---|---|
| 1 | **les corps existent** | 6 défenseurs, 4 victimes, 3 appuis, à chaque essai | effectif relevé avant l'ordre |
| 2 | **les défenseurs délivrent** | le témoin produit des impacts sur les victimes | `delivre > 0` au pré-vol |
| 3 | **les deux chemins s'accordent** | `HandleDamage` ≈ 7,2 × `HitPart` | rapport dans ±20 % au pré-vol |
| 4 | **le témoin est silencieux** | zéro coup d'appui, arme retirée | `coupsapp = 0` au pré-vol |
| 5 | **le bras natif prend son ordre** | les appuis tirent | `coupsapp > 0` au pré-vol |
| 6 | **le tir du natif ARRIVE** | les murets encaissent | `murs > 0` au pré-vol |
| 7 | **les fusils tiennent** | personne ne s'assèche | réserve ≥ 60 coups |

⚠️ **Le canal 6 est celui qui vient de tomber**, et il est le seul dont la classe de panne n'est
**pas encore instrumentée** : on sait que 37,5 % des essais natifs ne touchent aucun muret, on
ne sait pas où vont leurs balles.

## LA RÈGLE, ÉCRITE AVANT LA CAMPAGNE 4

> **Si la campagne 4 tombe sur un canal de cette liste → on répare ce canal, et on relance.**
>
> **Si elle tombe sur autre chose → le banc est SOUS-SPÉCIFIÉ. Il se redépose ENTIER, et plus
> court** — moins de canaux entre la mesure et le verdict.

C'est la règle de l'arc appliquée au banc : une liste fermée déposée d'avance, et l'aveu que
sortir de la liste condamne la conception, pas l'exécution.

## ⚠️ CE QUI DOIT ÊTRE FAIT AVANT DE LANCER LA CAMPAGNE 4

**Le canal 6 doit être décomposé**, parce qu'on ne répare pas ce qu'on n'a pas séparé. ⟨Fable⟩
*« Deux pannes, pas deux faces — et ta table les sépare déjà. »*

- **Panne A — l'ordre est mort** : zéro coup tiré. Rare (1 essai sur 24). C'est la capture du
  piège, `prets` et `apn_avant` la voient.
- **Panne B — le coup ne porte pas** : le groupe tire **46 coups en moyenne** et ne touche
  rien. **Un groupe qui tire 46 coups a pris son ordre.** C'est un tiers des essais, et c'est
  une autre panne.

**Pour B, trois relevés à instrumenter, en lecture pure :** la **cible** de chaque tireur à
l'instant du coup, sa **ligne de vue** à cet instant, et **ce que le `HitPart` touche** quand ce
n'est pas un muret.

**Et un contrôle du capteur lui-même** : un tireur posé à distance connue face à un muret — le
compteur d'impacts doit compter. Sinon c'est le capteur qui est aveugle, pas le tir qui rate.

## ⚠️ CE QUE JE M'INTERDIS EN ÉCRIVANT CETTE LISTE

- **Comparer les 37,5 % au seuil de 15 %** : la sonde radio mesurait *l'ordre qui ne prend
  pas*, pas *le coup qui ne porte pas*. Même grandeur, même formule, **même échantillonnage** —
  et je ne l'avais pas appliqué à moi-même.
- **Requalifier `prets` sur les 28 essais** : la relation y est inversée et l'effectif minuscule.
- **Re-dériver un seuil pour le canal 6 avant d'avoir décomposé.** Un seuil par classe de
  panne, et les classes ne sont pas encore séparées.
