# CONTRAT DE L'ORDRE DE MISSION — figé avant toute ligne de code

Écrit le 2026-07-28. Un seul monde, l'objectif est un paramètre. Une escouade de 4.
Ce document est le contrat : tout ce qui n'y est pas ne doit pas exister dans le code.

---

## 1. L'ORDRE DE MISSION — 12 nombres, vus par l'agent à CHAQUE pas

| # | champ | valeur | note |
|---|---|---|---|
| 1-4 | **verbe** | one-hot : prendre / tenir / extraire / infiltrer | toujours exactement un actif |
| 5-6 | **objectif** | (dx, dy) depuis le départ, divisé par la distance max | où, pas quoi |
| 7 | **rayon de succès R** | R / R_max | à quelle distance on considère l'objectif atteint |
| 8 | **délai restant** | (T − t) / T | **recalculé à chaque pas** |
| 9 | **vies restantes** | (K_max − pertes) / A | budget, pas plafond |
| 10 | **exposition restante** | (E_max − expo_cumulée) / E_max | budget, pas plafond |
| 11 | **effectif vivant** | vivants / A | |
| 12 | **phase** | 0 = aller, 1 = retour | ne sert qu'à EXTRAIRE, 0 ailleurs |

### Trois règles non négociables

**A. Les budgets sont affichés en RESTANT, jamais en plafond.** Un plafond est une constante :
l'agent l'ignore au bout de dix épisodes. Un budget qui descend est la variable de décision
elle-même. C'est le choix le plus important de ce contrat.

**B. L'ordre ne contient AUCUNE information sur l'ennemi.** Ni position, ni effectif, ni
géométrie. Un ordre dit ce qu'il faut faire, pas ce qu'il y a en face. Sinon on n'apprend pas
la reconnaissance, on la contourne.

**C. Vecteur de taille FIXE, champs inutilisés à zéro.** Jamais de longueur variable selon le
verbe.

---

## 2. LES QUATRE VERBES — une seule fonction de récompense

Elle lit le verbe et n'en tire que deux choses : **la mesure de progrès** et **le prédicat de
succès**. Rien d'autre ne change entre les verbes.

| verbe | mesure de progrès (dense) | succès (terminal) | échec |
|---|---|---|---|
| **PRENDRE** | rapprochement du plus proche survivant vers l'objectif | ≥K hommes dans R, défenseurs neutralisés ou chassés, avant T | délai, ou escouade détruite |
| **TENIR** | temps passé avec ≥K hommes dans R | ≥K hommes dans R au pas T | point débordé avant T |
| **EXTRAIRE** | phase 0 : rapprochement vers le colis ; phase 1 : rapprochement du colis vers l'exfil | colis vivant sur la ligne d'exfil avec ≥K escorteurs | colis mort, ou délai |
| **INFILTRER** | rapprochement vers l'objectif, moins l'exposition dépensée | dans R **et** exposition cumulée < E | exposition dépassée, **même arrivé** |

### La règle anti-bricolage
**Aucun poids par verbe.** La pénalité de pertes est la même pour les quatre. Les différences
viennent des prédicats de succès et des budgets, jamais de coefficients ajustés mission par
mission. Le jour où un verbe « a besoin » d'un poids à lui, c'est qu'il n'appartient pas à
cette table.

---

## 3. CE QUI EST TIRÉ AU HASARD À CHAQUE ÉPISODE

| paramètre | plage |
|---|---|
| verbe | uniforme parmi les verbes actifs |
| distance de départ | 120 à 220 m |
| axe d'approche | 0 à 360° |
| rayon de succès R | 15 à 30 m |
| défenseurs D | 4 à 16 |
| géométrie défensive | arc, étalement, distance de ligne, décentrage — comme aujourd'hui |
| délai T | 40 à 80 pas |
| plafond de pertes K_max | 1 à 3 sur 4 |
| plafond d'exposition E_max | calibré pour qu'INFILTRER soit tendu, pas impossible |

Attaquants **A = 4**, fixe. C'est l'escouade, pas une variable.

---

## 4. L'AUDIT D'ORDRE — la garde qui décide si tout ça sert à quelque chose

Descendant direct de l'audit des boutons du 28/07 : **un paramètre qu'on croit piloter et qui
ne change rien.**

À l'évaluation, on rejoue les mêmes épisodes en **permutant le verbe** dans le vecteur d'ordre,
sans rien changer d'autre.

- **La réussite s'effondre** → l'agent LIT son ordre. Le monde paramétré a un sens.
- **La réussite ne bouge pas** → l'agent ignore l'ordre et joue la moyenne des verbes.
  Le monde paramétré n'apporte rien tant que ce n'est pas réparé. **Rien d'autre ne se lit.**

Seuil pré-enregistré : **chute d'au moins 20 points de réussite** sous permutation.

---

## 5. COMMENT ON JUGE

