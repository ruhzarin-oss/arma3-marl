# CRITÈRES DU JALON 1 — ÉTALONNER LES INSTRUMENTS (figés avant toute mesure)

Écrits le 2026-07-29. Architecte : Fable. Exécution : Opus 5. Arbitrage : Younes.
**Aucun chiffre produit par ce projet n'est admissible tant que J1 n'est pas vert.**

## POURQUOI CE JALON EXISTE
Sept pannes en deux jours, toutes dans l'instrument, jamais dans l'objet mesuré : causes
d'arrêt lues après la remise à zéro, journaux tronqués par un `tail`, seuil posé sur une
moyenne de deux effets opposés qui s'annulaient, plafond d'exposition dix fois trop haut,
poids par verbe interdit par le contrat et pourtant écrit, substitution mal placée.

**La règle qui ferme la boucle :** on possède des objets dont la réponse est connue — les six
doctrines écrites à la main. **Aucun instrument n'a le droit de produire un chiffre tant qu'il
n'a pas retrouvé ces chiffres-là.** Un thermomètre qu'on n'a jamais plongé dans l'eau
bouillante ne mesure rien.

## LA TABLE PUBLIÉE — STATUT : A PRIORI, PAS VÉRITÉ
Mesurée le 2026-07-29 sur 1024 environnements, graine 3, D=8. **Son protocole n'est pas
persisté** : elle a été produite par un script jetable. Un chiffre dont le protocole n'existe
pas sur disque n'est pas une référence, c'est un souvenir. Elle sert ici de test de cohérence
de l'instrument, dans ce sens-là uniquement.

| doctrine | PRENDRE | INFILTRER |
|---|---|---|
| frontal_delibere | 44,0 | 7,6 |
| appui_mouvement | 49,8 | 14,5 |
| debordement_simple | 54,3 | 32,2 |
| debordement_double | 54,3 | 31,7 |
| infiltration | 53,0 | 18,1 |
| bonds_alternes | 24,8 | 9,6 |

## PLAN DE MESURE (E4)
`episodes=1024`, `graine=3`, `D=8`, `pas=80`, `mode=episode` (`auto_reset=False`), `permute=0`.
Six doctrines × deux verbes **forcés** = 12 passes, 12 288 épisodes.

**Le forçage du verbe n'est pas négociable** : il donne 1024 épisodes par cellule au lieu de
~512, et il rend les deux verbes **appariés** — même flux de générateur, donc mêmes R, T, K,
E et même terrain ; seule la contrainte change. À p=0,5 et n=1024 l'écart-type est de 1,56
point : ±3 points devient un test honnête. À n=512 il ne l'est pas, et sur douze cellules on
attendrait deux échecs par pur hasard.

**Le pas `t` désynchronisé ne se corrige pas, il se supprime par construction.** En mode
`episode`, tous les environnements démarrent à t=0 et ne se réinitialisent jamais : le `t`
scalaire passé aux doctrines est exact. C'est le mode du banc déjà éprouvé (`matrice_manuel.py`).
Le mode `continu` est **interdit** pour les doctrines, et l'instrument doit le refuser.

## TOLÉRANCE ET VERDICT (E4)
- **12 cellules sur 12 dans ±3,0 points** → a priori confirmé, instrument étalonné.
- **Au moins une cellule hors ±3,0** → **la mesure reproductible gagne.** On ne bricole pas
  l'instrument pour retomber sur la table. On prépare un AMENDEMENT 4 qui retire la table du
  29/07 en nommant le motif — protocole non persisté — et inscrit la nouvelle avec sa ligne de
  commande complète et les sha256 des trois fichiers. **Soumis à Younes. Il tranche, pas moi.**

Avant d'invoquer l'échec, **une seule bissection**, un paramètre à la fois, journalisée :
`--verbe tire` contre forcé ; `--pas` 60 contre 80 ; `--episodes` 1024 contre 2048. Rien
d'autre. Si l'un des trois retrouve la table, c'est le protocole d'origine et c'est lui qu'on
inscrit.

## CONSOLIDATION (E5)
Même plan sur cinq graines : 3, 4, 5, 6, 7. Étalon de record = moyenne des cinq, **étendue
rapportée par cellule**. Porte : **étendue < 8 points par cellule** (la variance connue du bac
à sable est de 8,5 points sur douze graines). Au-delà, le monde n'est pas assez stable pour
juger un agent et J1 n'est pas vert.

## CONTRÔLE NUL (E6) — LA PORTE QUI REND J1 VERT
L'audit d'ordre passé sur les **six doctrines scriptées**. Une doctrine ne lit aucune
observation : ses actions sont identiques, les graines sont identiques, le prédicat utilise le
verbe vrai inchangé. **L'écart attendu n'est pas « petit », il est exactement 0,000.**
Toute valeur non nulle prouve que le chemin de permutation contamine l'état du monde.
Dans ce cas : arrêt, aucun verdict sur `mission_v3.pt`, on répare.

**Un instrument qui n'a pas prouvé son zéro ne mesure pas, il opine.**

## SEUIL DE LECTURE DE L'ORDRE (inchangé, contrat amendement 3)
Par verbe, jamais moyenné : `écart[v] = |taux_vrai[v] − taux_permuté[v]|`, moyenné sur cinq
graines tenues à l'écart (`1000+s`). **max(écart) ≥ 20,0 points** → l'agent lit son ordre.

## LES NEUF INTERDITS DE J1
1. Toucher `manuel.py`. Le pas désynchronisé se règle par le mode du banc.
2. Toucher `fabrique` : courbes, `tir_par_pas`, `supp_*`, `cible_unique`, `def_*`. Un
   instrument ne se règle pas en déplaçant l'objet mesuré.
3. Toucher les bornes de mission (`E/K/T/R_MIN/MAX`) ou la récompense (`W_PROGRES`,
   `W_PERTE`, `R_SUCCES`). Si un chiffre ne tombe pas juste, ce n'est pas là qu'on cherche.
4. Entraîner quoi que ce soit. Pas de v4, même « pendant que ça mesure ». Le GPU sert au banc.
5. Publier, citer ou raisonner sur un chiffre produit avant E6. Y compris un chiffre qui plaît.
6. Moyenner les deux verbes, ou conclure sur une seule graine. Deux fautes déjà commises.
7. Écraser ou supprimer un journal. Ouverture en ajout, jamais en écrasement.
8. Retirer la table publiée de sa propre autorité si E4 échoue. On prépare la pièce, Younes tranche.
9. Rendre un verdict sur `mission_v3.pt` tant que E6 n'a pas donné 0,000.

## ORDRE DES OPÉRATIONS ET PORTES
| # | opération | porte |
|---|---|---|
| E0 | ce fichier | il existe et contient les douze nombres |
| E1 | patcher `monde_mission.py` (M1-M4) | preuve imprimée : sous permutation, l'observation ne diffère QUE sur les colonnes du verbe |
| E2 | écrire `banc_mission.py` | journal de fumée = 1 + 64 + 1 lignes, aucun `fin` à `horizon` |
| E3 | écrire `analyse_journal.py` | succès recalculé == succès du monde sur 100 % des lignes, appariement `mission_hash` tenu |
| E4 | étalon graine 3, 12 passes | 12/12 dans ±3, sinon bissection puis amendement soumis |
| E5 | étalon 5 graines | étendue < 8 points par cellule |
| E6 | contrôle nul, 6 doctrines | **écart == 0,000 partout — J1 devient vert ICI** |
| E7 | audit de `mission_v3.pt` | aucune porte : E7 produit le verdict, il ne le conditionne pas |
