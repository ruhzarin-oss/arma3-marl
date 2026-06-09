---
title: "Arma–Harmattan–RL"
subtitle: "Architecture complète & état des lieux — ce qui fonctionne, ce qui ne fonctionne pas"
author: "Harmattan — atelier MARL"
date: "9 juin 2026"
lang: fr-FR
papersize: a4
fontsize: 11pt
mainfont: "Noto Serif"
sansfont: "Noto Sans"
monofont: "DejaVu Sans Mono"
linestretch: 1.15
table-use-row-colors: true
titlepage: true
titlepage-color: "1a2733"
titlepage-text-color: "ffffff"
titlepage-rule-color: "c9a227"
toc: true
toc-own-page: true
colorlinks: true
header-includes: |
  \usepackage{tikz}
  \usetikzlibrary{positioning,arrows.meta,calc,shapes.geometric,fit,backgrounds}
  \usepackage{newunicodechar}
  \newunicodechar{→}{\ensuremath{\rightarrow}}
  \newunicodechar{≥}{\ensuremath{\geq}}
  \newunicodechar{≫}{\ensuremath{\gg}}
  \newunicodechar{∼}{\ensuremath{\sim}}
  \newunicodechar{↑}{\ensuremath{\uparrow}}
  \newunicodechar{×}{\ensuremath{\times}}
  \newunicodechar{≈}{\ensuremath{\approx}}
---

# Résumé exécutif

**Arma–Harmattan–RL** est un laboratoire multi-échelle de *dynamiques de puissance* et de *systèmes
multi-agents capables de gagner des batailles* dans Arma 3. L'architecture repose sur **deux moteurs**
(une RTX 3090 qui *fabrique* des cerveaux par simulation massive, 16 serveurs Arma qui servent de
*capteur de vérité*) et une **pile hiérarchique** stratégique → opérationnel → tactique.

**État au 9 juin 2026 :**

- Le **niveau opérationnel (« gagner une bataille ») est RÉSOLU** par une manœuvre fixe (M3,
  enveloppement simple) : **100 % de succès contre la défense de référence, contre 72 % pour la
  partition hand-codée et 0/32 pour le manager appris**.
- La piste **« officier / sélecteur appris » s'est dissoute DEUX fois** au contact de la mesure : ce
  qu'on croyait être des problèmes à résoudre par RL/LLM (le *runaway* à 3 camps ; la *sélection* de
  manœuvre) se sont révélés des **artefacts de design de jeu**, qui s'évaporent quand le jeu est propre.
- La **seule question vraiment ouverte** au niveau opérationnel : enrichir la *géométrie* des défenses
  (pas seulement leur difficulté) — c'est le seul test qui pourrait redonner une raison d'être à
  l'officier.

\newpage

# 1. Architecture complète

La pile a quatre étages. Chaque décision « lente » s'arrête **au-dessus** du réflexe : le RL/LLM
choisit *quoi* et *quand*, jamais le contrôle moteur (qui reste au micro gelé).

```{=latex}
\begin{center}
\begin{tikzpicture}[node distance=5mm, font=\small,
  layer/.style={rectangle, rounded corners, draw, minimum width=12cm, minimum height=1.15cm, align=center}]
\node[layer, fill=blue!10] (strat) {\textbf{STRATÉGIQUE} — multi-acteurs (3+ factions)\\[1pt]\footnotesize KOTH 3 factions · sandbox géopolitique · \textit{officier-coalition = dissous (artefact)}};
\node[layer, fill=green!14, below=of strat] (op) {\textbf{OPÉRATIONNEL} — gagner une bataille\\[1pt]\footnotesize École de guerre : répertoire M1–M7 · sélecteur \textit{(porte fermée → M3-fixe)}};
\node[layer, fill=green!14, below=of op] (tac) {\textbf{TACTIQUE / MICRO} — escouades\\[1pt]\footnotesize cerveau gelé \texttt{koth\_finetuned} · postures = biais de logits};
\node[layer, fill=gray!14, below=of tac] (infra) {\textbf{INFRASTRUCTURE}\\[1pt]\footnotesize Sim GPU (\texttt{koth\_gpu}, ligue) · 16 serveurs Arma · pont-socket · \texttt{enemy\_profiles}};
\draw[-{Stealth[length=2mm]}] (strat)--(op);
\draw[-{Stealth[length=2mm]}] (op)--(tac);
\draw[-{Stealth[length=2mm]}] (tac)--(infra);
\end{tikzpicture}
\end{center}
```

## 1.1 Les deux moteurs (le cœur du dispositif)

La leçon centrale du projet : **le GPU et les serveurs Arma ne font PAS le même travail.** Le GPU
*fabrique* des cerveaux vite et en masse (fiction rapide) ; Arma *juge* lentement mais sans mentir
(vérité réelle). Le cerveau (`.pt`) circule entre les deux ; la donnée, elle, ne circule pas.

