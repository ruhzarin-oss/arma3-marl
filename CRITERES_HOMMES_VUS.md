# Critères du test « nombre d'hommes vus » — écrits AVANT le run

*4 août 2026, 19h. Aucune donnée du nouveau run n'existe au moment où ce fichier est écrit.*

## D'où vient l'hypothèse, et pourquoi il faut un run neuf

Le banc d'escouade du 4/08 a **échoué** à son critère pré-enregistré : `deux_axes` ne bat pas
`flanc_seul` sur la survie aux jalons (9 victoires, 3 défaites, 8 égalités, p = 0,146).

Mais une colonne **non pré-enregistrée** montrait un écart large :

| | hommes du groupe manœuvrant repérés |
|---|---|
| `deux_axes` (avec base de feu) | **31 / 60** — 52 % |
| `flanc_seul` (sans base de feu) | **51 / 60** — 85 % |

**Cette observation ne prouve rien.** Elle a été trouvée après coup, dans des données déjà
utilisées pour un autre test. La rapporter comme un résultat serait exactement le glissement
que Fable me reproche depuis deux jours.

Elle a en revanche une explication mécanique plausible : le score de jalons prend le
**maximum sur le groupe** — dès qu'un homme est repéré, les trois comptent comme repérés.
La métrique écrase donc, par construction, un effet qui porterait sur *combien* d'hommes
sont vus plutôt que sur *si* le groupe l'est.

D'où ce test : **hypothèse déposée avant, sur des données neuves.**

## L'hypothèse

> Une base de feu réduit la **part des hommes du groupe manœuvrant qui sont repérés**,
> même quand elle ne change pas le moment où le groupe, pris comme un tout, est détecté.

## La mesure

Pour chaque configuration et chaque bras : la part d'hommes du groupe manœuvrant dont
`knowsAbout` a atteint 1,5 au moins une fois. Relevée **à chaque jalon** (120, 90, 60, 40 m)
et à l'arrivée.

Comparaison **appariée** : `deux_axes` contre `flanc_seul` — même chemin de flanc, même
effectif de 3, même configuration défensive. Seule la base de feu change.

## Les critères, fixés maintenant

**C0 — VALIDITÉ.** Le bruit est mesuré par deux rejeux du même bras :
`|part(deux_axes) − part(deux_axes_bis)|` **et** `|part(flanc_seul) − part(flanc_seul_bis)|`.
Si l'écart entre `deux_axes` et `flanc_seul` ne dépasse pas **le double** du plus grand des
deux bruits, le banc est nul et rien n'est conclu.

**C1 — PRINCIPAL.** `deux_axes` a une part repérée **strictement inférieure** à
`flanc_seul` dans au moins **14 configurations sur 20**, test des signes bilatéral
**p < 0,05** (égalités exclues), **et** écart médian supérieur au bruit de C0.

**C2 — CONTRÔLE NÉGATIF.** L'effet ne doit **pas** apparaître entre `flanc_seul` et
`flanc_seul_bis` — deux bras identiques, tous deux sans base de feu. S'il y apparaît,
c'est du bruit d'ordre et C1 ne vaut rien.

**C3 — DOSE.** Si l'effet est réel, il doit être **plus marqué près de l'objectif**
qu'au premier jalon : à 120 m les manœuvrants sont encore loin, la base de feu n'a pas
encore engagé. Un effet identique à tous les jalons serait suspect.

**C4 — TIR.** `deux_axes` doit avoir tiré, `flanc_seul` non. Les coups sont comptés.

## Ce qui ferait échouer ce test, dit d'avance

- si C0 cède, le dispositif est en cause, pas la tactique ;
- si C2 montre le même écart entre deux bras identiques, l'effet est un artefact d'ordre ;
- si C1 passe mais C3 non, l'effet ne suit pas la logique de l'engagement et n'est pas
  interprétable comme de la fixation.

## Ce que le test ne dira pas

Il ne dira pas *pourquoi*. Le banc précédent a déjà établi que les armes défensives **ne
sont pas détournées** du flanc (+8° seulement, dans 9 configurations sur 20). Si l'effet
existe, son mécanisme reste à trouver — et ce sera un autre test.
