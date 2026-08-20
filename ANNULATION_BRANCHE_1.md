# ⛔ ANNULATION DE LA DÉCISION « BRANCHE 1 » — par Younes, le 20/08/2026

## LA DÉCISION ANNULÉE

**19/08/2026, ~20 h.** Sur la base du `DOSSIER_DOCTRINE_TEMPO.md`, Younes a tranché la
**branche 1** : *rendre la gravité au canal et **recaler le gymnase** sur la capacité au sol* —
ce qui impliquait un **réentraînement complet**.

## POURQUOI ELLE EST ANNULÉE

**La prémisse du dossier était fausse.** Il affirmait que « le gymnase enseigne 6 m/s ».
Vérifié le 20/08, sur l'objet construit et non dans un fichier :

```
move = 14,0 m   ·   sec_par_pas = 3,28 s   →   VITESSE = 4,27 m/s
```

Le « 6 m/s » était la **consigne envoyée à Arma par la couture** (`arma_couture.py:21`), dont
le commentaire le disait déjà : *« le sandbox move=14/pas ; on tempère pour le FPS »*.

Le corps mesuré rend 3,75 m/s en montée (~57 % du terrain) et 5,5 en descente (~43 %), soit
un mélange pondéré de **≈ 4,5 m/s**. **L'écart réel est de ~5 %, non de 60 %.**
`SEC_PAR_PAS` avait d'ailleurs été **dérivé** d'une vitesse mesurée sur des lieux aléatoires :
le gymnase était déjà calibré sur ce mélange.

## CE QUI EST ANNULÉ, EXACTEMENT

| | |
|---|---|
| **le recalage du gymnase** | **ANNULÉ** — il n'y a rien à recaler |
| **le réentraînement qui en découlait** | **ANNULÉ** — aucun n'est justifié par le tempo |
| **les branches 2 et 3** | sans objet — elles répondaient au même faux problème |

## CE QUI SURVIT, ET N'EST PAS ANNULÉ

**Le passage du canal à la gravité préservée** (`sv_vz_preserve_10hz`, socle 4.0.0) **reste
adopté**. Il n'a jamais dépendu du tempo : il a été décidé sur une mesure appariée propre
(12 lieux × 2 canaux, prédictions écrites avant), et il **abolit le vol** — la hauteur en
descente passe de 6,8 m à 0,4 m. C'était une correction de **physique**, pas de vitesse.

## POURQUOI CE FICHIER EXISTE

Retirer le dossier annule le **raisonnement**. Il n'annule pas la **décision** : ce sont deux
traces distinctes, et seule la seconde porte le nom de celui qui l'a prise. Sans cette ligne,
le dépôt montrerait dans trois semaines « Younes a tranché la branche 1 » **sans montrer que
la prémisse était fausse** — et quelqu'un rebâtirait dessus.

> ⚠️ **CLIQUET : une décision prise sur une prémisse retirée s'annule EXPLICITEMENT, et par
> celui qui l'a prise.** Le retrait du document qui l'a motivée ne suffit pas.

## LE SUJET QUI SUBSISTE, ET QUI N'EST PAS CELUI-LÀ

Dans le gymnase, **la pente n'agit pas sur le déplacement** — elle est dans l'observation
seule. Arma sépare les deux régimes à **1,47×**, établi causalement. Question ouverte,
**non urgente**, et mesurable **sans réentraîner** (ablation à l'évaluation + différentiel
scripté). Voir `DOSSIER_DOCTRINE_TEMPO.md`, section corrigée.