- **Par verbe séparément**, jamais en moyenne globale — une moyenne cache un verbe raté.
- **≥5 graines**, moyenne rapportée (mesure de variance du sandbox du 28/07 : étendue 8,5 pts
  sur 12 graines, une seule graine ne suffit pas).
- **Tirages tenus à l'écart** : les épisodes d'évaluation ne sont jamais ceux d'entraînement.
- **Étalon à battre**, un par verbe, tiré de `manuel.py` : appui-mouvement pour PRENDRE,
  ligne défensive pour TENIR, débordement simple pour EXTRAIRE, infiltration pour INFILTRER.
  L'agent ne les exécute pas : il doit faire mieux.

---

## 6. ORDRE DE CONSTRUCTION

1. **PRENDRE + INFILTRER** — deux monnaies opposées (des vies contre de l'exposition), et
   presque tout existe déjà. C'est le test décisif : une seule politique tient-elle deux
   objectifs contraires ?
2. **EXTRAIRE** — demande une entité colis et une ligne d'exfiltration.
3. **TENIR** — demande un ennemi qui manœuvre. C'est un chantier, pas un paramètre.

**Portes** : on ne passe à l'étape suivante que si l'audit d'ordre passe à l'étape en cours.

---

## 7. CE QUE CE CONTRAT INTERDIT

- Une récompense par mission.
- Un poids ajusté pour un verbe.
- Un ordre de mission qui grandit quand on ajoute un verbe.
- De l'information sur l'ennemi dans l'ordre.
- De juger sur une moyenne des quatre verbes.
- D'ajouter un cinquième verbe avant que les quatre passent l'audit d'ordre.

---

## AMENDEMENT 1 — 2026-07-29, après l'étalon

**Constat.** Entraînement de 26 millions de pas : 0 % de réussite sur les deux verbes.
Étalon passé ensuite : **les six doctrines écrites à la main font 0 % elles aussi**, alors que
`debordement_simple` obtient 87 % dans `balayage_menace` avec le même monde et les mêmes
réglages. Épisodes d'une durée moyenne de 19 pas pour un délai de 40 à 80.

**Diagnostic.** Le prédicat de succès de la version 1 était de mon invention — « ≥2 hommes
vivants dans le rayon » — alors que l'environnement possède déjà un signal de succès calibré
et utilisé toute la journée du 28/07 : `info['took']`. J'ai construit un instrument neuf à
côté d'un instrument certifié. C'est exactement l'erreur traquée toute la journée.

**Trois corrections, et rien d'autre :**

1. **Le succès de PRENDRE devient `info['took']`**, le signal de l'environnement. INFILTRER
   reste `info['took']` **ET** exposition cumulée < E. Le verbe ne change plus que la
   contrainte ajoutée, plus la définition de l'objectif.
2. **Plafond de pertes : plancher relevé de 1 à 2.** À K_max = 1, l'épisode échouait dès la
   deuxième perte sur quatre hommes — une escouade n'a pas le temps d'exister.
3. **Fin par anéantissement : `vivants == 0`** au lieu de `vivants < 2`.

**Ce qui ne change pas** : les 12 nombres de l'ordre, les budgets en restant, l'absence
d'information sur l'ennemi, l'audit d'ordre et son seuil de 20 points, l'interdiction des
poids par verbe.

**Porte ajoutée, et elle est obligatoire désormais** : avant tout entraînement, **l'étalon
doit passer**. Si les doctrines écrites à la main n'obtiennent pas au moins 40 % sur PRENDRE,
le monde est cassé et on n'entraîne rien. Un agent ne se juge que dans un monde où une
solution connue fonctionne.

---

## AMENDEMENT 2 — 2026-07-29, refonte de l'enveloppe et calibrage de l'exposition

**Trois défauts corrigés, tous dans mon code, aucun dans le monde.**

1. **L'épisode appartient au monde.** La v1 tenait sa propre comptabilité et appelait
   `_reset(idx)` à la main : les attaquants renaissaient devant une ligne défensive déjà
   engagée et mouraient aussitôt (épisodes de 10 pas, 48 % d'anéantissement, 0 % de réussite
   y compris pour les doctrines écrites à la main). Désormais `auto_reset=True` : le monde
   gère ses remises à zéro, et **la mission ne fait plus que conditionner le succès** — un
   budget dépassé ne termine rien, il rend le succès impossible.

2. **`took` est un éclair, il se retient.** Le signal de succès se déclenche au moment où
   l'objectif est atteint, pas au pas terminal. Le lire seulement à la fin ne montrait jamais
   rien : 5246 déclenchements mesurés pour 0 succès compté. Une mémoire d'acquis par épisode
   corrige ça, et la récompense de succès n'est versée qu'une fois, sur le front montant.

3. **`info['losses']` est une FRACTION de l'escouade** (0,25 = un homme sur quatre), pas un
   compte. Le plafond de pertes était comparé en hommes à une fraction.

**CALIBRAGE DE L'EXPOSITION — le plafond ne mordait pas.**
Mesuré au motif du balayage (env frais, `auto_reset=False`, accumulation sur 60 pas, ancré
sur une valeur connue : `debordement_simple` rend 87,5 % de prise contre 87 % au balayage
d'hier). Exposition cumulée au moment du succès, D=8, graine 5 :

| doctrine | prise | exposition |
|---|---|---|
| frontal délibéré | 54,1 % | **2,90** |
| appui-mouvement | 46,2 % | 1,96 |
| bonds alternés | 28,3 % | 1,99 |
| infiltration | 93,6 % | 1,26 |
| débordement double | 95,5 % | 1,00 |
| débordement simple | 87,5 % | **0,93** |

Facteur 3 entre la plus discrète et la plus bruyante. `E_max` était tiré dans 8-20 — dix fois
au-dessus de tout, il n'interdisait rien, et **INFILTRER était strictement identique à
PRENDRE** (44,0 % contre 44,4 %). Nouveau tirage : **1,0 à 1,8**, entre les deux.

**Étalon après correction — la porte du contrat est franchie** (seuil : ≥40 % sur PRENDRE) :

| doctrine | PRENDRE | INFILTRER |
|---|---|---|
| frontal délibéré | 44,0 % | 7,6 % |
| appui-mouvement | 49,8 % | 14,5 % |
| débordement simple | **54,3 %** | **32,2 %** |
| débordement double | 54,3 % | 31,7 % |
| infiltration | 53,0 % | 18,1 % |
| bonds alternés | 24,8 % | 9,6 % |

Le frontal s'effondre d'un facteur 5,8 sous contrainte de discrétion. Les deux verbes sont
désormais deux tâches distinctes, condition nécessaire pour que l'audit d'ordre ait un sens.

**Leçon de méthode, cinq fois répétée aujourd'hui** : chaque fois qu'un résultat était nul ou
absurde, la cause était dans l'instrument de mesure, jamais dans l'objet mesuré. Les sondes
écrites à la chaîne lisaient l'état APRÈS qu'il avait bougé. La sortie a été de reprendre le
motif d'un banc déjà éprouvé et de l'ancrer sur une valeur connue, au lieu d'en écrire un neuf.

---

## AMENDEMENT 3 — 2026-07-29, l'agent LIT son ordre : deux fautes de ma part, aucune de lui

**Résultat brut de l'entraînement v2** (400 itérations, 26 M pas, 5 graines tenues à l'écart) :

| | ordre VRAI | ordre PERMUTÉ |
|---|---|---|
| prendre | **51,8 %** | **0,4 %** |
| infiltrer | **0,0 %** | **23,5 %** |

**L'agent lit son ordre, et il le lit fort.** Montrer « infiltrer » à un épisode qui est en
réalité un « prendre » fait chuter la réussite de 51,8 % à 0,4 %. Montrer « prendre » à un
épisode qui est un « infiltrer » la fait monter de 0 % à 23,5 %. Deux comportements distincts,
que la permutation échange.

### Faute 1 — la statistique effaçait le phénomène
Le seuil était posé sur la **moyenne des deux verbes**. Or ils bougent en sens **opposés** :
25,5 % → 11,9 %, soit 13,7 points, sous le seuil de 20, alors que l'effet par verbe est
écrasant. **Corrigé** : l'audit lit désormais **par verbe**, et un changement dans n'importe
quel sens ≥20 points prouve que l'ordre est lu. C'est la deuxième fois en deux jours qu'un
seuil mal spécifié rate ce qu'il devait détecter (après le seuil d'abandon du 28/07).

### Faute 2 — j'avais appris à l'agent à se figer
INFILTRER correctement ordonné : **0 %**. Mal ordonné : **23 %**. Son comportement « discret »
était pire que son comportement agressif, pour la tâche discrète elle-même.

Cause : le progrès soustrayait l'exposition **à chaque pas**, pour le seul verbe INFILTRER.
Bouger coûtait tout de suite, le succès était loin — la politique optimale à court terme était
l'immobilité. **Et c'était un POIDS PAR VERBE, que ce contrat interdit explicitement.**
J'ai enfreint ma propre règle et elle avait raison.

**Corrigé** : progrès identique pour les deux verbes. Le budget d'exposition est déjà dans le
prédicat de succès et déjà visible dans l'ordre de mission — c'est suffisant.

### Ce qui reste vrai et qui est acquis
Le monde à objectif paramétré **fonctionne** : une seule politique produit deux comportements
distincts selon l'ordre reçu. C'était la question ouverte du contrat. Elle est tranchée.
Ce qui reste à obtenir, c'est que le comportement d'infiltration soit *bon*, pas seulement
*distinct*.
