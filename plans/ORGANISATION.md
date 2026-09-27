# Organisation du projet : une seule direction ( 27/09/2026 )

Décision de Younes ( 27/09, 13 h 50 ) : « rassembler le travail fait, s'organiser avec les autres sessions pour avoir une
direction unique ». La session **« Organisation du projet »** fait office de chef de projet : elle tient le tronc,
intègre, tranche, et tient ce fichier à jour.

## Le tronc

- **Une seule branche de référence : `pays-sur-colonnes`** ( dépôt `/mnt/data/hmt/depot-colonnes` ). Au 27/09 13 h 50 elle
  avance jusqu'à `ca0765b` ( `pays-reel-porte` ), qui contient la fusion des 27 domaines, `moteur-realiste` /
  `moteur-perf`, `pays-reel-pop` et la guerre des îles jusqu'à G19.
- **Seul le chef de projet écrit dans le tronc**, après `bash portes.sh` = 0 porte refusée ( et `guerre/porte_guerre.py`
  pour ce qui touche la guerre ). Rien n'est poussé sur GitHub sans Younes.
- Chaque session travaille sur **sa** branche et **son** atelier ( un worktree ), partis du tronc. Avant de demander
  l'intégration : fusionner le dernier tronc dans sa branche, résoudre SES conflits, passer `portes.sh`, puis envoyer au
  chef de projet le commit, la liste des portes et ce qui change dans le monde.
- Un travail non commité n'existe pas pour les autres : commiter souvent, sur sa branche.

## Les chantiers et qui les tient

| Chantier | Session | Branche | Atelier |
|---|---|---|---|
| Intégration, portes, références, **armée du budget** ( loi de programmation militaire, domaine 25 ) | Organisation du projet | `pays-sur-colonnes` ( tronc ), `armee-budget` | `/mnt/data/hmt/atelier-colonnes` |
| Moteur réaliste et performant : vitesse, colonnes, identité au bit ; **la correction des prix de d03** ( couverture mesurée avant les courses, ancrage de coût de la nourriture, demande de carburant des stations ) | Moteur plus réaliste et performant | `moteur-realiste` ( `moteur-perf` y est fusionnée ) | `/mnt/data/hmt/atelier-moteur` |
| Le pays réel : ressemblance à la Grèce ( l'instrument, terminé : `ca0765b` ), population grecque à la naissance ( mode `demographie="grece"` ) | Classes d'un pays simulé | `pays-reel-pop` ( en cours ), `pays-reel-porte` ( terminée ) | `/mnt/data/hmt/atelier-reel-pop`, `/mnt/data/hmt/atelier-reel-porte` |
| La guerre des îles ( Arma, archipel en guerre, conseil de guerre ) ; l'autoconsommation des familles paysannes ( d09 ), le revenu minimum KEA ( d06 ), G18-G22 | Windows workstation en lab moteur | `guerre-des-iles` | `/mnt/data/hmt/atelier-guerre` |

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

## En cours ( tenu par le chef de projet )

- Certifier `ca0765b` ( `portes.sh` complet ), puis y avancer `pays-sur-colonnes`.
- `guerre-des-iles` : `a16fc92` + 6 fichiers non commités, à rebaser sur le tronc et le modèle de la faim du tronc.
- `pays-reel-pop` : 9 fichiers non commités = le travail EN COURS de la session « Classes » ( mode `demographie="grece"` :
  pyramide, ménages familiaux, métiers neufs à la fin de `ROLES`, ~1,4 % de militaires à la naissance ) ; personne d'autre
  n'y touche. Défaut identique au bit.
- Les prix doublent entre les jours 5 et 35 puis montent d'environ 140 % par an ( d03 ) : signalé à la session du
  moteur, à suivre.
- Armée du budget ( chef de projet ) : la loi de programmation ( 6,6 % des dépenses publiques, SIPRI ; 55 % de soldes ),
  l'effectif payé, le plan de départs, la solde réelle des appelés. Partage convenu avec « Classes » : la part de
  militaires À LA NAISSANCE vient de la population grecque ( ~1,4 %, contre 9,33 % dans le monde E1 par défaut ) ; d25
  ne fait que la dynamique ( budget → effectif ), jugée par l'indicateur `part_militaires`.
