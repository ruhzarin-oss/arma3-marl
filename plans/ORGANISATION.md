# Organisation du projet : une seule direction ( 27/09/2026 )

Décision de Younes ( 27/09, 13 h 50 ) : « rassembler le travail fait, s'organiser avec les autres sessions pour avoir une
direction unique ». La session **« Organisation du projet »** fait office de chef de projet : elle tient le tronc,
intègre, tranche, et tient ce fichier à jour.

## Le tronc

- **Une seule branche de référence : `pays-sur-colonnes`** ( dépôt `/mnt/data/hmt/depot-colonnes` ). Au 28/09 elle est certifiée à
  `7b0be18` ( 27 domaines, prix de d03, armée du budget, population grecque, porte unique des devises, portes de la guerre ).
- **Seul le chef de projet écrit dans le tronc**, après `bash portes.sh` = 0 porte refusée ( et `guerre/porte_guerre.py`
  pour ce qui touche la guerre ). Rien n'est poussé sur GitHub sans Younes.
- Chaque session travaille sur **sa** branche et **son** atelier ( un worktree ), partis du tronc. Avant de demander
  l'intégration : fusionner le dernier tronc dans sa branche, résoudre SES conflits, passer `portes.sh`, puis envoyer au
  chef de projet le commit, la liste des portes et ce qui change dans le monde.
- Un travail non commité n'existe pas pour les autres : commiter souvent, sur sa branche.

## Les chantiers et qui les tient ( 28/09 )

| Chantier | Session | Branche | Atelier |
|---|---|---|---|
| Intégration, portes, références ; armée du budget ( d25 ) ; **code à la demande de Qwen** ; d17, d19 et les domaines sans titulaire ; la mesure de la faim des morts ( HMT-136 ) | Organisation du projet | `pays-sur-colonnes` ( tronc ), `qwen-service`, `faim-des-morts` | `atelier-colonnes`, `atelier-qwen`, `atelier-faim` |
| Moteur réaliste et performant : vitesse, colonnes, identité au bit ; **prix de d03** ( plafond, inflation, ancre ) ; **d09** ( offre agricole, `test_temoin_affame`, `test_pays_nourri` ) ; d01 ( décès vectorisés ) ; le pic de faim du jour 17 | Moteur plus réaliste et performant | `moteur-realiste` | `atelier-moteur` ( + `atelier-plafond`, `atelier-deces` ) |
| Le pays réel : ressemblance à la Grèce, population grecque ; **budgets et revenus des ménages** ( HMT-126 b à e : métiers selon les sites de l'île, émigration, épargne, ordre des dépenses ) ; l'inflation mesurée sur 90 jours ; les morts de faim dans `ressemblance.py` | Classes d'un pays simulé | `iles-metiers-emigration`, `menages-revenus` | `atelier-iles-metiers`, `atelier-menages-revenus` |
| La guerre des îles ( Arma, archipel en guerre, conseil de Qwen ) ; **les devises** ( porte unique, priorité ) ; **HMT-126 a)** ( salarié non payé → chômeur → KEA ) ; KEA ; portes G11-G24 | Windows workstation en lab moteur | `guerre-des-iles` | `atelier-guerre` |

## Ce qui est tranché

