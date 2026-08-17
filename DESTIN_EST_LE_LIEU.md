# LE DESTIN DE SESSION EST LE LIEU DU TÉMOIN — trouvé en LISANT le code

17/08/2026. Trouvé par **lecture**, sur suggestion de Younes, après sept sondes causales
infructueuses. Zéro serveur démarré pour ce diagnostic.

## Le mécanisme, dans le code

`bancs/socle/socle.sqf:166-177` — le placeur balaye **24 points FIXES** autour du premier
attaquant de la scène :

```sqf
for "_k" from 0 to 23 do {
    private _a = _k * 15; private _r = 250 + (_k mod 4) * 40;
    private _c = [(getPosATL _ref select 0) + _r * sin _a, ...];
    ...
    if ((getTerrainHeightASL _c) > 3 && _s < _meilleure) then { _meilleure = _s; _pt = ... };
    if (_meilleure < 0.10) exitWith {};
};
```

**Aucun aléa.** Angles multiples de 15°, rayons 250/290/330/370 m. La recherche ne dépend que
de `_ref` — un homme né **une seule fois**, à la naissance de la scène.

> **Le lieu du témoin est donc FIXÉ PAR SESSION. C'est la structure exacte du destin.**

## La preuve dans les journaux

43 lieux distincts pour 72 tirages sur 12 sessions — et dans chaque session le même point
revient, aux quelques mètres que les hommes parcourent près :

| session | lieu | verts /6 |
|---|---|---|
| 2 | `4776,5196` répété 5× | **6** |
| 9 | `4445,6138` répété 5× | **6** |
| 4 | `4989,5877` répété 5× | **0** |
| 12 | `4716,5207` répété 5× | **0** |

## ⚠️ CE QUE ÇA N'EXPLIQUE PAS ENCORE — la pente NE SÉPARE PAS

| critère | vivantes | mortes | verdict |
|---|---|---|---|
| pente au lieu | 0,040 – 0,340 | 0,010 – 0,350 | **chevauchent** |
| meilleure pente | 0,160 – 0,280 | 0,130 – 0,280 | **chevauchent** |
| hauteur | 58 – 150 | 40 – 208 | **chevauchent** |

La session 8 a une pente de **0,01** — parfaitement plate — et meurt 5 fois sur 6.
La session 9 a **0,04** et vit 6 fois sur 6.

> **Le placeur choisit sur la PENTE, et la pente ne prédit RIEN.** Ce qui rend un lieu mauvais
> est ailleurs : obstacles, encombrement, bâtiments, végétation — tout ce que la pente moyenne
> d'un carré de 60 m ne voit pas.

## La contrainte de Fable est SATISFAITE : ça prédit quel canal meurt

**Session 1 : 4 échecs T7, ZÉRO T5.** Le lieu permettait de marcher mais pas de voir ni de
tirer. Les autres sessions mortes meurent par T5. Un lieu encombré casse les jambes ; un lieu
sans ligne de vue casse le feu. **Une même cause, deux canaux, selon le lieu.**

C'était l'exigence posée : *« une cause recevable doit prédire QUEL canal meurt. »*

## Ce qui est ACQUIS et ce qui reste

**ACQUIS** — le destin de session est **le lieu**, et le lieu est déterminé sans aléa par la
naissance de la scène. Cela explique d'un coup : l'unité (la session), le caractère quasi
binaire, le fait que le temps ne guérisse pas, l'absence de lien avec la charge, l'heure,
l'ordre, le pont — et le choix du canal.

**RESTE** — **ce qui rend un lieu mauvais.** Ni la pente, ni la hauteur. Non identifié.

## Le test qui trancherait, et il est bon marché

**Rejouer les MÊMES lieux.** Prendre trois lieux morts (`4989,5877` · `4716,5207` ·
`4210,5369`) et deux lieux vivants (`4776,5196` · `4445,6138`), y poser le témoin de force
dans des sessions neuves, et voir si **le destin suit le lieu**.

- **le destin suit le lieu** → la cause est établie, et le placeur est le fautif ;
- **le destin ne suit pas** → le lieu n'est qu'un corrélat, et l'acquis ci-dessus tombe.

Signature à écrire avant, `n` calculable puisque l'unité est connue. **Non lancé.**

## Le correctif qui se dessine, à ne pas appliquer avant le test

Le placeur doit juger un lieu sur ce que le témoin doit **y faire** — parcourir 24 m et voir
à 40 m — et non sur une pente moyenne. C'est la règle 6 : vérifier la propriété que le
mécanisme EMPLOIE. Un test de traversabilité et un test de ligne de vue, tous deux avec
contrôle positif.
