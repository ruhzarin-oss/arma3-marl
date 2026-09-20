# Les contrôles de l'Oracle — critères écrits avant le premier épisode

*20/09/2026, campagne `CONTROLES-ORACLE-20-09`. Règle 16 : un instrument ne vaut que si on l'a vu échouer.
Ces contrôles sont dus depuis le plan `plans/plan-oracle-commandant.md` § 7 ; ils n'ont jamais été joués, et la
campagne `ORACLE-P2-19-09` a été lue — puis refusée — sans eux. Ils passent **avant** toute nouvelle campagne.*

## Pourquoi maintenant

`ORACLE-P2-19-09` s'est refusée deux fois : d'abord sur quatre portes, puis, l'intention de traiter posée, sur la
porte Q4 (deux cases du monde 9 sous trois épisodes, par refus reproductibles du banc). **Cette campagne est close et
ne sera pas lue** : chaque amendement supplémentaire ajouterait de la liberté d'analyse à un jeu de données déjà vu.

Avant d'en payer une neuve (≈ 4 h de ferme), deux questions doivent être tranchées, et elles ne coûtent qu'une heure :

1. **L'adversaire peut-il seulement punir ?** Si non, tout résultat nul est un plancher d'instrument.
2. **L'Oracle triche-t-il ?** S'il lit nos positions vraies, il est un mur, et sa mesure ne vaut rien.

## Dispositif

Deux bras, joués sur le banc `chacaloracle`, paramètre neuf `CHACAL_ORACLE_CTRL` (fichier `chacal/46_controles_oracle.sqf`,
qui ne touche pas à la logique de l'Oracle : il agit sur le monde et journalise).

| bras | réglage | mondes × situations | épisodes |
|---|---|---|---|
| **positif** | `oracle_ctrl=1`, `oracle_cmd=1`, `jour=1`, `traversee=1` | 8 × 2 | 16 |
| **non-triche** | `oracle_ctrl=3`, `oracle_cmd=1`, `jour=0`, `traversee=1` | 8 × 2 | 16 |

- **Positif** : à T+30 s de la phase 2, la patrouille est posée sur la route la plus proche du détachement (< 400 m),
  de jour, et nos hommes sont mis **debout**. On lui amène la cible.
- **Non-triche** : à T+150 s, le détachement est **téléporté** dans la case la plus lointaine du couloir, formation
  conservée. Personne n'est prévenu. La croyance de l'Oracle est journalisée juste avant et juste après.

## Portes de qualité (avant toute lecture)

- **C1** : zéro erreur SQF sur les épisodes acceptés.
- **C2** : ≥ 90 % des épisodes prévus acceptés par le banc (≥ 29 sur 32).
- **C3** : chaque bras a au moins 12 épisodes acceptés.
- **C4** : dans le bras positif, la ligne `CHACAL|O|ctrl|positif` est présente et `patrouille_a` ≤ 400 m.
- **C5** : dans le bras non-triche, les deux lignes `teleport_avant` et `teleport_apres` sont présentes, et le saut
  est ≥ 1 000 m.

Si une porte échoue : **aucun contrôle n'est conclu**, et la cause est réparée avant de rejouer.

## Les deux lectures, et ce qui les falsifie

### CP — contrôle positif : l'adversaire doit prendre le détachement

Issue : `compromis = 1` sur la ligne de fin de phase 2.

- **PASSE** si l'interception est ≥ 90 % des épisodes acceptés du bras (≥ 15 sur 16 ; ≥ 90 % si moins d'épisodes).
- **ÉCHOUE** sinon. Conséquence écrite d'avance : **le canal par lequel l'Oracle punit est bouché**, et aucun
  résultat nul d'une campagne Oracle ne pourra être lu comme « le choix n'a pas d'effet » — seulement comme
  « l'instrument ne sait pas punir ». Il faudra réparer la létalité de la patrouille avant toute campagne.

### CN — non-triche : la croyance ne doit pas suivre le corps

Pour chaque épisode du bras non-triche, on prend les **cinq décisions qui suivent le téléport**, en s'arrêtant à la
première qui journalise une détection légitime (`vu` différent de `RIEN`). Sur cette fenêtre :

- **violation** si la croyance sur la case d'arrivée dépasse `p_arr + 10 points` (sa valeur juste avant le saut),
  **ou** si la patrouille prend pour cible la case d'arrivée.
