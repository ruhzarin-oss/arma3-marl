# Plan — rendre la menace visible au moment de choisir (version 2)

*17/09/2026, 22 h. Version 1 (4cd083e, 8bc624d) appliquée (mission 97cef21), contrôles joués : 74 épisodes, 0 erreur
SQF, 0 refus. **Les contrôles ont refusé le montage**, et cette version 2 en tire les conséquences. Demandé par Younes :
« corrige les deux et relance les contrôles », puis « refait moi le plan ». Rien n'est relancé avant validation.*

## 1. Ce que les contrôles ont mesuré

| contrôle | résultat | verdict |
|---|---|---|
| POSITIF, groupe inerte à 150 m devant | menace **connue** dans 2 épisodes sur 8 ; **vue** dans 5 sur 8 | ❌ attendu ≥ 80 % |
| NÉGATIF, groupe à 1500 m derrière | 0 vue sur 8 | ✅ |
| NUL, aucune menace | 0 perception, 0 vérité, sur 8 | ✅ |
| ORIGINE, fenêtre à 0 | décisions identiques à CHOIX-P2, 0 erreur | ✅ |
| GLOBAL | 0 erreur SQF sur 74 épisodes, marqueur version 3 partout | ✅ |
| Variance sous vraie menace, à 90 s | connue au choix : 0/8 partout, sauf 1/8 en P1 type 2 | ❌ attendu 30 à 70 % |

**Deux fautes, l'une de code, l'autre de conception.**
1. **La fenêtre fige le détachement.** J'arrête les hommes (`doStop`) pour qu'ils observent et je ne leur rends jamais la
   main. En P4, les trois éléments ne rejoignent plus leurs positions : les 8 épisodes finissent au plafond, 55 min au
   lieu de 5. P1 et P2 s'en tirent parce que leurs phases se terminent au temps.
2. **Le canal « connaissance » est presque mort de nuit.** La mission se joue de nuit ; une menace accroupie et immobile
   à 150 m n'entre presque jamais dans la liste de cibles du groupe, même avec des jumelles de nuit et de bonnes
   compétences (0,75 et 0,80, vérifiées dans `40_blufor.sqf`). Rien n'est cassé : c'est le monde.
3. **Ma sonde géométrique ignore la nuit.** `CHACAL_fnc_voit` ne teste que portée, cône et ligne de vue. Elle
   **surestime** ce qu'un homme perçoit, quand la connaissance de l'IA le **sous-estime**. La vérité est entre les deux.

## 2. Ce que la version 2 change

### a. Réparer la fenêtre (faute de code)

À la fin de la fenêtre, chaque homme vivant retrouve son groupe : `_x doFollow (leader (group _x))`, et la posture
revient à `AUTO`. Contrôle : en P4, la phase doit se terminer comme avant (ATTEINT ou COMPROMIS en 4 à 7 min), jamais au
plafond.

### b. Observer veut dire **scruter un secteur**

Pendant la fenêtre, les hommes regardent la direction qui compte, au lieu de garder leur cap :
- P1 : la zone de poser et ses abords ;
- P2 : la route, dans l'axe de la traversée ;
- P4 : l'axe vers le regroupement.

En SQF : `doWatch` sur le point de référence de la phase, puis `doWatch objNull` à la fin. C'est le correctif le plus
honnête : un détachement qui observe regarde où il faut, et l'IA acquiert dans son cône de regard.

### c. Garder les **deux canaux**, et les nommer

La ligne de décision écrit désormais, côté perception :
- `menaces_vues` : canal géométrique, ce qu'un œil pourrait atteindre (portée, cône, ligne de vue) ;
- `menaces_connues` : canal connaissance, la liste de cibles du **groupe** (`targetKnowledge`, champ 0) ;
- `menaces_connues_camp` : `knowsAbout` du camp, **ajouté** pour le diagnostic ;
- `menaces_connues_homme` : connaissance **individuelle** (`targetKnowledge`, champ 1), ajoutée aussi ;
- et, pour la plus proche connue : `distance_menace`, `erreur_position`, `menace_mobile`, `vue_depuis`.

