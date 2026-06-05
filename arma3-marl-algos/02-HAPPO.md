# HAPPO
### « S'améliorer ensemble, à coup sûr, quand on est différents »

## Le problème qu'il résout

MAPPO suppose volontiers que les agents sont interchangeables (un même cerveau partagé). Mais ton
équipe est faite de **rôles distincts** : un chef, un médecin, un mitrailleur. Surtout, un danger
guette toute équipe qui apprend : si **tous se corrigent en même temps**, chacun suppose que les
autres ne bougent pas — et tout le monde se trompe ensemble. On appelle ça le « pas de deux
catastrophique » : deux agents qui, chacun raisonnant juste de son côté, produisent ensemble une
régression. Rien ne garantit alors que l'équipe progresse.

## L'idée centrale

**On se corrige l'un après l'autre, pas tous à la fois.** Chaque agent s'ajuste *en tenant compte*
du changement que les précédents viennent de faire. Cet ordre — d'apparence anodine — suffit à
**garantir mathématiquement** que l'équipe ne recule jamais d'une étape à l'autre (amélioration dite
*monotone*). C'est la grande force théorique de HAPPO.

## Le mécanisme, pas à pas

1. On fige une référence : la politique d'équipe actuelle.
2. **Agent 1** calcule sa meilleure petite correction (à la PPO, avec la laisse *ε*) et l'applique.
3. **Agent 2** calcule la sienne, mais **en intégrant** ce que l'agent 1 a déjà changé.
4. **Agent 3**, puis 4, de même — chacun voit l'effet cumulé des précédents.
5. L'ordre peut être tiré au hasard à chaque tour, pour ne privilégier personne.
6. Comme chacun ne fait qu'un petit pas (laisse *ε*) *et* tient compte des autres, le total des pas
   améliore l'équipe sans la déstabiliser.

## Les formules, traduites

**① La mise à jour en cascade.**

<div class="formule">agent 1 se corrige → agent 2 se corrige (sachant le pas de 1) → agent 3 (sachant 1 et 2) → …</div>

> *Pour un littéraire :* des musiciens qui s'accordent **à tour de rôle**. S'ils tendaient tous leur
> corde en même temps sans s'écouter, l'orchestre sonnerait faux ; en s'accordant l'un après
> l'autre, chacun se règle sur ce que les précédents ont déjà fait.

**② La garantie d'amélioration monotone.**

<div class="formule">valeur de l'équipe APRÈS le tour ≥ valeur AVANT  (jamais de recul, prouvé)</div>

> *Pourquoi c'est rare et précieux :* la plupart des méthodes multi-agents *espèrent* progresser ;
> HAPPO le **garantit**, à la manière dont TRPO/PPO le garantissaient pour un agent seul. La cascade
> est précisément ce qui transporte cette garantie du solo vers le groupe.

## Un exemple concret

Le chef décide de resserrer la formation ; **puis** le mitrailleur ajuste sa position de tir *en
sachant* que la formation s'est resserrée ; **puis** le médecin se replace *en sachant* où sont
désormais les deux autres. Personne n'optimise « dans le vide ». Si, au contraire, les trois
s'étaient repositionnés simultanément en imaginant les autres immobiles, ils auraient pu se
masquer mutuellement les angles de tir — une régression que la cascade évite.

## Variantes & pièges

- **HATRPO** : la même idée avec la contrainte dure de TRPO (plus rigoureuse, plus lourde).
- **HASAC** : variante hors-politique (entropie maximale), plus économe en données.
- **MAT** (*Multi-Agent Transformer*) : traite l'équipe comme une *séquence* à décider l'un après
  l'autre — cousin moderne de l'idée de cascade.
- *Pièges :* l'ordre séquentiel coûte un peu en calcul ; et il faut un critique central bien conçu,
  comme pour MAPPO.

## Pourquoi on l'utilise ici

Ton équipe est **hétérogène par conception**. HAPPO est taillé pour ça : il évite que les quatre se
marchent dessus en se corrigeant en même temps, et il offre une **progression sûre** là où MAPPO
« simple » suppose des agents semblables. C'est le moteur recommandé pour « 1 chef + 3 spécialistes ».

<div class="philo">En dernier regard. HAPPO énonce une vérité politique : une communauté de rôles distincts ne tient pas par la simultanéité, mais par l'ordre du dialogue. On ne parle pas tous en même temps ; on s'écoute, on tient compte de ce que l'autre vient de faire. Adam Smith y voyait la division du travail ; Durkheim, la « solidarité organique » — cette cohésion paradoxale où c'est la différence des fonctions, non leur uniformité, qui soude le corps social. L'algorithme retrouve l'intuition : quatre êtres dissemblables deviennent une équipe non en agissant pareil, mais en s'ajustant tour à tour, chacun à sa place et au su des autres.</div>
