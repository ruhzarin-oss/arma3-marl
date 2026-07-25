# Spec de perception — « augmenter le soldat Arma »

Principe : **obs égocentrique, taille fixe, scalable, par blocs activables.**
- Égocentrique = tout en repère du soldat (azimuts en sin/cos relatifs à son cap).
- Taille fixe = pour les comptes variables (ennemis, alliés) → top-K trié par distance.
- Par blocs = chaque sens s'active/désactive → on **empile et on mesure le gain de chacun**.
- Même calcul **des deux côtés** : Arma (réel) et AssaultTerrain (sandbox d'entraînement) → obs identique = train vite / deploy fidèle.

## Blocs d'observation

| # | Bloc | Features | dim | Source Arma (SQF) | Source sandbox |
|---|------|----------|-----|-------------------|----------------|
| 1 | **Soi (proprio)** | santé, suppression, posture(3), vitesse, munitions, recharge, endurance | 9 | getDammage, getSuppression, stance, speed, ammo, fatigue | état interne |
| 2 | **Couvert (coque)** | 12 distances rayons (norm) | 12 | lineIntersectsSurfaces ×12 | _cover_shell ✅ |
| 3 | **Couvert vs menace** | par rayon : bloque-t-il la LOS vers l'ennemi le + proche | 12 | intersect rayon↔ennemi | échantillon grille |
| 4 | **Terrain** | pente sous pieds(2), élévation relative à l'ennemi(1) | 3 | surfaceNormal, getTerrainHeightASL | slope grid |
| 5 | **Ennemis top-K** (K=4) | par ennemi : azimut(sin,cos), dist(norm), LOS, me-vise | 5×4=20 | nearTargets, knowsAbout, LOS, getHideFrom | dpx/dpy + LOS |
| 6 | **Tirs entrants** | azimut(sin,cos) dernier tir, récence, sous-le-feu | 4 | EH Fired/Hit/FiredNear | événement combat |
| 7 | **Alliés top-M** (M=3) | par allié : azimut(sin,cos), dist, état | 4×3=12 | units group, getDammage | team_feats ✅ |
| 8 | **Mémoire spatiale** | azimut du danger(sin,cos), danger total | 3 | (maintenu Python) | SpatialMemory ✅ |
| 9 | **Objectif** | azimut(sin,cos), distance | 3 | position objectif | dgx/dgy ✅ |

**Total complet ≈ 78** (modulable). v0 minimal = blocs 1,2,5,9 (~37). On ajoute 3,4,6,7,8 un par un.

## Espace d'action (le cerveau → soldat Arma)

Discret enrichi :
`0-7` cap (8 dir) · `8` tenir · `9` supprimer · `10` couvert/posture-bas · `11` viser-ennemi-proche · `12` tirer · `13` recharger · `14` sprint
→ chaque action = commande SQF native (doMove/setVelocity, doSuppressiveFire, setUnitPos, doTarget+doFire, reload, forceWalk off).

## Protocole « scaling de perception »

1. Entraîner le cerveau avec **bloc minimal** (1,2,5,9) → score de référence.
2. Ajouter **un bloc** → ré-entraîner → mesurer Δ score.
3. Garder les blocs à Δ positif. Le profil de gain = le résultat de recherche.
4. La **souffrance** = blocs 1(suppression/santé) + 6(tirs) : le corps perçu comme éprouvé.

## Fréquence

- **Canal action** : 50 Hz (EachFrame + hmt_native TCP) — existe.
- **Canal perception** : plus lourd → viser 10-20 Hz en SQF/EachFrame ; **upgrade Intercept (C++ in-process)** pour monter la fréquence et passer à N soldats.
- Mur : le coût des requêtes moteur (raycasts/LOS) reste, Intercept enlève seulement le scheduler SQF.
