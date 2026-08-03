# CRITERES — AUDIT DE CONTAMINATION DU CORPUS OUVERT

Pre-enregistre AVANT toute capture persistante. Empreinte prise apres ecriture.

## Ce que l audit tranche

Le monde persistant VIRTUALISE les entites lointaines : elles n existent plus comme objets. Le
risque est de capturer de l abstraction en croyant capturer de la physique — le mode d echec qui
nous a coute des mois. L audit mesure combien le corpus est contamine. Il ne repare rien.

Un taux sans denominateur explicite est INFALSIFIABLE. Chaque ligne porte le sien.

| quantite | numerateur | denominateur | seuil |
|---|---|---|---|
| fantomes | references entite-tick dont l identifiant n a AUCUN evenement d apparition | total des references entite-tick | < 1 % |
| morts_non_tracees | morts sans impact sur la victime dans [t-5 s ; t] | total des morts | < 1 % |
| tireurs_intracables | impacts dont le tireur vaut -1 | total des impacts | < 1 % |
| teleportation | paires de ticks consecutifs d une meme entite a vitesse horizontale > PLAFOND | total des paires consecutives | < 1 % |
| tirs_sans_projectile | tirs dont le projectile est nul | total des tirs | < 1 % |
| couverture | ticks ou l ecart entre le compte annonce et le nombre d entites listees depasse 1 % | total des ticks | < 1 % |
| horloge | ecarts de temps hors de [0,8 ; 1,2] x nominal | total des ecarts | < 1 % |

PLAFOND de teleportation = 60 m/s en horizontal. Ce n est pas un reglage : c est une
impossibilite physique pour tout ce qui roule ou marche sur cette carte. La distribution complete
des vitesses est RAPPORTEE a cote, avec le p99,9, et le taux au-dela de 15 m/s est rapporte
separement comme indicateur (un fantassin ne depasse pas ~7 m/s).

## Empreinte du monde — condition d entree

Toute session porte l empreinte sha256 de sa ligne de mods. L audit REFUSE de fusionner ou de
comparer des sessions d empreintes differentes. Motif : le 30/07 la ferme a tourne sans aucun mod
pendant que l instance de mesure tournait avec le jeu complet, et l accord zero contre zero a ete
pris pour un accord. Deux mondes differents peuvent echouer tous les deux.

## Les trois controles qui rendent l audit lui-meme digne de confiance

Notre mode d echec recurrent est de mesurer notre instrumentation en croyant mesurer le monde.

1. CONTROLE NUL — doit sortir a EXACTEMENT ZERO.
   Un corpus synthetique PROPRE, ecrit par nous : trois entites en ligne droite a vitesse
   raisonnable, un tir avec projectile, un impact, une mort correctement chainee, aucun trou
   d horloge, aucune disparition. Les sept taux doivent valoir 0. Un seul non nul et l audit est
   cable de travers : tout ce qu il dira du vrai corpus est nul.

2. CANARI — doit etre compte EXACTEMENT.
   Sur l instance de developpement : une entite isolee, un deplacement delibere de +500 m en un
   pas, puis une suppression. L audit doit compter exactement une teleportation et une disparition
   de plus que le corpus temoin. Un autre compte signifie que les filets ont des trous.

3. FAUSSETE DU CHAINAGE — doit s effondrer.
   On decale tous les horodatages d impact de +300 s et on recalcule le taux de morts tracees.
   Il doit tomber sous 5 %. S il reste haut, la fenetre de 5 s apparie par hasard et le critere
   « mort tracee » ne veut rien dire. C est le garde-fou contre un seuil qu un comportement
   degenere traverse.

## Interdits

- Ne rien corriger dans le monde a partir de l audit : il constate, il ne repare pas.
- Ne pas blanchir les morts par explosion ou par chute : elles comptent comme non tracees. On
  mesure d abord.
- Ne pas ajuster le PLAFOND pour faire passer un taux.
