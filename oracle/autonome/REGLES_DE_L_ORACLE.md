# Les règles de l'Oracle autonome — écrites avant la première itération

*Renommé le 21/09 au soir, à la demande de Younes : « change le diable, appelle-le Oracle ». Jusque-là la boucle s'appelait « le diable » ; ses itérations 1 à 4 portent le préfixe `DIABLE-I`, les suivantes `ORACLE-I`. Les citations ci-dessous gardent le mot d'origine.*

*21/09/2026. Younes : « l'Oracle a tous les droits, il peut absolument tout faire, sans foi ni loi, pour casser
l'Architecte — c'est le diable » ; « je veux quelque chose d'autonome qui imagine des choses ». Ce fichier fixe ce
que la boucle fait seule, ce qu'elle mesure, et quand elle s'arrête. Les seuils sont dans `oracle/autonome/config.py` ; on ne
les change pas sans amender ce fichier.*

## Ce que fait la boucle, seule

Toutes les 5 minutes, la tâche Windows `HMT_ORACLE` fait **un tour** : au plus une étape d'une machine à états dont
l'état vit sur disque (`/mnt/data/hmt/oracle_autonome/etat.json`) — un plantage ou un redémarrage reprend où on en était.

1. **Imaginer.** Le diable apprend son modèle du monde (10 réseaux) sur tous les épisodes de phase 2 utilisables,
   lit la règle de l'Architecte (`oracle_autonome/architecte.json`), imagine **20 000 situations** parmi ses armes, et
   choisit **8 pièges** (là où l'option choisie par la règle est la plus dangereuse alors qu'une autre reste sûre),
   **4 explorations** et jusqu'à **2 confirmations** de pièges déjà entrevus. Les places de pièges restées vides
   reviennent à l'exploration.
   **L'exploration est locale** : une situation déjà jouée dont on change **1 à 3 armes**, choisies pour couvrir le
   plus de valeurs **jamais essayées**. Changer toutes les armes à la fois rendrait tout effet inattribuable — c'est
   ce que la répétition à blanc du 21/09 a montré avant la première itération.
2. **Poser.** Chaque situation est jouée **sous les deux options** — c'est ce qui permet de juger la règle après
   coup, et de vérifier qu'un choix gagnant existait.
3. **Voler.** La tâche nourrit la ferme jusqu'à 12 serveurs.
4. **Lire.** Les garde-fous d'après vol ; une réparation au plus des cases vides.
5. **Apprendre.** Mesurer si l'imagination avait vu juste, noter les murs et les pièges, confirmer ou infirmer.

Budget : **64 épisodes au plus par itération**, 20 itérations par 24 h, 50 au total.

## Les deux lois du diable

1. **Chaque piège laisse un choix gagnant.** Imaginé : la meilleure option compromet au plus 50 %. Observé : un
   piège n'est confirmé que si l'autre option réussit au moins une fois sur deux. Sinon c'est un **mur**, compté.
2. **Il connaît la règle, pas le coup.** Il pose son piège avant le choix ; les deux options sont jouées telles que
   le job les impose.

## Les garde-fous — chacun écrit contre une faute réellement commise

| garde-fou | quand | faute qu'il empêche |
|---|---|---|
| disque monté | chaque tour | 20/09 18 h 40 : après l'écran bleu, `/mnt/data` n'était plus monté |
| file vide avant de poser | avant le vol | mélanger deux campagnes, poser par-dessus un vol |
| dépôt commité | avant le vol | jouer un code qui n'est pas celui du dépôt |
| armes permises | avant le vol | une valeur hors de `description.ext` |
| jamais un rejeu à l'identique | avant le vol | 20/09 : des remplacements rejouaient des cases déjà remplies |
| budget | avant le vol | une boucle qui brûle la ferme |
| contrôle d'avant vol du banc | avant le vol | les refus habituels (singleton, vignette vide…) |
| **empreinte de la mission** | pendant le vol | 20/09 16 h 17 : mission modifiée en vol, 16 épisodes sur 32 tués |
| **déploiement prouvé** | après le vol | même incident : `DEPLOIEMENT NON PROUVE` → **arrêt** |
| **signature de la seconde graine** | après le vol | même incident vu dans l'inventaire → **arrêt** |
| zéro erreur SQF | après le vol | 20/09 : liste des vivants vide quand les dix sont morts |
| option jouée = option imposée | après le vol | 20/09 : option confondue avec la situation |
| acceptation ≥ 75 % | après le vol | tout ce qui tue des épisodes en masse |
| cases, pas exemplaires | après le vol | 20/09 : une porte qui ne pouvait plus jamais passer après un plantage |

