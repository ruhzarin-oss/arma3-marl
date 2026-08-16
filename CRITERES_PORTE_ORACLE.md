# LA PORTE ORACLE — critères déposés avant lancement

*16 août 2026. ⟨Fable⟩ « L'information ne paie que si une DÉCISION la consomme. Si l'exécutant
au sol est un `doMove` vers l'objectif, savoir ne change rien — sauf le rendre nerveux. »*

## POURQUOI CETTE PORTE EXISTE

Un verdict antérieur du projet dit que **le banc refusait l'oracle** : l'information parfaite
faisait 10/20 sur un critère où un agent ordinaire faisait 15. Cinq refus successifs ont fini
par juger le banc, pas l'agent. Tant que ce fait n'est pas retourné sur un banc qui contienne
une vraie décision, **aucun banc drone ne peut rien mesurer** : on lirait l'allergie du banc à
l'information, pas la valeur du drone.

⚠️ Cette porte ne mesure pas un drone. Elle mesure **si un banc sait payer l'information**.

## LE MONDE — une décision, et une seule

Objectif `O` en `[4644, 5652]` sur Stratis, socle **figé 1.10.0** (`sha256 91269784…`), mods
du juge. À chaque répétition on tire un cap `β` et un côté tenu (gauche/droite) au hasard.

- **Départ** : 4 attaquants (`B_Soldier_F`, mode `natif`, **destructibles**) à **200 m** de `O`.
- **Deux axes** vers `O`, en deux jambes : `S → M±  → O`, où `M±` est décalé
  **perpendiculairement de 120 m** au milieu du trajet — soit **240 m entre les deux axes**, pour que la planque n'en couvre qu'un. Un axe passe à gauche, l'autre à droite.
- **La planque** : 3 défenseurs (`O_Soldier_F`), immobiles (`PATH` coupé, le reste natif),
  couchés, posés à **30 m** de l'un des deux axes et face à lui. **Ils ne tiennent qu'un seul
  axe.** L'autre est libre.

Le seul choix du scénario est **par quel axe on passe**. C'est là, et nulle part ailleurs, que
l'information peut se dépenser.

## LES TROIS BRAS — appariés par scène (même cap, même côté tenu)

| bras | ce qu'il sait | ce qu'il fait |
|---|---|---|
| **FORCÉ-TENU** | — | prend toujours l'axe **tenu** — la borne basse |
| **AVEUGLE** | rien | tire son axe **au hasard** — le bras sans information |
| **ORACLE** | la position exacte de la planque | prend toujours l'axe **libre** |

⚠️ **`reveal` n'est PAS le canal ici, et c'est voulu.** L'oracle informe **la décision**, pas la
base de connaissance du moteur. Le contrôle positif certifié la veille a établi ce que `reveal`
fait ; il n'a rien à faire dans une porte qui juge une décision.

## LES VARIABLES — celles que le projet a déjà validées

- **PRISE** (jugement) : un attaquant **vivant** à moins de 15 m de `O`, **et toujours vivant
  20 s plus tard** (tenue). Binaire, par répétition.
- **EXPOSITION PAR MÈTRE GAGNÉ** (coût) : somme, par pas de 1 s, du nombre d'attaquants vus
  par au moins un défenseur, divisée par les mètres réellement gagnés vers `O`.

⛔ **Pas les éliminations.** Trois verdicts du projet disent qu'elles ne bougent pas : le flanc
donne +17,3 points de tenue et **zéro** sur l'élimination.

Plafond de temps : **280 s** par bras. **20 répétitions** (~2 h 30).

### ⚠️ AMENDEMENT DU 17/08 — le monde était injouable, et le dépôt l'avait prévu

Premier lancement, 5 répétitions : **prise = 0 dans les trois bras, toujours**. Le bras
ORACLE traversait pourtant proprement — `expo 0`, 4 survivants — mais s'arrêtait à 146 m
sur 200, faute de temps : en conduite `COMBAT` les hommes rampent à ~1 m/s pour un trajet
en deux jambes de ~460 m. C'est la branche « **l'objectif est injouable** » écrite avant.
**Deux changements, tous deux de MONDE, aucun de seuil** : plafond 150 → 280 s, et marche
en `AWARE`/`FULL` au lieu de `COMBAT`/`NORMAL` — une marche à l'ennemi, pas un ramper.
Identique dans les trois bras. **Les 5 répétitions du premier lancement sont jetées.**

## LA PRÉCONDITION — le contrôle positif de CETTE porte

> **PRISE(ORACLE) − PRISE(FORCÉ-TENU) ≥ 25 points.**

Si les deux axes ne diffèrent pas, **il n'y a rien à acheter** et la porte est **SANS OBJET** :
on ne peut pas demander à l'information de payer dans un monde où le choix est gratuit. Une
porte se **dimensionne** ; c'est ici qu'on le vérifie, et c'est écrit avant.

Deux façons d'y échouer, toutes deux déclarées d'avance :
- **les deux bras à ~100 %** → les défenseurs sont trop faibles, ou ils ne couvrent pas leur axe ;
- **les deux bras égaux et moyens** → la planque voit **les deux** axes : il n'y a pas d'axe libre ;
- **les deux bras à ~0 %** → ils sont trop forts, l'objectif est injouable.
Dans les deux cas on re-dimensionne le monde et **on ne lit pas la porte**.

## LA PORTE — écrite avant

> **PRISE(ORACLE) − PRISE(AVEUGLE)**, apparié par scène, **borne inférieure à 95 % au-dessus
> de ZÉRO**.

Zéro, et pas 25 : on ne demande pas à l'information de faire mieux que la précondition, on lui
demande de **payer quelque chose**.

## CE QUI FERAIT ÉCHOUER — écrit avant

- **La porte tombe alors que la précondition passe** → **LE BANC NE SAIT PAS PAYER
  L'INFORMATION**, sur un banc qui contient pourtant une vraie décision et un vrai gain à
  obtenir. Le verdict « le banc refusait l'oracle » cesse alors d'être un accident de montage
  et devient un fait du monde Arma. **Tout banc drone bâti là-dessus serait sans objet**, et
  c'est le résultat le plus lourd que cette nuit puisse produire. C'est l'issue que je crains,
  et c'est pour ça qu'elle est écrite avant.
- **La précondition tombe** → le monde est mal dimensionné, la porte est sans objet, on ne lit
  rien d'autre ce jour-là.
- **AVEUGLE ne tombe pas à mi-chemin** entre FORCÉ-TENU et ORACLE (à la marge d'échantillonnage
  près) → le tirage d'axe n'est pas indépendant du côté tenu, l'instrument est cassé.

## CE QUE CETTE PORTE NE PROMET PAS

Qu'un drone paie. Elle prépare seulement le terrain : sans elle, aucun chiffre de drone n'aurait
de sens.
