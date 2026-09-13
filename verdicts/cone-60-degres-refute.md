# Le cône à ±60° ne suffit pas à expliquer l'angle mort

*Verdict du 13/09/2026. Labo MCP, site plat certifié [24100, 18900]. Dépend de [angle-mort-certifie-arma].*

## L'hypothèse

La récolte du moteur donne `maxHeadTurnAI = 60` et `minHeadTurnAI = −60` sur `CAManBase`, dont dérive
tout fantassin ; l'arme ne pivote que de ±30° avant que le corps ne suive. Le dossier de nuit en fait
un candidat pour la mesure du 2 août : un ennemi à 50 m sur le flanc reste invisible quand un ennemi
à 300 m droit devant est vu 94 % du temps. « La falaise n'était pas une portée, c'était un cône. »

Prédiction testable : si le cône d'observation est borné à ±60°, la détection doit rester rapide
jusqu'à 60° puis s'effondrer juste après.

## Le banc, et les deux fois où il était faux

Un défenseur seul, immobile, orienté au nord. Un assaillant seul, immobile, à 150 m, à un angle
relatif variable, en mode BLUE pour qu'il ne se trahisse pas en tirant. On mesure le temps jusqu'à
ce que le défenseur le connaisse, plafonné à 60 s.

**Contrôle positif** : `checkVisibility` est purement géométrique et ignore l'orientation ; il doit
valoir à peu près pareil à tous les angles.

Deux versions du banc ont été jetées avant d'obtenir une mesure :

1. Unités créées par `createGroup west` + `createUnit` : elles ne sont **jamais vivantes** dans cette
   mission. Remplacé par `LABO_fnc_poser_groupe`, qui crée avec `createGroup [côté, true]`.
2. Site sur terrain en pente : l'œil du défenseur à 127 m ASL, la cible à 131 m, sol à 125 m. Le rayon
   était bloqué par une bosse, `checkVisibility` valait 0 partout. Remplacé par un site cherché sur
   400 sondes : dénivelé **nul** sur huit directions à 150 m, aucune ligne bloquée.

Le contrôle positif ne passe qu'à la troisième version : vue géométrique **1,00 sur les huit angles**.

## Ce qui est mesuré

| Angle | Vue | Détecté à | Cap final du défenseur |
|---|---|---|---|
| 0° | 1,00 | 28 s | 0° |
| 30° | 1,00 | 28 s | 1° |
| 45° | 1,00 | **jamais** | 0° |
| 60° | 1,00 | **jamais** | 0° |
| 75° | 1,00 | 50 s | **43°** |
| 90° | 1,00 | 55 s | **58°** |
| 120° | 1,00 | jamais | 0° |
| 180° | 1,00 | jamais | 0° |

## Le verdict

**L'hypothèse ne tient pas telle quelle.** Si la détection était bornée à ±60°, on détecterait à 45°
et à 60°, et jamais à 75° ni 90°. C'est l'inverse qui se produit.

La colonne du cap est le fait le plus intéressant : aux deux angles détectés au-delà de 60°, le
défenseur a **tourné** — cap final 43° et 58°. Il a pivoté vers la menace et l'a acquise. Aux angles
non détectés, il n'a pas bougé.

## Ce que ce verdict ne dit pas

- **n = 1 par angle.** Huit essais ne séparent pas un secteur mort d'un tirage malheureux.
- Les cas « jamais » à 45° et 60° restent inexpliqués, et ils sont les plus gênants pour toute
  théorie simple, y compris celle qu'on vient de réfuter.
- `maxHeadTurnAI` n'est pas réfuté comme **paramètre** : il est réfuté comme **explication suffisante**
  de la falaise angulaire du 2 août.

## La mesure suivante

Cinq répétitions par angle, et le cap journalisé en continu plutôt qu'à la fin, pour voir *quand* le
défenseur tourne et si la rotation précède ou suit l'acquisition.
