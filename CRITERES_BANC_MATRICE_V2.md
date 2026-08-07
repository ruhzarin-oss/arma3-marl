# LE BANC-MATRICE v2 — paire réparée, critères redéposés

*7 août 2026. Redépôt après le refus du 06/08. Aucun chiffre de la v2 n'est lu.*

**Fiches relues avant ce chantier ⟨règle 10⟩** : `fibua-line-bench-certified`,
`etre-vu-tue-deux-fois-plus`, `angle-mort-certifie-arma`, `knowsabout-est-de-camp-pas-de-soldat`,
`expo-vaut-le-hasard`. Aucune ne porte déjà ce calcul.

## Pourquoi un redépôt

La v1 a rendu trois refus. Deux venaient de **mes propres définitions**, et je ne les ai pas
réécrites après les avoir vues échouer — je suis allé chercher pourquoi.

**La paire « vu / non vu » donnait −0,3 point.** Le code de l'émetteur en donne la raison
(`hmt_capture_v9_battlelines.sqf`, ligne 257) :

```sqf
_i = lineIntersectsSurfaces [eyePos _a, aimPos _b, _a, _b, true, 1, "VIEW", "FIRE"];
```

C'est une **ligne de vue pure entre deux points — donc symétrique**. Elle dit « il y a de la
vue entre ces deux hommes », jamais « il me voit, moi ». Or le fait certifié — être vu tue
deux fois plus fort — est **directionnel**.

## La paire réparée, et elle ne coûte pas une nuit

L'orientation était déjà dans le corpus : `a_lui`, l'angle sous lequel je suis dans son champ.

> **« Il me voit » = ligne de vue ET je suis dans son cône (35°, mesuré).**

Mesuré, à suppression subie constante :

| définition | part des instants | écart de mortalité |
|---|---|---|
| vu **symétrique** | 18,9 % | **−0,27 %** — ne sépare pas |
| dans un **cône** | 39,3 % | **+3,68 %** |
| **vu directionnel** | **6,0 %** | **+3,91 %** |

⟨et la nuit d'Arma prévue pour capturer cette colonne est **annulée** : le corpus portait les
deux morceaux, il manquait de les croiser. Deuxième chantier économisé en une heure par
l'amendement de la règle 6 — *une propriété du monde se lit dans son code avant qu'on ne
bâtisse dessus*.⟩

**Chiffre à retenir : 6 % des instants seulement.** Être dans le champ *et* en vue dégagée est
rare — c'est l'intersection étroite où la mortalité se joue, et ça donne sa portée réelle au
sursis de quatre secondes.

## PORTE 0 — les deux paires, ordre connu

| paire | ordre connu | source certifiée |
|---|---|---|
| **dans le cône / hors** | dedans plus mortel | angle mort, 18/18 contre 0/26 |
| **vu directionnel / non** | vu plus mortel | être vu tue 2× plus, 563 000 obs |

**Taille de la porte, déclarée avant, inchangée** : ≥ 20 000 instants par paquet, écart exigé
**≥ 3 points** dans le sens connu. ⟨la paire directionnelle en compte 33 824 d'un côté :
l'effectif tient.⟩

## AIGUILLE — la règle corrigée par Fable

La v1 exigeait des strates à mortalité entre 20 % et 80 %. **Aucune ne l'atteignait** — la
mortalité vaut 7 à 12 % partout. Fable a tranché : la bande vise **ce qui pourrait saturer la
lecture — le séparateur**, pas le taux brut. À 7-12 % sur 563 000 lignes, chaque strate contient
des milliers de morts : **l'aiguille n'est pas au butoir.**

> **Critère redéposé : une strate est utilisable si elle porte ≥ 2 000 instants ET ≥ 200 morts.**
> Le butoir qu'on surveille est celui du séparateur, pas celui de la mortalité.

## LES CONTRÔLES

**C1 — NÉGATIF, remplacé.** La v1 exigeait que le prédicteur lissé échoue la porte du
contraste. **Il l'a écrasée : 314 % du contraste du corpus.** Ma prémisse était fausse — il
n'a jamais lissé. Fable en désigne un autre, certifié : **`expo` vaut le hasard, AUC 0,5005.**

> **`expo` doit ÉCHOUER toutes les portes. S'il en passe une, cette porte est décorative.**

**C2 — NUL.** Étiquettes brassées, tout retombe à l'indifférence, |écart| < 3 points.

**C3 — STRATIFICATION obligatoire.** Toute comparaison à **suppression subie constante** :
92 % de l'écart entre prédicteur enrichi et transférable vient de cette quasi-tautologie.

## Ce que ce banc ne dira JAMAIS

Si **agir** sur la lecture paie. Les instants sont figés, l'agent ne peut pas changer la suite.
Cette question reste à **Arma, une seule campagne, à la fin**, architecture du banc A2.

## Et ce qu'il servira à mesurer ensuite

**Les faits discrets** — l'idée de Younes : *suis-je vu, par combien, sous quel angle, mon
flanc est-il masqué*. Son levier est déjà certifié à **−28 % d'exposition pour deux nombres**.
Le banc dira si ces faits ordonnent le danger mieux qu'un scalaire continu. **Pas de LLM, pas
de texte libre** — deux résultats négatifs au dossier ; des **états**, dans le vecteur
d'observation.
