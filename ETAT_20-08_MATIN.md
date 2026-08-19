# ÉTAT AU 20/08 AU MATIN — ce qui est fait, ce qui bloque, ce qui attend Younes

## FAIT ET VÉRIFIÉ

- **Le corps est corrigé.** Canal `sv_vz_preserve_10hz` en production (couture + socle),
  gardien de canal posé. Le vol est aboli : 6,8 m → 0,4 m de hauteur en descente.
- **Le critère du canal vivant est validé** sur tirage frais (`356b0fc`) :
  `max` des 8 azimuts ≥ **15,2 m**. 0/60 faux-rouge, 0/60 faux-vert, 0/60 désaccord.
- **Le placeur et T5 sont fusionnés** (socle 5.4.0). Le sélecteur est mort, la ligne
  `GESTE` morte est supprimée, « faux-reçu » a disparu du juge, la batterie est passée
  de six sabotages à cinq (celui de la traverse visait un acte retiré).
- **Arrêt anticipé** : un canal sain coûte 1 à 3 azimuts, un canal mort paie les 8.
- **Contrôle positif du T5 fusionné, dans le prévol réel** : `jambes` → **3 rouges sur 3**,
  message « T5 CANAL MORT : max 0 m sur 8 azimuts (plancher 15,2) ». Code de sortie 0.

## CE QUI BLOQUE — UN SEUL DÉFAUT, ET IL EST ANCIEN

**Le sabotage du `gel` ne rend plus PLANTÉ que 1 fois sur 3.**
Le premier tirage plante correctement à T4. Les deux suivants échouent en 27 s et 5 s
avec des **écarts vides** : un prévol abandonné continue de tourner et son verdict est
lu par le tirage suivant.

Le mécanisme d'écartement existe (`HMT|SOCLE|PREVOL|ABANDONNE`), mais il ne se déclenche
qu'à un **point de contrôle de génération** — et un prévol gelé n'en atteint aucun,
puisque c'est précisément ce que le gel lui fait.

**Piste, non implémentée** : après une rupture de figement, le monde est dans un état
inconnu — le continuer, c'est mesurer sur un monde contaminé. La réparation probable est
de **redémarrer le serveur après un `_fige_break`** plutôt que d'enchaîner. À dériver et
pré-inscrire proprement, pas à rustiner.

⚠️ **Tant que le gel n'est pas réparé, la ligne 4 ne peut pas passer** : elle exige les
cinq tampons verts sur le même hash. **Donc aucune porte.**

## CE QUI ATTEND YOUNES

1. **Le tempo du gymnase.** Il enseigne 6 m/s ; le canal rend ~3,75 m/s en montée. Rendre
   la gravité a réduit l'écart de 1,7× à 1,47× — il **persiste**. Recaler le gymnase veut
   dire réentraîner. Dossier : `DOSSIER_DOCTRINE_TEMPO.md`.
2. **La refonte de la porte.** `quatre.py` est réécrit pour le canal, mais la ligne 1 et la
   ligne 3 n'ont jamais tourné sous cette forme.

## LE DOSSIER DORMANT

Les blocages locaux (un tiers du terrain, réels à 69 % de retour, ni pente ni objets) sont
**laissés en sommeil** avec conditions de réouverture écrites — voir
`EFFET_REEL_INSTRUMENT_BRUYANT.md`. Le dessin fusionné y est robuste par construction.
