# LE FEU NATIF S'EST TU — le discriminant, déposé AVANT toute fouille

*10 août 2026, 18 h. **Écrit avant d'avoir regardé quoi que ce soit.** C'est le seul moment où
je peux encore l'écrire sans l'avoir choisi.*

**Fiches relues ⟨règle 10⟩** : `accord-sur-zero-nest-pas-accord`, `pont-arma-meurt-en-service`,
`mesure-doit-savoir-echouer`, `arma-fps-wall-headless-clients`.

## LE FAIT, TEL QU'IL EST AU JOURNAL

Session 3 lancée à 1 h 31, arrêtée par elle-même à 1 h 33 sur
`HMT|AP|ECHEC|arrivee|aucun_impact_sur_les_couverts`. Deux essais. Le bras **feu natif** a tiré
`coupsapp|0` au pré-vol, quand ce même bras tirait 99 à 461 coups aux sessions 1 et 2 (quatorze
essais, jamais zéro). Les trois appuis étaient `vivant|1 captif|0 etat|HEALTHY`, `armes|9`.

⚠️ **Et c'est précisément pour ça qu'on ne relance pas sur la foi de `vivant` et `armes`.**
⟨Fable, 10/08 : *« jamais une relance sur la seule foi de `vivant|armes` — l'aiguille du trieur
est l'impact délivré, pas la santé des tireurs »*⟩ Trois hommes en pleine santé, armés, qui ne
tirent pas : la santé n'est pas l'aiguille.

## LE DISCRIMINANT — deux issues, écrites avant de regarder

La question est : **le monde de la session 3 était-il celui des sessions 1 et 2 ?**

On compare **l'empreinte du monde** — sha256 du répertoire de mission, liste de mods dans
l'ordre, config serveur, `serverMod` — de la session 3 contre celle des sessions 1-2, relevée
dans leurs propres journaux de démarrage.

> **Issue A — empreintes IDENTIQUES** → c'est une **panne intermittente** du banc, cause externe
> (zombie, état serveur, ordre de chargement). La session 3 **se relance telle quelle**, après
> réparation externe, et **seulement si son pré-vol relit `coupsapp` et `delivre` dans la bande
> historique** (coups > 0 sur le bras natif ; `delivre` entre 56 et 264). Les trois sessions
> restent comparables : une réparation qui **restaure** l'état déposé sans toucher un paramètre
> déposé n'est pas un amendement ⟨règle 13⟩.

> **Issue B — empreintes DIFFÉRENTES** → le monde a changé sous le banc. Les sessions ne sont
> plus comparables, **le banc est redéposé entier**, et les sessions 1 et 2 sont à refaire
> dessus. C'est cher, et c'est le prix juste.

**Ce que je n'ai pas le droit de faire** : trouver une troisième explication après avoir
regardé. Si les pièces ne rendent ni A ni B — par exemple si les empreintes des sessions 1-2 ne
sont pas relevables — alors **on ne conclut rien**, on le dit, et on redépose. ⟨la fiche
`accord-sur-zero-nest-pas-accord` : un accord qu'on ne peut pas empreindre n'est pas un accord⟩

## CE QUI FERAIT ÉCHOUER CETTE INVESTIGATION — écrit avant

- **Les journaux de démarrage des sessions 1-2 ne portent pas le modset** → on ne peut pas
  empreindre, on ne conclut pas, on redépose le banc avec l'empreinte obligatoire au démarrage.
- **Le pré-vol de relance ne rend pas de coups sur le bras natif** → on ne relance pas, quel que
  soit ce que dit l'empreinte. L'empreinte autorise la relance ; c'est le pré-vol qui l'ouvre.
- **`delivre` hors de la bande historique au pré-vol** → même conclusion : le monde n'est plus
  celui-là, on ne mesure pas dedans.

---

## LA LECTURE — faite après le dépôt, contre les deux issues écrites plus haut

| pièce | sessions 1-2 | session 3 | |
|---|---|---|---|
| modset, dans l'ordre | CBA, LAMBS, PinnedDown ×2, rhsafrf, rhsusaf | **identique** | = |
| mission jouée | `BancAppui.Stratis` | **identique** | = |
| code du banc (`banc_appui.sqf`) | inchangé depuis le 09/08 19 h 13 | **identique** | = |
| six terrains candidats | mêmes coordonnées | **identiques** | = |
| phase | 3 | 3 | = |
| `createPeer failed` | — | **aucun** | = |
| indice de session | 1, puis 2 | 3 | **déposé comme variant** |

**Le seul paramètre qui a bougé est l'indice de session** — et il est déposé comme variant : le
plan EST trois sessions. Lu sur pièces, il ne commande que l'indice de répétition
(`_plan pushBack [2, _sess]`), et le pré-vol tourne à répétition 0, donc **hors de sa portée**.

> **ISSUE A. Panne intermittente.** Le monde de la session 3 était celui des sessions 1 et 2.

Et le pré-vol le dit deux fois plutôt qu'une : au même essai, les défenseurs de la session 3 ont
délivré **201 impacts** — davantage que les 56 de la session 2 — pendant que les trois appuis
tiraient **zéro**. Ce ne sont pas les fusils, ce n'est pas le terrain, ce n'est pas la charge :
**c'est l'ordre de feu des appuis qui n'est pas parti**, cette fois-là et pas les autres.

## LA RELANCE, ET SA PORTE

La session 3 se relance **telle quelle** — aucun paramètre déposé n'est touché, donc les trois
sessions restent comparables ⟨règle 13⟩. Réparation externe seule : tuer proprement, attendre
que le port soit rendu, repartir sur un serveur neuf.

**Et la porte du pré-vol existe déjà — c'est elle qui a arrêté la session 3.** Le contrôle
`arrivee` exige des impacts sur les couverts ; il a refusé de produire une donnée fausse et a
coupé en deux minutes. On ne relance donc pas *en espérant* : si le feu natif se tait encore,
**le banc s'arrêtera encore**, et ce sera la deuxième occurrence d'une panne qu'il faudra alors
chasser dans le code de l'ordre de feu, plus dans le monde.

⚠️ **Ce que cette lecture NE dit pas** : pourquoi l'ordre n'est pas parti. Une empreinte
identique établit que le monde n'a pas changé — **elle n'explique pas la panne**, elle dit
seulement où il est inutile de la chercher.
