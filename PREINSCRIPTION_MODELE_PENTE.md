# PRÉ-INSCRIPTION — LE TERRAIN COMME COVARIABLE, NON COMME PORTE

**19/08/2026, 22 h 20.** Écrit **avant** tout ajustement et **avant** d'avoir regardé la
moindre corrélation. Cadre endossé par Fable après trois arrêts déclarés
(`DERIVATION_CRITERE_ARRET.md`, `CORPUS_PLAT_FALSIFICATEUR.md`).

> **On met une porte devant un ACTE. On met une covariable devant le MONDE.**
> T4 et T7 jugent des actes binaires — une balle part ou non : la porte y reste le bon
> objet. T5 jugeait une **propriété continue du terrain** à travers un binaire inventé,
> « praticable ». Un seuil posé sur un continuum **est mécaniquement de la sélection** :
> c'est ce qui a produit le « 104 % ».

Le placeur cesse de **trier** et se met à **ordonner** : il mesure la pente, prédit la
distance attendue, et T5 juge le **résidu**.

## 1 · LA COVARIABLE — LISTE FERMÉE ICI, AVEC CLAUSE DE CHUTE

| rang | covariable | mesurée sur |
|---|---|---|
| principale | **dénivelé le long de la course** | les **25 m** réellement parcourus dans l'azimut |
| principale | **pire montée sur un pas de 5 m** | le long des mêmes 25 m |
| **repli unique déclaré** | profil d'obstacles dans un tube de 2 m le long de la course | idem |

⚠️ **La fenêtre de la covariable couvre la course qu'elle explique** — 25 m, pas un disque
de 10 m autour du départ. C'est la faute qui a tué la tentative 3, corrigée ici.

> **CLAUSE DE CHUTE : si la principale ET le repli échouent en validation tenue, le cadre
> covariable TOMBE** et l'on revient au couloir marché. Aucune autre covariable ne sera
> ajoutée : chercher à en ajouter serait la version savante du déplacement de buts.

## 2 · LA FORME DU MODÈLE — PAR RÉGIME, JAMAIS LINÉAIRE

Le verdict du soir établit **deux régimes**. Un ajustement linéaire sur les deux mélangés
rendrait un mauvais score et **tuerait faussement le cadre**. La forme est donc :

1. **classificateur de régime** sur la covariable principale — frontière cherchée dans
   l'intervalle mesuré **(−5,6 % ; +15 %)** de pente le long de la course ;
2. **prédiction de distance PAR BRANCHE** ;
3. **résidu jugé dans sa branche.**

## 3 · LA COUPE — PAR LIEU, JAMAIS PAR AZIMUT

Les 8 azimuts d'un lieu **partagent leur terrain** : couper par azimut serait une fuite de
validation. **Coupe par LIEU**, moitié-moitié, tirage à graine fixe déclarée (19).

## 4 · LA PROCÉDURE QUI FIXE LES NOMBRES — pas un goût

- **X (qualité du modèle)** : la bande de prédiction à 95 % calculée sur la moitié
  d'entraînement doit couvrir **95 ± 3 %** de la moitié de validation.
- **Y (seuil de résidu)** : le résidu qui attrape le **sabotage des jambes 3 fois sur 3**
  en accusant **≤ 5 %** des lieux sains. Y sort de la séparation **mesurée** entre la
  signature de panne (0-3 m) et l'enveloppe basse saine.

Ni X ni Y ne sont choisis en regardant lesquels feraient passer ce qu'on aimerait voir passer.

## 5 · LE JEU DE DONNÉES — les trois « échecs » de la soirée

| source | n | rôle |
|---|---|---|
| 60 lieux **aléatoires** × 8 azimuts | 480 | **ajustement** — échantillon non restreint |
| 50 lieux du **décile plat** × 8 azimuts | 400 | **test dur, amplitude restreinte** |
| 12 lieux connus (montée/descente) | 96 | frontière de régime |
| sabotage jambes × 110 lieux | 880 | contrôle négatif |

⚠️ Le corpus plat a une **variance de pente comprimée par construction**. Un score faible
**sur lui seul ne tue pas le cadre** — c'est dit ici, avant de le voir.

⚠️ Tout est mesuré sur le canal **`sv_vz_preserve_10hz`** (socle 4.0.0). **Le modèle est
versionné par canal** et lié au gardien : un modèle qui survit à son canal en silence
serait la divergence certificateur/servi sous sa forme suivante.

## 6 · LE DESSIN DE T5 QUE LE CADRE OFFRE

T5 ne subit plus l'azimut : il **prédit les 8**, marche **le plus diagnostique** (distance
prédite maximale), et juge le résidu là.
**Cas limite déclaré** : si même le meilleur azimut prédit une distance ≤ la signature de
panne, T5 se déclare **NON DIAGNOSTIQUE** et le dit. *Une mesure doit savoir échouer.*

## 7 · CE QUI ANCRE SANS CERCLE — on abandonne « praticable » en absolu

| ancrage | mesuré |
|---|---|
| **reproductibilité** | 12/12 inter-mondes |
| **intervention** | bras sud, **3/3 et 3/3** — manipuler la covariable inverse le résultat |
| **sabotage** | jambes → 0 m partout, 0 reçu sur 60 |

L'intervention est le contrôle positif **causal** : elle n'exige aucun corpus, parce
qu'elle **agit** au lieu de sélectionner.

## 8 · LE FALSIFICATEUR

> **Si la bande de prédiction à 95 % de l'entraînement couvre moins de 92 % de la
> validation tenue, le modèle est rejeté.** Si le repli échoue aussi, le cadre tombe et
> le couloir marché reprend la main — sans regret : le falsificateur aura payé sa place.