```{=latex}
\begin{center}
\begin{tikzpicture}[font=\small,
  b/.style={rectangle, rounded corners, draw, align=center, minimum height=1.3cm, minimum width=4.6cm}]
\node[b, fill=orange!18] (gpu) {\textbf{RTX 3090 — SIM}\\[1pt]\footnotesize \texttt{koth\_gpu} / ligue PSRO\\ env. 150 000 transitions/s\\ \textit{fabrique en masse}};
\node[b, fill=blue!14, right=22mm of gpu] (arma) {\textbf{16 serveurs Arma (CPU)}\\[1pt]\footnotesize le vrai jeu, env. 15 tr/s\\ borné par le temps réel\\ \textit{capteur de VÉRITÉ}};
\node[b, fill=green!16, below=16mm of $(gpu)!0.5!(arma)$] (pt) {\textbf{cerveau \texttt{.pt} partagé}\\[1pt]\footnotesize \texttt{league\_learner} → \texttt{koth\_finetuned}};
\draw[-{Stealth[length=2mm]}] (gpu)--(pt) node[midway, left, font=\footnotesize] {entraîne};
\draw[-{Stealth[length=2mm]}] (arma)--(pt) node[midway, right, font=\footnotesize] {valide / fine-tune};
\end{tikzpicture}
\end{center}
```

**Conséquence dure (mesurée) :** en *mesure* Arma, le GPU est à **0 %** — chaque pas attend
env. 1,5 s que le vrai moteur joue (`step\_wait`+`settle`). Le goulot est le **temps réel d'Arma**,
pas le calcul : un CPU plus rapide n'y change rien. Le GPU n'est moteur que pour l'*entraînement*.

## 1.2 La voie « école de guerre » (le niveau opérationnel)

Au lieu de laisser un RL *découvrir* la tactique en simulation (où il invente des fictions — voir §3),
on lui donne un **répertoire de manœuvres doctrinales M1–M7, Arma-exécutables par construction**
(moteur de phases scripté + micro gelé). On ne **mesure** que *laquelle gagne, contre quelle défense*,
sur des **données réelles** — ce qui court-circuite le mur simulation→réel.

```{=latex}
\begin{center}
\begin{tikzpicture}[node distance=7mm, font=\small,
  b/.style={rectangle, rounded corners, draw, align=center, minimum height=0.95cm, minimum width=4.4cm},
  d/.style={diamond, aspect=2.2, draw, align=center, fill=yellow!25, inner sep=1pt}]
\node[b, fill=gray!12] (front) {Frontière de difficulté\\[1pt]\footnotesize (le \textit{skill} est le levier)};
\node[b, fill=green!14, below=of front] (t1) {\textbf{Étape 1} — table précise\\[1pt]\footnotesize M1–M7 $\times$ n=16 (skilled)};
\node[d, below=9mm of t1] (gate) {\textbf{Étape 2}\\ PORTE :\\ le gagnant\\ change ?};
\node[b, fill=red!14, below left=12mm and 2mm of gate] (no) {\textbf{NON} → M3-fixe\\[1pt]\footnotesize 100\%@normal $>$ scripté 72\%};
\node[b, fill=blue!14, below right=12mm and 2mm of gate] (yes) {\textbf{OUI} → officier-LLM\\[1pt]\footnotesize étape 3 (non déclenchée)};
\draw[-{Stealth[length=2mm]}] (front)--(t1);
\draw[-{Stealth[length=2mm]}] (t1)--(gate);
\draw[-{Stealth[length=2mm]}] (gate.south) -- (no.north) node[midway, left, font=\footnotesize] {fermée};
\draw[-{Stealth[length=2mm]}] (gate.south) -- (yes.north) node[midway, right, font=\footnotesize] {ouverte};
\end{tikzpicture}
\end{center}
```

\newpage

# 2. Ce qui FONCTIONNE

| Brique | Statut | Preuve / chiffre |
|---|---|---|
| **Sim GPU** (`koth_gpu`) | \textbf{OK} solide | 100 % GPU, env. 150k tr/s une fois *gavé* (envs) ; le défaut le sous-alimentait (25k) |
| **Ligue PSRO/PFSP** (`league_learner`) | \textbf{OK} solide | arms-race sain (montée puis redescente quand le pool grossit) ; cerveau robuste |
| **KOTH 3 factions DANS Arma** | \textbf{OK} POC validé | C.1–C.4 ; capture par présence, AO tournante |
| **Pont-socket (humain dans la boucle)** | \textbf{OK} validé | DLL `callExtension` via `C:\hmt_bridge` ; joueur jouable, invulnérable |
| **Transfert du micro** | \textbf{OK} | les manœuvres *s'exécutent* en Arma (93 % vs défense normale en v3) |
| **École de guerre** (M1–M7) | \textbf{OK} | manœuvres Arma-exécutables par construction + tables empiriques réelles |
| **Solution opérationnelle M3-fixe** | \textbf{OK} **résolu** | **100 %@normal**, dégrade gracieusement (skilled 62 / pro 31) |
| **Posture = biais de logits** | \textbf{OK} | zéro réentraînement ; pilote le micro gelé (porté sim–Arma) |
| **Défenses graduées** (`enemy_profiles`) | \textbf{OK} | 9 profils ; *le skill est le levier de difficulté, pas l'effectif* |

