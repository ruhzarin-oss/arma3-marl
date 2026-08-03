# CRITÈRES FIGÉS — RÉPLICATION DIMENSIONNÉE DU FRONTAL SILENCIEUX (avant les données)

Figés le 2026-07-28, AVANT tout run.

## POURQUOI UNE RÉPLICATION
Le pilote à n=6 (`45f3851a98d62c57`) a rendu : frontal bruyant 33 % de prise, frontal
silencieux 67 %, envelop bruyant 83 %. Effet fort, direction prédite — mais 6 opérations par
bras ne tranchent pas, et le seuil d'abandons que j'avais fixé (≤25 %) était **mal calibré** :
un effet qui divise par deux les abandons atterrit à 33 % et échoue. Le pilote reste consigné
tel quel ; il sert ici à dimensionner.

## DISPOSITIF
A=12 vs D=8 (la bande discriminante), Altis/Pyrgos, 120 pas, **18 opérations par bras**,
trois bras :
- **frontal bruyant** (`fire=1`, l'existant)
- **frontal silencieux** (`--silencieux`)
- **envelop bruyant** (l'existant)

L'ordre d'assaut final reste DÉSACTIVÉ dans les trois bras.

## COMPARAISON PRIMAIRE — décidée d'avance
**Prise du frontal silencieux − prise du frontal bruyant.**
- **≥ +20 points** → l'ordre de feu est bien ce qui figeait le frontal. Confirmé.
- **entre 0 et +20** → effet réel mais mineur ; l'ordre de feu n'est pas l'explication principale.
- **≤ 0** → le pilote était du bruit. L'hypothèse tombe.

## COMPARAISON SECONDAIRE — lue seulement si la primaire est ≥ +20
**Prise de l'envelop bruyant − prise du frontal silencieux.**
- **≤ +10 points** → **l'avantage du flanc sur ce banc est un artefact de l'ordre de feu.**
  Tous les A/B frontal-vs-débordement du banc sont à relire, FIBUA du 23/07 compris.
- **> +10 points** → le flanc garde un avantage propre, au-delà du mécanisme de feu.

## GARDE
Un bras dont plus de **40 %** des opérations s'enlisent est NON MESURÉ. Seuil relevé de 25 à
40 % en connaissance de cause : à ce rapport de forces, l'enlisement fait partie du phénomène
mesuré, et une barre trop basse écarterait des bras qui portent le signal (leçon du pilote).

## INTERDICTIONS
Pas de retouche des seuils, des effectifs, du nombre d'opérations ni des paramètres de doctrine
après un chiffre. Aucun troisième réglage du mécanisme de feu dans ce chantier.
