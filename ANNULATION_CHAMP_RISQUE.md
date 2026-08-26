# ⛔ ANNULATION — la pré-inscription du champ de risque, avant tout entraînement

**26/08/2026.** `PREINSCRIPTION_CHAMP_RISQUE.md` (`b1ecc8e`) est **annulée avant d'avoir
consommé une seule heure de calcul**.

## Pourquoi

Une **autre conversation du même projet** a déjà mesuré exactement sa prédiction C1 :

| bras | prise |
|---|---|
| **A — 12 nombres, MLP** | **49,6 %** |
| **P — 12 nombres + le prix des 8 actions** | **47,2 %** |

**Mettre le prix du terrain dans l'entrée d'un apprenant ne donne rien.** C1 prédisait
+5 points ; la mesure existante dit **−2,4**. **On ne rejoue pas une question tranchée.**

## Et le résultat qui compte, qu'elle a trouvé

La **greffe** : politique **figée**, zéro gradient, parmi ses 3 actions les plus probables
prendre **la moins chère** au sens du danger → **39,3 % à 61,6 %**, dont **+15,3 points
attribuables au prix** par un contrôle à permutation retirée à chaque décision.

> **+15,3 points récoltables sans un seul gradient — et ZÉRO quand on pose la même
> information dans l'entrée d'un apprenant.**

Leur verdict : **l'attribution du crédit**, chaque autre suspect exonéré par mesure
(le monde, l'échelle, l'architecture, le juge).

## Ce que ma ligne apporte à la leur, et qui n'y est pas

**Un mécanisme concret sous leur « attribution du crédit ».** Mesuré le 25/08 :

- **les dégâts se calculent sur la géométrie de FIN de pas** — un homme caché à l'arrivée
  n'a **rien** pris, dénominateur **nul** dans toutes les bandes de distance ;
- l'observation, elle, décrit la position **quittée** ;
- d'où l'inversion de signe de `los` : **0,11×** à 0-40 m, **3,71×** au-delà de 130 m.

> **L'observation est un compte rendu du passé, pas une variable de décision.**
> Ça explique pourquoi le prix marche **au décodage** — il évalue des **destinations** — et
> pas dans l'entrée, où il est noyé parmi des colonnes qui décrivent l'endroit qu'on quitte.

⚠️ **Deux réparations à moi ont été codées et mesurées avant d'être payées, et ont échoué** :
`los` contre tous les défenseurs plutôt que le plus proche, et le sens du rayon inversé.
Aucune ne redresse le signe. **C'était le temps, pas la géométrie.**

## Une donnée pour leur greffe

**`champ_R = 35 m` alors qu'un pas fait 14 m.** Leur greffe évalue donc le danger d'un point
**deux fois et demie plus loin** que là où l'action mène — et elle **marche**. Deux lectures :
un hasard heureux, ou le signe que ce qui compte est le danger de la **DIRECTION** et non du
point d'arrivée. **Ça se tranche en une mesure** : rejouer la greffe à `champ_R = 14` et
comparer. Si 14 fait moins bien que 35, la seconde lecture tient.

⭐ **Cliquet : avant de pré-inscrire, lire ce que les autres fronts du projet ont déjà
mesuré.** J'allais payer sept heures pour une question tranchée dans une autre conversation.
