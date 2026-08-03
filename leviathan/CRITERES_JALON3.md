# CRITÈRES DU JALON 3 — UNE POLITIQUE, DEUX VERBES (figés avant le premier pas)

Écrits le 2026-07-29. Architecte : Fable. Exécution : Opus 5. Arbitrage : Younes.
Le jalon 1 est vert : l'instrument a prouvé son zéro sur les six doctrines.

## CE QUI EST ÉTABLI ET NE SE REDISCUTE PAS
- **Étalon consolidé, 5 graines, protocole persisté** (`etalon_j1_5graines.sh`) :
  débordement double 87,5 / 62,9 · débordement simple 84,9 / 61,5 · infiltration 83,7 / 50,2 ·
  appui-mouvement 46,0 / 13,2 · frontal 45,0 / 7,8 · bonds alternés 24,6 / 10,0 (PRENDRE / INFILTRER).
- **`mission_v3.pt` vaut environ 5 %**, mesuré dans les deux régimes : 4,1 / 1,8 en mode
  épisode, 6,3 / 2,5 en mode continu. Les deux concordent.
- **Le compteur interne de `train_mission.py` est condamné comme instrument.** Il annonçait
  43,6 %. Il n'a plus voix au chapitre, jamais.
- **`mission_v3.pt` est jeté comme fondation** : entraîné sur un monde d'avant les correctifs.
  Pas de reprise, pas d'affinage. Archivé comme pièce à conviction.

## LE CHANGEMENT UNIQUE DE v4
**Le monde.** Mêmes hyperparamètres, même récompense (amendement 3, aucun poids par verbe),
même budget nominal, mais sur `monde_mission.py` certifié — quatre correctifs depuis v3 :
permutation résolue après le re-tirage, premier pas permuté, instantanés du toucher figés
avant le re-tirage, bornes de mission figées avant le re-tirage.

Empiler du façonnage de récompense par-dessus un changement de monde non contrôlé, ce serait
recréer la situation de la veille. **Un changement, une preuve.**

## LA SEULE COURBE QUI COMPTE
Tous les 50 pas d'itération : point de contrôle, puis évaluation par **l'instrument certifié**
(`banc_mission` → `analyse_journal`), mode épisode, une graine tenue à l'écart, 1024 épisodes.
L'affichage interne peut rester à l'écran ; il n'a plus voix au chapitre.

## PORTE D'ARRÊT ANTICIPÉ — non négociable
À **100 itérations** (le quart du budget) : **PRENDRE au banc ≥ 15 %**.
- Atteint → on va au bout des 400 itérations.
- Non atteint → **arrêt**. On ne brûle pas 26 millions de pas une deuxième fois.
  L'hypothèse « le monde cassé empêchait l'apprentissage » tombe, et le levier suivant devient
  la **densité de récompense** : façonnage à l'événement de prise, sous forme potentielle pour
  ne pas déplacer l'optimum. Ce sera le changement unique de v5, pas un ajout à v4.

## SEUILS DU JALON 3
Mesurés par l'instrument certifié, ≥1000 épisodes par verbe, graines tenues à l'écart.
1. **PRENDRE ≥ 50 %** — soit 57 % de l'étalon, et il faut battre le frontal (45,0) et
   l'appui-mouvement (46,0), donc la moitié des doctrines scriptées.
2. **INFILTRER ≥ 20 %** — soit 32 % de l'étalon, au-dessus de quatre doctrines sur six.
3. **PORTE DE LECTURE D'ORDRE, ajoutée après E7 et non négociable** : sous permutation du
   verbe, **chaque verbe chute à ≤ 50 % de son taux en ordre vrai**.
   E7 a prouvé qu'un taux de succès ne dit rien de la lecture de l'ordre — l'agent y était à
   0,2 point d'écart. Un agent qui atteint 50 / 20 sans franchir cette porte a appris une
   politique moyenne insensible à l'ordre, et **le jalon n'est pas franchi**.

## INTERDITS
Ceux du jalon 1 restent en vigueur, avec deux précisions :
- **Aucun changement de récompense dans v4.** Elle est gelée par l'amendement 3.
- **Aucun chiffre issu du compteur interne** ne peut être cité, ni pour décider, ni pour
  rassurer.