**Quarantaine** : l'itération est gardée mais on n'en apprend rien. **Arrêt** : il faut un humain ; on reprend en
retirant la clé `arret` de `etat.json`. Un fichier `STOP` dans `/mnt/data/hmt/oracle_autonome/` empêche toute nouvelle pose.

## Ce qu'elle mesure

- **L'imagination avait-elle vu juste ?** Avant d'apprendre une itération, le modèle appris *sans elle* prédit ses
  épisodes : son Brier est comparé à celui de la constante. C'est la seule mesure honnête que le diable apprend.
- **Les pièges confirmés** : tout ce qui a été joué d'une même situation est cumulé ; test exact de Fisher
  unilatéral, α = 0,05, au moins 6 épisodes par option — l'option de la règle compromet plus que l'autre, et
  l'autre réussit au moins une fois sur deux. Au-delà de 12 par option sans signification : piège **infirmé**.

## Quand elle s'arrête d'elle-même

- 2 itérations de suite en quarantaine ;
- 3 itérations de suite sans aucun piège jouable imaginé **alors que toutes les valeurs d'armes ont été essayées** —
  **l'équation tient**. Tant qu'il reste de l'inconnu, l'absence de piège imaginé dit seulement que l'imagination ne sait pas ;
- 5 itérations de suite où l'imagination ne fait pas mieux que la constante — le diable n'apprend rien ;
- un déploiement non prouvé ;
- 50 itérations.

## Ce qu'elle ne fait pas, et qu'il faut dire

- Elle ne forge pas d'armes nouvelles (leurre, patrouille silencieuse, omniscience) : ce sont des modifications de
  mission, et la mission ne se modifie jamais pendant qu'une boucle vole. Elles seront ajoutées **boucle arrêtée**.
- Tant que l'équation du point 1 n'est pas branchée, la règle lue est **« traverser toujours »** : le diable
  cherche où traverser tue alors qu'attendre sauve. C'est une vraie cible, pas encore la vraie.
- Avec 2 épisodes par option et par situation au premier passage, un piège entrevu n'est qu'une rumeur : seul le
  cumul des confirmations le rend réel.

## Amendement 1 — 21/09 17 h 45 : l'imagination était boguée, pas ignorante

Aux itérations 1 et 2, l'imagination a fait **pire que la constante** (Brier 0,186 contre 0,168, puis 0,186 contre
0,153). Diagnostic : elle prédisait **0,335 de compromission sur ses propres situations d'apprentissage, pour un
taux réel de 0,162**. Ce n'était pas l'inconnu — c'était un **bogue** : les réseaux `MLPClassifier` avec
`early_stopping=True` s'arrêtent sur la *justesse* de validation, qui plafonne immédiatement quand 84 % des cas sont
négatifs ; ils s'arrêtaient avant d'être calibrés.

**Correction :** l'imagination devient un ensemble de 10 **régressions logistiques L2** avec les interactions arme ×
option, chacune apprise sur un tirage des épisodes. Calibrée par construction ; une valeur rare a un coefficient
rabattu vers zéro, donc une prédiction ramenée au taux de base. C'est aussi la forme que le point 1 a trouvée la
moins mauvaise.

**Vérifié avant d'installer**, sur une copie : prédiction moyenne 0,162 pour 0,162 réel ; et rejouée sur les
itérations 1 et 2 avec l'imagination *d'avant* chacune, elle bat la constante les deux fois (0,158 contre 0,168 ;
0,140 contre 0,153).