La vérité (`verite_menaces`, `verite_distance_menace`) reste écrite à part, interdite à l'Architecte.

### d. Une sonde avant de rejouer 74 épisodes

4 épisodes P2, de nuit, groupe inerte à 150 m devant, qui journalisent **toutes les 5 s pendant 300 s** les quatre
canaux. Elle répond à trois questions, sans rien décider :
- le `doWatch` fait-il monter la connaissance ?
- au bout de combien de secondes une menace posée à 150 m devient-elle connue ?
- la connaissance de camp ou individuelle donne-t-elle plus que celle du groupe ?

## 3. Les contrôles rejoués, et leurs critères

Mêmes 19 jobs (74 épisodes), avec la fenêtre réparée et le `doWatch`. **Le canal retenu comme perception principale est
choisi par la sonde, et écrit dans les critères avant de rejouer** :

| cas | perception principale | POSITIF | variance attendue |
|---|---|---|---|
| la sonde montre que la connaissance monte avec `doWatch` | `menaces_connues` | ≥ 80 % à 150 m devant | 30 à 70 % sous vraie menace |
| la connaissance reste rare même en regardant | `menaces_vues` (géométrie), la connaissance restant écrite comme perception secondaire | ≥ 80 % | 30 à 70 % |

Dans le second cas, un contrôle s'ajoute, parce que la géométrie ignore la nuit : **NÉGATIF PROCHE**, une menace à 150 m
derrière un relief, attendu `menaces_vues` = 0 dans au moins 95 % des épisodes.

Les autres critères ne changent pas : NÉGATIF, NUL, ORIGINE, GLOBAL, et « aucune campagne ne part » si l'un échoue.

## 4. Si la perception ne varie toujours pas

Trois leviers, à toi de trancher, aucun n'est pris seul :
1. **Allonger la fenêtre** à 120 ou 180 s (la sonde dira à partir de quand la connaissance arrive).
2. **Poser les menaces debout** plutôt qu'accroupies, ou plus près : le monde change, les mesures passées ne s'y
   comparent plus.
3. **Jouer de jour** (`jour = 1`) comme second bras : la perception varierait beaucoup plus, mais c'est une autre
   mission que celle mesurée depuis août.

## 5. Ordre et durées

| étape | durée | serveurs |
|---|---|---|
| Corriger la fenêtre et ajouter le `doWatch` et les deux canaux, essai à blanc | 25 min | 0 |
| Sonde (4 épisodes de 5 min) | 20 min | 4 |
| Lire la sonde, choisir le canal, écrire les critères, commiter | 25 min | 0 |
| Rejouer les 19 jobs, 74 épisodes (P4 redevenus courts) | 1 h 15 | 12 |
| Lecture unique et consignation | 15 min | 0 |

Total : environ **2 h 40**. La boucle EvoGP part ensuite, la nuit, sur les 12 serveurs, puisqu'elle n'utilise pas la
fenêtre.

## 6. Ce qui ne change pas

- Fenêtre de 90 s par défaut (fixée par Younes), ordre P2 puis P1 puis P4, connaissance du **groupe** plutôt que du
  camp comme canal de référence.
- La vérité n'entre jamais dans la règle.
- Aucune campagne ne part tant que les contrôles ne passent pas.

## Décisions pour Younes

1. **La sonde** : d'accord pour dépenser 20 minutes et 4 serveurs avant de rejouer les 74 épisodes ?
2. **Le canal de repli** : si la connaissance reste rare, accepte-t-on la géométrie comme perception principale, avec la
   connaissance en second ?
3. **Les leviers du § 4** (fenêtre plus longue, menaces debout, jour) : lesquels s'autorise-t-on si la perception ne
   varie toujours pas ?
