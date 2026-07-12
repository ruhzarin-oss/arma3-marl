# PROGRESSION — Répertoire des agents (A BOUCLÉ, 30/06)

## ✅ RÉPERTOIRE COMPLET (~26 briques, écart voyant/aveugle)
| Catégorie | Briques (écart) |
|---|---|
| Réflexe | R1 +54 · R2/R3 +19 · voyage · suppression +4 |
| Tactique | flanc +54 · soutien +78 · bounding 96% · formations |
| Rôles | médic +69 · MG +67 · AT +38 · marksman2 +24 · grenadier +22 · grenade +20 |
| Équipement | mines +66 · fumigène · (sapeur = doublon mines) |
| Contexte | nuit/NVG +87 · soin +83 |
| Team | ratissage +74 · défense +75 · embuscade +53 · récup +45 · conduite +34 · CQB +24 · mortier +12 |
| Rework | **B6 repli CRACKÉ 100%** (+2, la marée fuit via la force) · marksman |
| 🏆 Orchestration | **+91 sur features Arma RÉELLES** (orchestration_arma_voyant.pt, déployable) |
| ⚔️ Co-évolution F | **+59 robustesse pire-cas · 5/5 tactiques · stable** (coevo2.py) |

## 🏁 A + phase F : BOUCLÉS
Toute la pyramide maîtrisée. Les 2 percées finales : B6 repli (piège optimal-stopping vaincu par
« lire la marée / tenir tant qu'on gagne ») ; la vraie co-évolution (naïf 41% → league 100% pire-cas,
emploie tout le répertoire).

## Reste = câblage LIVE (chez Leviathan 001, handoffs prêts)
C officier · D assemblage · calculer les 10 features de l'orchestration en Arma · arsenal ACE par rôle.
Le plateau GPU est vide.

## Principes établis (réutilisables)
- Équipement : PRIMER l'usage effectif + rendre le sondage-aveugle coûteux.
- Tout env : un signal POSITIF vers l'état réussi, pas que des pénalités (a débloqué B7, sapeur, B6).
- 0% persistant = piège d'exploration → départ aléatoire/curriculum (flanc, récup, conduite).
- Optimal-stopping (B6) → primer l'action utile TANT qu'elle l'est, pas juste pénaliser l'attente.