- **PASSE** si au plus 2 épisodes sur 16 sont en violation (on tolère le hasard : `selectRandom` sur les ex æquo et
  15 % d'erreur volontaire peuvent l'y envoyer sans qu'il triche).
- **ÉCHOUE** à 3 violations ou plus. Conséquence écrite d'avance : **l'Oracle lit nos positions vraies**, la
  campagne `ORACLE-P2-19-09` et toute campagne à venir sont sans valeur, et il faut retrouver la ligne fautive
  (un `getPos` à la place de `(_kn select 6)`).

*Une détection légitime après le saut est normale et attendue : nos hommes sont réellement là-bas. C'est pourquoi la
fenêtre s'arrête à la première détection.*

## Ce que ces contrôles ne disent pas

Ils ne disent rien de l'utilité de l'Oracle, ni de l'effet du choix de traversée. Ils disent seulement si
l'instrument peut punir et s'il est honnête. Les trois autres contrôles du plan § 7 (négatif, jouabilité,
calibration du budget) restent dus.

## Amendement 1 — 20/09 16 h 05, écrit avant toute lecture : la case d'arrivée, et la porte de vacuité

La fumée des quatre premiers épisodes (zéro erreur SQF, les deux lignes de contrôle présentes, saut de 2 762 m,
patrouille posée à 297 m) a montré un **défaut du contrôle de non-triche, pas de l'Oracle** : la case la plus
lointaine est toujours le `SITE`, c'est-à-dire la garnison. Nos hommes y étaient vus en quelques secondes, la fenêtre
d'observation se fermait aussitôt, et **le contrôle ne pouvait plus échouer**. Un contrôle qui ne sait pas échouer
ne mesure rien (règle 16).

Deux corrections, écrites avant d'avoir lu la moindre croyance :

1. **La case d'arrivée exclut `ABORDS` et `SITE`.** On saute vers la case la plus lointaine parmi les six autres.
2. **Porte C6, de vacuité :** au moins 12 épisodes de non-triche doivent offrir une fenêtre d'au moins **deux
   décisions sans détection** après le saut. En dessous, la lecture CN est refusée pour vacuité — on ne conclura pas
   « il ne triche pas » parce qu'on ne lui a pas laissé l'occasion de tricher.

Les épisodes déjà joués dont la case d'arrivée est `SITE` ou `ABORDS` **ne sont pas lus** : ils appartiennent à la
version défectueuse du contrôle. Quatre jobs de non-triche sont reposés pour les remplacer, avec des mondes et des
situations que la campagne n'a pas encore joués, de sorte qu'aucun ne soit un rejeu à l'identique — l'erreur du
remplacement d'`ORACLE-P2-19-09`.

## Amendement 2 — 20/09 16 h 40, écrit avant toute lecture : la mission modifiée pendant que les serveurs tournaient

La lecture s'est refusée sur C2, C3 et C6 : **16 épisodes acceptés sur 32**. La cause n'est ni le banc ni l'Oracle,
c'est moi. J'ai corrigé la case d'arrivée (amendement 1) **alors que douze serveurs jouaient**. Au lancement de
l'épisode suivant, le banc n'a pas pu remplacer le dossier de mission — un serveur Arma le tenait ouvert :

```
mv: cannot move '.../MPMissions/CHACALORACLE.Altis' ... : Permission denied
DEPLOIEMENT NON PROUVE : la mission jouee differe du depot
```

Le banc a **refusé de jouer une mission qu'il ne pouvait pas prouver**, et a tué l'épisode : c'est exactement ce
qu'il doit faire. La signature est nette dans l'inventaire : dans chaque job de deux graines, la **première** a un
résultat et la **seconde** n'en a aucun — la bascule a eu lieu entre les deux. Un résidu `CHACALORACLE.Altis.neuf`
est resté dans le dossier déployé ; il a été supprimé, serveurs éteints.

**Règle de conduite, désormais :** on ne modifie jamais la mission d'un banc pendant qu'une campagne vole. Une
correction attend la file vide, ou bien on arrête la campagne d'abord.

**Ce qui est reposé :** uniquement les (bras, monde, situation) sans épisode valide, graine par graine, 11 jobs et
22 épisodes. Deux graines déjà valides (12 en situation 1) sont rejouées faute de pouvoir poser un job à une seule
graine — le banc les refuse.

**Règle de lecture, écrite avant tout effet :** on lit le **premier épisode ACCEPTÉ** de chaque (bras, monde,
situation). « Accepté », et non « premier tout court » : c'est précisément l'erreur qui a rendu le remplacement
d'`ORACLE-P2-19-09` sans effet, un exemplaire refusé bloquant le rejeu valide de la même case.

## Résultat — 20/09 17 h 10 : les huit portes passent, **les deux contrôles échouent**, et les deux sont des défauts d'instrument

31 épisodes acceptés sur 32, zéro erreur SQF, les huit portes de qualité passent, y compris C6 (15/15 épisodes
offrent une vraie fenêtre). La mesure a donc bien eu lieu — et elle refuse les deux contrôles.

### CP — interception 3/16 = 0,188. ÉCHOUE au critère écrit.

**Mais le contrôle n'a pas tenu l'adversaire en place.** La patrouille est posée à 247-398 m (porte C4 passée), puis
elle **repart aussitôt** : ses distances à sa propre cible, décision après décision, passent de ~800 m à 1 000,
2 000, jusqu'à 4 000 m. Elle ne confronte pas, elle passe. Le téléport déplace le véhicule sans lui retirer ses
points de passage.

Ce que le contrôle mesure réellement, et qui n'est pas rien : **une patrouille motorisée qui passe à 300 m de dix
hommes debout, de jour, ne les prend pas 13 fois sur 16.** Ce n'est pas la question posée. `CP est NON CONCLUANT` :
on ne peut pas encore dire si le canal de punition est bouché.

### CN — 4 violations sur 15. ÉCHOUE au critère écrit.

Décomposition : **zéro violation sur la croyance** ; les quatre violations viennent toutes de la seconde clause,
« la patrouille prend pour cible la case d'arrivée », et toutes sur la même case, `CRETE`.

**Contre-épreuve sur données indépendantes** (les 62 épisodes Oracle d'`ORACLE-P2-19-09`, sans aucun téléport, même
fenêtre de 5 décisions après t = 175 s) : la patrouille vise `CRETE` dans **24 épisodes sur 62, soit 38,7 %**. Avec
téléport : 4 sur 15, soit 26,7 % — **moins souvent que par hasard**.

La clause est donc **réfutée comme instrument** : elle se déclenche quatre fois sur dix sur rien. Elle n'aurait
jamais dû être écrite sans modèle nul. `CN est NON CONCLUANT` : la croyance, elle, n'a jamais suivi le corps
(0/15), mais je ne m'autorise pas à conclure « il ne triche pas » en retirant après coup la clause qui échoue.

### Ce qu'il faut réparer avant de rejouer

1. **CP** : après le téléport, effacer les points de passage de la patrouille et lui ordonner de rester et
   d'observer, pour qu'elle confronte au lieu de passer.
2. **CN** : remplacer le seuil de la clause « cible » par une **comparaison au taux sans téléport**, ou ne garder
   que la croyance — mais alors l'écrire avant, et le confirmer sur des épisodes neufs.

## Version 2 des contrôles — critères écrits avant le premier épisode de `CONTROLES-ORACLE-V2-20-09`

Les deux contrôles de la v1 étaient défectueux, chacun d'une façon différente, et les deux défauts sont réparés
**file vide, zéro serveur en vol** (règle du 20/09 : on ne modifie pas la mission d'un banc pendant qu'une campagne
vole).

### CP — la patrouille est désormais tenue au contact

Après le téléport, ses points de passage sont **effacés**, elle passe en `COMBAT` / `RED` / `FULL`, et elle reçoit
un ordre de mouvement sur nos hommes **toutes les 15 secondes pendant trois minutes**. Chaque ordre est journalisé
avec sa distance (`CHACAL|O|ctrl|positif_suivi`).

**Porte C7, de confrontation :** dans au moins 80 % des épisodes du bras positif, la patrouille doit être venue à
**moins de 150 m** d'un de nos hommes. Sinon la lecture est refusée : un contrôle positif qui ne met personne en
face ne prouve rien, et c'est exactement ce qui s'est passé en v1 (posée à 300 m, repartie à 4 000 m).

Lecture CP inchangée : interception ≥ 90 %. **Ce qu'elle veut dire maintenant** — si, avec l'adversaire collé à
moins de 150 m, de jour, sur dix hommes debout, l'interception reste basse, alors le canal de punition est
réellement bouché, et six campagnes de résultats nuls s'expliquent d'un coup.

### CN — la clause « cible » devient une comparaison, pas un seuil

La clause « la patrouille prend pour cible la case d'arrivée » se déclenchait **38,7 % du temps sans aucun
téléport** (62 épisodes Oracle d'`ORACLE-P2-19-09`, même fenêtre). Un seuil nu était donc un détecteur de hasard.

- **CN** ne garde que la croyance : violation si la croyance sur la case d'arrivée dépasse sa valeur d'avant le saut
  de plus de 10 points, avant toute détection légitime. Passe à 2 violations ou moins sur 16.
- **CN-bis**, annoncée séparément : le taux de ciblage de la case d'arrivée doit rester **sous 38,7 % + 15 points**.
  Au-dessus, la patrouille est attirée par l'endroit où nous sommes réellement.

Les portes C1 à C6 sont inchangées.
