# LE FALSIFICATEUR A TIRÉ — le critère du placeur n'est pas écrit

**19/08/2026, 21 h 55.** Spec `PREDICTIONS_CORPUS_PLAT.md` (`ed0501e`) + amendement de
sélection (`82594c2`). Journal `serverVUEPLAT.out`.

## LA MESURE

Corpus **construit sur le terrain seul** : décile le plus plat de Stratis (dénivelé
≤ 8,1 m sur ±15 m, 10ᵉ centile mesuré sur 3 000 points), zéro objet à 10 m.
**50 lieux trouvés en 1 779 tirages** (2,8 % du terrain). Puis les 8 azimuts, puis le
sabotage des jambes sur les mêmes 50.

**Minima sur 8 azimuts :**
```
0,5  1  1  2  2  2  2  2  3  3  4  4  4  5  7  8  9  9
10 10 10 10 11 11 11 11 12 12 12 12 12 12 13 13 13 13 13 13 13 13 13
14 14 14 14 14 15 15 15 16,2
```
min 0,5 · **Q1 4,6** · méd 11,4 · **Q3 13,1** · max 16,2

## LES PRÉDICTIONS

| n° | prédiction | obtenu | |
|---|---|---|---|
| P1 | ≥ 90 % des lieux plats ont min ≥ 10 m | **58 %** | ÉCHOUE |
| **P2** | **interquartile < 4 m — FALSIFICATEUR** | **8,5 m** | **ÉCHOUE** |
| P3 | jambes coupées : 0 reçu | 49/50 | ÉCHOUE¹ |

¹ conséquence de P2 : le seuil dérivé s'effondre à 1 m, sous le tassement naturel d'un
homme reposé. Ce n'est pas un fait indépendant.

> **⛔ P2 EST LE FALSIFICATEUR ÉCRIT, ET IL A TIRÉ.**
> Des lieux choisis dans le **décile le plus plat** de Stratis, sans un objet à 10 m,
> s'étalent de 0,5 à 16,2 m. **La platitude et le dégagement ne déterminent pas le
> blocage.** Le « minimum sur 8 azimuts » n'est pas dérivable sur ce corpus.

## LE DÉFAUT, ET IL EST DANS MA SPÉCIFICATION

**La fenêtre de sélection est plus petite que le geste qu'elle prétend garantir.**
J'ai vérifié la platitude sur **±15 m** et le dégagement à **10 m** — l'homme, lui,
parcourt jusqu'à **22 m**. Il sort de la zone inspectée et entre dans du terrain que la
sélection n'a **jamais regardé**. Un corpus « dégagé » qui ne l'est que sur les dix
premiers mètres ne dit rien des douze suivants.

⚠️ Cliquet : *la fenêtre d'un critère de terrain doit couvrir la course qu'il certifie.*
C'est la même faute de dimensionnement que les minuteurs de lot — un chiffre choisi sans
le rapporter au coût réel du mécanisme.

## CE QUE LA SOIRÉE ÉTABLIT QUAND MÊME

- **Un tiers du terrain libre bloque un homme dans au moins une direction sur huit**
  (19/60 au tirage libre) — le mode d'échec est fréquent.
- **Stratis est raide** : dénivelé médian **12,8 m sur ±15 m** ; le 5ᵉ centile est 6,7 m.
  Mon premier seuil de « plat » (3 m) était sous le 5ᵉ centile : 1 lieu sur 6 000.
- **La mesure parallèle est bon marché** : 50 hommes, 8 azimuts, 48-50 FPS, ~50 s.
  Elle servira de routine quelle que soit la grandeur retenue.
- **Le sabotage des jambes refuse tout** dès que le seuil est réaliste (0/60 à 6 m).

## CE QU'IL FAUT, ET QUI SERA PRÉ-ENREGISTRÉ SÉPARÉMENT

La sélection doit inspecter **le corridor réellement parcouru** : pour chaque azimut, le
terrain et les objets **le long des 25 m** que l'homme couvrira, pas un disque de 10 m
autour du départ. C'est une spécification neuve, à écrire avant mesure — **pas un
troisième rustinage de celle-ci**.

## ÉTAT

Bloc C **éteint**. **Aucune porte.** Le placeur n'a **pas** de critère valide.
Trois tentatives de dérivation ce soir, trois arrêts déclarés — et aucun chiffre rond posé.
