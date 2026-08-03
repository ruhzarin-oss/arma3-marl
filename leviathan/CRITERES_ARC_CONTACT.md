# CRITÈRES — DURÉE DE VIE DE L'ANGLE MORT AU CONTACT

Figés le 27/07/2026, **avant** le premier relevé. Aucun seuil ne bouge après.

## Ce qu'on mesure et pourquoi

La sonde du 27/07 (`sonde_arc_arma.py`) a mesuré un **état** avec un attaquant **passif**, et
elle a posé **trois de ses cinq angles EN MER** (altitudes −22, −118, −146 m — vérifié par
`sonde_terrain.py`). Ses « 0 tir / 35 touches / MORT » à 90°, 135° et 180° sont de la
**noyade**, pas de l'arc de tir. Ce résultat est **annulé**.

Ce qu'on mesure ici est une **DURÉE**, avec un attaquant qui **OUVRE LE FEU** :

> combien de secondes s'écoulent entre le premier coup tiré par l'attaquant et le moment
> où le défenseur, initialement orienté au nord, **se retourne** puis **riposte** ?

Si cette durée est finie et courte, l'arc de tir n'est pas une géométrie mais un
**comportement à latence**. La correction du sandbox devient alors petite et propre : le
cône se réoriente vers le feu entendu, avec la latence mesurée.

## Dispositif

| élément | valeur |
|---|---|
| angles testés | 0°, 45°, 90°, 135°, 180° (0° = droit devant le défenseur) |
| distance | 60 m |
| défenseur | `O_Soldier_F`, `setDir 0` (nord), `disableAI PATH`, COMBAT/RED, skill 0.5, `allowDamage false` (voir addendum) |
| attaquant | `B_Soldier_F`, `disableAI PATH`, COMBAT/RED, `allowDamage false`, forcé au feu (`doTarget`+`doFire` réémis toutes les 2 s) |
| durée | 75 s par répétition |
| répétitions | ≥ 5 par angle |
| terrain | cellules **vérifiées terre, plates, sans bâtiment à 120 m, sans eau à 250 m** (`cellules_altis.json`) |
| espacement | ≥ 700 m entre cellules |

### Les deux corrections oubliées, appliquées ici

1. **Filtre par source** : un impact ne compte que si `(_this select 3) == le défenseur de
   CETTE cellule`. Sans ça, on compte la noyade, la chute, et le voisin.
2. **Déduplication par tick** : `HandleDamage` est appelé ~1,9 fois par balle → un impact
   n'est retenu que si `diag_tickTime` a avancé de plus de 0,05 s depuis le précédent.

Les deux, pas l'un ou l'autre. Espacement 700 m **en plus**, pas à la place.

### Canari (l'instrument avant le résultat)

Le bras **0°** est le canari : le défenseur regarde l'attaquant, à 60 m, en plein jour.
**Il DOIT riposter en moins de 10 s dans au moins 4 répétitions sur 5.**
Si le canari échoue, **on ne conclut rien** sur les autres angles — l'instrument est mort.

## Les seuils, écrits avant

Notations : `t_rip(θ)` = médiane du délai « premier tir attaquant → premier tir défenseur »
à l'angle θ. `t_dir(θ)` = médiane du délai avant que le défenseur ait tourné à moins de 25°
de la direction de l'attaquant. Un bras qui ne riposte jamais compte comme `t = 75 s`
(la durée de la fenêtre), pas comme une donnée manquante.

**V1 — l'angle mort existe-t-il au contact ?**
- `t_rip(180°) ≥ t_rip(0°) + 3,0 s` → **OUI, il existe une latence dorsale**.
- `t_rip(180°) < t_rip(0°) + 3,0 s` → **NON**. L'arc de tir est une fiction dès que
  l'attaquant tire. Le sandbox doit retirer l'arc, pas l'affiner.

