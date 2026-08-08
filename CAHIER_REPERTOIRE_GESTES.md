# LE RÉPERTOIRE DE GESTES — cahier des charges

*7 août 2026. Déposé avant toute production. Aucun geste n'est encore scripté.*

**Fiches relues ⟨règle 10⟩** : `angle-mort-certifie-arma`, `arc-tir-sursis-mesure`,
`etre-vu-tue-deux-fois-plus`, `courbe1-toucher-mesuree`, `bounding-overwatch`,
`detection-en-cascade-part-hommes-vus`, `posture-couche-est-observation`,
`shamal-imitation-rl`, `formations-catalog-foundation`, `flanc-fait-arriver-pas-proteger`,
`knowsabout-est-de-camp-pas-de-soldat`, `cahier-des-charges-etage1-trieur`.

## Le diagnostic qui fonde ce document

> **Younes, 07/08 : « Notre agent manque de connaissance, manque de profondeur. »**

Et les mesures le confirment. Le mur n'a jamais été la perception — la fiche est explicite :
*« le mur n'est PAS la représentation de la perception, c'est la learnability »*. Cinq graines
sur la mission qui force le couvert : **78 %, 0, 0, 0, 0**. Quatre agents sur cinq ne trouvent
jamais la solution.

Parce qu'on leur demande de **réinventer seuls le métier de fantassin**, avec sept nombres et
une récompense, en quelques centaines d'épisodes. Un vrai fantassin arrive avec des années de
gammes.

**Et le dossier sait déjà comment on donne un métier** : SHAMAL a **imité** un professeur, puis
appris — et il a **battu son professeur 3 fois sur 3** sur des cas jamais vus. C'est la seule
méthode du dossier qui ait produit un agent meilleur que ce qu'on savait coder à la main.

## La règle du répertoire

Chaque geste porte trois choses, et **aucun ne se produit sans les trois** :

1. **le FAIT CERTIFIÉ qu'il exploite** — pas une intuition militaire, une mesure du dossier ;
2. **le PROFESSEUR scripté** — déterministe, reproductible, sans apprentissage ;
3. **sa PORTE** — le geste doit battre son témoin, sur la grandeur nommée, au-delà d'une taille
   déclarée avant.

> **Un geste dont le professeur ne bat pas son témoin ne s'enseigne pas.** On ne fait pas
> imiter une doctrine qui ne paie pas — c'est le premier filtre, et il est gratuit.

## LES DIX GESTES

| # | geste | le fait certifié qu'il exploite | le témoin qu'il doit battre |
|---|---|---|---|
| 1 | **Bond par binôme** — l'un progresse, l'autre couvre | bounding overwatch perce **96 % / 91 %** face à 12 gardes | progression simultanée des deux |
| 2 | **Appui-feu / suppression** — arroser pour figer | sous le feu il reste **8 %** de la capacité de nuire | assaut sans appui |
| 3 | **Prise de couvert sous le feu** — s'arrêter derrière un masque | toucher **75 % → 26 %** de 25 à 200 m ; le couvert coupe la vue | continuer à découvert |
| 4 | **Tenue d'angle** — rester hors du demi-cône | **18/18** détectés dans le cône, **0/26** hors | trajet ignorant l'orientation |
| 5 | **Débordement par le mort** — entrer par le dos | le cône ne pivote pas, il **s'ouvre en 4 s** | assaut frontal |
| 6 | **Décrochage sous le feu** — rompre le contact | être vu tue **2× plus fort**, effet **croissant** avec la distance | tenir la position |
| 7 | **Franchissement de découvert** — traverser vite, au bon moment | le sursis de **4 s** avant que l'arc ne s'ouvre | traverser sans timing |
| 8 | **Réaction à l'embuscade** — trancher assaut ou repli, vite | on découvre le danger **en mourant**, et on meurt près | délai de décision |
| 9 | **Observation couchée à longue distance** | couché **invisible au-delà de 120 m**, mais vitesse ÷3,6 | couché en progression ⟨l'erreur corrigée le 05/08⟩ |
| 10 | **Dispersion à l'approche** — ne pas offrir le groupe | part d'hommes vus : **31/60 contre 51/60** selon la densité | approche groupée |

## Les portes, et leur taille

**Taille commune, dérivée et non posée** : les effets comportementaux certifiés du dossier
vivent vers **15-17 points** (le flanc : +17,3 puis +15,0). ⟨Fable, 07/08⟩ *« la porte doit
savoir lire 5 points — le tiers du plus petit effet certifié ; en dessous, même vrai, l'effet
ne changerait le rang d'aucun levier. »*

> **Chaque geste doit battre son témoin d'au moins 5 points**, sur la grandeur qui lui est
> propre, avec l'effectif qui sait lire 5 points — de l'ordre de **800 accrochages par bras**,
> à recalculer exactement avant chaque dépôt.

**Contrôles obligatoires, les mêmes pour tous :**
- **PORTE 0 du banc** : deux doctrines d'ordre connu doivent s'y séparer, **au point de
  fonctionnement du jugement**, dans la bande 20-80 % ⟨la règle de l'aiguille au butoir⟩ ;
- **bras contemporains**, même nuit, empreinte du monde vérifiée ;
- **journal de santé** — groupes par camp, compteur monotone du pont ;
- **filtre de santé** au dépouillement, avec le nombre de rejets dit à voix haute.

## Ce qui se passe ensuite — le protocole SHAMAL, sans retouche

1. Les gestes qui **passent leur porte** deviennent des professeurs.
2. L'élève **imite** — apprentissage supervisé sur leurs trajectoires.
3. Puis **RL ancré**, et le verdict est celui qui a déjà marché :
   **l'élève doit battre son professeur sur des accrochages jamais vus.**

> Ce n'est pas une liste de jeux de données à télécharger. **C'est un corpus à produire**, et
> c'est le seul dont le dossier ait démontré qu'il injecte du savoir dans un agent.

## Ce qui la ferait échouer — écrit maintenant

- **Un geste dont le professeur ne bat pas son témoin** : il ne s'enseigne pas, on le retire du
  répertoire et on le dit.
- **Aucun geste ne passe sa porte** : alors ce ne sont pas les gestes qui manquent, et le
  diagnostic « manque de savoir-faire » est faux — il faudra chercher ailleurs.
- **L'élève imite bien mais ne dépasse jamais son professeur** : l'imitation aura plafonné, et
  c'est le RL ou la tâche qu'il faudra regarder — pas ajouter un onzième geste.

## Ce que ce cahier ne dit pas

Combien de nuits il coûte. La répétition générale du 07/08 donne les chiffres du pont — boot
34 s, FPS 44-48, zéro panne sur 25 min — mais **pas le débit du banc de gestes**, qui n'existe
pas. Chaque geste se dimensionne à sa répétition générale, comme le reste.
