# Dépôt — les 20 épisodes du banc live, critères écrits AVANT

Déposé le 14/08/2026, avant lancement. C'est le « banc live rejoué avec le contrat
réparé » que Fable pose comme travail principal — et le préalable à toute citation du
gymnase comme transféré.

Le monde du banc correspond enfin à celui de l'entraînement : **4 contre 4** (le gymnase
entraîne `A=4, D=4`), site apparié (écart de pente 0,006), les 12 colonnes dans leur plage.

## Le dispositif

20 épisodes **indépendants**, chacun avec son propre lancement de serveur. Aucun code
nouveau : la boucle vit dans le lanceur, où elle ne peut pas corrompre la mesure. Chaque
épisode écrit son relevé (`ep_N.npz`) et son journal (`ep_N.txt`).

## CONTRÔLES POSITIFS ⟨règle 16 clause 1⟩

1. **Chaque scène confirmée par le JEU** — `HARMATTAN_SCENE def=4 att=4`, pas par mon
   script. Les épisodes sans confirmation sont écartés et comptés.
2. **Les azimuts de naissance doivent DIFFÉRER entre épisodes.** La scène tire
   `_az = random 360` ; si les 20 épisodes partagent un azimut, je n'ai pas 20 épisodes,
   j'ai 20 copies du même. C'est le contrôle qui manquait quand j'ai comparé deux mondes
   en croyant comparer des camarades.

## Ce qui se lit, et comment

**La prise** — définie par le critère DÉJÀ CODÉ dans le banc, `dmin < 25 m`, pas par un
nouveau seuil inventé aujourd'hui. Référence du gymnase : **59,4 %** sur graine 101.
À n=20, l'intervalle binomial vaut ±22 points : on saura si Arma est du même ordre, pas
mieux.

**Le gel** — un épisode est « figé » s'il émet **une seule action de bout en bout**. Le
gymnase le fait dans **3,1 %** de ses épisodes. Règle déposée :

| épisodes figés sur 20 | lecture |
|---|---|
| **≥ 18** | le taux du gymnase (3,1 %) est rejeté sans discussion. Le gel est RÉEL. |
| **≤ 3** | Arma est compatible avec le gymnase. **Il n'y a jamais eu de gel** — un événement rare vu une fois. |
| **4 à 17** | indécis. On ne conclut pas, et on ne rejoue pas en espérant mieux. |

La bande indécise est là exprès : sans elle, tout résultat serait lisible dans le sens qui
m'arrange.

**Rapportés sans juger** : mètres gagnés, pas survécus, actions distinctes par épisode.

## Ce qui ferait échouer la mesure

- Moins de 15 épisodes valides sur 20 → la taille ne porte plus la lecture, on ne lit pas.
- Azimuts identiques → un seul épisode répété, aucune lecture.
- Une colonne qui ressort de sa plage → le monde a bougé sous la mesure.

## Ce qui n'est PAS jugé ici

La concordance gymnase↔Arma comme **verdict certifié**. À ±22 points, on obtient un ordre
de grandeur, pas une certification. Le 51,1 % / 59,4 % ne devient pas citable comme
transféré au vu de ces 20 épisodes seuls.
