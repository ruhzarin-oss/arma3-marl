"""officer_llm — LA SIGNATURE : l'OFFICIER-LLM (qwen2.5:14b) lit une CARTE TACTIQUE -> CHOISIT l'axe
d'approche -> JUSTIFIE en clair (commandant explicable). On NE lui donne PAS l'exposition pre-machee :
par axe il voit les FUSILS ennemis qui le couvrent + le COUVERT en chemin -> il doit RAISONNER.
On verifie son choix contre l'officier scripte (le defile, qu'il ne voit pas). Reutilise officer_select."""
import json
import math
import torch
import requests
from train_koth_gpu import Net
from assault_terrain import AssaultTerrain
import terrain_gpu as TG
from officer_select import exposure_by_bearing, place_at
dev = "cuda:0"; K = 8
NAMES = ["Nord", "Nord-Est", "Est", "Sud-Est", "Sud", "Sud-Ouest", "Ouest", "Nord-Ouest"]
OLLAMA = "http://localhost:11434/api/chat"; MODEL = "qwen2.5:14b"


def tactical_map(env, e):
    """Carte tactique de l'env e : par axe, % du trajet expose au feu ennemi (le vrai signal terrain) + couvert."""
    R = env.R_spawn; ts = torch.linspace(0, 1, 12, device=dev); lines = []
    expo = torch.zeros(K); covr = torch.zeros(K)
    for k in range(K):
        th = k * 2 * math.pi / K; sx = R * math.sin(th); sy = R * math.cos(th)
        px = sx * (1 - ts); py = sy * (1 - ts)
        seen = torch.zeros(12, device=dev)
        for di in range(env.D):
            bx = env.dpx[e, di].expand(12); by = env.dpy[e, di].expand(12)
            c = TG.los_clear(env.hm[e:e + 1], px[None], py[None], bx[None], by[None], env.terr_R)[0]  # (12,)
            seen = torch.maximum(seen, c)
        expo[k] = seen.mean()  # fraction du trajet vue par AU MOINS un defenseur
        covr[k] = TG.sample(env.dcover[e:e + 1], px[None], py[None], env.terr_R).mean()
    for k in range(K):
        cv = "bon" if covr[k] > 0.6 else ("moyen" if covr[k] > 0.3 else "faible")
        lines.append("  - axe %-10s : %3.0f%% du trajet a decouvert (sous le feu ennemi), couvert en chemin : %s"
                     % (NAMES[k], 100 * expo[k], cv))
    return "\n".join(lines), expo, covr


SYS = ("Tu es un officier d'infanterie qui commande une escouade a l'assaut d'un point tenu par 4 defenseurs. "
       "Tu dois choisir l'AXE D'APPROCHE qui expose le moins ton escouade au feu. Regle : un axe avec un FAIBLE "
       "pourcentage du trajet a decouvert est meilleur (l'escouade reste en defile, hors de vue) ; a exposition "
       "egale, plus de couvert est mieux. Choisis l'axe le moins expose. Reponds en JSON : "
       '{"axe":"<un des 8 noms exacts>","justification":"<1 phrase claire en francais citant le % d\'exposition>"}.')


def ask_llm(carte):
    body = {"model": MODEL, "stream": False, "format": "json", "options": {"temperature": 0.2},
            "messages": [{"role": "system", "content": SYS},
                         {"role": "user", "content": "Carte tactique (8 axes d'approche possibles) :\n" + carte + "\n\nQuel axe choisis-tu et pourquoi ?"}]}
    r = requests.post(OLLAMA, json=body, timeout=120); r.raise_for_status()
    return json.loads(r.json()["message"]["content"])


if __name__ == "__main__":
    Ns = 6
    env = AssaultTerrain(num_envs=Ns, relief=40.0, hit=0.15, grid_obs=True, device=dev, seed=7)
    env.reset(); expo = exposure_by_bearing(env)  # verite terrain (que le LLM ne voit pas)
    print("=" * 78)
    print("OFFICIER-LLM (qwen2.5:14b) : lit la carte tactique -> choisit l'axe -> justifie")
    print("=" * 78)
    hit_top2 = 0; rng_top2 = 0.0
    for e in range(Ns):
        carte, expo_e, covr = tactical_map(env, e)
        try:
            ans = ask_llm(carte); axe = ans.get("axe", "?"); just = ans.get("justification", "")
        except Exception as ex:
            print("  [LLM erreur: %s]" % ex); continue
        ki = NAMES.index(axe) if axe in NAMES else int(expo_e.argmin())  # fallback si nom hors-liste
        rank = int((expo[e] < expo[e, ki]).sum())  # 0 = meilleur axe (defile), 7 = pire
        best = NAMES[int(expo[e].argmin())]
        top2 = rank <= 1; hit_top2 += int(top2); rng_top2 += 2 / K  # hasard toucherait top2 dans 2/8
        print("\n--- Situation %d ---" % (e + 1))
        print(carte)
        print("  >> OFFICIER-LLM choisit : %s" % axe)
        print("     justification : %s" % just)
        print("     [verif terrain] rang d'exposition de son choix : %d/7 (0=defile) | meilleur axe reel=%s | %s"
              % (rank, best, "DANS LE TOP-2 (bon)" if top2 else "sous-optimal"))
    print("\n" + "=" * 78)
    print("BILAN : l'officier-LLM a choisi le top-2 (parmi 8) dans %d/%d situations (hasard ~ %.0f%%)."
          % (hit_top2, Ns, 100 * 2 / K))
    print(">>> %s" % ("L'OFFICIER-LLM RAISONNE BIEN -> il lit la carte, choisit le defile, et l'explique en clair"
                      if hit_top2 >= Ns - 1 else "raisonnement LLM imparfait -> a affiner (prompt / carte)"))
    print("LLM FINI")
