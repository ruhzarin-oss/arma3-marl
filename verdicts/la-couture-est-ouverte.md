# La couture est ouverte : le banc prend enfin une décision fondée sur l'ennemi

*15 septembre 2026. Commit du correctif : `bf6871b`. Contrôle : campagne `PHASE1-CONTROLE-15-09`,
4 mondes, 17 épisodes, `depart=3`, `obs=1`, `arret=4`, `azimut=0`.*

## Ce qui était cassé

Le script choisissait toujours la première des deux ouvertures de l'enceinte — **145 épisodes sur
145**, et sur tout le corpus **l'indice retenu était l'ouverture la plus proche dans 871 cas sur
871**. Sa règle comparait pourtant un compte d'ennemis connus :

```sqf
private _n = { ((_x select 0) distance2D _o) < 110 } count CHACAL_VUES;
private _sc = _n + (_d / 150);
```

Mais l'enceinte a un rayon de 46 m, les deux portes sont à 108,0° et 282,857° relatifs — une corde
de **92 m** — et les défenseurs naissent dans 55 m. **Tout défenseur était donc à moins de 110 m des
DEUX portes.** Le terme était identiquement égal des deux côtés, inerte par construction :
`gardes` valait `[k,k]` dans **1 337 épisodes sur 1 337**, oracle compris, où il valait `[4,4]`
dix-huit fois sur dix-huit. On donnait la vérité au script et sa décision ne bougeait pas.

Deuxième verrou : `CHACAL_VUES` n'est rempli que par la phase 3 OBSERVATION, sautée partout parce
que son seuil valait 3 alors que le maximum jamais atteint est 2 — 110 échecs sur 111, 55 heures
pour zéro information.

## Ce qui a été fait, et comment les seuils ont été choisis

**Le terme de garde** : chaque défenseur connu est attribué à l'ouverture dont il est **le plus
proche**. Sans seuil, donc sans arbitraire. Le score n'a pas changé, et c'est mesuré : l'écart de
distance entre les deux portes vaut 18 m en médiane, 83 m au pire, jamais plus que la corde — soit
**0,55 point de score contre 1,00 pour un seul garde d'écart**. Le compte décide dès qu'il diffère ;
la distance ne tranche plus que les égalités.

**Le seuil de renseignement**, dérivé de 148 épisodes ayant joué la phase 3 :

| seuil | part des épisodes qui l'atteignent |
|---|---|
| 0 | 100,0 % — une porte qui ne sait pas se fermer |
| **1** | **44,6 % — le seul dont l'issue soit vraiment incertaine** |
| 2 | 12,2 % |
| 3 | 0,7 % — l'état d'avant |

## Le contrôle, et ses trois prédictions enregistrées d'avance

| prédiction | falsificateur | résultat |
|---|---|---|
| `gardes` doit différer entre les deux portes | si `[k,k]` partout, le correctif n'agit pas | **7 sur 17** (avant : 0 sur 1 337) |
| la porte B doit pouvoir être choisie **pour ses gardes** | si `indice=1` n'arrive que par la distance | **2 sur 17, les deux par un écart de gardes** |
| la phase 3 doit savoir réussir **et** échouer | si l'issue est uniforme, le seuil est encore faux | **ATTEINT 47 % / PAUVRE 53 %** |

Et **zéro erreur SQF** : le bloc ajouté n'était pas compilable hors du jeu, il tourne.

## L'épisode qui fait la démonstration

```
g11_r4 : indice|1  gardes|[1,0]  distances|[695,716]  dgarde|[37,56]  score|4.77  rens|1
```

Un défenseur à **37 m** de la porte A et **56 m** de la porte B : il est attribué à A. Score de
A = 1 + 695/150 = 5,63 ; score de B = 0 + 716/150 = 4,77. **Le script a choisi la porte la plus
loin parce qu'elle n'a pas de défenseur devant.**

C'est la première fois, en 1 337 épisodes, que ce banc prend une décision fondée sur ce qu'il sait
de l'ennemi.

## Ce que cela ne dit PAS, et il faut l'écrire

**Aucun gain de taux n'est démontré, ni attendu.** L'amendement du 15/09 a mesuré que la position
des défenseurs au moment du choix ne prédit rien : pente intra-graine **−0,1 point**, IC 95 %
[−4,2 ; +4,4], **p = 1,00**. Ce correctif répare un **instrument** et ouvre une couture
**décidable** ; il ne prétend pas améliorer la mission, et annoncer un gain serait mentir.

La question suivante est entière : **ce choix paie-t-il ?** Elle demande un bras apparié porte A
contre porte B forcée, sur huit mondes — la puissance d'un plan apparié vient du nombre de mondes,
et quatre plafonnent à p = 0,625 même avec trois signes positifs.

## Ce qui reste ouvert, nommément

- `CHACAL_AZIMUT > 0` écrase le choix juste après : le correctif n'agit que dans le bras SCRIPT,
  il est inerte en HASARD et en IMPOSE.
- Les deux replis `CHACAL_OUVERTURES select 0` ne passent pas par le score.
- La ligne `AVERT|hors_corpus|observation_coupee|...|jamais_atteint|1` devient fausse ; non touchée.
- `bancs/alize1` porte les deux mêmes défauts et n'est pas patché.

*Voir aussi : `le-script-ne-choisit-pas-son-ouverture` et son amendement,
`phase3-porte-hors-datteinte`, `mesure-doit-savoir-echouer`.*