**V2 — l'angle mort est-il une géométrie ou un comportement ?**
- Si `t_rip(180°) < 75 s` (le défenseur finit par riposter dans tous les cas)
  → **COMPORTEMENT** : le cône se réoriente. Le sandbox doit modéliser une **latence**.
- Si `t_rip(180°) = 75 s` dans ≥ 4 répétitions sur 5 → **GÉOMÉTRIE** : le dos est un abri
  durable. Le sandbox actuel (arc dur) est fidèle, et le 0 % du banc s'explique ailleurs.

**V3 — la réorientation précède-t-elle la riposte ?**
- `t_dir(θ) ≤ t_rip(θ)` attendu pour tout θ. Si l'inverse, le défenseur tire sans se
  tourner : le modèle correct n'est pas un cône mais une portée omnidirectionnelle.

**V4 — l'ampleur, pas seulement le délai.**
Nombre d'impacts du défenseur sur l'attaquant sur les 75 s, par angle. Rapport
`impacts(180°) / impacts(0°)`. C'est le facteur que le sandbox doit reproduire.

## Ce qui invaliderait ce run
- Canari en échec (voir plus haut).
- Une cellule en mer, sur une pente > 8 m, ou avec un bâtiment à moins de 120 m.
- Un attaquant qui ne tire pas : si `tirs_attaquant == 0` dans une cellule, cette cellule
  est jetée, pas interprétée.
- Un impact dont la source n'est pas le défenseur de la cellule : filtré, jamais compté.

## ADDENDUM — correction d'INSTRUMENT, aucun seuil touché

Écrit après `sonde_arret.py`, avant le run définitif. **Les seuils V1 à V4 et le canari sont
inchangés.** Seule la façon de garder les deux hommes en vie change, parce que la première
était fausse.

Mesuré, quatre cellules, régimes de dégâts différents, tout le reste identique :

| cellule | montage | issue à 90 s |
|---|---|---|
| 0 | les deux mortels | **attaquant mort à +10 s** (déf. 6 tirs) |
| 1 | défenseur `allowDamage false` | **défenseur vivant et tirant** (45 tirs) ; attaquant mort à +20 s |
| 2 | `HandleDamage → min(dégât, 0,55)` sur le déf., `→ 0` sur l'att. | **défenseur MORT à +10 s** ; attaquant vivant 90 s |
| 3 | idem 2 + `setVehicleAmmo 1` toutes les 10 s | **0 tir des deux côtés** sur 90 s |

Trois enseignements, tous coûteux s'ils étaient restés cachés :
1. **`HandleDamage` renvoyant `min(dégât, 0,55)` NE PROTÈGE PAS.** Le défenseur ainsi monté
   est mort. C'est ce montage que la première version de cette sonde utilisait.
2. **`allowDamage false` protège**, et ne rend pas le défenseur muet (45 tirs).
   **`HandleDamage` renvoyant `0` protège aussi** (attaquant vivant 90 s) et laisse compter.
3. **`setVehicleAmmo 1` périodique ÉTEINT le tir.** Ne jamais réarmer en boucle.

Montage retenu : **défenseur `allowDamage false`**, **attaquant `HandleDamage → 0`** (qui
compte les impacts, filtre par source, déduplique par tick).

**Réserve honnête à porter au verdict** : un défenseur `allowDamage false` n'encaisse pas
de dégât. Sa réaction au coup reçu passe donc uniquement par le système de danger d'Arma
(claquements, impacts proches), pas par la blessure. Si le verdict V1 conclut « pas d'angle
mort », il est solide (il se réoriente malgré une stimulation appauvrie). S'il conclut
« angle mort durable », il est à confirmer avec un défenseur mortel.

### Ce que le diagnostic a aussi tranché
Le « gel des compteurs à 20 s » observé partout **n'était pas un gel** : c'était la fin du
combat, un des deux hommes étant mort. La simulation dynamique est **innocente**
(`simulationEnabled` = 1 et `dynamicSimulationEnabled` = 0 sur toutes les unités, et les
paires explicitement « dégelées » s'arrêtent exactement comme les autres).
