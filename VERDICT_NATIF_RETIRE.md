# ⛔ LE NATIF À 68,2 % EST RETIRÉ — même standard que la porte, appliqué à l'étalon

**21/08/2026.** Retrait de `VERDICT_NATIF_20-08.md`.

## LE MOTIF, MESURÉ

`_m` n'a existé qu'entre la fusion du 20/08 et sa réparation à 00 h 51 le 21/08. Toute
erreur `_m` du journal de campagne appartient donc à cette fenêtre, sans ambiguïté.

| fenêtre | erreurs `_m` | erreurs `certifier_positions` |
|---|---|---|
| **13 h – 20 h — les 135 épisodes NATIF** | **214** | **5 092** |
| 22 h – 23 h — nuit politique interrompue | 56 | 1 216 |

> **102 erreurs ont fait retirer la porte du 20/08.
> Le NATIF a été mesuré sur un monde qui en jetait plus de 5 300.**

Les deux causes sont nommées : la variable orpheline `_m` dans la ligne de retour du
placeur, et l'ordre **scène-avant-socle** dans `banc_live.py` — le second n'ayant été
réparé que le 21/08.

## POURQUOI CE RETRAIT EST OBLIGATOIRE ET NON DISCUTABLE

J'ai retiré la porte pour 102 erreurs. Ne pas retirer le NATIF pour 5 306 serait **une
justice à deux vitesses, et elle pencherait du côté qui flatte** : le NATIF est l'étalon
contre lequel la politique doit se comparer, et un étalon indulgent rend la politique belle.

⚠️ **Cliquet : le standard qui condamne un instrument condamne aussi son étalon.**
Appliquer un critère à ce qu'on mesure et l'épargner à ce contre quoi on mesure, c'est
choisir son résultat.

## DEUX ISSUES, PAS TROIS

1. **Re-mesurer le NATIF sur socle sain** — 2 × 67 épisodes, ~8 h, sur le socle 5.5.0 avec
   la ligne 5 branchée.
2. **Déclarer la comparaison impossible** et le dire.

Il n'y a pas de troisième. En particulier, « le chiffre est probablement bon quand même »
n'en est pas une : c'est exactement ce que j'ai voulu dire de la porte avant de me raviser.

## CE QUI SURVIT DU DÉPÔT RETIRÉ

Ce sont des trouvailles d'**instrument**, elles ne dépendent d'aucun nombre :
- la **condition 3 levée** — le compteur de coups posé, le natif tire 60 à 130 coups par
  épisode (mesuré sur la douzaine du 20/08, socle 5.4.0 — donc **elle aussi à rejouer**) ;
- la **non-dégénérescence de la mission** : 63 % des épisodes sans perte attaquante,
  0,73 perte moyenne sur 4 — le banc mord faiblement ;
- la **signature d'attrition** : les refus de prévol sont des T7 à `vue:0`, l'anneau fixe
  par session.

## CE QUI DOIT PRÉCÉDER LA RE-MESURE ⟨revue du 21/08⟩

1. **`banc_live.py` n'a pas de journal jugeable** : nom fixe `serverLV.out`, ouvert en
   ajout, jamais tronqué — 27,8 Mo et 279 démarrages d'hôte accumulés. `prevol.py` tronque
   et nomme par session ; **la discipline n'a jamais été transposée**. Sans elle, la ligne 5
   ne peut pas juger une nuit. **Quatrième non-transposition de la semaine.**
2. **`porte_lots.sh` compte des LIGNES** : `grep -c` a rendu T5=2 pour **un** événement.
   La faute que j'ai corrigée trois fois dans la ligne 5, toujours vivante dans le fichier
   que l'humain lit en premier.
3. **Deux seuils incompatibles cohabitent** : `prevol.py` imprime « PORTE TENUE : 1 échec
   sur 12, seuil 2 » quand la ligne 1 exige zéro sur 60. Le lot 4 a été déclaré **tenu** par
   un instrument et **rouge** par l'autre, dans le même run.
4. **La ligne 5 n'a pas de gardien** liant les journaux lus aux lots jugés — le défaut que
   la ligne 4 avait avant sa réparation.