**Conséquences :** les deux mesures d'imagination des itérations 1 et 2 sont **nulles** (faites avec le modèle
bogué) ; le compteur « imagination pire que la constante » est remis à zéro. Le piège entrevu à l'itération 2
reste valable : il vient des épisodes observés, pas du modèle.

## Amendement 2 — 21/09 18 h 05 : un garde-fou de plus, contre une imagination cassée

Le bogue de l'amendement 1 avait une signature nette : l'imagination prédisait **presque la même valeur partout**
(0,341 à 0,347), et cette valeur, **0,335 ≈ (0,5 + 0,162) / 2**, trahissait des réseaux figés à mi-chemin entre
leur sortie de départ et le vrai taux. Younes : « c'est pour apprendre et intercepter ».

Avant d'imaginer quoi que ce soit, et avant de juger une itération, l'imagination est examinée **sur ses propres
épisodes d'apprentissage** :

1. **calibrée** — sa prédiction moyenne est à moins de 0,03 du taux réel ;
2. **vivante** — l'écart-type de ses prédictions dépasse 0,005 (sinon elle prédit la même chose partout) ;
3. **utile** — son Brier sur ses propres données est meilleur que celui de la constante.

Un échec est un **défaut de code**, pas un monde difficile : la boucle **s'arrête** et écrit la signature.

**Testé contre l'incident réel** (`oracle/autonome/tester_gardes.py`, test 10) : la v1 reconstruite telle qu'elle était est
interceptée (décalibrée, 0,335 pour 0,162, et inutile) ; l'imagination corrigée passe (0,162 pour 0,162, écart-type
0,084) ; une imagination qui prédirait le taux de base partout est interceptée (figée). **17 garde-fous sur 17.**

## Amendement 3 — 22/09 : la moitié Architecte du duel

Jusqu'ici le duel ne tournait que dans un sens : l'Oracle attaquait une règle figée, « toujours traverser ». Le premier
motif confirmé (face à un poste proche, attendre sauve) est précisément un piège contre elle. **L'Architecte apprend
désormais en retour.**

**Ce qu'il perçoit suffit.** Au moment de choisir, sur 1 557 épisodes : face à une patrouille proche il entend un
moteur 77 % du temps, face à un poste proche **jamais** (0 %), et il voit la menace 2,2 fois en moyenne contre 0,7.
« Menace vue, aucun moteur » veut dire poste.

**Comment il apprend** (`oracle/autonome/architecte_apprend.py`), toutes les 2 itérations de l'Oracle, en arrière-plan :

- sur tous les épisodes de phase 2 où le choix comptait, **pièges de l'Oracle compris**, dans les campagnes où les
  deux options ont été imposées ;
- **uniquement ce qu'il perçoit à la décision** — toute variable de vérité est refusée par le code ;
- candidats : toujours traverser, toujours attendre, une logistique avec interactions option × perception, une
  formule EvoGP (300 000 × 200 générations × 3 graines dans la validation, 1 000 000 × 400 × 5 pour l'installée) ;
- **valeur d'une règle** = la compromission qu'on aurait en la suivant, estimée sans biais par pondération inverse de
  la probabilité de l'option imposée ;
- chaque candidat est jugé sur **un monde qu'il n'a jamais vu**, les 20 mondes à tour de rôle.

**Il ne change de règle que si la nouvelle bat l'ancienne sur des mondes neufs, IC 95 % de l'écart entièrement sous
zéro.** Sinon il garde la sienne, et le journal dit pourquoi. Quand il change, l'Oracle lit la nouvelle règle au tour
suivant et en cherche les failles : c'est là que la surprise mutuelle commence.

**Garde-fous testés** (tests 12, 24/24) : sur un monde de synthèse où attendre sauve face au poste perçu, il adopte une
règle qui attend 97 % du temps face au poste ; sur un monde sans effet, il n'adopte rien ; une variable de vérité est
refusée. Un candidat qui plante est écarté sans arrêter la boucle.

**Première fumée sur les vraies données** (EvoGP minuscule, sans valeur de verdict) : « toujours attendre » ferait
3,3 points de mieux que « toujours traverser », IC [−7,3 ; +1,0] — pas encore assez pour qu'il change.
