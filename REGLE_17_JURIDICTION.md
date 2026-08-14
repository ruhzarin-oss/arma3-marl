# Règle 17 — tout instrument déclare sa juridiction dans son schéma de sortie

Amendement de Fable, 14/08/2026. Posé après la **quatrième** occurrence de la même panne.

## Le constat

Quatre fois, le statut d'un instrument a vécu **en prose** au lieu de vivre **dans la donnée** :

| | ce que la prose disait | ce que le flux de travail a fait |
|---|---|---|
| sonde `vue` | (rien — aucun contrôle positif) | lue comme une mesure |
| `alerte_niv` | présent mais jeté | la courbe « juge » = l'alerte effacée |
| segmenteur | « les identifiants repartent à 1 » | 779 accrochages non ventilables |
| `banc_live.py` | *« aucun verdict de concordance sans répétitions »* | pris pour un banc |

Le docstring de `banc_live.py` **savait**. Le flux de travail ne lit pas les docstrings.

## La règle

**Tout instrument déclare sa juridiction dans son schéma de sortie.** Un champ
`statut` sur **chaque ligne émise** :

- `montage` — la ligne prouve que la chaîne tourne. Elle n'est **jamais** citable.
- `banc` — la ligne est admissible dans une lecture.

**Tout agrégateur aval refuse les lignes `montage`** — refus dur, pas avertissement.

> **Un montage ne doit pas POUVOIR produire une ligne citable.**

## Le corollaire, du même mouvement

**Aucune campagne ne part si son réglage n'est pas estampillé sur chaque ligne émise.**
Le segmenteur a mordu trois fois ; à la troisième, ce n'est plus un piège, c'est une règle.

## Le principe

**Le savoir en prose meurt ; le savoir dans le schéma se défend seul.**

Même famille que l'empreinte sha256 du monde ⟨[[accord-sur-zero-nest-pas-accord]]⟩ : ce qui
compte doit être porté par la donnée, pas par la mémoire de celui qui l'a écrite.

## Portée

Tout capteur, tout banc, sandbox et Arma, à compter du 14/08/2026. Complète la règle 16
(contrôle positif obligatoire ; juger l'acte pas l'état).
