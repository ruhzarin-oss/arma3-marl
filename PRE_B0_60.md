# PRE-INSCRIPTION — BARREAU B0@60, 01/09/2026 23:15
Ecrite APRES le dimensionnement des temoins, AVANT le premier episode d'entrainement.

## Les temoins, mesures ce soir a 60 m (jamais recopies de B0@30)
    DOCTRINE  : 51/51 = 100,0 %   IC95 Wilson [93,0 ; 100,0]   (835 s, 0 rejet)
    ALEATOIRE :  4/51 =   7,8 %   IC95 Wilson [ 3,1 ;  18,5]   (1653 s, 0 rejet)

Mesures EN PARALLELE, doctrine sur l'instance 1, aleatoire sur l'instance 0 — premier
usage reel de la parallelisation certifiee ce soir.

⚠️ L'aleatoire tombe de 13,7 % (30 m) a 7,8 % (60 m). La tache est bien plus dure, mais
il RESTE du gradient : ~1 succes sur 13. Une recompense terminale a donc de quoi mordre.
J'avais craint le contraire sur un 0/10 initial ; c'etait un petit echantillon, pas un mur.

## Bandes de temoins exigees avant toute lecture (controle 4)
    DOCTRINE  dans [93,0 ; 100,0]
    ALEATOIRE dans [ 3,1 ;  18,5]
Un seul temoin hors bande -> la nuit est NULLE, aucun chiffre d'entrainement n'est lu.

## La porte
    B0@60 >= 93,0 %   ·   5 series de 51   ·   4 series sur 5 exigees
    graines de mission NEUVES (777000+serie, disjointes du 90210+graine d'entrainement)
    mode ECHANTILLONNE, jamais argmax   ·   aucun gradient   ·   SHA du monde verifie
93,0 % = borne basse de Wilson de la doctrine mesuree CE SOIR a 60 m. Non-inferiorite :
on ne demande pas de battre la doctrine, on demande de la rejoindre.

## Le protocole d'entrainement
    2000 episodes, maj toutes les 24, lr 3e-4, beta 0,01, decodeur echantillonne
    DEUX graines torch (0 et 1), UNE PAR INSTANCE, en parallele
    REPRISE depuis le point certifie de B0@30 (ckpt_b0/pt_001992.pt, graine 0)

⚠️ POURQUOI LA REPRISE, ET CE QU'ELLE NOUS INTERDIT DE DIRE. L'echelle fait le pari que
les barreaux se composent : chaque barreau part du precedent. C'est ce pari qu'on teste.
MAIS si B0@60 passe, ce banc NE DIRA PAS si la reprise a servi — il se peut que 60 m soit
simplement aussi facile que 30 m. L'ablation « depuis zero » n'est pas jouee cette nuit.
Elle est DUE, elle est nommee ici, et aucun texte ne devra dire « la reprise a aide »
tant qu'elle n'aura pas ete jouee.

## La regle des deux graines
Si les deux graines divergent, on ne cite NI l'une NI l'autre : recette instable.
Elle a tenu a B0@30 (5/5 des deux cotes) ; elle ne se presume pas ici.

## Ce qui rendrait la nuit nulle, decide d'avance
  · un temoin hors bande
  · plus de 5 % de rejets « void » sur un run (a B0@30 : 1 sur 2000)
  · SHA de mission discordant entre les deux instances
