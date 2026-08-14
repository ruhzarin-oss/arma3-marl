# Acte de décès — la sonde `vue` du canal BALLE

Posée le 13/08/2026 au soir. **Déclarée morte le 14/08/2026**, sous la règle 16 clause 1
qui venait d'être écrite.

## Ce qu'elle prétendait mesurer

Dans le canal `HMT|AP|BALLE`, pour chaque appui à chaque réémission d'ordre :

```sqf
private _v = [objNull, "VIEW"] checkVisibility [eyePos _u, getPosASL _c];
```

la visibilité moteur entre l'œil du tireur et le muret visé.

## Comment elle a échoué

Elle a lu **0 sur les six terrains** — y compris le terrain 0, **où 347 coups partaient**.
Un capteur qui affiche zéro là où le phénomène est massif ne dit rien sur les cinq
autres. J'ai pourtant failli m'en servir pour conclure que le moteur refusait l'ordre
sur cinq terrains.

## Pourquoi elle a échoué

Deux causes possibles, non départagées, et **on ne les départage pas** : la sonde ne sert
plus à rien depuis que l'essai A a montré que l'ordre ne déclenche aucun feu.

1. `getPosASL _c` sur un muret rend son **point d'origine**, pas la surface visée ;
   la ligne œil→origine traverse le muret lui-même et rend 0.
2. `[objNull, "VIEW"]` avec un `objNull` comme ignorant peut ne pas exclure le tireur.

Dans les deux cas le défaut est le même que les cinq autres du 14/08 : **la sonde
interroge une abstraction commode au lieu de l'acte que le mécanisme émet.** Le tir est
un événement (`Fired`) ; j'ai interrogé une géométrie.

## Statut

**Retirée du chemin de décision.** Aucune lecture passée ou future de ce champ n'est
citable. Le champ reste écrit dans le journal — l'effacer serait effacer la trace de
l'erreur — mais il porte désormais cet acte.

## Ce qu'elle coûte, pour mémoire

Une soirée d'analyse orientée dans une mauvaise direction, et le début d'un troisième
faux diagnostic. Elle aurait été rejetée en cinq minutes par un contrôle positif — la
porte que Fable vient de rendre obligatoire.
