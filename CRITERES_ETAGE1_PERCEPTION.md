# Étage 1 — le CHAMP DE RISQUE : critères déposés AVANT toute mesure

*6 août 2026, 00h10. Aucun entraînement lancé. La 3090 est libre, Arma tourne en CPU.*

## D abord, une prémisse corrigée

Le plan disait « ajouter deux nombres : l arc de tir ». **C est déjà fait, et déjà payé.**
`agent_complet.py:191` calcule `ec_lui` — mon écart à la face du défenseur — et la ligne 194
le donne à l observation, avec sa saturation `sigmoid((CHAMP - ec_lui) * 1,2)`. Le −28 %
d exposition du 27/07 est un acquis **encaissé**, pas une piste à ouvrir.

⟨lu dans le code, pas dans mes souvenirs. La règle du projet : demander « QUE VOIT-IL ? »
en ouvrant le fichier, jamais en se rappelant.⟩

Ce que l agent voit aujourd hui, exhaustivement : sa position, la position / distance /
azimut de chaque défenseur vivant, s il est dans le cône de chacun, leur suppression et leur
posture, et **un scalaire de risque appris pour SA case à lui**.

Ce qu il ne voit pas : **le prix d un pas qu il n a pas encore fait.** Il connaît le coût
d où il est. Il ignore le coût d où il irait. C est le trou réel.

## Ce qui se teste

Le **champ de risque** : le danger qu il subirait **à 35 m dans chacune des 8 directions**,
huit nombres, calculés avec le risque **APPRIS** (`risque_geo.pt`, AUC 0,714 sur corpus Arma).

C est le dispositif conçu le 27/07 — mais il reposait alors sur `expo`, dont on a mesuré
depuis qu elle **vaut le hasard** (AUC 0,5005). Un champ bâti sur une fonction qui n ordonne
rien ne pouvait rien dire. La fondation existe maintenant ; le dispositif redevient sensé.

Trois choix, repris sans retouche du 27/07 :
- **à 35 m, pas au pas suivant** — c est l échelle de la MANŒUVRE, pas du réflexe ;
- **le PRIX, jamais la réponse** — le moins cher est toujours de fuir, l arbitrage reste
  entier. Pas de booléen « peut-il me tirer dessus » : ce serait souffler la réponse ;
- **géométrie générique** — qui voit quoi d où, même principe que la coque à 12 rayons.

## Le verrou d entrée : l instrument doit prouver qu il discrimine

**Rien ne se juge sur un banc qui a échoué à ses propres portes.** État constaté du banc 150
avec risque appris (`RESULTAT_BANC150_RISQUE.txt`) : **P2 (contrôle nul) et P3 (l agent bat la
droite) ont CÉDÉ**, et l oracle libre fait 7/20 quand la droite fait 2,0 — l information
parfaite ne s y détache pas.

Donc, **avant** de lire quoi que ce soit sur le champ de risque :

> **PORTE 0.** Sur le banc retenu, le **crochet scripté** doit battre l **assaut frontal
> scripté** sur la métrique primaire. Si les deux doctrines ne se séparent pas, le banc ne
> peut pas juger un agent, et **l étage 1 n est pas lancé** — on répare le banc, point.

C est le contrôle qui a manqué quatre nuits durant : cinq « refus » de l agent jugeaient en
réalité le banc.

## La métrique primaire : l ARRIVÉE, pas l exposition

L exposition est le moyen ; l objectif est la fin. Un agent moins exposé qui n arrive pas
n a rien gagné.

**PRIMAIRE — le palier de rayon tenu.** La distance de départ la plus grande à laquelle
l agent arrive encore, curriculum identique, 3 graines. Référence sans champ : **125 m**
(`RESULTAT_CHAMP_RISQUE.log`, graine 1 : tenu à 110 m, divergence à 125 m).

> **Succès : +1 palier au moins (≥ 140 m) sur 2 graines sur 3.**

**TÉMOIN DE MÉCANISME — la distance du détour.** Choisi **dans les données**, pas dans
l intuition : c est la grandeur qui a ordonné correctement les trois doctrines le 27/07
(crochet 184 m · appris voyant 132 m · frontal 118 m). Seuil **repris sans retouche du
27/07 : ≥ 155 m**, la mi-chemin entre l appris et le crochet.

> Le témoin dit si l explication est **la bonne** ou seulement compatible. Il ne sauve pas
> un échec de la primaire et ne le remplace pas.

⟨rappel de la faute du 27/07 : mon témoin d alors — « temps passé dans l angle mort » — est
monté de 18,9 à 20,2 % pendant que l exposition chutait de 28 %. Je savais QUE ça marchait,
pas COMMENT. Un témoin se choisit dans les données.⟩

