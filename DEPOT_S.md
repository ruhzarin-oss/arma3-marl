# PRÉ-INSCRIPTION — DISTILLATION DU MAÎTRE À 84,6 %

**Déposée le 26/08/2026, AVANT le premier pas.** Amende `DEPOT_DISTILLATION.md`
(`eaf6bbeed4ae8180`) en changeant de professeur ; toutes ses règles de méthode tiennent.

## LE NOUVEAU PROFESSEUR
`shamal_action(drop_to=1, retreat=True, mode="assault", bounding=False, flank=True)` —
**84,6 %**, étendue [79,3 ; 89,1], six graines jamais vues. Dépôt `cee4a563999d5112`.
Il n'exige **rien** à l'exécution, contrairement à la greffe qui réclamait le prix des
8 actions. Référence à battre : `A` = **49,6 %**.

## LA LEÇON EXISTE — mesuré AVANT d'entraîner ⟨lame de Fable⟩
Désaccord maître ↔ référence : **90,4 %** sur la distribution du maître, **86,4 %** sur celle
de la référence. Contre le contrôle S3 : 64,1 % / 77,7 %.
**Pour mémoire, la leçon d'hier valait 26,2 % / 14,3 %** — et D1 s'était effondré sur la
référence (il la suivait à 93-95 % là où elle différait). Le rapport est de **sept**.

⚠️ **Conséquence à écrire d'avance :** à 90 % de désaccord, l'élève n'apprend pas un
raffinement, il apprend une politique **entièrement neuve**. Aucun démarrage à chaud depuis
`A` n'est légitime, et un échec ne pourra pas être imputé à un mauvais point de départ.

## LES DEUX ÉLÈVES
| élève | ce qu'il voit | cible |
|---|---|---|
| **S1** | les 12 nombres | l'action du maître |
| **S3** | les 12 nombres | **LE CONTRÔLE** — même forme d'ordre, **cap tiré au hasard** parmi les 8 ; tenir, tirer et postures conservés |

S3 mesure ce que rapporte le seul fait d'imiter **quelque chose de cohérent**, sans le contenu
tactique. Il désaccorde du maître à 64-78 %, donc ce n'est pas un contrôle mou.

## LES PORTES, ÉCRITES AVANT LES DONNÉES
· **G2 — LE CONTRÔLE, SE LIT EN PREMIER.** `S1 − S3 ≥ +3,0`. Sinon G1 ne veut rien dire.
· **G1 — LA PORTE.** `S1 − A ≥ +5,0`, donc **S1 ≥ 54,6 %**. Échec sous 52,6 %.
· **G4 — PLAFOND.** Le maître est à 84,6 %. Un élève **au-dessus** est suspect et appelle une
  vérification, pas une célébration.
· **G5 — LES DEUX TÉMOINS SÉPARÉS** : danger par homme-pas **et** survivants. Le maître tient
  **2,68 survivants sur 4** ; un élève qui gagne avec des survivants effondrés a copié la
  prise sans le métier — c'est ce qui a démasqué le façonnage (0,11) et D1 (0,12).
· **BUDGET** jugé sur le **plateau de la perte**, pas sur la parité d'itérations. Si elle
  descend encore à 600, le verdict est **suspendu** et le budget étendu.
· **DÉCODEUR** : échantillonnage, pour tous, comme tout le dossier.

## CE QUE ÇA NE PROUVERA PAS
Résultat de **GYMNASE**. Et même un succès ne dira rien du bounding overwatch en général :
seulement que **cette** implémentation, à **cette** densité de défense, coûtait 36,6 points.

---

# AMENDEMENT — LE MAÎTRE v2, À 91,0 %. Déposé le 26/08 avant tout élève jugé.

## LA PANNE QUI L'A RÉVÉLÉ
Le premier lancement a planté sur une assertion CUDA : `cur_target >= 0 && cur_target <
n_classes`. Cause : `B.NA` vaut **10** par défaut, or le maître émettait l'action **11**
(accroupi) **5,74 %** du temps. C'est le défaut que `boucle.py` documente déjà — *« la
politique n'en avait que 10, donc elle ne pouvait PAS changer de posture »*.

## LA MESURE QUI A SUIVI, ET QUI DONNE MIEUX
Plutôt qu'élargir la tête de l'élève à 13 sorties — ce qui aurait donné à `S1` un vocabulaire
plus large que la référence, donc un confondant — on a mesuré ce que vaut le bridage :

| maître | prise | étendue | survivants |
|---|---|---|---|
| complet, 13 actions | 84,6 % | [79,3 ; 89,1] | 2,68 |
| **bridé à 10 : postures → TIRER** | **91,0 %** | [89,1 ; 94,1] | **3,17** |
| bridé à 10 : postures → TENIR | **0,7 %** | [0,0 ; 1,2] | 0,01 |

**Supprimer l'accroupissement et tirer à la place gagne 6,4 points**, et monte les survivants
de 2,68 à 3,17 sur 4.

⭐ **Le contraste avec TENIR est ce qui rend la mesure lisible** : ce n'est pas « n'importe
quel remplacement marche ». C'est **TIRER qui paie** et **s'immobiliser qui tue**.

## ⭐⭐ LE MOTIF DES TROIS GESTES TOMBÉS
| geste du cahier | coût mesuré | ce qu'il fait |
|---|---|---|
| bond par binôme (n°1) | **−37,0** | gèle la moitié de l'escouade |
| accroupissement (n°4) | **−6,4** | gèle un homme un pas |
| tenir | **−83,9** | gèle tout |

**Dans ce monde, tout ce qui fige un homme coûte.** La tâche est `secure_only` : on ne gagne
qu'en ARRIVANT. Tout pas non consacré à fermer la distance est un pas payé au tarif du feu
sans rien acheter.

## CE QUE ÇA RÉSOUT
Le maître v2 n'émet **que les 10 actions de la référence** (vérifié : action maximale = 7 sur
un lot). **Le confondant de vocabulaire disparaît** : `S1` et `A` jouent le même répertoire.

## LES PORTES SONT INCHANGÉES, LE PLAFOND SE DÉPLACE
`G1` `S1 − A ≥ +5,0` (A = 49,6 %) · `G2` `S1 − S3 ≥ +3,0`, lu en premier · `G5` les deux
témoins séparés, le maître tient **3,17 survivants sur 4**.
`G4` — **le plafond passe de 84,6 % à 91,0 %.** Un élève au-dessus est suspect.
