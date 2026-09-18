# Critères pré-enregistrés — choisir la bande de distance de la menace

*18/09/2026, écrit **avant** de lire la fin du banc `BANC-SEUIL-18-09`. Suite des contrôles de
`CONTROLES_MENACE_VISIBLE.md` : la variance de perception sous vraie menace est restée hors de la plage 30–70 %
(0 à 2 épisodes sur 8), parce que les niveaux de menace à un seul type posent la menace à 300–800 m, hors de portée
de la perception de nuit.*

## Ce que le banc mesure

Une menace inerte est posée à une distance fixée, avec ligne de vue contrôlée (les épisodes sans ligne de vue sont
refusés, `banc_refuse`, 3b31348). Tous les hommes la regardent. On note le premier instant où
`menace_percue` atteint 2, c'est-à-dire où la menace entre dans la liste de cibles du **groupe**.

## La règle de choix, écrite d'avance

1. On ne retient qu'une distance ayant **au moins 6 épisodes** avec ligne de vue.
2. Pour chaque distance, on calcule `p(d)` = part des épisodes où la menace est **connue dans les 90 s** — la fenêtre
   d'observation fixée par Younes.
3. **La bande retenue est la distance dont `p(d)` est la plus proche de 50 %**, à condition que `p(d)` soit dans
   **[30 % ; 70 %]**. À égalité, on prend la plus proche du détachement (moins de terrain entre les deux, moins de
   chances de mesurer le relief).
4. Les niveaux de menace à un seul type (4 et 5, `patch_types_proches.py`) posent alors leur menace dans cette bande,
   **la même pour les deux types**, pour que le type ne soit plus confondu avec la distance.

## Falsificateur

« Si **aucune** distance ne donne entre 30 et 70 % de menaces connues dans les 90 s, alors la perception de ce monde
est un interrupteur, pas une échelle : on ne peut pas faire varier la menace perçue au moment de choisir, et la
campagne P2 à types séparés ne part pas. »

Dans ce cas, deux issues, à trancher par Younes : jouer **de jour** (autre mission, incomparable aux mesures d'août),
ou renoncer à la perception de la menace comme variable de la règle, et chercher l'inversion ailleurs.

## Ce qu'on en fait

La bande retenue, et le `p(d)` mesuré, sont écrits dans le verdict du banc avant que la campagne P2 ne soit posée.
Aucune campagne ne part tant que la règle ci-dessus n'a pas désigné une bande.
