# CRITERES — TEST DE VALEUR DU CORPUS HORS BANC

Pre-enregistre AVANT le premier pas de gradient. Empreinte prise apres ecriture.

## La question, nommee exactement

On NE teste PAS « le monde vivant aide-t-il ». Le systeme de scenario persistant a ete mesure
inapte sans joueur : 15 entites materialisees, zero tir, zero mort en six minutes sur deux
instances ; il resout tout en virtuel. Il a ete remplace par un generateur d accrochages a variete
controlee (generateur_engagements.sqf v2).

La question testee est donc, dans ces mots et pas d autres :

  LA VARIETE RANDOMISEE HORS BANC AIDE-T-ELLE LE MODELE A PREDIRE LE BANC ?

Une conclusion etiquetee plus large que sa mesure est une dette qu on paie trois semaines plus tard.

## Les deux bras

  A — BANC SEUL   : episodes de nuit0 modee, moins le held-out.
  B — MIXTE       : les memes, plus les fenetres du corpus hors banc, echantillonnage 50/50 PAR
                    MINIBATCH. C est le ratio de melange qui controle la distribution, pas la
                    taille brute des deux corpus sur le disque.

Meme architecture, memes hyperparametres, MEME NOMBRE DE PAS DE GRADIENT. Seules les donnees
different. Trois graines par bras, six entrainements.

## Held-out — jamais vu par aucun des deux bras

Tous les episodes d UNE manoeuvre entiere du banc, identique pour A et B. C est le test de
generalisation inter-manoeuvre : celui qui approche ce que fera une politique qui devie des
professeurs. Le held-out ne sert a rien d autre, jamais.

Sont EXCLUS de tout entrainement : les episodes du monde sans mods (replay/nuit0_sansmods), les
sessions de mise en service (replay/mise_en_service), et les scenarios de la porte.

## Protocole de mesure

Sur chaque episode held-out : fenetres glissantes, amorce 5 s, deroule EN BOUCLE OUVERTE 10 s avec
les actions observees, pas de 5 s. Au moins 150 fenetres au total.

  metrique primaire   : erreur quadratique moyenne de position, en metres, moyennee sur le deroule,
                        sur les entites vivantes a la fin de l amorce ;
  metrique secondaire : score de Brier sur le drapeau « vivant » a la fin du deroule.

Agregation PAR EPISODE : les fenetres d un meme episode sont correlees, elles ne comptent pas comme
independantes.

## Regle de decision, posee avant le premier entrainement

« LE MIXTE GAGNE » si et seulement si les trois conditions tiennent ensemble :

  1. amelioration relative de l erreur moyenne (moyenne des graines) >= 10 % ;
  2. Wilcoxon apparie sur les moyennes par episode, p < 0,05 ;
  3. coherence de signe : sur les neuf paires de graines (3 x 3), au moins huit dans le meme sens.

Une seule des trois qui manque -> « BRUIT », et on le dit tel quel.
Amelioration entre 0 et 10 % avec p significatif -> « gain reel mais trop petit pour payer
l infrastructure ». C est aussi un verdict decidable, et il compte.

## Controle de code, avant de croire quoi que ce soit

Le bac a sable ecrit a la main, condamne le 30/07, sert de BANC D ESSAI du code du modele : c est
un simulateur a donnees illimitees et a dynamique connue. Le modele doit y atteindre une prediction
en boucle ouverte quasi parfaite en une journee. S il n y arrive pas, le code est faux et rien de
ce qui suit ne veut dire quoi que ce soit. Ce controle passe AVANT le test de valeur.

## Empreintes exigees

Chaque entrainement journalise : empreinte du monde des donnees de banc, version et parametres du
generateur pour les donnees hors banc, empreinte de ce fichier, graine, nombre de pas de gradient.
Un entrainement sans ces cinq lignes n est pas comparable et ne compte pas.

## Interdits

- Ne pas regarder le held-out avant que les six entrainements soient finis.
- Ne pas ajuster un hyperparametre entre les deux bras : ce serait comparer deux modeles et non
  deux corpus.
- Ne pas conclure sur le corpus hors banc au-dela de la question nommee en tete de ce fichier.