## Les contrôles qui savent échouer

**C1 — NUL (placebo).** Même agent, même architecture, huit nombres **de bruit** à la place
du champ. **Doit ne rien gagner.** S il gagne, ce n est pas l information qui paie, c est la
capacité ajoutée au réseau — et tout le résultat tombe.

**C2 — PRÉSENCE.** Le champ doit **discriminer** : écart-type entre les 8 directions
supérieur à la moyenne du champ. S il est plat, on donne huit copies du même nombre.

**C3 — SMOKE-TEST, avant les heures de GPU.** Un run de 2 itérations doit imprimer la
dimension d entrée passée de 8 à 16 canaux par entité **et** un champ non constant sur un
lot. Tant que ça n est pas à l écran, rien de long ne part.
⟨la règle maison : prouver que le changement est ACTIF avant de payer la nuit.⟩

## Ce qui la ferait échouer — écrit maintenant

- **La primaire ne bouge pas** (palier < 140 m sur 2 graines / 3) : le champ est du confort,
  pas de la capacité. **On ferme le chantier perception ce soir-là.** Pas de deuxième réglage,
  pas de « il manquait un tarif » — c est ainsi qu on perd quatre nuits.
- **La primaire monte mais C1 monte aussi** : c est la taille du réseau, pas l information.
  Résultat nul, versé tel quel.
- **La primaire monte et le témoin ne suit pas** (détour < 155 m) : on garde le gain et on
  écrit **« ça marche, on ne sait pas pourquoi »**. On ne raconte pas d histoire.
- **PORTE 0 cède** : rien n est lancé, et la nuit passe à réparer le banc.

## Coût

Une nuit. Le champ coûtait **×1,4** en temps de calcul au 27/07, indépendamment du nombre
d environnements — le GPU est sous-employé, la 3090 est libre, Arma occupe le CPU.

Si l étage 1 échoue, **l étage 2 n existe pas** et un trimestre est économisé.
C est à ça que sert un chantier qui porte son propre couteau.

---

## Addendum — LA TAILLE DE LA PORTE, exigée par Fable et absente de la première version

*6 août, avant tout lancement. Ce fichier avait un critère de mort ; il n'avait pas sa
sensibilité. Une porte sans ce chiffre n'est pas une porte.*

Le plan initial disait : « succès = +1 palier au moins sur **2 graines sur 3** ». J'ai calculé
ce que ce dispositif sait voir, et **il ne sait pas voir grand-chose**.

Le palier est une échelle à barreaux (60, 80, 95, 110, 125, 140 m). D'une graine à l'autre,
sans aucun effet réel, il arrive qu'une graine gagne un barreau par simple chance de tirage —
disons une fois sur trois, ce qui est l'ordre de grandeur observé sur les runs précédents.

> Alors « 2 graines sur 3 » se produit **par hasard une fois sur cinq environ**.
> Une porte qui s'ouvre toute seule 20 % du temps ne prouve rien.

**Le dispositif est donc corrigé AVANT le lancement, et sur ce seul motif :**

- **5 graines**, pas 3 ;
- **succès = +1 palier au moins sur 4 graines sur 5.**

Avec la même chance de gain fortuit, ce seuil ne s'atteint tout seul qu'environ **3 fois sur
100**. C'est une porte.

⟨coût : cinq curriculums au lieu de trois. Ils tiennent dans la journée et la nuit sur une
3090 libre, et le goulot de cette machine est le CPU, pas le GPU.⟩

### Ce que la porte ne saura pas voir, et qu'on ne prétendra pas

Un gain **inférieur à un barreau** — un agent qui arrive un peu mieux au même palier — est
**invisible** à ce dispositif. Si le champ de risque améliore la marge sans franchir le
barreau suivant, on lira « pas d'effet », et ce sera faux. C'est le prix d'une métrique en
escalier, et il est accepté ici parce que la question posée est un franchissement, pas un
raffinement.

> En conséquence : un ÉCHEC de l'étage 1 se rapportera comme **« pas de franchissement »**,
> jamais comme « le champ n'apporte rien ».

### Le placebo garde le même barème

Le contrôle C1 (huit nombres de bruit) est jugé **au même seuil, sur les mêmes 5 graines**. Si
le placebo passe aussi, c'est la taille du réseau qui paie, et le résultat tombe — quel que
soit le score du vrai champ.

---

## Le smoke-test a REFUSÉ le lancement — et une erreur de chiffre à moi

*6 août, 10h50. Aucune heure de GPU n'a été dépensée.*

### 1. Correction : l'AUC du risque appris

Ce fichier annonçait **0,714**. Le point de sauvegarde réellement chargé
(`/mnt/data/corpus/risque_geo.pt`, le seul qui existe) rapporte **0,6549**.

