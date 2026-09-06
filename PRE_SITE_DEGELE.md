# PRE-INSCRIPTION — BARREAU DU SITE DEGELE (B0@30 sur sites tires)
02/09/2026, 13:10. Ecrite APRES le dimensionnement des temoins, AVANT toute mesure d'agent.

## La question du barreau
La politique certifiee a B0@30 a-t-elle appris a NAVIGUER, ou a-t-elle memorise CE site ?
Deux hypotheses distinctes, deux predictions distinctes. La doctrine scriptee navigue par
construction ; l'agent peut etre un memorisateur. C'est la configuration ou plafond-temoin
et plancher-agent se separent.

## Une seule variable change
D reste a 30 m, le barreau reste "B0" (pas d'adversaire). SEUL LE SITE varie.
Changer aussi la distance rendrait un echec inattribuable.

## Le bassin, et comment il a ete borne
Prospection 41x41 a 55 m, 36 azimuts (la resolution de la recherche qui avait produit le
site gele) : 6473 candidats.
  · BANDE DE DIFFICULTE : score >= 1,00 -> 270. Le site gele score 1,32 et tombe DANS la
    bande. Tirer dans tout le bassin (median -1,18) aurait fait varier DEUX choses :
    l'identite du site ET la difficulte. Un echec y serait inattribuable.
  · TRAJET SEC : hauteur du sol >= 0,5 m sur les 30 m -> 268 (2 ecartes).
    ⚠️ Ces 2 sites la sont ceux ou la doctrine ratait (2/51). Diagnostic mesure :
    objectif sous 60-70 cm d'eau, soldat immobile (dfin=30 m, vivant, budget epuise).
    Le MEME site reussissait 4/4 ailleurs : avec un jitter de ±1,2 m et ±6°, l'objectif
    tombe tantot dans des hauts-fonds passables a gue, tantot au-dela du seuil ou le
    pathfinding refuse. On borne donc sur la POSSIBILITE, jamais sur la difficulte : un
    site dur penalise une mauvaise politique plus qu'une bonne (signal) ; un site dont
    l'issue tient a l'humeur du moteur penalise tout le monde pareil (bruit d'instrument).
  · GARDE AUTOUR DU SITE GELE : 200 m -> 252. Un site a 55 m dans le meme azimut, c'est
    le meme terrain sous un autre nom.
  · DECOUPE : graine de tirage DEDIEE 313131, disjointe des graines de mission.
    126 sites de jugement, 126 d'apprentissage, intersection nulle.

## Les temoins, mesures sur le bassin propre
    DOCTRINE  : 153/153 = 100,0 %   IC95 [97,6 ; 100,0]
    ALEATOIRE :   6/51  =  11,8 %   IC95 [ 5,5 ;  23,4]
Bandes exigees avant toute lecture : DOCTRINE >= 97,6 % · ALEATOIRE dans [5,5 ; 23,4].

## LA PORTE — et un defaut de la regle, corrige ici
    PORTE = 93,0 %   ·   5 series de 51   ·   4 series sur 5 exigees

⚠️ LA REGLE HISTORIQUE DEGENERE ET ON LA REMPLACE. « Borne basse de Wilson de la
doctrine » donne 93,0 % a n=51 (51/51) mais 97,6 % a n=153 (153/153) : mesurer le temoin
plus finement rendrait la porte plus dure pour l'agent, et a la limite exigerait la
perfection. La regle confondait l'incertitude sur le TEMOIN avec la marge accordee a
l'AGENT. Nouvelle regle, non degeneree :
    PORTE = estimation ponctuelle de la doctrine  -  MARGE DE NON-INFERIORITE de 7 points
Contre une doctrine a 100,0 % : 93,0 %. C'est EXACTEMENT la porte des deux barreaux
certifies (B0@30 et B0@60) : la marge de 7 points n'est pas inventee pour l'occasion,
c'est celle que la pratique du projet a employee deux fois. Elle ne bouge plus avec n.

## L'ORDRE DES LECTURES EST CONTRAIGNANT
**LECTURE 1 — SONDE DE VACANCE, avant tout entrainement.**
La politique CERTIFIEE a B0@30, gelee, echantillonnee, sans gradient, sur les 126 sites
de JUGEMENT. Les deux graines torch.
  · elle franchit la porte  -> BARREAU VACANT. On n'entraine rien. On cite
    « la politique navigue, elle n'avait pas memorise son site », et on monte d'un cran.
  · elle echoue             -> barreau vivant, l'entrainement a quelque chose a apprendre.

⚠️ AVEU OBLIGATOIRE : la mission a change (SHA ce66bf9cfd4654da -> b0c6c4b4e57205fc) pour
que le site voyage dans le ticket. Le jugement est donc un TRANSFERT assume : `--transfert`
imprime les deux SHA, et toute citation doit porter cette phrase. Controle de
non-regression deja passe : la doctrine refait 51/51 sur le site GELE avec le nouveau SHA.

**LECTURE 2, seulement si la sonde echoue** — entrainement sur les 126 sites
d'APPRENTISSAGE (jamais ceux de jugement), deux graines, avec regle d'arret a issue
uniforme, puis temoins et porte.

## La regle des deux graines
Si les deux graines divergent, on ne cite NI l'une NI l'autre.

## Ce qui rendrait la mesure nulle, decide d'avance
  · un temoin hors bande
  · plus de 5 % de rejets sur une serie
  · un site de jugement apparaissant dans le lot d'apprentissage
