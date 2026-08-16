# Résolution — l'anomalie `AUTOCOMBAT` n'est PAS confirmée

Mesuré le 16/08/2026. Clôt `ANOMALIE_AUTOCOMBAT.md`.

## Ce qui était soupçonné

Que `disableAI "AUTOCOMBAT"` ne prenne pas sur les attaquants du banc — donc que l'IA
d'Arma choisisse ses cibles **en parallèle** de la politique, et que les 44,8 % de prise
soient ceux d'un **attelage** plutôt que d'une politique seule.

## Trois mesures, aucune ne le confirme

**1. Pas-à-pas, onze lectures du même homme** — à la création, après `selectWeapon`, après
chaque `disableAI`, après `setBehaviour`, après `setCombatMode`, après `allowFleeing`, après
3 s, **après le `WAKE`**, après 5 s de plus, après un tir forcé :

> `AUTOCOMBAT` passe à **false** au moment où on le coupe, et **y reste partout**.

**2. Le `format` à dix arguments est innocenté** — testé isolément, SQF les gère, et la
forme exacte de la sonde imprime bien `autoc|false` quand la valeur est `false`.

**3. Sept lectures autour de l'engagement soutenu** — `reveal`, `doTarget`, `doWatch`,
6 s de tir forcé, 4 s de `setVelocity`, retour à `objNull` : **`false` aux sept lectures.**

## Le verdict

**L'ordre prend et il tient.** L'attribution des 44,8 % **n'est pas suspendue** : c'est la
politique apprise qui décide, l'IA d'Arma ne choisit pas ses cibles à côté d'elle.

Le bandeau de suspicion posé ce matin est levé.

## Ce que je ne peux pas expliquer, et que je n'efface pas

Une lecture antérieure — l'attaquant du bras B de la sonde du témoin — donnait
**`autoc|true`**. Trois mesures ultérieures, dont une reproduisant sa séquence exacte à
douze secondes près, disent l'inverse. **Je ne sais pas d'où venait ce `true`.**

Il n'est pas effacé du dossier. Une lecture isolée que trois mesures contredisent ne fonde
rien — mais elle reste au procès-verbal, parce qu'une mesure qu'on ne sait pas expliquer
n'est pas une mesure qui n'a pas eu lieu.

## Le coût, et la règle qui a tenu

Trois sondes, environ quarante minutes. Chacune posée **avant** d'être lancée, chacune
discriminant plusieurs causes d'un coup, et l'arrêt annoncé d'avance à la troisième —
tenu.

⟨Fable⟩ *« Le premier pari est gratuit, le deuxième s'achète avec une sonde. »* Ici il n'y
a pas eu de pari : le soupçon venait d'une mesure, et il est mort d'autres mesures.
