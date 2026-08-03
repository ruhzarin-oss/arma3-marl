# CRITÈRES — LE MODÈLE D'ALERTE DANS LE GYMNASE (figés avant la première ligne)

Écrits le 2026-07-30. Modèle **mesuré sur Arma**, pas inventé. Arbitrage : Younes.

## LE MODÈLE MESURÉ
Instrument validé par un contrôle positif : à 30 m, debout et armé, la connaissance monte à
4,00 en moins de dix secondes et les défenseurs tirent 228 fois par minute.

| grandeur | mesure |
|---|---|
| détection passive, debout et armé | **4,00 à 30 m · 1,72 à 60 m · 0,00 à ≥100 m** |
| trois tirs depuis l'invisibilité (100 m) | **+1,50**, sur **tout le groupe**, en **3 secondes** |
| feu soutenu | saturation à **4,00 en 10 s** |
| riposte | commence **6 à 10 s** après le premier coup |
| mémoire | **aucune décroissance en 300 s** |

Cinq tentatives ont été invalidées avant d'obtenir ces chiffres, toutes par ma faute
d'instrumentation. La recette qui marche vient de `mesurer_suppression.py` : mode de tir RED,
`disableAI AUTOTARGET`, `setVehicleAmmo 1`, puis `reveal` + `doTarget` + `doFire` répétés — et
la distance de 100 m, pas 150.

## CE QUE ÇA REMPLACE
Le gymnase modélise aujourd'hui la visibilité par un **cône de caméra** : un défenseur voit à
l'infini dans son arc, et rien du tout en dehors. Contourner rend donc **littéralement
invisible**, ce qui explique pourquoi le débordement y réussit 96 % du temps quand le juge en
donne 0 %.

Arma dit l'inverse : le défenseur voit à **60 mètres dans toutes les directions**, et au-delà
de 100 m il ne voit rien même de face.

## L'IMPLANTATION — trois pièces
1. **Détection par la DISTANCE, pas par l'arc.** Un attaquant est détecté selon son rayon :
   pleine connaissance sous 30 m, moitié à 60 m, nulle au-delà de 100 m. L'arc de tir reste
   pour décider *qui peut tirer*, il ne décide plus *qui voit*.
2. **Un compteur d'alerte unique par groupe défenseur**, plafond 4, **jamais décroissant**.
   Il monte par la détection passive et par le feu de l'attaquant.
3. **Le feu de l'attaquant coûte 0,5 par tir** (1,50 pour trois), appliqué à tout le groupe,
   quelle que soit la distance.

**Conséquence attendue, et c'est le but** : le contournement cesse d'être gratuit. Un attaquant
qui passe à 60 m du bout de la ligne se fait connaître, même hors du cône.

## LE CRITÈRE D'ACCEPTATION — le gymnase doit PRÉDIRE L'ÉCHEC
À A=4 contre D=8, débordement, 1024 épisodes : **taux de prise dans [0 ; 8,8 %]**, l'intervalle
de Wilson du juge (0 prise sur 40 opérations).

Deux garde-fous :
- **ne pas viser zéro** : à A=24 le gymnase doit encore rendre quelque chose (> 5 %), sinon il
  est devenu impossible au lieu d'être devenu difficile ;
- **l'ordre des doctrines doit être préservé** : le débordement devant, les bonds alternés
  derniers. Une inversion signifie qu'on a cassé autre chose que ce qu'on voulait réparer.

## INTERDITS
- Ne pas toucher aux courbes de toucher et de suppression mesurées en juillet. Elles sont
  justes ; c'était leur assemblage qui mentait.
- Défaut à zéro : sans le drapeau, le comportement historique est inchangé et l'étalon reste
  reproductible à l'identique.
- Aucune revendication tirée du gymnase ne reprend vie avant que le critère d'acceptation soit
  franchi. Les 72 % de l'agent restent gelés.
