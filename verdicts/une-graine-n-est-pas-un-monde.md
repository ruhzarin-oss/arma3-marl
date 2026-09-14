# Une graine n'est pas un monde — cinq graines juges sur huit étaient déjà brûlées

*Verdict du 14/09/2026. Septième faute d'instrument de la semaine, trouvée par Fable, vérifiée sur
28 géométries récoltées. C'est la plus insidieuse : elle ne casse rien visiblement, elle fabrique une
fausse généralisation.*

## Le mécanisme

`CHACAL_fnc_rnd` est un générateur de Lehmer — `x → 75x + 74 mod 65537`. C'est un **cycle unique de
65 536 états**. Deux graines n'y sont pas deux mondes : ce sont deux **points de départ sur le même
anneau**.

Et le tirage du monde consomme énormément : plus de deux mille tirages par essai de génération — 440
pour la recherche de terrain plat, 1 000 pour la crête, 440 pour la vue. Deux graines distantes de
quelques milliers d'états voient donc leurs marches **se rejoindre**, et rendent le même site.

## La mesure

| Sites partagés à la virgule près | Graines |
|---|---|
| [12113,6 ; 19333,8] | **3754** et 108 |
| [7991,6 ; 19546,9] | **5701** et 106 |
| [12678,7 ; 15760,4] | 109 et 115 |

Et par proximité, sous 1 km :

```
415 m entre 3664 et 5701      660 m entre 101 et 3940
825 m entre 109 et 3694       303 m entre 103 et 113
820 m entre 103 et 111        825 m entre 115 et 3694
```

**Cinq des huit graines juges gelées le matin même sont brûlées** : 3664, 3694, 3754, 3940, 5701.
Il ne reste que 3183, 5625 et 7579.

## Pourquoi c'est grave

Les graines juges devaient garantir qu'un agent est mesuré sur des sites **jamais vus**. Avec cinq
d'entre elles identiques ou voisines de sites d'entraînement, l'agent aurait été déclaré généralisant
alors qu'il rejouait ses propres sites.

C'est exactement la cicatrice que le gel devait éviter : une politique du projet avait mémorisé son
site et rendait 90,9 % sur ses graines contre 93 % à la porte. Le gel par numéro n'aurait rien
empêché — il aurait juste rendu la mémorisation invisible.

Et le corpus lui-même est touché : 109 et 115 sont le même monde. Je les aurais comptés comme deux
sites indépendants dans une validation croisée.

## Ma faute, précisément

J'ai pris soin de tirer les huit graines par empreinte cryptographique, de les documenter, de les
commiter avant tout entraînement, et d'exclure toute collision **de numéro** en les prenant au-dessus
de mille. Toute cette précaution portait sur la mauvaise grandeur.

**L'identité d'un monde est son site, pas son numéro.**

## Le remède

1. **Geler des mondes, pas des graines.** On récolte large — 96 graines en mode géométrie seule,
   quarante secondes chacune — on dédoublonne **par coordonnées de site**, et on retient des mondes
   séparés d'au moins 1 km de tout site déjà joué ou retenu.
2. **Le fichier gelé porte les deux** : la graine qui produit le monde, et les coordonnées du site
   qui l'identifient. Une collision future se verra.
3. **Le script de sélection est commité** avec le fichier, ce qui manquait la première fois.

## Ce que ce verdict ne dit pas

Le générateur lui-même reste à changer — un cycle de 65 536 états est trop court pour un tirage qui
en consomme deux mille. Mais en changer maintenant changerait **tous les mondes**, donc la référence
mesurée aujourd'hui. On dédoublonne d'abord par la géométrie ; on changera de générateur à la
prochaine génération de mondes, et on le dira.
