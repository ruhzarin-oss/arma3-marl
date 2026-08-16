# LES CLIQUETS DU 16/08 — ce qui n'était pas écrit avant n'a pas le droit de peser après

Cinq fautes de la soirée, chacune convertie en test permanent. Elles sont **toutes de la
même famille** : des choses vues, citées ou décidées **hors des critères écrits**.

## 1 · Un mécanisme absent de la liste pré-écrite ne peut pas devenir un verdict

Ma sonde du geste jugeait **quatre** causes pré-écrites. La séparation sur
`isTouchingGround` est une **cinquième signature, trouvée dans les données**. Je l'ai
déposée comme VERDICT, avec effet de sursis sur trois acquis.

Pire : la cause pré-écrite qui **survivait** était (c) — « vitesse 6, déplacement nul »,
soit exactement la signature de l'**obstacle** que j'avais moi-même écrite. Elle n'a jamais
été traitée.

> **CLIQUET** — un mécanisme découvert dans les données d'une sonde entre comme
> **hypothèse de la sonde suivante**, jamais comme verdict. « Le premier pari est gratuit,
> le deuxième s'achète avec une sonde » : le vol était mon deuxième pari, et il est entré
> au registre **avant** son banc.

## 2 · Une signature de sonde est un instrument, et la règle 16 s'y applique

La signature (b) — « l'IA ré-engage → la vitesse relue retombe » — **n'a jamais eu de
contrôle positif**. Rien ne prouvait que la vitesse relue retombe quand l'IA reprend la
main. Ma sonde a donc « réfuté » (b) avec un instrument non contrôlé — et **(b) est
exactement la cause que mon correctif final traite**.

S'ajoute la puissance : n = 4 sur un phénomène intermittent à ~25 %, soit **P(silence)
≈ 0,32**. Une absence à cette puissance ne réfute rien.

> **CLIQUET** — chaque signature attendue d'une sonde est un instrument : elle déclare son
> contrôle positif, et la sonde déclare la puissance qui rend une absence lisible.

## 3 · Un banc muet est muet

La v1 du banc des jambes a échoué son contrôle positif. J'ai néanmoins « vu au passage »
que le bras en service rendait 11,8 m — puis je l'ai **cité**. Et les seuils de la v3
(≥ 8 m) sont assis juste sous ce chiffre.

> **CLIQUET** — les chiffres d'un banc muet ne sont ni lus ni cités. S'ils l'ont été, la
> **fuite est déclarée en tête du banc suivant**, et les seuils du suivant s'ancrent sur
> une référence **externe** (ici : les 19,7 m du gymnase, le < 3 m de T5) — jamais sur elle.

## 4 · Le lanceur vérifie son budget, et les bras décisifs passent en premier

Le minuteur de `banc_jambes.py` était calé sur la v2 : il a coupé à **51 essais sur 64**.
Le bras tronqué est le **bras 7**, le seul qui décidait du verdict, parce qu'il était
**dernier** — il finit à n = 4.

> **CLIQUET** — un lanceur calcule `bras × essais × durée` et refuse de partir si son
> minuteur est plus court. Les bras décisifs sont **entrelacés ou placés en premier**.

## 5 · T4 certifie un canal de feu que l'homme servi n'a pas — VÉRIFIÉ

Soupçon de Fable, **confirmé par lecture** ce soir :

- `arma_couture.py:27` — l'homme servi reçoit `disableAI "AUTOCOMBAT"` et `disableAI "FSM"`.
- T4 du prévol certifie le feu d'un témoin qui **garde** `AUTOCOMBAT` — et il le garde
  précisément parce que, mesuré le 16/08, `forceWeaponFire` **seul ne suffit pas**.

**Le vert de T4 couvre donc une capacité que la politique n'a pas.**

À rapprocher de `ANOMALIE_AUTOCOMBAT.md`, ouverte et non résolue : la scène appelle
`disableAI "AUTOCOMBAT"` sur ses attaquants et **ils l'ont pourtant actif**. Si l'anomalie
est réelle, l'homme servi tire par un canal que personne n'a déclaré ; si elle ne l'est
pas, le feu de la politique n'est certifié par **aucun** test.

> **À FAIRE AVANT TOUT ÉPISODE DE POLITIQUE** — établir par quel canal part le feu de
> l'homme servi, et faire certifier **ce canal-là** par un T du prévol.
> **La nuit NATIF n'en dépend pas** : le natif joue l'IA entière et n'emprunte pas le
> canal de la consigne.

## 6 · Et T5 n'a pas de contrôle positif POST-correctif

J'ai appliqué la règle 16 à T4 — sabotage des munitions, 3 rouges sur 3, bon diagnostic —
et **pas à T5**. Un test qui rend zéro rouge sur cinquante est soit réparé, soit devenu
**incapable d'échouer**, et rien ne dit lequel.

> **À FAIRE AVANT TOUT ÉPISODE DE POLITIQUE** — `HMT_SABOTER = "jambes"` (retrait de `PATH`
> ou équivalent) doit faire rougir T5 **3 fois sur 3**, avec diagnostic.
