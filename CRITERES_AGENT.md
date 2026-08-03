# Agent à répertoire ouvert — seuils figés AVANT le lancement

*03/08/2026, avant tout entraînement. Aucun chiffre de ce document n'est modifiable après
lecture des résultats.* ⟨règle payée quatre fois le 31/07⟩

## Ce qu'on cherche

Un agent qui reçoit tout ce qu'on a capturé et qui **découvre lui-même** quoi en faire —
et non un optimiseur à un paramètre. Les trois versions précédentes ont échoué, et la
quatrième a réussi en réduisant le problème à un seul angle. C'est ce rétrécissement qu'on
corrige ici.

## L'ADVERSAIRE À BATTRE — chiffré avant

v4, l'agent qui ne choisit qu'un axe d'approche :
- **93 %** d'exposition en moins que l'axe moyen
- **94 %** de ce qu'un choix d'axe parfait obtiendrait

**La marge disponible est donc de six points au mieux sur ce terrain.**
⟨Fable : « un gain de un ou deux points est un vrai résultat, et un gain nul est un résultat
légitime — pas une invitation à retourner les données jusqu'à trouver mieux »⟩

Une réserve honnête : le plafond de 94 % est celui du **choix d'axe en ligne droite**. Un agent
qui peut se coucher ou s'arrêter peut en principe descendre plus bas. Si ce n'est pas le cas,
c'est que le répertoire n'apporte rien — et c'est un résultat.

## LES SEUILS D'ÉCHEC, chiffrés

| # | test | ÉCHEC si |
|---|---|---|
| 1 | arrivée | l'agent arrive moins souvent que v4 de plus de 2 points |
| 2 | exposition | il ne bat pas v4 (93 %) — égalité comptée comme échec du répertoire |
| 3 | contrôle des regards au hasard | son avantage sur l'axe moyen ne perd pas au moins la moitié |
| 4 | **ablation du répertoire** | geler posture et allure (debout + course) coûte **moins de 2 points** d'exposition relative |
| 5 | **corrélation au contexte** | l'usage de « couché » n'est pas corrélé à une exposition élevée (corrélation < 0,15) |
| 6 | sensibilité au tarif | la tactique ne survit pas aux trois coefficients 1,4 · 1,75 · 2,1 |
| 7 | exposition par mètre gagné | pire que v4 |
| 8 | temps de mission | plus de 2× celui de v4 (un agent qui rampe vingt minutes ne vaut rien) |

**Le test 4 est celui qui répond à la demande de Younes.** Si geler le répertoire ne coûte
rien, l'agent n'a pas découvert son répertoire : il a appris à marcher.

## CE QUE LE SIMULATEUR MODÉLISE — et sur quoi c'est calibré

| effet | valeur | source |
|---|---|---|
| être dans le champ ennemi | ×1,75 sur le risque | sonde 3, 563 000 observations |
| pente avec la distance | +45 % à 80 m → +84 % à 300 m | sonde 3 |
| se coucher | risque ÷ 1,4 | courbe n°1 mesurée sur Arma en juillet |
| se coucher | vitesse ÷ 3 | choix de conception, NON mesuré — déclaré |
| courir | vitesse × 1,5, **détection inchangée** | la détection est insensible au mouvement ⟨mesuré⟩ |

**Aveu à porter au rapport :** rien dans nos mesures ne pénalise la course. L'agent choisira
donc probablement de courir en permanence, et **ce sera un résultat, pas un échec** — cela
dira que dans ce monde l'allure n'a pas d'arbitrage. Inventer un malus pour rendre le choix
intéressant reviendrait à fabriquer le résultat.

## LE PIÈGE CENTRAL, écrit d'avance

**Ce simulateur est le nôtre. L'agent optimisera NOS règles, pas le monde.**
⟨juillet : 96 % de réussite en sandbox, 0/38 dans Arma⟩

**Aucun verdict ne sort de ce run.** Sandbox = gymnase, Arma = certificateur.
Surveillance explicite de l'exploitation du simulateur : discrétisation du cône de vision,
pas de temps, bord de carte, immobilité rentable.

## Traçabilité

Chaque rapport porte : graine, taille de lot, version du simulateur, empreinte du corpus de
configurations, et l'écart entre les trois graines — **jamais la meilleure seule**.