Le 0,7138 est bien mesuré — c'est le score de l'étude du 05/08 sur 99 188 observations tenues
à l'écart. Mais **ce n'est pas ce que porte le modèle en service**. Les deux chiffres ne
parlent pas de la même chose, et j'ai cité le plus flatteur sans vérifier l'artefact.

> **Chiffre à utiliser désormais : 0,6549.** Il reste très au-dessus de l'`expo` morte
> (0,5005), et l'argument de l'étage 1 ne dépend pas de l'écart entre les deux.

### 2. Le smoke a mordu, et le diagnostic donne la cause

```
dispersion du champ entre les 8 directions   0,0077     seuil 0,010   REFUS
```

Cause mesurée : ce n'est **pas** un risque plat. Le risque appris varie bien d'une position à
l'autre (écart-type 0,066 à 0,087 selon la distance). C'est la **portée de 35 m qui est un pas
de fourmi** sur une approche de 250 m.

```
dispersion entre directions, selon la portee et la distance a l objectif
  portee     40m     60m     90m    120m    160m    200m    250m
     35m  0,0612  0,0430  0,0282  0,0186  0,0125  0,0104  0,0103
     60m  0,0737  0,0701  0,0501  0,0332  0,0227  0,0176  0,0186
    100m  0,0871  0,0814  0,0778  0,0569  0,0381  0,0293  0,0306
    150m  0,0892  0,0878  0,0828  0,0752  0,0618  0,0442  0,0450
```

À 35 m, le champ ne devient informatif qu'**en deçà de 90 m** — c'est-à-dire une fois la
manœuvre déjà jouée. Or l'agent part à 250 m et le palier du curriculum est à 125 m : sur tout
le trajet qui décide, il lirait huit copies du même nombre.

Le choix « 35 m » venait du 27/07, où il était calibré sur l'`expo` — la fonction qu'on a
depuis mesurée à 0,5005. **Il a été hérité d'un instrument mort.**

### 3. Ce que je ne fais pas

Je ne baisse pas le seuil de dispersion de 0,010 à 0,007 pour faire passer le smoke. Et je ne
change pas la portée de ma propre autorité : c'est un des trois choix de conception inscrits
plus haut, et le modifier après diagnostic est un arbitrage, pas une correction de plomberie.

**Décision demandée à Fable. Rien n'est lancé en attendant.**

---

## Soupçon PRÉ-ENREGISTRÉ — déposé pendant que le run tourne, avant tout résultat

*6 août, 15h40. Les trois bras sont en cours. Aucune graine n'est finie.*

La PORTE 0 vient de mesurer ceci, dans le monde qui tue :

```
             arrivee    pic
DROITE        49,6 %   0,617
CROCHET       61,9 %   0,604
```

Le crochet achète **+12,3 points de survie** et ne baisse le pic que de 0,013. Autrement dit,
dans ce monde, **le pic ne distingue pas une bonne manœuvre d'une mauvaise ; la survie, si.**
C'est cohérent avec tout le dossier : le flanc n'abaisse pas le pire moment, il achète du
temps hors du cône — et c'est l'engagement cumulé qui tue.

Or la récompense de l'étage 1 en cours paie **le pic** :

```
rec_l.append(-tarif*d_pic + 0.05*gagne)
```

> **Donc : si l'étage 1 ressort nul, le suspect numéro un n'est ni le concept, ni le champ à
> 0,6549, ni le tarif — c'est le terme de risque de la récompense, qui paie une grandeur dont
> la PORTE 0 vient de mesurer qu'elle ne sépare pas les doctrines.**

Écrit maintenant, avant la fin du run. Après, ce ne serait plus un soupçon, ce serait une
histoire.

⟨la loi de mort rend désormais la survie observable et dérivable : elle est disponible comme
monnaie de récompense. Ce n'était pas le cas hier — le monde ne tuait pas.⟩

## Le drapeau « fragile », posé au même moment

La seule zone extrapolée de la loi de mort — au-delà de 200 m, où la courbe n'est pas mesurée
— est **exactement là où commence chaque épisode**. L'agent part à 250 m. Les cinquante
premiers mètres de toutes les trajectoires sont gouvernés par le seul morceau supposé.

Et la loi est **fidèlement construite, pas encore fidèle** : chaque constante est mesurée, mais
leur **produit** ne l'est pas. Quatre constantes justes peuvent composer une mortalité
d'ensemble fausse. Tant que la mortalité globale de la sandbox n'aura pas été posée à côté de
celle des corpus Arma, la PORTE 0 prouve que le monde **discrimine**, pas qu'il discrimine
**au bon tarif**.
