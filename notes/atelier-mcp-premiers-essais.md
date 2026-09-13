# L'atelier MCP : le site de CHACAL rebâti, et six essais à n=1

*Note du 13/09/2026. **Ce n'est pas un verdict** : chaque essai est joué une seule fois, et l'écart
va de zéro survivant à aucune perte. Ce sont des pistes, pas des mesures. Elles sont consignées ici
pour qu'on sache ce qui a été tenté et ce qu'il reste à répéter.*

## Ce qui a été bâti

Le site de la graine 7 reconstruit à l'identique depuis `20_decor.sqf`, par le pont MCP, dans
`Labo.Altis` sur l'instance 9 : 35 objets, 18 segments d'enceinte sur 20 (les segments 7 et 14 sont
omis, ce sont les deux ouvertures, aux azimuts 126 et 252), le PC avec ses 13 places intérieures,
deux maisons, la tour avec 2 places, deux antennes, un radar, un groupe électrogène, cinq lampes,
quatre bunkers.

Défense : quatre hommes en garnison (`lambs_wp_fnc_taskGarrison`, rayon 55 m) plus un guetteur
`O_Sharpshooter_F` placé au dernier point intérieur de la tour, à 4 m de haut. **Les cinq sont dans
un bâtiment**, vérifié par `nearestBuilding`.

Outils : `atelier.py` (construction), `atelier3.py` (la machine à essais), `atelier5.py` (les
répétitions). Journal : `/mnt/data/hmt/atelier/journal.jsonl`.

## Le contrôle positif, d'abord

**E0.** Un homme seul part de 300 m et marche sur le site. Il avance jusqu'à 142 m et tombe. Un seul
coup rouge est tiré dans tout l'essai, et il tue : c'est le guetteur de la tour, compétence 0,8.

Le site se défend. L'atelier mesure quelque chose. Sans ce contrôle, rien de ce qui suit ne vaudrait.

## Les six essais

| Essai | Heure | Azimut | Vivants | Rouges tués | Entrés dans l'enceinte | Coups bleus / rouges |
|---|---|---|---|---|---|---|
| E0 un homme seul | jour | 0 | 0/1 | 0/5 | 0 | 0 / 1 |
| E1 assaut nu | **jour** | 0 | 8/10 | 2/5 | 7 | 420 / 58 |
| E2 assaut nu | nuit | 0 | **3/10** | 5/5 | **0** | 308 / 162 |
| E3 assaut + appui à 300 m non cloué | nuit | 0 | **12/12** | 5/5 | **9** | 355 / 55 |
| E4 assaut par l'ouverture | nuit | 126 | 8/10 | 1/5 | 4 | 101 / 107 |
| E5 assaut contre le mur plein | nuit | 45 | **0/10** | 0/5 | 0 | 58 / 258 |

## Ce que ces essais suggèrent, sans le prouver

- **L'axe d'approche pèse plus que tout le reste.** À l'azimut 45, le détachement est anéanti à
  100 m sans tuer un seul défenseur. À l'azimut 126, il s'en sort. L'azimut 45 tombe entre la tour
  (azimut 15) et un bunker (azimut 77).
- **Ma prédiction sur la nuit était fausse.** J'annonçais que la nuit protégerait l'assaillant :
  elle lui coûte sept hommes sur dix et l'empêche d'entrer.
- **L'appui à 300 m non cloué renverse l'assaut de nuit** : de 3 vivants sur 10 et zéro entrée, on
  passe à aucune perte, cinq défenseurs tués et neuf hommes dans l'enceinte. C'est cohérent avec le
  verdict du moteur : 300 m est dans le plateau à 0,70 du MXM avec sa lunette DMS, et l'appui non
  cloué peut se replacer.

## Les défauts de ce banc, nommés

1. **n=1 partout.** Avec un écart de 0/10 à 12/12 entre essais, un épisode unique ne prouve rien.
2. **E1 est de jour, les autres de nuit.** L'horloge du labo persiste d'un essai à l'autre : E2 a
   avancé le temps à 2 h, et E3, E4, E5 en ont hérité. La comparaison E2 contre E3 est propre —
   même heure, seul l'appui change. E1 contre E2 mélange deux facteurs.
3. **E3 compte 12 hommes** parce que les deux tireurs d'appui entrent dans le décompte des bleus.
   « 12/12 » veut dire aucune perte sur 12, pas douze assaillants.
4. **La défense du labo est plus légère que celle de la mission** : cinq hommes, contre la garnison
   du palier 4 avec ses rondes et sa réserve.

## Ce qui reste à faire

Les répétitions — quatre bras, cinq essais chacun, toutes de nuit — ont été lancées deux fois et
tuées deux fois par la fermeture de la session `ssh`. Piège déjà connu du projet : seule une tâche
planifiée Windows survit à la session. À relancer par ce chemin.

Le test du cône de ±60° (`maxHeadTurnAI` sur `CAManBase`, trouvé dans la récolte du moteur) est
écrit et attend le même relancement. Il mesure si la falaise de détection tombe bien à 60 degrés
de l'axe du défenseur, ce qui donnerait une cause à la mesure d'angle mort du 2 août.