**Le résultat-phare :** le micro appris, déployé en **M3 (enveloppement simple)**, **bat la partition
hand-codée de +28 points** (100 % contre 72 %) et le manager appris (0/32). Au niveau d'une bataille,
le système *gagne*.

# 3. Ce qui NE FONCTIONNE PAS (ou s'est dissous)

| Élément | Verdict | Cause établie |
|---|---|---|
| **Manager RL appris** | \textbf{KO} 0/32 en Arma | sur-apprend une **fiction du sim** (CRÊTE = suppression gratuite, inexistante en Arma) |
| **Officier anti-*runaway* (KOTH)** | \textbf{KO} inutile | le *runaway* à 3 camps était un **artefact de la victoire par attrition** ; jeu propre → s'auto-équilibre |
| **Officier-sélecteur (opérationnel)** | \textbf{KO} non justifié | **porte fermée** : M3 gagne sur les 3 défenses testées → rien à sélectionner |
| **`mistral-nemo:12b` comme officier** | \textbf{KO} | **mislit l'état** (se croit dernier en menant) → politique inversée. `qwen2.5:14b` lit juste |
| **Brouillard comme levier sim→réel (KOTH)** | \textbf{KO} non concluant | A/B fog 0.72 vs omni 0.74 ; le gap 83→0 est en *opérations*, pas en KOTH |
| **Accélérer Arma par le matériel** | \textbf{KO} | la mesure est bornée par le **temps réel** (`step_wait/settle`), pas le CPU/GPU |
| **Mesure à petit n** | \textbf{KO} piège | n=3–8 très bruyant (M2 « 62 % »@n8 → **31 %**@n16) → **n≥16 obligatoire** |

**Le fil rouge :** plusieurs « problèmes » qu'on voulait résoudre par du RL/LLM sophistiqué étaient en
réalité des **artefacts de mauvais design de jeu ou de mesure**. Les démonter proprement *est* le
résultat de recherche — et c'est ce qui évite de brûler du calcul sur des chimères.

# 4. Non testé / questions ouvertes

| Sujet | Pourquoi c'est ouvert |
|---|---|
| **Défenses de GÉOMÉTRIE variable** | porte fermée *dans l'espace accessible* (mêmes garnisons) ; une garnison concentrée vs dispersée pourrait faire **changer le gagnant** → rouvrirait un vrai problème de sélection. **C'est un build, pas un réglage.** |
| **Couche stratégique multi-acteurs** | le sandbox géopolitique « N pays » reste à instancier au-dessus de l'opérationnel |
| **Passage à l'échelle** | borne matérielle (env. 15–25 unités/faction) ; compagnie complète $>$ une workstation |
| **M3 vs scripté en tête-à-tête** | comparaison faite via deux tables séparées (même harnais), pas un duel direct |

\newpage

# 5. Recommandations

Deux voies, mutuellement informatives :

**(a) Construire le knob de *géométrie de défense*** (garnison concentrée / dispersée / à flanc faible).
C'est **le test décisif de toute la thèse officier** : si le gagnant change selon la structure, le
sélecteur (étape 3, `qwen2.5:14b`) reprend un sens, sur des bases solides. Tant qu'on ne l'a pas fait,
on ne *sait* pas si l'officier a une raison d'être.

**(b) Capitaliser l'opérationnel** (M3-fixe = acquis net qui bat le baseline) et **monter d'un cran
vers le stratégique** (multi-acteurs, « mener une guerre » — le *nord* du projet).

**Avis :** faire **(a) d'abord** — c'est cheap (un build de mission, mesurable à n≥16) et il tranche
une question qui hante le projet depuis deux dissolutions. Puis (b).

## Règles de méthode gravées

1. **Mesurer cheap avant de dépenser cher** (le GPU/Arma se paie) ; jamais de gros run sur une intuition.
2. **n ≥ 16** pour toute conclusion (le petit n ment).
3. La **difficulté se règle par l'adversaire** (skill), tenue à la *frontière* (env. 50 %) — ni
   plafond ni plancher, sinon zéro signal d'apprentissage.
4. Séparer **fabriquer** (GPU/sim) et **juger** (Arma/réel) ; ne pas confondre fiction rapide et
   vérité lente.
