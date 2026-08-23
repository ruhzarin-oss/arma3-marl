# PRÉ-INSCRIPTION — RENDRE À LA POLITIQUE SES TROIS ACTIONS DE POSTURE

**23/08/2026, 13 h 30. Écrite avant tout entraînement, et avant que la comparaison sur le
banc réparé soit connue** (la passe 2 de la politique en est à 29 épisodes sur 67).

## Le fait qui la motive, déjà mesuré

`boucle.py:21` — `NA = 10` : *8 caps + tenir + feu*. Le monde, lui, en offre **13**
(`assault_terrain.py:230`, postures activées). **La politique ne peut pas changer de
posture.** Conséquence mesurée (`2dd0f8c`) : ses trois colonnes de posture sont
**strictement constantes** (1, 0, 0) — trois de ses douze entrées sont **mortes par
construction**, et l'ablation ne pouvait rien en dire.

Et les quatre canaux qui **varient** — `SLOPE`, `los`, `nd`, `alive` — sont **ignorés** :
brouillés tous ensemble avec `dcover` et les postures, ils coûtent **−3,3 points**, c'est-à-dire
rien. Seules les quatre colonnes de géométrie décident (les brouiller : **50,7 % → 0,1 %**).

## Le geste, et lui seul

**`NA = 10` → `NA = 13`**, puis réentraînement à protocole identique
(`entrainer(iters=140, n=256, lr=3e-4)`, mêmes graines d'entraînement, mêmes récompenses).
**Rien d'autre ne change** : ni le monde, ni la récompense, ni l'observation, ni le lecteur.
Un réentraînement qui change deux choses ne prouve ni l'une ni l'autre.

## Les prédictions, écrites ici

| n° | prédiction |
|---|---|
| **P1** | la nouvelle politique **bat l'ancienne d'au moins 5 points** dans le gymnase (témoin : 50,7 %) |
| **P2** | les **trois colonnes de posture cessent d'être constantes** — dispersion > 0,05 |
| **P3** | **`los` devient lu** : le brouiller coûte **plus de 5 points** (aujourd'hui : −3,0, soit rien) |

**P3 est la vraie question.** P1 et P2 peuvent passer sans que rien de tactique soit appris :
se coucher ralentit, donc un agent peut gagner des points en se couchant **au hasard** si
ça réduit les dégâts. **Seule P3 dit qu'il se couche PARCE QU'IL EST VU.**

## Le falsificateur

> **Si P1 passe et P3 échoue**, l'agent a gagné en survivant mieux **sans regarder personne** :
> ce n'est pas de la tactique, c'est un réglage. On l'écrira ainsi, et on ne présentera
> pas le gain comme une lecture du monde.

> **Si P2 échoue** — les postures restent constantes alors que l'action existe — c'est que
> **rien ne paie de se coucher**, et le levier n'est pas dans les actions mais dans la
> récompense. Le geste suivant serait alors sur le coût, pas sur le vocabulaire.

## Ce qui est interdit ici

- **Toucher au monde, à la récompense ou à l'observation** dans le même geste.
- **Lancer quoi que ce soit avant 15 h 40** : l'entraînement écrit `boucle_pol.pt`, et
  `banc_live.py` **recharge ce fichier à chaque épisode**. Un entraînement lancé maintenant
  remplacerait la politique **en pleine nuit** — la moitié des épisodes joueraient un autre
  réseau, et la comparaison serait détruite sans que rien ne le signale.
- **Choisir les seuils après avoir vu les nombres.** 5 points, 0,05 et 5 points sont posés ici.

⚠️ **Dette technique à solder dans le même geste** : l'entraînement doit écrire sous un nom
**daté**, jamais sur l'artefact courant. Un fichier unique partagé entre l'entraînement et
la mesure est un accident qui attend son heure — celui-ci a failli arriver aujourd'hui.
