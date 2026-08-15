# Dépôt — l'exécuteur de FEU FORCÉ, critères AVANT mesure

Déposé le 15/08/2026, sur le plan de Fable après le recadrage de Younes.

## Pourquoi

`commandSuppressiveFire` **oriente la visée sans déclencher le feu** — mesuré ce matin,
94 % du feu part sans ordre, 3 paires sur 3. Fable : *« arrête de demander poliment à
l'IA. Le déclencheur, c'est toi. »*

L'appui est le verbe qui manque à l'étage soldat, et l'indice le plus fort du dossier le
désigne : **A3C tue 3,2× plus à positions égales** (p=0,011, géométrie non séparable
p=0,065) — *« le gain est dans le QUAND du feu, pas dans le OÙ des positions »*.

## QUELLE DÉCISION CETTE MESURE FAIT BASCULER ⟨garde-fou⟩

Si la boucle forcée tire **sur ordre**, l'appui devient un verbe utilisable et l'étage
soldat peut être scripté puis appris. Si elle échoue, **il n'y a pas d'appui sur Arma** et
tout le plan de Fable perd son verbe central.

## L'exécuteur

```sqf
HMT_APPUYER = {
    params ["_u", "_pos", ["_duree", 5]];
    private _t0 = time;
    while { alive _u && time - _t0 < _duree } do {
        _u setDir (_u getDir _pos);
        _u doWatch _pos;
        _u forceWeaponFire [currentWeapon _u, currentMuzzle _u];
        sleep 0.33;                       // 3 coups par seconde
    };
    _u doWatch objNull;
};
```

## Le dispositif — fenêtres ALTERNÉES, 5 s d'ordre / 5 s de silence

Un tireur à **150 m**, une cible derrière un couvert. Dix cycles par bras.
C'est la logique de l'essai A appliquée à un seul homme : **le silence mesure ce qui part
sans qu'on demande rien.**

Deux bras appariés :
- **A — `commandSuppressiveFire`**, réémis toutes les 4 s (ce que le banc fait aujourd'hui) ;
- **B — la boucle forcée** ci-dessus.

## CONTRÔLES POSITIFS ⟨règle 16⟩

1. **Contrôle positif de l'exécuteur** : la même boucle sur une cible **à découvert** doit
   la tuer. Un exécuteur qui ne tue pas une cible offerte ne tire pas vraiment.
2. **Le silence doit être silencieux** : moins de 20 % des coups d'un bras tombent dans ses
   fenêtres de silence. Sinon le tireur tire par contact et la mesure ne sépare rien —
   c'est exactement la panne de l'essai A.

## LA PORTE, écrite avant

**Le bras B doit tirer au moins 80 % de ses balles DANS ses fenêtres d'ordre.**

| part des balles sur ordre, bras B | lecture |
|---|---|
| **≥ 80 %** | l'exécuteur MORD. L'appui est un verbe utilisable. |
| **< 50 %** | l'exécuteur est MORT, comme `commandSuppressiveFire`. Pas d'appui sur Arma. |
| **50 à 80 %** | INDÉCIS, on ne conclut pas et on ne rejoue pas. |

## Rapporté, non jugé

- `getSuppression` de la cible ≥ 0,5 tenu 4 s ;
- les tirs de riposte de la cible pendant la fenêtre.

Ce sont les effets espérés ; en faire des portes reviendrait à déclarer bon ce qui donne
ce que j'espère.

## Ce qui n'est PAS promis

Un exécuteur qui mord ne dit pas que l'appui **paie**. Le saut de 12 % à 50 % se juge
ailleurs — sur la paire *appuyer + bond* contre *bond seul*, et c'est une autre mesure.
