# Les règles du diable — écrites avant la première itération

*21/09/2026. Younes : « l'Oracle a tous les droits, il peut absolument tout faire, sans foi ni loi, pour casser
l'Architecte — c'est le diable » ; « je veux quelque chose d'autonome qui imagine des choses ». Ce fichier fixe ce
que la boucle fait seule, ce qu'elle mesure, et quand elle s'arrête. Les seuils sont dans `diable/config.py` ; on ne
les change pas sans amender ce fichier.*

## Ce que fait la boucle, seule

Toutes les 5 minutes, la tâche Windows `HMT_DIABLE` fait **un tour** : au plus une étape d'une machine à états dont
l'état vit sur disque (`/mnt/data/hmt/diable/etat.json`) — un plantage ou un redémarrage reprend où on en était.

1. **Imaginer.** Le diable apprend son modèle du monde (10 réseaux) sur tous les épisodes de phase 2 utilisables,
   lit la règle de l'Architecte (`diable/architecte.json`), imagine **20 000 situations** parmi ses armes, et
   choisit **8 pièges** (là où l'option choisie par la règle est la plus dangereuse alors qu'une autre reste sûre),
   **4 explorations** (là où il ne connaît rien) et jusqu'à **2 confirmations** de pièges déjà entrevus.
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
retirant la clé `arret` de `etat.json`. Un fichier `STOP` dans `/mnt/data/hmt/diable/` empêche toute nouvelle pose.

## Ce qu'elle mesure

- **L'imagination avait-elle vu juste ?** Avant d'apprendre une itération, le modèle appris *sans elle* prédit ses
  épisodes : son Brier est comparé à celui de la constante. C'est la seule mesure honnête que le diable apprend.
- **Les pièges confirmés** : tout ce qui a été joué d'une même situation est cumulé ; test exact de Fisher
  unilatéral, α = 0,05, au moins 6 épisodes par option — l'option de la règle compromet plus que l'autre, et
  l'autre réussit au moins une fois sur deux. Au-delà de 12 par option sans signification : piège **infirmé**.

## Quand elle s'arrête d'elle-même

- 2 itérations de suite en quarantaine ;
- 3 itérations de suite sans aucun piège jouable imaginé — **l'équation tient** ;
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
