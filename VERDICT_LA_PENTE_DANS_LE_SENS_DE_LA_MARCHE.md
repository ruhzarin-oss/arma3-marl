# ⭐⭐⭐ LE PLACEUR MESURAIT LA PENTE, PAS LA PRATICABILITÉ

**19/08/2026.** Socle `3.1.0-19082026`. Sonde `bancs/socle/sonde_vue.sqf` 1.2.0,
lanceur `run_vue.py`, rendu `rendu_vue.py`.
Preuves : `/mnt/data/preuves/2026-08-19_controle_visuel` (journaux + `profils.png` +
`lieux.png`) et `/mnt/data/preuves/2026-08-19_porte_31_tronquee` (29 journaux, empreintes
SHA-256).

> **Demandé par Younes** : « fais un contrôle visuel des agents pour savoir où ils sont
> exactement sur la carte et l'environnement autour ». Le dossier reposait jusque-là sur une
> **chaîne de caractères** (`afal` contre `amov`) lue au dernier tick. La sonde l'a remplacée
> par la **hauteur au-dessus du terrain, à chaque tick**. C'est cette demande qui a produit
> l'instrument décisif.

---

## LA REVENDICATION

**Sur le canal de campagne** — `setVelocity [0, _vy, 0]` réémis à 10 Hz, commande 6 m/s,
celui de `arma_couture.py:185` que la politique emploie **et** celui du socle :

> **Le régime de déplacement est décidé par la PENTE DANS LA DIRECTION DE MARCHE.**
> En montée, le contrôleur d'animation colle l'homme au terrain et **mange sa vitesse** :
> il parcourt **11 à 15 m en 4 s** (2,8-3,7 m/s, soit **47 à 62 % de la commande**).
> En descente, le sol se dérobe, plus rien ne s'oppose à la consigne : il parcourt
> **23 à 25 m** (97-105 %) en paraissant voler.
> **Le seuil de 23 m du placeur n'est donc franchissable qu'en descente.**

⚠️ La revendication porte sur **ce canal**, pas sur « le corps ». La locomotion **native**
d'Arma (animation de marche de l'IA) n'est pas mesurée ici.

---

## LES CLAUSES, CHACUNE AVEC SON n ET SON INSTRUMENT

| clause | mesure | n | instrument |
|---|---|---|---|
| aucun acte finissant au sol n'atteint 23 m | **0** | **188** | 150 archives `ACTE2` + 32 bloc C frais + 6 sonde |
| la classe d'un lieu se reproduit dans un monde neuf | **12/12** | 12 | archive porte → sonde (test-retest inter-mondes) |
| en montée, distance | 11,0 – 15,0 m | 6 | sonde, 100 % au sol dans les 6 |
| en descente, distance | 21,8 – 25,6 m | 6 | sonde, 0-3 % au sol dans les 6 |
| **inverser la direction inverse le régime** | **3/3 et 3/3** | 6 | bras `sud` |
| la pente nord sépare les deux familles | **+15…+51 % contre −5,6…−34 %** | 12 | relief 13×13, ±30 m |
| vitesse relue en fin d'intervalle | **0,0 m/s au sol · 6,0 m/s en l'air** | 16 | sonde |

**Le contrôle qui établit la CAUSE** (`sud`, 3 par condition) :

| bras | mètres | part au sol |
|---|---|---|
| marche **nord** sur un lieu montant | 13,1 – 15,0 | 100 % |
| marche **sud** sur le même lieu | **24,6 · 25,2 · 24,6** | **0-3 %** |
| marche **nord** sur un lieu descendant | 21,8 – 25,6 | 0-3 % |
| marche **sud** sur le même lieu | **14,7 · 14,7 · 15,0** | **100 %** |

**Ce n'est donc pas le lieu : c'est le couple (lieu, direction).**

## LES CONTRÔLES DE L'INSTRUMENT ⟨règle 18⟩

| bras | attendu | obtenu | n |
|---|---|---|---|
| `jambes` (vy = 0) | 0 m, 100 % au sol | **0,0 m, 100 %** | 5/5 |
| `volforce` (vz = +5) sur lieu descendant | vol détecté | **24,2-25,3 m, 0-3 %, z ≤ 7,9** | 4/4 |
| `volforce` sur lieu **montant** | — | **13,1-14,3 m, 95-100 % au sol** | 4/4 |

Le troisième n'était pas prévu et il est le plus instructif : **on ne peut pas faire décoller
l'homme en montée, même en le poussant vers le haut.** Le contrôleur d'animation mange
l'impulsion verticale tant que l'homme est en état de sol.

---

## LE MÉCANISME

1. `setVelocity` est réémis à 10 Hz et **remet vz à zéro** à chaque impulsion.
2. **En montée**, l'homme reste en état d'animation « au sol » : à chaque intervalle le
   contrôleur de personnage le recolle au terrain et **annule sa vitesse** — la relecture
   en fin d'intervalle donne **0,0 m/s**, dix cas sur dix. Il n'avance que pendant la
   fraction de tick précédant la reprise.
