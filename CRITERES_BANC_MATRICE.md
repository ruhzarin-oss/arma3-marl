# LE BANC-MATRICE — critères déposés avant toute écriture de code

*6 août 2026, nuit. Rien n'est codé, rien n'est lancé, aucun chiffre n'est lu.*

## Pourquoi ce banc existe

La question de l'étage 1 — *le gain de perception devient-il de l'arrivée ?* — était en réalité
**deux questions collées** :

1. **l'agent LIT-il le monde ?** — ses yeux ordonnent-ils le danger comme le monde l'ordonne ;
2. **agir sur cette lecture PAIE-t-il ?** — en mètres gagnés, en objectifs pris.

On a passé trois semaines à vouloir les trancher **ensemble**, dans un simulateur incapable des
deux. Cinq bancs de sandbox, cinq refus. Le dernier, ce soir, avec la meilleure physique
possible — le prédicteur appris sur le corpus lui-même : **le crochet y arrive moins souvent
que la ligne droite**, inversant un verdict certifié quatre fois sur Arma.

> **Le verdict du flanc vit dans une discontinuité. Tout modèle fidèle en moyenne efface les
> discontinuités. Ce n'est pas une panne, c'est un plafond.**

D'où la découpe, qui est de Younes : **la matrice juge les yeux, Arma juge les actes.**

## Ce que le banc fait, en une phrase

Il ne simule rien. Il prend **563 383 instants réels d'Arma dont on connaît la suite** — cet
homme est-il mort dans les 30 secondes ? — montre à l'agent **ce qu'un soldat pouvait voir à
cet instant**, et compte s'il classe ces instants dans l'ordre que le monde a certifié.

**La falaise du cône y est brute, dans les données.** On ne demande plus à un modèle de la
reproduire : on la lit.

## PORTE 0 — le certificat de naissance, naturel et gratuit

Deux paquets d'instants **dont l'ordre est connu d'avance**, tirés de deux acquis certifiés du
dossier :

| paire | ordre connu | source |
|---|---|---|
| **dans le cône / hors du cône** | dedans est plus mortel | angle mort, 18/18 contre 0/26 |
| **vu / non vu** | vu tue ~2× plus | 563 000 observations, effet croissant avec la distance |

> **Le banc doit séparer ces deux paires, dans le bon sens.** S'il n'y arrive pas, il ne peut
> rien dire d'un agent, et **rien ne se lit** — on répare le banc, point.

**Taille de la porte, déclarée AVANT** — et je la déclare ici parce que je viens de l'oublier
sur la PORTE 0 de ce soir, deux heures après avoir cité la règle qui l'exige :

> Avec des paquets d'au moins **20 000 instants** de chaque côté, ce banc voit un écart de
> mortalité d'environ **1 point**. Il exige donc, pour passer : **écart ≥ 3 points, dans le
> sens connu**. En dessous, un « non significatif » ne veut rien dire et il faudra l'écrire.

## L'AIGUILLE — les strates, choisies avant de regarder l'agent

Là où tout le monde meurt, ou personne, aucune perception ne se distingue. On ne juge que dans
la bande où l'aiguille bouge.

> **Strates retenues : celles dont la mortalité observée tombe entre 20 % et 80 %.**
> Elles se déterminent **sur le corpus seul**, avant que le moindre agent ne soit évalué.

Si aucune strate n'atteint cette bande, **le banc ne juge pas** et on le dit tel quel.

## LES DEUX CONTRÔLES QUI SAVENT ÉCHOUER

**C1 — le contrôle NÉGATIF, et c'est le plus important.** Le prédicteur lissé — celui qui a
échoué ce soir avec *« le bon ordre, le mauvais contraste »* — **DOIT ÉCHOUER la porte du
contraste de falaise**.

> Concrètement : sur la paire dans-le-cône / hors-du-cône, l'écart que **le prédicteur**
> attribue doit être **nettement plus faible** que l'écart que **le corpus** mesure.
> **Si le prédicteur passe cette porte, c'est que la porte est décorative** — elle ne
> mesurerait pas le contraste — et rien de ce banc ne se lit.

C'est un contrôle négatif adossé à un défaut **mesuré il y a une heure**, pas à une intuition.

**C2 — le contrôle NUL.** Sur étiquettes brassées, tout doit retomber à l'indifférence. Le
dossier a déjà été mordu là-dessus : un contrôle nul mal branché avait rendu 0,5304 au lieu de
0,5047, en évaluant un modèle contre les **vraies** étiquettes.

## La stratification obligatoire — 92 %

L'écart entre le prédicteur enrichi et le prédicteur transférable vient à **92 % de la
suppression subie** — « je suis déjà sous le feu », une quasi-tautologie : on meurt quand on
est déjà arrosé. Une porte qui ne stratifie pas là-dessus mesurerait surtout cette tautologie.

> **Toute comparaison se fait à suppression subie constante.**

## Ce que ce banc ne dira JAMAIS

- Si agir sur la lecture **paie**. Pas de boucle fermée : les instants sont figés, l'agent ne
  peut pas changer la suite.
- Si le gain **transfère** à un comportement. Cette question reste à Arma, **une seule
  campagne, à la fin**, sur l'architecture du banc A2 — celui qui a prouvé qu'il savait dire
  non (+17,7 pts, p = 0,0016).

## Ce qu'il coûte, et pourquoi c'est le bon banc

**Des minutes, pas des nuits.** Les données sont sur disque, il n'y a ni monde à simuler, ni
pont à maintenir, ni serveur à surveiller. Et surtout : **il est rejouable**, contrairement à
la fourche de la sandbox qui, elle, était à un coup.

⟨la sandbox garde le gymnase — exploration, plomberie, locomotion. Elle a perdu le tribunal,
définitivement, ce soir.⟩
