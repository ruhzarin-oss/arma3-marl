# LES SESSIONS 1 ET 2 — L'ATTRIBUTION, déposée avant lecture

*10 août 2026, 21 h 15. La sonde a rendu `11 sur 12` en état sain. ⟨Fable⟩ **« 11 sur 12 tue
"la radio ne prend jamais", et c'est tout ce que ça tue. L'opérabilité est rendue, pas
l'attribution. »***

## LE RATÉ SILENCIEUX EST DÉSORMAIS UNE PROPRIÉTÉ DÉPOSÉE DU BRAS

La sonde a mesuré, en état sain, **1 raté sur 12 — environ 8 %**. Ce n'est plus une anomalie :
c'est une **propriété du bras natif**, mesurée, et elle s'écrit ici comme telle.

> **RÈGLE DÉPOSÉE : aucun essai des sessions 1 et 2 n'est exclu.** Ce qu'on trouve se registre.
> Un essai natif à zéro coup, s'il en existe, reste dans la moyenne, et son existence est
> nommée. Rien ne s'exclut après coup, quel que soit l'effet sur le ratio.

## ⚠️ CE DÉPÔT N'EST PAS AVEUGLE, ET JE LE DIS AVANT DE M'EN SERVIR

Fable demande de déposer cette règle **avant de regarder**. **Je ne peux pas l'affirmer** : à
18 h, en cherchant si le bras natif avait tiré dans les sessions 1-2, j'ai imprimé la
distribution complète de `coupsapp` pour ces deux sessions. Je l'ai donc déjà vue, dans un autre
but, et prétendre le contraire serait le genre de silence que ce registre existe pour empêcher.

**Ce que cela coûte, et ce que cela ne coûte pas.** La règle déposée est *« on n'exclut rien »*.
Une règle qui n'exclut rien ne peut pas être taillée sur les données : il n'existe aucune version
d'elle-même qui m'arrangerait davantage en ayant vu les chiffres. Le biais que la cécité protège
— choisir le critère d'exclusion qui sauve le résultat — **n'a pas de prise ici**. Je verse donc
la règle en la déclarant non aveugle, plutôt que de la re-déposer en faisant semblant.

## CE QUE L'ATTRIBUTION PEUT ÉTABLIR, ET CE QU'ELLE NE PEUT PAS

⟨Fable⟩ *« les coups partent des APPUIS, et APRÈS la ligne d'ordre »* — deux questions, et elles
n'ont pas la même force de preuve.

- **Des appuis : OUI, par construction.** `coupsapp` somme la variable `ap_n` portée par les
  trois hommes de `HMT_APP`, incrémentée par leur propre `Fired`. Les défenseurs comptent
  séparément dans `coupsdef`. L'attribution par tireur est structurelle, pas inférée.
- **Après l'ordre : NON, pas depuis le journal.** Le journal ne porte aucun horodatage par coup ;
  il ne rend que le total en fin d'essai. Cette question se lit **dans le code**, et il faut le
  dire ainsi au lieu de fabriquer une vérification qui n'existe pas.

> **Ce que le code rend** : `ap_n` est remis à zéro dans la boucle de remise à l'état, et l'ordre
> part sept secondes plus tard. Tout coup tiré **dans cette fenêtre de sept secondes** serait
> donc compté sans avoir été commandé. `AUTOTARGET` est coupé sur les appuis, ce qui doit
> l'empêcher — **doit**, et c'est précisément le mot qu'on ne s'autorise pas ici.

> **CONSÉQUENCE : la fenêtre de sept secondes est un trou d'attribution que les sessions 1 et 2
> ne peuvent pas combler rétroactivement.** L'instrumentation en lecture pure qui suit relèvera
> `ap_n` **juste avant l'ordre** ; à partir de là le trou est bouché, et pour les sessions 1-2 il
> reste ouvert et déclaré.

## CE QUI FERAIT ÉCHOUER CETTE LECTURE — écrit avant

- **Des essais natifs à zéro coup existent** → ils restent, ils sont nommés, et le taux observé
  se compare aux ~8 % de la sonde. Un taux très supérieur dirait que le banc n'est pas dans
  l'état sain de la sonde.
- **Des coups apparaissent dans la fenêtre de sept secondes** (mesurable seulement à partir de
  l'instrumentation) → l'attribution des sessions 1-2 est entamée, et on le dit.
- **Le ratio des sessions 1-2 change si l'on retire les zéros** → on ne les retire pas, et
  l'écart est écrit. C'est la raison d'être de la règle ci-dessus.
