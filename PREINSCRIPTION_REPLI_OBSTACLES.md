# PRÉ-INSCRIPTION DU REPLI — LE PROFIL D'OBSTACLES. Écrite avant la mesure.

**19/08/2026, 23 h 00.** Dernier candidat déclaré dans `PREINSCRIPTION_MODELE_PENTE.md`
(`c6535a1`) avant la **clause de chute**. La covariable « pente » est tombée non pas sur
son falsificateur mais sur un **témoin sans modèle** (`MODELE_PENTE_SANS_POUVOIR.md`).

## LE MÉCANISME SUPPOSÉ, ET IL EST SIMPLE

> **L'homme s'arrête où il rencontre quelque chose.** Si un rocher est à 4 m dans son
> couloir, il parcourt ~4 m. La distance n'est donc pas prédite par la pente, mais
> **bornée par la distance au premier obstacle**.

C'est ce que la mesure d'hier oriente sans le démontrer : les blocages ne se distinguent
pas par la pente (dénivelé médian **+3,3 m** contre **+0,8 m** ; pire montée **0,7** contre
**0,5**), donc la cause est ailleurs.

## LA COVARIABLE

Pour chaque lieu et chacun des 8 azimuts : on échantillonne **tous les mètres sur les 25 m
parcourus** et on relève, dans un **tube de rayon 2 m** :
- **`d1`** — la distance au **premier** point du couloir portant un objet ;
- **`nobs`** — le nombre de mètres du couloir portant au moins un objet.

⚠️ La fenêtre couvre **la course entière**, pas un disque autour du départ. C'est la faute
de la tentative 3, corrigée ici comme elle l'a été pour la pente.

## LES PRÉDICTIONS, CHIFFRÉES

| n° | prédiction |
|---|---|
| **P1** | parmi les couples **bloqués** (distance < 6 m), **≥ 70 %** ont `d1 < 8 m` |
| **P2** | parmi les couples **libres** (distance ≥ 15 m), **≤ 20 %** ont `d1 < 8 m` |
| **P3** | **le détecteur « `d1` court » BAT LE TÉMOIN SANS MODÈLE** |

## P3 — LE TÉMOIN, ET C'EST LE TEST QUI ENGAGE VRAIMENT

Le témoin est le détecteur du soir : la bande unique sur la distance, **sans aucune
information d'obstacle**. Ses chiffres sont **déjà mesurés et déposés** :

> **témoin : 11 blocages attrapés sur 27, en accusant 2 % des couples.**

> **Le repli n'est retenu que s'il attrape STRICTEMENT PLUS de blocages que 11/27 à taux
> de fausse accusation égal ou inférieur.** Couvrir, calibrer, corréler ne suffisent pas :
> *le seul test qui engage un modèle est la comparaison à l'absence de modèle.*

## LE FALSIFICATEUR — ET IL DÉCLENCHE LA CLAUSE DE CHUTE

> **Si P1 échoue** — moins de 70 % des blocages ont un obstacle proche — **alors les
> obstacles n'expliquent pas le blocage.** C'était le dernier candidat de la liste fermée :
> **le cadre covariable TOMBE**, et l'on revient au couloir marché, c'est-à-dire à mesurer
> les 8 azimuts pour de bon plutôt qu'à les prédire.

Aucune covariable ne sera ajoutée pour sauver le cadre. La liste a été fermée par écrit.

## LES DONNÉES

Les **60 lieux aléatoires × 8 azimuts** déjà mesurés (480 couples, 27 blocages), canal
`sv_vz_preserve_10hz`. La covariable est une **lecture de terrain** : aucune unité créée,
donc aucune nouvelle source de variance. Le lien lieu↔distance est celui du journal
`serverVUEAZ.out`, archivé.

⚠️ Les distances ont **déjà été vues**. C'est donc un test **de confirmation du mécanisme**
sur données existantes, pas une validation tenue : si le repli passe, il devra être rejoué
sur un tirage frais avant d'être adopté. Dit ici, avant de mesurer.
