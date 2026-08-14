# Rétractation — « les hommes sont 2,3× plus serrés » est FAUX, et le banc n'est pas le monde d'entraînement

Déposé le 14/08/2026. **Deux choses tombent, une bien plus grave que l'autre.**

## 1. Mon chiffre était un artefact de mon propre regroupement

J'ai mesuré l'étalement entre camarades en découpant les observations du gymnase en
**paquets de huit**. Le gymnase a **quatre attaquants** : `MONDE_ARMA` ne fixe ni `A` ni
`D`, donc les valeurs par défaut `A=4, D=4` s'appliquent. Vérifié :

```
env reel : A=4 attaquants · D=4 defenseurs
apx du 1er env : [70.0, 76.0, 70.0, 76.0]
apy du 1er env : [147.5, 153.5, 159.5, 165.5]
```

Chaque « groupe de huit » mélangeait donc **deux environnements**, nés à deux azimuts
aléatoires sans rapport. L'écart-type mesuré n'était pas celui entre camarades, c'était
celui entre deux mondes.

**Le « 2,3 fois plus serrés » (0,160 contre 0,069) est VOID.** Les vrais offsets du gymnase
donnent 3 m d'écart-type en x et 6,7 m en y, soit 0,015 et 0,034 une fois normalisés — donc
**moins** que les 0,036 et 0,054 mesurés sur Arma. Les hommes du banc sont plus étalés que
ceux du gymnase, pas moins. **Inversion complète.**

La greffe de naissance posée aujourd'hui reproduit désormais la formule du gymnase à
l'identique. Elle est correcte et sans dommage, mais **elle répondait à un problème qui
n'existait pas**.

## 2. Le grave : le banc ne teste pas le monde d'entraînement

`banc_live.py` déclare dans son docstring :

> *« le monde d'entraînement : 13 défenseurs, 8 attaquants, 200 m. On le reproduit. »*

**C'est faux.** Le gymnase entraîne **4 contre 4**. Le banc joue **8 contre 13**.

La politique n'a jamais rencontré treize défenseurs. Elle décide par homme, donc huit
attaquants au lieu de quatre ne la gêne pas architecturalement — mais **tripler les
défenseurs triple la menace**, écrase `nd` (distance au plus proche ennemi) vers le bas,
et explique sans mystère que les huit hommes meurent en quatorze à dix-sept pas.

Le 51,1 % du gymnase et le 0 % du banc **n'ont jamais mesuré le même monde.**

## 3. Ce que ça remet en cause, et ce que ça ne remet pas

Tient toujours : le changement de site (les marges sont rentrées, 5 colonnes hors plage →
0), le contrôle positif de la politique (8 actions sur 10 au gymnase), la fidélité de la
plomberie (100 % vif = rejeu), et le fait qu'Arma tombe dans la distribution conjointe.

Tombe : le « 2,3× plus serrés », et l'idée que la naissance était la faute.

## 4. La leçon, et c'est la même que ce matin

**J'ai comparé deux grandeurs en supposant qu'elles portaient le même nombre d'hommes.**
C'est la septième fois aujourd'hui qu'un chiffre porte le bon nom et la mauvaise chose —
après `slope`, `los`, `dcover`, `disableAI PATH`, `HMT_PEUT_TIRER` et la sonde `vue`.

La règle 16 clause 1 aurait dû l'attraper : **un contrôle positif sur mon propre
regroupement** — vérifier que les hommes d'un même groupe partagent bien un azimut de
naissance — l'aurait montré en une ligne.

## 5. Ce qu'il faut faire

Rendre le banc identique au gymnase : **4 attaquants contre 4 défenseurs**, ou réentraîner
la politique à 8 contre 13. Tant que les deux mondes diffèrent d'un facteur trois sur la
menace, **aucune comparaison ne veut rien dire.**
