# RAPPROCHER LE MONDE D'ENTRAÎNEMENT DE STRATIS — déposé avant tout changement

*12 août 2026. **C'est un changement de MONDE.** Tout ce qui a été entraîné avant devient
partiel — la politique à 53,3 % comprise.*

## LE FAIT MESURÉ, une fois les quatre écarts de définition réparés

| | p01 | médiane | p99 |
|---|---|---|---|
| **Stratis** (403 points, formule du gymnase) | **0,009** | **0,460** | **1,098** |
| **Gymnase** (1024 points) | 0,148 | 0,563 | 1,507 |

**Le gymnase n'est pas seulement 22 % trop raide : son PLANCHER est à 0,148.** Il ne produit
**jamais** de terrain plat, quand Stratis en est couvert — et le banc y joue souvent en plaine.

## LA CAUSE, LUE SUR PIÈCES

`gen_terrain` normalise **chaque** carte à exactement `relief` mètres :
`hm = hm / hm.amax() × relief`. Toutes les cartes ont donc **la même amplitude**. C'est la
normalisation elle-même qui interdit les plaines : elle rend chaque terrain également accidenté.

## LE CHANGEMENT

> **`relief` est tiré PAR ENVIRONNEMENT**, dans la distribution mesurée de Stratis, au lieu
> d'être une constante. La pente étant linéaire en `relief`, reproduire la distribution des
> reliefs reproduit celle des pentes — par construction, pas par réglage.

Les 403 pentes mesurées sur Stratis sont conservées et tirées au sort ; le facteur d'échelle
vient du rapport des médianes, il n'est pas choisi.

## LA PORTE DU CHANGEMENT — écrite avant

> **Le gymnase doit reproduire les trois quantiles de Stratis à ±15 % : p01, médiane, p99.**

⚠️ **±15 %, et pas mieux** : le gymnase reste une carte générée, pas Stratis. Exiger l'égalité
serait exiger la même carte.

## CE QUI FERAIT ÉCHOUER — écrit avant

- **Un quantile hors de ±15 %** → le tirage ne reproduit pas la carte, on cherche pourquoi au
  lieu d'ajuster un coefficient.
- **La politique réentraînée ne passe plus la porte** (battre les deux doctrines, borne > 0) →
  **c'est un résultat, pas un échec** : il voudra dire que les 53,3 % tenaient à un monde
  uniformément accidenté, donc à une béquille. On le dira.
- **Le monde devient trop facile ou trop dur** — aiguille hors de la bande 20-80 % → on
  recalibre l'effectif avant de lire quoi que ce soit ⟨règle de l'aiguille au butoir⟩.

## CE QUI DEVIENT PARTIEL

**La politique `boucle_pol.pt` à 53,3 %**, et toute la lecture qui va avec. Elle a été entraînée
dans un monde uniformément accidenté. Elle n'est pas fausse : elle est **d'un autre monde**.
