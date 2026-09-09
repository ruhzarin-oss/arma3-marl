# ETAT — 2026-09-09 02:14

Journal, detail des verdicts, historique des runs : le wiki de Plane — http://localhost:8080 (tunnel `ssh -f -N ws`) > espace travaux > projet HMT > Pages. Pages generees, ne pas les editer.

Un agent peut-il apprendre, dans Arma et sans doctrine scriptee, a ne pas se faire tuer
tout en atteignant son but ? Etage 1 : le trieur (CHACAL, corpus d'imitation). Toute
tache qui ne remonte pas a cette phrase sort du projet ou va en attente.

## Machine

- dernier boot : 2026-09-07T11:23:14+02:00 ok=True  pile harmattan non relevee ;
- GPU : 719 MiB, 24576 MiB, 0 %
- /mnt/data : 2.6T libres sur 3.6T
- serveurs Arma : 3 · residus : aucun

## File

- en cours : 2026-09-09_D2_tenir.json, 2026-09-09_N1_plancher_i2.json, 2026-09-09_N2_plancher_i3.json
- en attente : 2026-09-09_V0_essai_vignette.json

## Debit du mois 2026-09

- runs aboutis : 17 / 25

## Portes ouvertes

- **Comparaison appariee natif contre politique, banc repare** — aucune-revendication.md
- **Le flanc paie-t-il, sous quelle courbe de letalite** — flanc-degele.md

## Verdicts vivants

| porte | date | graines | chiffre | verdict | depend de | fichier |
|---|---|---|---|---|---|---|
| Choix du decodeur, fige contre echantillonne | 2026-08-24 | 0, 1 | fige de 3,3 a 51,1 % selon la graine ; en hesitant de 31,5 a 42,3 % | PASSE | recette-gymnase-loterie | agent-hesite.md |
| Angle mort et cout de se montrer, quatre bancs Arma | 2026-08-03 | n/a | 18/18 repere dans le cone, 0/26 hors du cone ; tirer plafonne a 1,50 quand se montrer donne 4,00 | PASSE | knowsabout-de-camp | angle-mort.md |
| Arc de tir d'Arma, latence de riposte par angle | 2026-07-28 | n/a | riposte a 0,0 s a 0 deg contre 3,5 a 4,1 s a 90-180 deg ; taux de riposte 100 % partout | PASSE |  | arc-tir-sursis.md |
| Reproductibilite du banc CHACAL, six pieges Arma | 2026-09-03 | 1 | meme graine et meme build rendent deux routes opposees ; 4163 s reels pour une phase budgetee a 1800 s | ECHEC |  | arma-pieges.md |
| Barreau B0@60, transfert zero-shot | 2026-09-02 | 0, 1 | 251/255 = 98,4 % et 251/254 = 98,8 %, sans un episode d'entrainement a 60 m | VIDE | b0-30 | b0-60-vide.md |
| Coupe du banc live selon la presence d'un defenseur vivant | 2026-08-22 | n/a | 26 episodes du natif et 31 de la politique sans aucun defenseur ; natif 26/26 en monde vide, politique 18/31 | ECHEC |  | banc-quart-sans-adversaire.md |
| Controle d'instrument du canal ennemi, avant le barreau adverse | 2026-09-03 | 1 | 4 champs sur 5 allumes ; 118 coups sur 20 episodes en B1 contre 0 en B0 | PASSE | site-degele | canal-ennemi.md |
| CHACAL palier 0, BRAS TEMOIN : marcher droit sur l'objectif ne le prend pas | 2026-09-08 | 5, 6 | 2 episodes ACCEPTES, 15 portes vertes sur 15 ; g5 ABANDON ARTICULATION_ROMPUE (103 min, 10 vivants, 0 charge) ; g6 ABANDON COMPROMIS_LOIN (52 min, 6 morts en 15 s par un MRAP a mitrailleuse lourde) ; 0 charge posee sur 3 dans les deux cas | PASSE | chacal-portes, lanceur-hmt-temoin | chacal-bras-temoin-palier0.md |
| CHACAL palier 0, premiers episodes : hors corpus, DEPART=3 trainait | 2026-09-07 | 3, 4 | g3 ECHEC EXFIL_MANQUEE (2333 s) ; g4 ABANDON ARTICULATION_ROMPUE (367 s, detachement detruit par la HMG en 86 s) | VIDE | chacal-portes, lanceur-hmt-temoin | chacal-palier0-premiers-episodes.md |
| CHACAL, 9 portes du lecteur d'episode | 2026-09-03 | n/a | 6 phases, 203 min par episode, 9 portes d'acceptation, 716 k etats d'unite a 1 Hz | PASSE | arma-pieges | chacal-portes.md |
| Controle positif spatial du modele du monde | 2026-08-27 | n/a | prix(vers l'ennemi) - prix(a l'oppose) = +0,00000, part positive 50,5 % sur 16 797 cas | ECHEC |  | champ-spatial.md |
| La compromission est la charniere : huit episodes avec ennemis, zero charge ; quatre sans ennemi, douze charges | 2026-09-09 | 5, 6, 7, 8 | 8 episodes du bras PLAN au palier 0 : 8 compromissions, 0 charge posee sur 24 ; 4 episodes au palier 9 (monde vide) : 0 compromission, 12 charges sur 12 et 4 SUCCES | PASSE | chacal-portes, monde-fixe-episode-libre | compromission-charniere.md |
| Courbe de toucher, niveau et forme, nuit N1 | 2026-09-04 | n/a | rapport a l'ancienne courbe x0,75 a 25 m et x1,91 a 150 m ; replication 0,402 contre 0,383 a 100 m | ECHEC |  | courbe-2607.md |
| Courbe de toucher remesuree a HitPart, instrument reproductible | 2026-09-04 | 2 repetitions independantes de la meme condition | 18 conditions, ~17 000 balles ; 100 m debout 0,402 IC95 [0,371 ; 0,435] n=902, puis 0,383 IC95 [0,335 ; 0,434] n=368 | PASSE | courbe-2607 | courbe-toucher-hitpart.md |
| Degat par impact re-derive sur l'acte de mort | 2026-09-04 | n/a | 0,175 par impact ; mediane 4,0 impacts jusqu'a la neutralisation, n=83 ; l'ancien 0,233 venait d'un capteur qui sur-comptait | PASSE | courbe-toucher-hitpart | degat-par-impact.md |
| Un UAV d'Arma renseigne-t-il l'IA | 2026-08-16 | 1 | knowsAbout = 0 sur 4 montages, y compris cloue a 148 m au-dessus de la cible pendant 60 s | ECHEC | knowsabout-de-camp | drone-arma-rien.md |
| Sonde 3 du corpus Battle Lines, mortalite selon le champ de vision ennemi | 2026-08-03 | n/a | mortalite 7,44 % a 0-20 % d'ennemis qui vous voient contre 13,00 % a 80-100 %, soit +75 % | PASSE | knowsabout-de-camp | etre-vu-tue-2x.md |
| Fidelite du monde assemble, contraste vu contre non vu | 2026-08-11 | n/a | etre vu multiplie la mortalite de +856 % dans la sandbox contre +75 % certifies sur Arma | ECHEC | etre-vu-tue-2x, sandbox-letalite-4x | fidelite-arma-couvert-11x.md |
| ? | ? | ? | ? | ? |  | file-par-instance-08-09.md |
| Greffe du prix sur une politique figee, marge attribuable | 2026-08-25 | 6 graines de jugement jamais vues | temoin 39,3 %, greffe 61,6 % ; +8,8 pts dus au decodeur, marge attribuable au prix +15,3 pts | PASSE | politique-est-navigateur | greffe-credit.md |
| Infrastructure de mesure : sentinelle de pont, harnais de banc, deploiement SQF depuis git | 2026-09-04 | n/a | trois outils en service ; une panne trouvee et non reparee : la couche bronze du lac est un lien mort | PASSE |  | infra-sentinelle-harnais.md |
| Controle positif de la connaissance dans Arma | 2026-08-02 | 1 | knowsAbout 4,00 avec un camarade qui voit, 0,00 seul ; 0,00 a 50 m de flanc contre 2,00 a 300 m de face | PASSE |  | knowsabout-de-camp.md |
| Lanceur HMT : un job dans queue/ produit un FIN.json sans session ssh | 2026-09-07 | 3, 4 | 2 runs COMPLET (4733 s puis 2793 s), 4 episodes CHACAL, 4 serveurs lances et arretes par PID, 0 session ssh ouverte | PASSE | chacal-portes | lanceur-hmt-temoin.md |
| Forme de la loi auditive de CWR validee sur Arma | 2026-09-03 | 12 episodes valides sur 12, six geometries | audSide(d) = min(2177/d2 ; 1,35), jamais 1,5, nulle au-dela de 100 m ; 1/d2 predit 1,78, mesure 1,79 ; constante a.d2 = 2160 / 2196 / 2176, soit 0,9 % d'ecart | PASSE | loi-cwr, knowsabout-de-camp | loi-auditive-forme.md |
| Loi couvert-tir lue dans la source CWR, confrontee a Arma 3 | 2026-09-03 | n/a | porte 0,63 refutee (237 impacts sur victime vivante, 29,5 % sous le seuil) ; exposant du couvert 0,72 au lieu de 2 ; ouie plafonnee a 1,35 en 1/d2 | PASSE | arc-tir-sursis, etre-vu-tue-2x | loi-cwr.md |
| Mecanisme de la memorisation, cap absolu | 2026-09-03 | 0, 1 | cap 315 dans 50,0 % des echecs contre 13,2 % des reussites ; 96,9 % a moins de 90 deg contre 84,9 % au-dela | PASSE | site-memorise | memorisation-cap-absolu.md |
| Le monde fixe ne fixe pas l'episode : deux runs identiques, deux histoires opposees | 2026-09-09 | 7 et 8, deux fois chacune | meme configuration et memes graines, run 1415 contre run 2255 : ECHEC/CHARGES_INCOMPLETES contre ABANDON/COMPROMIS_LOIN sur les DEUX graines ; compromission a 5155 s contre 1419 s sur la graine 7 ; 6 et 14 ennemis neutralises contre 0 et 0 ; 5 et 7 survivants contre 9 et 8 | PASSE | chacal-portes, lanceur-hmt-temoin | monde-fixe-episode-libre.md |
| Critere du placeur, praticabilite ou direction | 2026-08-19 | n/a | 11-15 m en montee contre 22-26 m en descente ; 0 acte sur 188 finissant au sol n'atteint le seuil de 23 m | PASSE |  | pente-sens-marche.md |
| Le PLAN contre son TEMOIN au palier 0 : le plan combat, aucun des deux ne pose de charge | 2026-09-08 | plan 7 et 8 ; temoin 5 et 6 | ennemis neutralises 6 et 14 (plan) contre 0 et 0 (temoin) ; charges posees 0 sur 3 dans les quatre episodes ; survivants BLUFOR 5 et 7 (plan) contre 10 et 4 (temoin) ; 4 episodes ACCEPTES, 15 portes vertes sur 15 | PASSE | chacal-portes, chacal-bras-temoin-palier0, lanceur-hmt-temoin | plan-contre-temoin-palier0.md |
| Candidat A, la politique lit-elle la pente | 2026-08-22 | 101, 102, 103 | ecart intact contre brouille = 0,7 pt (seuil pre-inscrit 3,0) ; controle positif jusqu'a -20,1 pts | PASSE |  | politique-est-navigateur.md |
| Controle positif de la liaison drone par reveal | 2026-08-16 | 1 | bras B 20/20 ont tire, mediane 3,2 s ; bras A0 sans reveal 2/20, mediane 17,8 s | PASSE | drone-arma-rien | reveal-certifie.md |
| Letalite de la sandbox, cible unique par defenseur | 2026-07-28 | n/a | frontal 22,2 % -> 80,8 % avec selection de cible ; avantage du flanc x1,82 -> x0,82 | ECHEC |  | sandbox-letalite-4x.md |
| Barreau site degele, apres entrainement sur sites disjoints | 2026-09-02 | 0, 1 | 90,9 % -> 98,4 % (graine 0) et 82,0 % -> 98,4 % (graine 1), amelioration attribuable +7,5 pts | PASSE | site-memorise, memorisation-cap-absolu | site-degele.md |
| Sonde de vacance du barreau site degele | 2026-09-02 | 0, 1 | 90,9 % (231/254) et 82,0 % (209/255) sur 126 sites jamais vus, porte a 93,0 %, 1/5 series | ECHEC | b0-30 | site-memorise.md |
| Dose-reponse d'immobilite au gymnase | 2026-08-26 | 301 a 306, jamais vues | doctrine scriptee 91,0 % contre 35,0 % pour la meilleure du depot ; pauses de 1, 2, 4 pas : -17,8 / -26,6 / -38,6 | PASSE | sandbox-letalite-4x | tout-ce-qui-fige-coute.md |
| Banc live 20 episodes, transfert gymnase vers Arma | 2026-08-15 | n/a | prise 0/20 = 0,0 % sur Arma contre 59,4 % au gymnase ; 9/20 tous morts, 11/20 sans prendre | ECHEC | boucle-fermee | transfert-non-etabli.md |
| Quatre valeurs de configuration lues directement sur Arma 3 | 2026-09-03 | n/a | rayon 1,688 m ; sensitivity 6,0 ; sensitivityEar 0,125 ; audible 0,05 ; indirectHitRange 0,0 | PASSE | loi-auditive-forme | valeurs-configfile-arma.md |

## Remplaces

- Barreau B0@30, non-inferiorite a la doctrine (b0-30.md) → remplace par site-memorise
- Etape 4, un agent apprend et bat les doctrines ecrites a la main (boucle-fermee.md) → remplace par transfert-non-etabli
- Niveau de reference de l'IA native d'Arma (natif-59-6.md) → remplace par aucune-revendication
- Reproductibilite de la recette du gymnase sur deux graines torch (recette-gymnase-loterie.md) → remplace par agent-hesite

## Derniers runs

| run | banc | etat du run | verdicts du banc | duree s |
|---|---|---|---|---|
| 2026-09-09_0214_factice | factice | COMPLET | g7:ACCEPTE g8:ACCEPTE | 40 |
| 2026-09-09_0213_factice | factice | COMPLET | g7:ACCEPTE g8:ACCEPTE | 41 |
| 2026-09-09_0209_factice | factice | COMPLET | g7:ACCEPTE g8:ACCEPTE | 40 |
| 2026-09-09_0155_chacal | chacal | EN COURS |  |  |
| 2026-09-09_0146_chacal | chacal | EN COURS |  |  |
| 2026-09-09_0106_porte0 | porte0 | COMPLET | g1:REFUSE g2:REFUSE | 2623 |
| 2026-09-09_0016_porte0 | porte0 | COMPLET | g1:REFUSE g2:REFUSE | 2399 |
| 2026-09-08_2255_chacal | chacal | COMPLET | g7:ACCEPTE g8:ACCEPTE | 6639 |
| 2026-09-08_2235_chacal | chacal | EN COURS |  |  |
| 2026-09-08_2225_chacal | chacal | COMPLET | g7:ACCEPTE g8:ACCEPTE | 6497 |
| 2026-09-08_2202_essai_vignette | chacal | SANS FIN.json |  |  |
| 2026-09-08_2155_essai_vignette | chacal | SANS FIN.json |  |  |
| 2026-09-08_2149_chacal | chacal | INTERROMPU |  |  |
| 2026-09-08_2137_chacal | chacal | INTERROMPU | g7:REFUSE |  |
| 2026-09-08_2126_porte0 | porte0 | COMPLET | g1:REFUSE g2:REFUSE | 4948 |
