# Critères du banc d'escouade n°4 — écrits AVANT le run

*4 août 2026, 20h45. Le banc n°3 tourne encore (config 12 sur 20). Aucune donnée du banc n°4
n'existe au moment où ce fichier est écrit. Il sera commité avant le premier essai.*

## Ce banc n'est PAS un test d'hypothèse. C'est un diagnostic d'instrument.

Il faut l'écrire noir sur blanc, parce que c'est là que le glissement se produit.

Le banc n°3 a échoué. Pas sur son hypothèse : sur sa mesure. La « part d'hommes du groupe
manœuvrant repérés » ne prend presque jamais de valeur intermédiaire — **3 essais sur 100**
sur trois bancs cumulés. Tout le reste vaut 0 % ou 100 %. La détection est en cascade : dès
qu'un homme est repéré, ses voisins le sont dans la seconde.

Conséquence : l'observation fondatrice « 31/60 contre 51/60 » n'était pas une nouvelle
mesure. C'est 11 groupes repérés contre 17, multiplié par 3 hommes. **La part d'hommes vus
était la métrique de groupe, rescalée.** Le banc bâti pour échapper à la métrique de groupe
mesurait la métrique de groupe.

Changer de mesure maintenant, sans avoir compris pourquoi la première ne varie pas, ce
serait choisir la mesure qui rend le test gagnable. C'est exactement le reproche de Fable.
Donc ce banc ne conclut rien sur la base de feu tant que D0 et D2 ne sont pas passés.

## Ce qu'on mesure désormais

Une distance, pas un compte. Une distance est continue : elle ne peut pas produire
d'égalités, et c'est le seul défaut de l'instrument précédent qu'on est sûr de corriger.

| champ | définition |
|---|---|
| `d_grp` | distance du centre du groupe, en mètres, quand le camp adverse le repère pour la première fois (`knowsAbout` ≥ 1,5). `-1` si jamais repéré. |
| `d_hom` | même chose, **par homme**, avec la distance propre à cet homme. Tableau. |
| `cascade` | écart en mètres entre le premier et le dernier homme repéré. `-1` si moins de deux hommes repérés. **C'est la mesure centrale de ce banc.** |
| `repere` | 0 / 1. La métrique de groupe, enfin nommée pour ce qu'elle est. |

Les champs du banc n°3 (`vus`, `jalons`, `arme_vers_man`) sont conservés tels quels pour que
les deux bancs restent comparables.

**Convention de codage, fixée maintenant pour qu'elle ne soit pas choisie après coup :**
un `d_grp` à `-1` — jamais repéré — est traité comme **0 mètre**, c'est-à-dire repéré au plus
tard possible. C'est le meilleur résultat, et il se range naturellement du bon côté de la
comparaison. Un `cascade` à `-1` — moins de deux hommes repérés — est **exclu** du calcul de
D0 et D1 : on ne fabrique pas un zéro à partir d'une absence de mesure.

## Le dispositif

Six bras, sur 20 configurations défensives, de 150 m à 40 m.

| bras | rôle |
|---|---|
| `bloc_1axe` | contrôle de présence — 6 hommes tout droit, ils doivent être repérés |
| `deux_axes` | 3 fixent de face + 3 par le flanc |
| `deux_axes_bis` | rejeu identique — mesure du bruit |
| `flanc_seul` | 3 par le flanc, sans appui |
| `flanc_seul_bis` | rejeu identique — mesure du bruit **et** contrôle négatif |
| `flanc_etale` | **le contrôle positif** — même chemin, même effectif, écartement porté de 8 m à 40 m |

**Défenseurs restreints à 5–8.** Sur le banc n°3, les configs à 4 défenseurs ne repéraient
jamais personne et celle à 12 repérait toujours tout le monde. Plancher et plafond : ces
configurations ne peuvent pas départager, quoi qu'il arrive. Le corpus contient 40 configs
dans la bande 5–8 ; on en prend 20.

## Les critères, fixés maintenant

**D0 — CONTRÔLE POSITIF. Sans lui, rien de ce banc ne vaut.**
`flanc_etale` doit produire un `cascade` **médian ≥ 15 m**, contre un `cascade` médian de
`flanc_seul` que le banc n°3 laisse attendre proche de 0.
→ Si D0 passe : la cascade est une affaire d'écartement, pas une loi. La détection peut être
graduée, et une mesure par homme redevient légitime *à condition de séparer les hommes*.
→ **Si D0 échoue** — `flanc_etale` cascade aussi peu que `flanc_seul` malgré 40 m d'écart —
alors la connaissance est bien de camp et instantanée. **Toute mesure « combien d'hommes »
est morte définitivement**, à n'importe quel écartement, et il ne faut plus jamais en
proposer. C'est un résultat, pas un échec. On l'écrit et on arrête cette branche.

**D1 — DESCRIPTION.** Distribution de `cascade` par bras, et part des essais où `cascade`
vaut 0. Aucun seuil : c'est la mesure du phénomène, elle ne peut pas « rater ».

**D2 — BRUIT.** Sur `d_grp`, le bruit est `|médiane(deux_axes) − médiane(deux_axes_bis)|` et
`|médiane(flanc_seul) − médiane(flanc_seul_bis)|`. On retient le plus grand des deux.
→ Si ce bruit dépasse **25 m**, l'instrument ne mesure rien d'utilisable et D3 n'est pas lu.
⟨le banc n°3 est mort là-dessus : deux rejeux identiques donnaient 0/3 contre 3/3⟩

**D3 — L'HYPOTHÈSE, et elle n'est lue que si D0 et D2 passent.**
Une base de feu retarde la détection du groupe qui manœuvre :
`d_grp(deux_axes)` **strictement inférieur** à `d_grp(flanc_seul)` — repéré plus près, donc
plus tard — dans au moins **14 configurations sur 20**, test des signes bilatéral **p < 0,05**,
**et** écart médian supérieur au bruit de D2.

**D4 — CONTRÔLE NÉGATIF.** L'effet ne doit **pas** apparaître entre `flanc_seul` et
`flanc_seul_bis`. S'il y apparaît, D3 ne vaut rien.

**D5 — PRÉSENCE.** `bloc_1axe` doit être repéré dans au moins 18 configs sur 20. Sinon la
ligne défensive ne voit rien et le banc entier est nul.

**D6 — TIR.** Les coups des fixateurs sont comptés. Si `deux_axes` tire zéro coup sur une
config, cette config est **exclue de D3** : sans stimulus il n'y a pas de base de feu.
⟨le 3/08 un tireur censé ne pas tirer en a lâché 21 ; on compte toujours⟩

## Ce que ce banc ne pourra pas dire

Il ne dira rien sur la survie, ni sur la prise d'objectif. Le groupe manœuvrant est désarmé
et invulnérable — c'est le prix à payer pour que « ce que le camp adverse sait de lui » garde
un sens. Un effet sur la distance de détection n'est pas un effet tactique tant qu'il n'est
pas rejoué avec des hommes qui peuvent mourir.

## Décompte public des bancs tentés sur cette hypothèse

1. banc d'escouade n°2 (pilote) — observation après coup, non pré-enregistrée, sans valeur
2. banc d'escouade n°3 — pré-enregistré, **verdict NUL par son propre critère C0**
3. banc d'escouade n°4 — celui-ci

Trois tentatives. Si D0 échoue, on s'arrête à trois et on l'écrit.