1. **Le modèle de la faim est celui du tronc** ( `853cecd`, « la faim copiée sur le réel » : adaptation du corps −40 %,
   Keys 1950 ; on travaille jusqu'à une faim de 12 ; un jour nourri répare une ration ; la mort de faim au domaine 1 ). Il
   vaut pour TOUS les mondes et il est dans les références. Le commit `a16fc92` de `guerre-des-iles` en écrivait un
   second ( drapeau `faim_realiste`, seuil 15, récupération d'un quart par jour, sa propre mort de faim au domaine 1 ) :
   la fusion conflictuelle a été annulée ; la session de la guerre reprend ce qu'elle veut de plus SUR le modèle du tronc,
   sans drapeau parallèle.
2. **Le juge du réalisme est l'instrument « ressemble à la Grèce »** ( `monde/ressemblance.py`, 42 indicateurs sourcés,
   `references/grece.json` ). Tout changement « au plus réaliste » dit quels indicateurs il fait entrer dans la bande, et
   n'en fait sortir aucun sans le dire.
3. **Dans le doute, copier le réel** ; une valeur sans source porte « à calibrer » ou « à vérifier ».
4. **Tout est enregistré** ( enregistreur, porte E6 ) ; une nouvelle structure d'état d'un domaine doit y tomber.
5. **Pas de drapeau d'île pour le réalisme** : un drapeau est un second modèle. Autoconsommation, prix, KEA valent pour
   tous les mondes, chacun dans son commit, avec son correctif de référence et le tableau `ressemblance.py` avant/après.
6. **La réparation de la faim reste « un jour nourri répare 1 ration »** : la réhabilitation du Minnesota ( Keys 1950 )
   rend une partie de la force après 12 semaines, l'essentiel après ~20 ; la guerre mesure G20 sur ce modèle et rapporte.
7. **Une faute, un seul titulaire** : les prix de d03 ont été diagnostiqués par trois sessions le même jour ; ils sont à
   la session du moteur, la guerre lui passe son code et ses mesures de Stratis.

8. **Qwen coder est toujours actif** ( Younes, 27/09 ) : `qwen3.8:27b` reste chargé dans Ollama en permanence
   ( keep_alive −1, ~17 Go de la 3090 ) ; la garde `/mnt/data/hmt/qwen/garde_qwen.sh` le recharge toutes les 5 minutes s'il
   disparaît ( journal `garde.log` ). Aucune session ne le décharge ni ne prend la carte graphique pour autre chose sans
   prévenir le chef de projet. Chaque run long et chaque nuit branche les gouvernements écrits par Qwen
   ( `--gouvernement` ), et le service de code à la demande ( `plans/plan-code-a-la-demande.md` ) dès qu'il existe.

9. **Une porte qui juge la faim, la pauvreté ou la santé compte les MORTS** ( 27-28/09 ). Les indicateurs ne comptaient
   que les vivants : Malden a perdu 99 % de sa population pendant que la faim « baissait », et trois portes ont passé
   grâce aux morts. Un ménage éteint par la faim compte affamé ( `monde.repas`, `T.faim`, HMT-136 ) ; le rapport d'un run
   donne les morts de faim avant tout autre chiffre ; une guerre s'arrête d'elle-même au-delà de 0,5 % de morts de faim.
10. **Une seule porte de sortie des devises** ( `d07.payer_en_devises`, HMT-131 ) : aucun paiement à l'étranger ne
    contourne le contrôle des changes ; quand les réserves manquent, nourriture et médicaments d'abord ; l'armement n'est
    pas essentiel par défaut ( choix à valider par Younes, HMT-132 ).
11. **Un critère réglé après avoir vu la mesure se juge sur des graines NEUVES** ( KEA : −34 % sur les graines vues,
    −21,6 % sur les neuves, porte refusée ). Un amendement qui rend une porte plus sévère n'en a pas besoin.
12. **Un contrôle positif doit savoir échouer** : une porte dont le contrôle ne fait jamais échouer le critère n'est pas
    une porte ( G24 ).


## Les règles techniques

- Un domaine n'écrit JAMAIS dans une constante ou un tableau d'un autre module : les six îles de l'archipel séquentiel
  partagent le processus ( fuite de `d14` sur `EC.PART_BIEN`, 27/09 ).
- Un nouveau métier s'AJOUTE à la fin de `config.ROLES` : le code d'un métier est son rang, écrit dans les tables et les
  instantanés.
- Un changement du comportement des 14 domaines d'origine passe aussi dans `references/correctifs/` et
  `refaire_references.sh` ; les références se refont, jamais à la main.
- **Seul le chef de projet réécrit les références partagées** de `/mnt/data/hmt` ( `ref_domaines*.json`,
  `ref/monde_ancien` ), depuis un commit du tronc. Une branche qui change le comportement se teste avec `HMT_REF` pointé
  sur un dossier à elle.
- `portes.sh` n'affiche que les 8 dernières lignes d'une porte refusée : lire la sortie complète avant de conclure.
- Messages de commit en français, avec « Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com> ».
- **Charge de la station** : au plus DEUX gros calculs à la fois, toutes sessions confondues ( `portes.sh`, guerre dans
  Arma, run long ), chacun annoncé au chef de projet. La station est tombée le 27/09 à 21 h 59 sous pleine charge.
  Un calcul MONO-CŒUR ( une mesure, une graine ) ne compte pas dans les deux, s'il l'est vraiment : dans tout pool ou
  toute campagne de processus, `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1` ( sans cela, numpy prend
  tous les cœurs dans chaque processus ) ; l'archipel borne déjà ses îles ( `HMT_FILS_PAR_ILE` ).
- **Un run long s'arrête seul sur la famine** : `monde.nuit --garde-famine 0.005` ( arrêt propre et instantané quand
  les morts de faim d'une île atteignent 0,5 % de ses vivants ). La « faim » affichée ne compte que les vivants : elle
  baisse quand les affamés meurent ( essais 19 et 21 ).
- **La station ne se met jamais en veille** : au réveil, le pilote NVIDIA ne répond plus avec Qwen chargé ( 28/09,
  01 h 19 → 10 h 31 ). Le réglage est à Younes.
- `portes.sh` écrit dans des fichiers PRIVÉS ( `mktemp` ) ; les tests dont l'issue suit le bruit vont dans
  `references/tests_fragiles_pays.txt` ( ignorés dans les deux sens, rapportés à part, chacun est une dette HMT-127 ),
  jamais dans `echecs_attendus_pays.txt`. Un test FAUX ( qui certifie des morts ) n'y va pas : il se corrige.
- Les portes de la guerre ( `guerre/porte_guerre.py` ) et des devises sont dans `portes.sh` ( 28/09 ).
- Lancer un calcul détaché sur la WS : `setsid nohup bash script > /dev/null 2>&1 < /dev/null &` ( sans `< /dev/null`, il
  meurt avec la session ssh ).
- Qwen : tâche Windows `HMT_QWEN` ( garde root sous `flock`, au démarrage puis toutes les 10 min ) ; elle relance Ollama
  si Qwen est chargé hors de la carte graphique. Pour libérer la 3090 : prévenir le chef de projet et désactiver la tâche.


## En cours ( tenu par le chef de projet, 28/09 )

Le détail vit dans Plane, module « Pays simulé — une seule direction » ( HMT-89 à HMT-137 ).

- **Intégrer** la livraison du moteur ( rupture, plafond, lissage et ancre des prix, décès vectorisés ) quand son
  `portes.sh` passe ; puis `faim-des-morts` ( HMT-136 ), `qwen-service` ( code à la demande branché par défaut dans la
  nuit, HMT-101/102 ), `924b8b5` de la guerre ( reprise des îles d'avant les devises ).
- **La guerre est arrêtée** ( essai22n, 562 morts de faim à Malden au jour 110, revenu fantôme ) jusqu'à HMT-126 a).
- **Le run long** de Younes ( 100 000 habitants par île, mode grec, tout enregistré, Qwen branché ) attend HMT-126 a) et
  la mesure des morts de faim : sans elles, il referait l'essai 21.
