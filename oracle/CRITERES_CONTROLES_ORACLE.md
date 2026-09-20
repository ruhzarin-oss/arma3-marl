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
