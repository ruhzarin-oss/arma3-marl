#!/usr/bin/env python3
"""fix_empreinte.py — l empreinte doit survivre a TOUS les modes de chargement.

`__file__` n existe pas quand agent_complet.py est execute par porte0.py ou par un
depouilleur (exec sur le source). L empreinte, qui est justement la barriere censee garantir
que tous les bras ont vu le meme monde, ne peut pas dependre du mode de chargement.
"""
import pathlib

p = pathlib.Path('/home/younes/arma3-marl/agent_complet.py')
t = p.read_text(encoding='utf-8')
a = '_EMPREINTE = _h.md5(open(__file__, "rb").read()).hexdigest()[:12]'
b = ('# chemin EN DUR : ce fichier est aussi execute par porte0.py et les depouilleurs, ou\n'
     '# __file__ n existe pas. La barriere doit survivre a tous ses modes de chargement.\n'
     '_EMPREINTE = _h.md5(open("/home/younes/arma3-marl/agent_complet.py", "rb")'
     '.read()).hexdigest()[:12]')
assert t.count(a) == 1, "ancre de l empreinte introuvable"
p.write_text(t.replace(a, b, 1), encoding='utf-8')
print("empreinte corrigee")
