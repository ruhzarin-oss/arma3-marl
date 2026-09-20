# ETAT — 2026-09-19 23:44

Journal, detail des verdicts, historique des runs : le wiki de Plane — http://localhost:8080 (tunnel `ssh -f -N ws`) > espace travaux > projet HMT > Pages. Pages generees, ne pas les editer.

Un agent peut-il apprendre, dans Arma et sans doctrine scriptee, a ne pas se faire tuer
tout en atteignant son but ? Etage 1 : le trieur (CHACAL, corpus d'imitation). Toute
tache qui ne remonte pas a cette phrase sort du projet ou va en attente.

## Machine

- dernier boot : 2026-09-15T15:42:36+02:00 ok=True  conteneurs=20 ;
- GPU : 613 MiB, 24576 MiB, 0 %
- /mnt/data : 2.5T libres sur 3.6T
- serveurs Arma : 6 · residus : aucun

## File

- en cours : 2026-09-19_OP2_n0_t1_s1_g6g7.json, 2026-09-19_OP2_n0_t1_s2_g4g5.json, 2026-09-19_OP2_n0_t2_s3_g6g7.json, 2026-09-19_OP2_n1_t1_s1_g4g5.json, 2026-09-19_OP2_n1_t1_s1_g8g9.json, 2026-09-19_OP2_n1_t1_s2_g11g12.json, 2026-09-19_OP2_n1_t2_s1_g8g9.json
- en attente : 2026-09-19_OP2_n0_t1_s1_g11g12.json

## Debit du mois 2026-09

- runs aboutis : 939 / 1020

## Portes ouvertes

- **Comparaison appariee natif contre politique, banc repare** — aucune-revendication.md
- **En vignette d'assaut, le feu de l'appui avant le premier pas fait passer l'assaut de 2 a 5 reussites sur 10 — tendance, pas encore etablie** — feu-avant-vignette.md
- **Le flanc paie-t-il, sous quelle courbe de letalite** — flanc-degele.md
- **A 20 hommes contre 5, l'issue n'est pas jugeable : le compteur d'exfiltration s'arrete a 6** — vingt-hommes-compteur-plafonne.md

## Verdicts vivants

| porte | date | graines | chiffre | verdict | depend de | fichier |
|---|---|---|---|---|---|---|
| La correction terrain (positions accessibles depuis le depart) ne change pas l'issue au palier 4 | 2026-09-10 | 7, 8, deux repetitions chacune par bras | accessible 0 : 2 succes sur 4 (graine 7 : 1/2, graine 8 : 1/2) ; accessible 1 : 2 succes sur 4 (graine 7 : 0/2, graine 8 : 2/2) ; la prediction — debloquer la graine 7 — donne 0 sur 2 AVEC la correction et 1 sur 2 SANS | ECHEC | palier4-gagne-une-fois-sur-deux, plancher-de-bruit-mission-complete | accessible-sans-effet-palier4.md |
| Choix du decodeur, fige contre echantillonne | 2026-08-24 | 0, 1 | fige de 3,3 a 51,1 % selon la graine ; en hesitant de 31,5 a 42,3 % | PASSE | recette-gymnase-loterie | agent-hesite.md |
| ALIZE, controle positif HMT-39 : le reflexe se declenche chez 63 % des hommes touches, et la moitie d entre eux sont touches par le PREMIER coup d un engagement - aucun signal reactif ne peut les prevenir | 2026-09-11 | 7, 8, dix vignettes d'assaut chacune (banc alize1, palier 4, de nuit) | 41 hommes touches sur 200 ; 27 tues du premier impact ; reflexe AVANT le vol de la balle qui touche (dernier pas < tc - 1 s) chez 26 sur 41 (63,4 %, critere 90 %, echec sous 50 %) ; avance mediane 3,1 s ; 21 touches sur 41 sans aucun coup ennemi dans les 10 s avant (hors la balle qui touche) ; pour les 20 autres, delai entre le debut de la rafale et le coup : mediane 3,7 s (quartiles 2,1 et 6,4) ; canal BRUIT reconstruit hors d Arma (590 coups ennemis joints a 100 %, ecart median 0,4 m) : 63,4 % a toutes les portees, avance 3,8 s au mieux | ECHEC | sirocco-immunite-tactique, alize-algo-propre, tout-ce-qui-fige-coute | alize-reflexe-trop-tard.md |
| ? | ? | ? | ? | ? |  | alize6-signal-existe-mais-chez-l-ennemi.md |
| Angle mort et cout de se montrer, quatre bancs Arma | 2026-08-03 | n/a | 18/18 repere dans le cone, 0/26 hors du cone ; tirer plafonne a 1,50 quand se montrer donne 4,00 | PASSE | knowsabout-de-camp | angle-mort.md |
| Arc de tir d'Arma, latence de riposte par angle | 2026-07-28 | n/a | riposte a 0,0 s a 0 deg contre 3,5 a 4,1 s a 90-180 deg ; taux de riposte 100 % partout | PASSE |  | arc-tir-sursis.md |
| Reproductibilite du banc CHACAL, six pieges Arma | 2026-09-03 | 1 | meme graine et meme build rendent deux routes opposees ; 4163 s reels pour une phase budgetee a 1800 s | ECHEC |  | arma-pieges.md |
| ? | ? | ? | ? | ? |  | attendre-la-patrouille-ne-sert-a-rien.md |
| ? | ? | ? | ? | ? |  | aucun-algorithme-d-equation-retenu-evogp-seul-trouve-les-trois-formes.md |
| ? | ? | ? | ? | ? |  | audit-banc-neuf-fautes-sur-vingt-quatre.md |
| ? | ? | ? | ? | ? |  | azimut-ne-porte-pas-et-le-bruit-commande.md |
| Barreau B0@60, transfert zero-shot | 2026-09-02 | 0, 1 | 251/255 = 98,4 % et 251/254 = 98,8 %, sans un episode d'entrainement a 60 m | VIDE | b0-30 | b0-60-vide.md |
| Coupe du banc live selon la presence d'un defenseur vivant | 2026-08-22 | n/a | 26 episodes du natif et 31 de la politique sans aucun defenseur ; natif 26/26 en monde vide, politique 18/31 | ECHEC |  | banc-quart-sans-adversaire.md |
| ? | ? | ? | ? | ? |  | cahier-des-charges-banc-a-decisions.md |
| Controle d'instrument du canal ennemi, avant le barreau adverse | 2026-09-03 | 1 | 4 champs sur 5 allumes ; 118 coups sur 20 episodes en B1 contre 0 en B0 | PASSE | site-degele | canal-ennemi.md |
| CHACAL palier 0, BRAS TEMOIN : marcher droit sur l'objectif ne le prend pas | 2026-09-08 | 5, 6 | 2 episodes ACCEPTES, 15 portes vertes sur 15 ; g5 ABANDON ARTICULATION_ROMPUE (103 min, 10 vivants, 0 charge) ; g6 ABANDON COMPROMIS_LOIN (52 min, 6 morts en 15 s par un MRAP a mitrailleuse lourde) ; 0 charge posee sur 3 dans les deux cas | PASSE | chacal-portes, lanceur-hmt-temoin | chacal-bras-temoin-palier0.md |
| CHACAL palier 0, premiers episodes : hors corpus, DEPART=3 trainait | 2026-09-07 | 3, 4 | g3 ECHEC EXFIL_MANQUEE (2333 s) ; g4 ABANDON ARTICULATION_ROMPUE (367 s, detachement detruit par la HMG en 86 s) | VIDE | chacal-portes, lanceur-hmt-temoin | chacal-palier0-premiers-episodes.md |
| CHACAL, 9 portes du lecteur d'episode | 2026-09-03 | n/a | 6 phases, 203 min par episode, 9 portes d'acceptation, 716 k etats d'unite a 1 Hz | PASSE | arma-pieges | chacal-portes.md |
| Controle positif spatial du modele du monde | 2026-08-27 | n/a | prix(vers l'ennemi) - prix(a l'oppose) = +0,00000, part positive 50,5 % sur 16 797 cas | ECHEC |  | champ-spatial.md |
| La compromission est la charniere : huit episodes avec ennemis, zero charge ; quatre sans ennemi, douze charges | 2026-09-09 | 5, 6, 7, 8 | 8 episodes du bras PLAN au palier 0 : 8 compromissions, 0 charge posee sur 24 ; 4 episodes au palier 9 (monde vide) : 0 compromission, 12 charges sur 12 et 4 SUCCES | PASSE | chacal-portes, monde-fixe-episode-libre | compromission-charniere.md |
| ? | ? | ? | ? | ? |  | cone-60-degres-refute.md |
| ? | ? | ? | ? | ? |  | contre-une-patrouille-on-traverse-contre-un-poste-on-attend.md |
| Courbe de toucher, niveau et forme, nuit N1 | 2026-09-04 | n/a | rapport a l'ancienne courbe x0,75 a 25 m et x1,91 a 150 m ; replication 0,402 contre 0,383 a 100 m | ECHEC |  | courbe-2607.md |
| Courbe de toucher remesuree a HitPart, instrument reproductible | 2026-09-04 | 2 repetitions independantes de la meme condition | 18 conditions, ~17 000 balles ; 100 m debout 0,402 IC95 [0,371 ; 0,435] n=902, puis 0,383 IC95 [0,335 ; 0,434] n=368 | PASSE | courbe-2607 | courbe-toucher-hitpart.md |
| Degat par impact re-derive sur l'acte de mort | 2026-09-04 | n/a | 0,175 par impact ; mediane 4,0 impacts jusqu'a la neutralisation, n=83 ; l'ancien 0,233 venait d'un capteur qui sur-comptait | PASSE | courbe-toucher-hitpart | degat-par-impact.md |
| ? | ? | ? | ? | ? |  | delai-porteur-le-mecanisme-tient-pas-le-resultat.md |
| Un UAV d'Arma renseigne-t-il l'IA | 2026-08-16 | 1 | knowsAbout = 0 sur 4 montages, y compris cloue a 148 m au-dessus de la cible pendant 60 s | ECHEC | knowsabout-de-camp | drone-arma-rien.md |
| Sonde 3 du corpus Battle Lines, mortalite selon le champ de vision ennemi | 2026-08-03 | n/a | mortalite 7,44 % a 0-20 % d'ennemis qui vous voient contre 13,00 % a 80-100 %, soit +75 % | PASSE | knowsabout-de-camp | etre-vu-tue-2x.md |
| Fidelite du monde assemble, contraste vu contre non vu | 2026-08-11 | n/a | etre vu multiplie la mortalite de +856 % dans la sandbox contre +75 % certifies sur Arma | ECHEC | etre-vu-tue-2x, sandbox-letalite-4x | fidelite-arma-couvert-11x.md |
| ? | ? | ? | ? | ? |  | file-par-instance-08-09.md |
| Greffe du prix sur une politique figee, marge attribuable | 2026-08-25 | 6 graines de jugement jamais vues | temoin 39,3 %, greffe 61,6 % ; +8,8 pts dus au decodeur, marge attribuable au prix +15,3 pts | PASSE | politique-est-navigateur | greffe-credit.md |
| ? | ? | ? | ? | ? |  | gymnase-de-decisions-predit-l-ecart-pas-le-niveau.md |
| ? | ? | ? | ? | ? |  | historique-08-au-13-septembre.md |
| Infrastructure de mesure : sentinelle de pont, harnais de banc, deploiement SQF depuis git | 2026-09-04 | n/a | trois outils en service ; une panne trouvee et non reparee : la couche bronze du lac est un lien mort | PASSE |  | infra-sentinelle-harnais.md |
| Controle positif de la connaissance dans Arma | 2026-08-02 | 1 | knowsAbout 4,00 avec un camarade qui voit, 0,00 seul ; 0,00 a 50 m de flanc contre 2,00 a 300 m de face | PASSE |  | knowsabout-de-camp.md |
| ? | ? | ? | ? | ? |  | l-allure-du-repli-rapide-tend-a-mieux-exfiltrer-sans-dependre-de-la-menace.md |
| ? | ? | ? | ? | ? |  | la-connaissance-de-nuit-porte-a-150-m-et-arrive-en-6-secondes.md |
| ? | ? | ? | ? | ? |  | la-couture-est-ouverte.md |
| ? | ? | ? | ? | ? |  | la-porte-nest-pas-une-decision.md |
| ? | ? | ? | ? | ? |  | la-situation-pese-sur-cinq-phases-la-phase-4-est-vide.md |
| Lanceur HMT : un job dans queue/ produit un FIN.json sans session ssh | 2026-09-07 | 3, 4 | 2 runs COMPLET (4733 s puis 2793 s), 4 episodes CHACAL, 4 serveurs lances et arretes par PID, 0 session ssh ouverte | PASSE | chacal-portes | lanceur-hmt-temoin.md |
| ? | ? | ? | ? | ? |  | le-chercheur-de-causes-n-est-pas-encore-cru.md |
| ? | ? | ? | ? | ? |  | le-delai-du-porteur-domine-sans-inversion.md |
| ? | ? | ? | ? | ? |  | le-detour-aveugle-est-domine-par-le-direct.md |
| ? | ? | ? | ? | ? |  | le-porteur-narrive-pas-et-personne-ne-le-remplace.md |
| ? | ? | ? | ? | ? |  | le-script-ne-choisit-pas-son-ouverture.md |
| Forme de la loi auditive de CWR validee sur Arma | 2026-09-03 | 12 episodes valides sur 12, six geometries | audSide(d) = min(2177/d2 ; 1,35), jamais 1,5, nulle au-dela de 100 m ; 1/d2 predit 1,78, mesure 1,79 ; constante a.d2 = 2160 / 2196 / 2176, soit 0,9 % d'ecart | PASSE | loi-cwr, knowsabout-de-camp | loi-auditive-forme.md |
| Loi couvert-tir lue dans la source CWR, confrontee a Arma 3 | 2026-09-03 | n/a | porte 0,63 refutee (237 impacts sur victime vivante, 29,5 % sous le seuil) ; exposant du couvert 0,72 au lieu de 2 ; ouie plafonnee a 1,35 en 1/d2 | PASSE | arc-tir-sursis, etre-vu-tue-2x | loi-cwr.md |
| Mecanisme de la memorisation, cap absolu | 2026-09-03 | 0, 1 | cap 315 dans 50,0 % des echecs contre 13,2 % des reussites ; 96,9 % a moins de 90 deg contre 84,9 % au-dela | PASSE | site-memorise | memorisation-cap-absolu.md |
| Le monde fixe ne fixe pas l'episode : deux runs identiques, deux histoires opposees | 2026-09-09 | 7 et 8, deux fois chacune | meme configuration et memes graines, run 1415 contre run 2255 : ECHEC/CHARGES_INCOMPLETES contre ABANDON/COMPROMIS_LOIN sur les DEUX graines ; compromission a 5155 s contre 1419 s sur la graine 7 ; 6 et 14 ennemis neutralises contre 0 et 0 ; 5 et 7 survivants contre 9 et 8 | PASSE | chacal-portes, lanceur-hmt-temoin | monde-fixe-episode-libre.md |
| ? | ? | ? | ? | ? |  | moteur-portee-optique-et-position-de-tir.md |
| ? | ? | ? | ? | ? |  | observer-8-minutes-domine-et-paie-davantage-sous-menace-a-la-limite.md |
| L oracle a l assaut ne fait pas gagner : savoir ou sont les defenseurs pendant l assaut pose les 3 charges 8 fois sur 18, contre 4 sur 12 sans | 2026-09-11 | 7, 8, trois repetitions chacune par job ; 3 jobs oracle (instances 1, 3, 5), 2 jobs reference (2, 4), joues en meme temps | oracle 8/18 (44 %) contre reference 4/12 (33 %), memes graines, meme charge, meme heure ; critere ecrit avant : reussite >= 15/18, echec <= 9/18 -> ECHEC ; ecart non significatif (Fisher unilateral ~0,4) | ECHEC | controle-positif-reveal-certifie, feu-avant-vignette, alize-reflexe-trop-tard | oracle-savoir-a-l-assaut.md |
| Au palier 4, la mission gagne de bout en bout une fois sur deux, et quand elle perd, ce n'est plus un massacre | 2026-09-10 | 7, 8, deux repetitions chacune, deux bras (accessible 0 et 1) | 4 SUCCES sur 8 episodes acceptes (IC95 Wilson 22 a 78 %) ; survivants des succes 10, 8, 10, 9 ; les 4 echecs sont TOUS CHARGES_INCOMPLETES avec 6 a 10 vivants (0 ou 2 charges sur 3) ; compromission 8 fois sur 8 ; 0 abandon | PASSE | plan-de-positions-sans-plan-de-feu, plancher-de-bruit-mission-complete | palier4-gagne-une-fois-sur-deux.md |
| Critere du placeur, praticabilite ou direction | 2026-08-19 | n/a | 11-15 m en montee contre 22-26 m en descente ; 0 acte sur 188 finissant au sol n'atteint le seuil de 23 m | PASSE |  | pente-sens-marche.md |
| ? | ? | ? | ? | ? |  | phase3-porte-hors-datteinte.md |
| Le PLAN contre son TEMOIN au palier 0 : le plan combat, aucun des deux ne pose de charge | 2026-09-08 | plan 7 et 8 ; temoin 5 et 6 | ennemis neutralises 6 et 14 (plan) contre 0 et 0 (temoin) ; charges posees 0 sur 3 dans les quatre episodes ; survivants BLUFOR 5 et 7 (plan) contre 10 et 4 (temoin) ; 4 episodes ACCEPTES, 15 portes vertes sur 15 | PASSE | chacal-portes, chacal-bras-temoin-palier0, lanceur-hmt-temoin | plan-contre-temoin-palier0.md |
| Un plan de positions sans plan de feu : UN defenseur tue cinq assaillants, le detachement tire UNE balle | 2026-09-09 | 8, palier 4 | l'unite adverse 3 tire 36 coups entre 4959 et 4997 s et signe LES CINQ morts (CHEF, ADJOINT, DEMO_1, DEMO_2, MEDECIN) ; le detachement de dix hommes tire UN seul coup sur tout l'episode, a 4996,57 s, une demi-seconde avant la mort de son tireur ; l'element d'appui, deux hommes en position, tire ZERO | PASSE | chacal-portes, etre-vu-tue-2x, angle-mort | plan-de-positions-sans-plan-de-feu.md |
| Plancher de bruit de la mission complete : a monde ET configuration fixes, l'issue va de 0 a 5 survivants | 2026-09-09 | 7, huit repetitions | 8 episodes acceptes, meme configuration et meme graine — survivants 5, 4, 5, 5, 0, 5, 3, 2 (de 0 a 5 sur 10, moyenne 3,6) ; QUATRE causes de fin differentes : ARTICULATION_ROMPUE, CHARGES_INCOMPLETES, COMPROMIS_LOIN, DETACHEMENT_DETRUIT ; durees de 4590 a 8899 s, soit un facteur 1,9 | PASSE | monde-fixe-episode-libre, chacal-portes | plancher-de-bruit-mission-complete.md |
| Candidat A, la politique lit-elle la pente | 2026-08-22 | 101, 102, 103 | ecart intact contre brouille = 0,7 pt (seuil pre-inscrit 3,0) ; controle positif jusqu'a -20,1 pts | PASSE |  | politique-est-navigateur.md |
| ? | ? | ? | ? | ? |  | qdax-trouve-l-aiguille-botorch-par-defaut-fait-pire-que-le-hasard.md |
| Controle positif de la liaison drone par reveal | 2026-08-16 | 1 | bras B 20/20 ont tire, mediane 3,2 s ; bras A0 sans reveal 2/20, mediane 17,8 s | PASSE | drone-arma-rien | reveal-certifie.md |
| ? | ? | ? | ? | ? |  | roe-le-moteur-ne-percoit-pas-les-civils.md |
| Letalite de la sandbox, cible unique par defenseur | 2026-07-28 | n/a | frontal 22,2 % -> 80,8 % avec selection de cible ; avantage du flanc x1,82 -> x0,82 | ECHEC |  | sandbox-letalite-4x.md |
| ? | ? | ? | ? | ? |  | se-terrer-a-l-insertion-ne-rend-pas-plus-discret.md |
| Barreau site degele, apres entrainement sur sites disjoints | 2026-09-02 | 0, 1 | 90,9 % -> 98,4 % (graine 0) et 82,0 % -> 98,4 % (graine 1), amelioration attribuable +7,5 pts | PASSE | site-memorise, memorisation-cap-absolu | site-degele.md |
| Sonde de vacance du barreau site degele | 2026-09-02 | 0, 1 | 90,9 % (231/254) et 82,0 % (209/255) sur 126 sites jamais vus, porte a 93,0 %, 1/5 series | ECHEC | b0-30 | site-memorise.md |
| Le SOCLE seul fait passer l assaut de 1 a 10 reussites sur 10 : la moitie des echecs etaient des pannes d execution, pas de tactique | 2026-09-12 | 7, 8, cinq repetitions chacune par bras, tous joues la meme nuit sur 7 instances, meme charge | socle seul 10/10 a 3 charges sur 3 contre 1/10 pour le script d origine (Fisher unilateral p = 0,0001) ; pertes 1,3 contre 2,5 hommes par episode ; 56 relances du chien de garde ; les tactiques POSEES SUR le socle font moins bien : neutralisation prealable 12/20, base de feu 11/20, infiltration 2/10 | PASSE | socle-posable-monde-vide, alize-reflexe-trop-tard, plan-de-positions-sans-plan-de-feu | socle-execution-10-sur-10.md |
| Les trois charges sont POSABLES : 20 episodes sur 20 a 3 sur 3 en monde vide, tour comprise | 2026-09-12 | 7, 8, dix vignettes chacune (palier 9, monde vide) | 20/20 episodes a 3 charges sur 3, aucune charge manquee, aucune cause ELEMENT_N_ARRIVE_PAS ni PORTEUR_N_ARRIVE_PAS | PASSE | chacal-portes | socle-posable-monde-vide.md |
| Dose-reponse d'immobilite au gymnase | 2026-08-26 | 301 a 306, jamais vues | doctrine scriptee 91,0 % contre 35,0 % pour la meilleure du depot ; pauses de 1, 2, 4 pas : -17,8 / -26,6 / -38,6 | PASSE | sandbox-letalite-4x | tout-ce-qui-fige-coute.md |
| Banc live 20 episodes, transfert gymnase vers Arma | 2026-08-15 | n/a | prise 0/20 = 0,0 % sur Arma contre 59,4 % au gymnase ; 9/20 tous morts, 11/20 sans prendre | ECHEC | boucle-fermee | transfert-non-etabli.md |
| ? | ? | ? | ? | ? |  | un-levier-ecrit-nest-pas-un-levier-lu.md |
| ? | ? | ? | ? | ? |  | une-graine-n-est-pas-un-monde.md |
| Quatre valeurs de configuration lues directement sur Arma 3 | 2026-09-03 | n/a | rayon 1,688 m ; sensitivity 6,0 ; sensitivityEar 0,125 ; audible 0,05 ; indirectHitRange 0,0 | PASSE | loi-auditive-forme | valeurs-configfile-arma.md |
| ? | ? | ? | ? | ? |  | victoire-bout-en-bout-47-pourcent.md |
| La vignette d'assaut DISCRIMINE, replique sur deux mondes : la mitrailleuse servie interdit la pose | 2026-09-09 | 7 et 9, cinq repetitions par niveau | AVEC une piece servie, 0 charge posee sur 8 episodes acceptes (graines 7 et 9 confondues), 5 survivants aux 8. SANS piece, une charge au moins dans 6 episodes sur 9 : graine 7 -> 2,3,2,1 (moyenne 2,0/3, survivants 7,7,7,5) ; graine 9 -> 0,3,2,0,0 (moyenne 1,0/3, survivants 5,6,8,5,5). Duree d'un episode 92 a 859 s, contre ~55 min pour une mission complete | PASSE | chacal-portes, monde-fixe-episode-libre, compromission-charniere | vignette-discrimine-mitrailleuse.md |
| ? | ? | ? | ? | ? |  | vingt-minutes-d-attente-ne-se-paient-pas-de-facon-mesurable.md |

## Remplaces

- Barreau B0@30, non-inferiorite a la doctrine (b0-30.md) → remplace par site-memorise
- Etape 4, un agent apprend et bat les doctrines ecrites a la main (boucle-fermee.md) → remplace par transfert-non-etabli
- Niveau de reference de l'IA native d'Arma (natif-59-6.md) → remplace par aucune-revendication
- Reproductibilite de la recette du gymnase sur deux graines torch (recette-gymnase-loterie.md) → remplace par agent-hesite

## Derniers runs

| run | banc | etat du run | verdicts du banc | duree s |
|---|---|---|---|---|
| 2026-09-19_234038_chacaloracle_i3 | chacaloracle | EN COURS |  |  |
| 2026-09-19_233834_chacaloracle_i1 | chacaloracle | EN COURS |  |  |
| 2026-09-19_233731_chacaloracle_i7 | chacaloracle | EN COURS |  |  |
| 2026-09-19_233051_chacaloracle_i11 | chacaloracle | COMPLET | g8:ACCEPTE g9:ACCEPTE | 813 |
| 2026-09-19_232948_chacaloracle_i8 | chacaloracle | COMPLET | g6:ACCEPTE g7:ACCEPTE | 671 |
| 2026-09-19_232438_chacaloracle_i5 | chacaloracle | EN COURS |  |  |
| 2026-09-19_232034_chacaloracle_i13 | chacaloracle | COMPLET | g4:ACCEPTE g5:ACCEPTE | 1348 |
| 2026-09-19_231900_chacaloracle_i10 | chacaloracle | COMPLET | g11:ACCEPTE g12:ACCEPTE | 1347 |
| 2026-09-19_231755_chacaloracle_i6 | chacaloracle | COMPLET | g11:ACCEPTE g12:ACCEPTE | 1512 |
| 2026-09-19_231606_chacaloracle_i12 | chacaloracle | EN COURS |  |  |
| 2026-09-19_231448_chacaloracle_i4 | chacaloracle | EN COURS |  |  |
| 2026-09-19_230705_chacaloracle_i3 | chacaloracle | COMPLET | g11:ACCEPTE g12:ACCEPTE | 1963 |
| 2026-09-19_230542_chacaloracle_i2 | chacaloracle | COMPLET | g6:ACCEPTE g7:ACCEPTE | 2126 |
| 2026-09-19_230326_chacaloracle_i11 | chacaloracle | COMPLET | g11:ACCEPTE g12:ACCEPTE | 1594 |
| 2026-09-19_230051_chacaloracle_i7 | chacaloracle | COMPLET | g6:ACCEPTE g7:ACCEPTE | 2147 |