3. **En descente**, le terrain s'enfonce plus vite que lui ; il quitte l'état de sol,
   plus rien ne l'annule, la relecture donne **6,0 m/s**, six cas sur six.
4. **Il ne monte pas** : sa vitesse verticale relue en l'air est **négative** (−0,6 à
   −1,2 m/s, la gravité d'un seul tick, remise à zéro par l'impulsion suivante).
   Ce qui croît, c'est sa hauteur **au-dessus du terrain** — parce que le terrain descend.
   **Il ne vole pas : il marche dans le vide.**

---

## CE QUE ÇA DÉTRUIT

- **Le critère du placeur ne mesure pas la praticabilité.** Il mesure « ça descend vers le
  nord », la direction étant **câblée** (`[0, _vy, 0]`). Tout lieu certifié depuis l'origine
  est un **versant orienté au nord**.
- **Le bloc C, activé, rend le monde inconstructible** : 37 positions jugées, **32 encombré,
  5 muet, 0 reçue**, six essais d'azimut à **0/4**. Désactivé par drapeau jusqu'au critère neuf.
- **`VERDICT_CORPS_NON_LIMITE` (le « 104 % ») et `CHARGE_FIDELITE_JAMBES` (le « 62 % »)
  restent morts tous les deux.** Ils sont **expliqués**, pas restaurés :
  *le hasard échantillonne, la sélection biaise.* L'ancien banc tirait au hasard dans ±60 m —
  il voyait surtout des montées, donc le régime lent : ~62 %. Le banc « amélioré »
  sélectionnait par le placeur, donc par la descente : 104 %. **Un instrument amélioré qui
  SÉLECTIONNE trompe plus fort qu'un instrument pauvre qui ÉCHANTILLONNE.**
- **Le tempo du gymnase est en cause** : il suppose 6 m/s uniformes ; le canal de production
  rend 2,8-3,7 m/s en montée. Arbitrage à Younes, dossier séparé.

## LE FALSIFICATEUR, ÉCRIT

- **Un lieu à 100 % au sol rendant ≥ 23 m tue la revendication.** 0 sur 188 à ce jour.
- **Le trou [17 ; 22] m** : aucun des trois instruments n'y a jamais posé une mesure.
  Toute mesure qui le remplirait rouvre le dossier.
- **Un couple (lieu, direction) qui ne s'inverse pas** sous le bras `sud` amende la thèse.

## ANGLES MORTS DÉCLARÉS ⟨règle 20⟩

- Sonde jouée **serveur au repos** (le bloc C ne pouvant plus construire de scène).
  Couvert non par les FPS mais par le **12/12 de conformité** : les classes ont été
  assignées en monde **éveillé** et se reproduisent au repos. Cadence identique par
  ailleurs : porte 48-49 FPS / nt 39-40 ; sonde nt 39-40.
- **Une seule direction testée en plus du nord** (le sud). Les azimuts obliques ne sont
  pas mesurés ; la thèse prédit un continuum, ce n'est pas vérifié.
- **Le seuil de bascule n'est pas mesuré** : on sait que +15 % cloue et −5,6 % libère.
  Entre les deux, rien.

## CLIQUETS

- **Une ligne de journal est un instrument.** À sa naissance : une ligne **réelle** relue,
  chaque champ portant une valeur du monde, le jour même. À la lecture : les parseurs
  **refusent** `any`, et aucun classifieur n'a de branche par défaut — un champ inconnu se
  **nomme**, il ne se range pas. *(Coût : `HMT|SOCLE|GESTE` écrivait `any` sur tous ses
  champs depuis le 17/08 23:02, et une revue l'a lu à travers un parseur qui les rangeait
  dans « au sol ».)*
- **Une garde qui avale doit avouer — ou définir son repli.** `if (!isNil "HMT_LOG") then
  { log }` a fait disparaître 100 % des lignes `HMT|CORPS|SOL` depuis le 16/08. L'idiome
  correct existait déjà dans le dépôt (`bancs/arma/couvert_c3.sqf:27`).
- **Resserrer n'immunise pas.** Le seuil de 23 m fut dérivé rigoureusement de « T5 attend
  24 m », lui-même dérivé de 6 m/s × 4 s — une vitesse que le canal n'atteint qu'en descente.
  La règle 13 protège du laxisme, pas du faux nord.
- **Un fait mesuré se dépose.** Le phénomène était écrit **en commentaire** dans
  `arma_couture.py` depuis le 15/08 (« setVelocity à Z=0 rend 25 m quand l'homme NE TOUCHE
  PAS le sol »). Sans dépôt ni lien, il n'a rien empêché pendant quatre jours.
