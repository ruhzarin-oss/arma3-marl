"""qwen_officer — ferme la boucle CARTE -> SITREP -> QWEN -> ORDRES (sandbox 3x3).
Envoie le SITREP brouillard a Qwen2.5:14b (Ollama), recoit des ORDRES en vocabulaire FERME, les parse.
Teste le vrai maillon : le LLM lit-il la carte et decide-t-il juste ? (le retour en drv.focus = etape suivante).
"""
import sys, re, json, urllib.request
import torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from commander_env import CommanderEnv
from sitrep import sitrep
DEV = "cuda:0"; A, K, D = 8, 4, 8
MODEL = "qwen2.5:14b"
SECTEURS = {"NO", "N", "NE", "O", "C", "E", "SO", "S", "SE"}
VERBES = {"TENIR", "PESER", "RECONNAITRE", "REPLIER"}

SYSTEM = """Tu es l'officier de theatre LEVIATHAN. Raison d'etre : TENIR et ETENDRE le theatre.
Tu recois un SITREP : c'est ce qui est SU. Un secteur marque TROU est un ANGLE AVEUGLE (pas du vide sur).
Priorite de decision A>B>C>D : A cibles ennemies vues > B concentrer la force > C terrain cle (objectif) > D attrition.
Tu reponds UNIQUEMENT par des lignes d'ordres, AUCUNE autre phrase, format STRICT :
SECTEUR : VERBE prio:N
- SECTEUR : un nom present dans le SITREP, rien d'autre.
- VERBE : exactement un de TENIR, PESER, RECONNAITRE, REPLIER.
- prio:N : 1 = priorite max.
Puis une seule ligne finale : RAISON: <une phrase>.
N'invente aucun secteur. Pas de markdown."""


def ask_qwen(sitrep_txt, libres):
    user = sitrep_txt + ("\nLIBRES (elements allouables): %d\nDonne tes ordres." % libres)
    payload = {"model": MODEL, "stream": False, "options": {"temperature": 0.2},
               "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]}
    req = urllib.request.Request("http://localhost:11434/api/chat",
                                 data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())["message"]["content"]


def parse_orders(txt):
    orders = []
    for ln in txt.splitlines():
        m = re.match(r"\s*([A-Z]{1,2})\s*:\s*([A-Z]+)\s+prio:\s*(\d+)", ln.strip(), re.I)
        if not m: continue
        sec, verb, prio = m.group(1).upper(), m.group(2).upper(), int(m.group(3))
        if sec in SECTEURS and verb in VERBES:
            orders.append((prio, sec, verb))
    orders.sort()
    return orders


if __name__ == "__main__":
    class CNet(nn.Module):
        def __init__(s, o, a, h=256):
            super().__init__(); s.body = nn.Sequential(nn.Linear(o, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
            s.mu = nn.Linear(h, a); s.v = nn.Linear(h, 1); s.log_std = nn.Parameter(torch.zeros(a) - 0.5)

        def forward(s, o): h = s.body(o); return s.mu(h), s.v(h).squeeze(-1)

    env = CommanderEnv(64, A=A, K=K, D=D, device=DEV, seed=5, max_steps=120, use_carte=True, carte_T=6.0)
    net = CNet(env.obs_dim, env.act_dim, 256).to(DEV)
    net.load_state_dict(torch.load("/home/younes/compose-embodiment/commander_carte_on.pt", map_location=DEV)); net.eval()
    obs = env.reset()
    with torch.no_grad():
        for _ in range(16):
            mu, _ = net(obs); obs, r, dn, info = env.step(mu.view(64, K, 2))
    e = int(env.carte.threat.sum(dim=(1, 2)).argmax().item())
    txt = sitrep(env, e); libres = int(env.body._aalive()[e].sum().item())
    print("======== SITREP envoye a %s ========\n%s\nLIBRES: %d" % (MODEL, txt, libres))
    print("\n======== REPONSE BRUTE de Qwen ========")
    raw = ask_qwen(txt, libres); print(raw)
    print("\n======== ORDRES PARSES (vocabulaire ferme) ========")
    orders = parse_orders(raw)
    if not orders:
        print("  AUCUN ordre valide -> on garderait le focus precedent (garde-fou).")
    for prio, sec, verb in orders:
        print("  prio %d | %-2s | %s" % (prio, sec, verb))
    if orders:
        print("\n  -> drv.focus = secteur prio 1 = %s (%s)" % (orders[0][1], orders[0][2]))
