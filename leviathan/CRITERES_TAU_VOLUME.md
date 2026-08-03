# CRITÈRES — LE SURSIS DÉPEND-IL DU VOLUME DE FEU REÇU ?

Figés dans la nuit du 27 au 28/07/2026, **avant** le premier relevé.

## La question, et pourquoi elle est préenregistrée

Mesuré hier (`CRITERES_ARC_CONTACT.md`, empreinte 82f3dad52683dd8f) : un défenseur orienté
au nord riposte à **100 %** quel que soit l'angle, mais **4,1 s plus tard** quand ça vient
de son dos — et **sans jamais pivoter**. L'angle mort est un **sursis**, pas un abri.

La question de cette nuit est la jonction entre l'arc et la suppression :

> **le sursis s'allonge-t-il quand le volume de feu reçu augmente ?**

Si oui, la suppression possède déjà un mécanisme **mesuré côté défenseur** : arroser
quelqu'un, ce n'est pas seulement le faire tirer moins, c'est **retarder le moment où il
vous trouve**. Et l'élément d'appui cesse d'être du folklore : il maintient le sursis
ouvert pour celui qui contourne.

Si non, l'arc et la suppression sont deux mécanismes indépendants, et il faudra mesurer la
suppression pour elle-même.

## Dispositif

Un défenseur, orienté **nord**, attaqué **dans le dos (180°)**. Deux conditions, seule la
quantité de feu change :

| condition | tireurs | dispersion |
|---|---|---|
| **UN** | 1 attaquant à 60 m | — |
| **QUATRE** | 4 attaquants à 60 m | étalés sur 24 m |

| élément | valeur |
|---|---|
| défenseur | `O_Soldier_F`, `setDir 0`, `disableAI PATH`, COMBAT/RED, skill 0,5, **`allowDamage false`** |
| attaquants | `B_Soldier_F`, `disableAI PATH/COVER/SUPPRESSION/AUTOCOMBAT`, **`HandleDamage → 0`**, feu forcé toutes les 2 s |
| fenêtre | 60 s |
| cellules | 4 par répétition, **certifiées terre ferme**, ≥ 700 m d'écart |
| répétitions | 6 → 12 cellules par condition |
| rotation | l'affectation condition→cellule tourne : la condition ne doit pas être confondue avec l'emplacement |

**Les montages d'invulnérabilité sont ceux qui ont été PROUVÉS hier**, pas ceux qui
semblaient raisonnables : `HandleDamage → min(dégât, 0,55)` **ne protège pas** (défenseur
mort en 10 s) ; `setVehicleAmmo 1` périodique **éteint le tir** (0 balle sur 90 s).
Ni l'un ni l'autre n'est utilisé ici.

Corrections d'instrument obligatoires, les deux : **filtre par source** (`_this select 3`)
et **déduplication par tick** (0,05 s).

## Canari

Chaque condition doit produire **au moins 6 cellules sur 12 où le défenseur riposte**.
En dessous, on ne compare rien : on n'aurait pas mesuré un sursis, on aurait mesuré un
silence.

## Seuils, écrits avant

`τ(c)` = médiane, sur les cellules retenues de la condition c, du délai entre le premier
coup tiré par un attaquant et le premier coup tiré par le défenseur. Un défenseur qui ne
riposte jamais compte pour 60 s.

- **LE VOLUME PROLONGE LE SURSIS** : `τ(QUATRE) − τ(UN) ≥ +2,0 s`.
  → la suppression a un mécanisme mesuré côté défenseur ; le sandbox devra faire dépendre
  le sursis du feu reçu.
- **LE VOLUME NE CHANGE RIEN** : `|τ(QUATRE) − τ(UN)| < 1,0 s`.
  → arc et suppression sont indépendants. C'est un résultat, pas un échec.
- **LE VOLUME RACCOURCIT LE SURSIS** : `τ(QUATRE) − τ(UN) ≤ −2,0 s`.
  → plus on tire, plus vite on est trouvé. Contre-intuitif, donc écrit d'avance pour ne
  pas être escamoté.
- **NON CONCLUANT** : entre 1,0 et 2,0 s en valeur absolue.

## Sentinelles (logguées, sans seuil)
- taux de riposte par condition ;
- impacts du défenseur sur les attaquants (filtrés par source) ;
- `knowsAbout` maximal atteint par le défenseur.

## Réserve à porter au verdict
Le défenseur est en `allowDamage false` : il n'encaisse pas. Sa réaction passe par le
système de danger d'Arma, pas par la blessure. Cela biaise τ **vers le haut** dans les deux
conditions — donc la **différence** entre conditions reste lisible, c'est elle qu'on juge.

## Interdits
1. Changer la distance, le nombre de tireurs ou la fenêtre après avoir vu les chiffres.
2. Conclure si le canari d'une des deux conditions échoue.
