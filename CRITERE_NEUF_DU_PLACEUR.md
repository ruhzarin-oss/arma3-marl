# LE CRITÈRE NEUF DU PLACEUR — spécification écrite AVANT la mesure

**19/08/2026, 20 h 50.** Socle 4.0.0, canal `sv_vz_preserve_10hz`.
Ce fichier est committé **avant** que la mesure tourne. Le seuil ne peut donc pas être
ajusté à ce qu'elle montrera : seule la **règle** de dérivation est écrite ici.

## POURQUOI L'ANCIEN CRITÈRE EST RETIRÉ

Il mesurait « distance parcourue en 4 s **en marchant vers le nord** ≥ 23 m ».
Trois faits le tuent :
- le seuil de 23 m n'était franchissable **qu'en descente** (0 acte sur 188 finissant au sol) ;
- **inverser la direction inverse le régime** (3/3 et 3/3) — la grandeur mesurait donc la
  **pente dans un azimut câblé**, pas la praticabilité ;
- sur le canal adopté, la plus longue distance mesurée est **22,5 m** : le seuil est
  désormais infranchissable **partout**.

⚠️ Ce n'est pas un desserrement de l'ancien critère. C'est un **critère neuf sur une
grandeur neuve**, l'ancien étant retiré pour **prémisse fausse**.

## CE QUE LE PLACEUR DOIT RÉELLEMENT CERTIFIER

Que l'homme **n'est pas coincé** — pas qu'il est rapide. Le mode d'échec qui a coûté la
semaine est le T5 à 3 m : un homme bloqué par un rocher, un mur, une pente. La vitesse,
elle, dépend du terrain et **c'est légitime** : un versant montant ralentit, et la campagne
doit l'apprendre, pas l'éviter.

## LE CRITÈRE, DANS SA FORME

| | |
|---|---|
| **grandeur** | distance parcourue en 4 s, sur le canal `sv_vz_preserve_10hz` |
| **échantillon** | **les 8 azimuts de la couture** (0°, 45°, … 315°) — l'espace d'action exact que la politique emploie (`arma_couture.py`, `_a*45`) |
| **statistique** | le **MINIMUM** sur les 8 azimuts |
| **seuil** | dérivé — voir la règle ci-dessous |
| **n minimum de la dérivation** | **≥ 50 lieux** ⟨règle 19⟩ |

**Pourquoi le minimum et non la médiane** : un lieu où l'homme part dans sept directions
sur huit et se cogne dans la huitième est un lieu qui produira des T5 à 3 m. Le placeur
doit refuser ce lieu-là. Le minimum est la statistique du mode d'échec.

## LA RÈGLE DE DÉRIVATION DU SEUIL — écrite avant de voir les nombres

La distribution des distances est **bimodale** : un régime **coincé** (queue basse) et un
régime **marchant**. Le seuil se pose **dans le creux**, et nulle part ailleurs :

> **seuil = la borne INFÉRIEURE du régime marchant, moins la tolérance de mesure.**
> Opérationnellement : sur les ≥ 50 lieux × 8 azimuts, on trace l'histogramme des minima ;
> le seuil est le **milieu du creux** séparant les deux modes, arrondi au mètre inférieur.

**Si le creux n'existe pas** — distribution unimodale ou continue — **la règle échoue et
le critère n'est pas écrit ce soir.** On ne pose pas un seuil dans un continuum : ce serait
un chiffre rond de plus. C'est le cas d'arrêt, déclaré maintenant.

## LES CONTRÔLES DU CRITÈRE ⟨règle 18⟩ — un critère qui n'a pas été jugé ne juge pas

| contrôle | attendu |
|---|---|
| **jambes coupées** (`vy = 0` sur les 8 azimuts) | **0 lieu reçu sur 50** |
| **lieux dans l'eau** | 0 reçu |
| **lieux connus praticables** (les 6 « montée » et 6 « descente » de la sonde visuelle) | **12 reçus sur 12** |
| **le critère doit être insensible à la direction** | la médiane des minima ne doit pas dépendre de l'azimut du meilleur |

Un critère qui ne refuse pas les jambes coupées **ne juge rien** et n'est pas adopté.

## ANGLES MORTS DÉCLARÉS ⟨règle 20⟩

- Il ne dit **rien du tir** : l'acte 3 reste inchangé et garde ses propres angles morts.
- Il ne dit **rien de la vitesse** : un lieu lent mais libre sera **reçu**, et c'est voulu.
  Le tempo est une affaire de gymnase, pas de placeur.
- 8 azimuts, pas un continuum : un blocage étroit entre deux azimuts passe inaperçu.
- Mesure au repos serveur ; la cadence d'impulsions y est la même qu'en monde éveillé
  (nt 39-40 des deux côtés), mais rien n'est dit d'une charge plus lourde.
