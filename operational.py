"""operational — couche OPERATIVE : un COMMANDANT-LLM conduit une campagne de conquete d'Altis objectif par
objectif. A chaque tour : lit la situation (qui tient quoi) -> choisit le prochain objectif attaquable ->
justifie -> delegue a l'officier tactique (resolution). Ecrit staff/altis_op.json -> la carte devient vivante."""
import json, time, math, random
import urllib.request
STAFF = "/home/younes/arma3-marl/staff"
OLLAMA = "http://localhost:11434/api/chat"; MODEL = "qwen2.5:14b"
random.seed(3)


def op_decide(report):
    sysp = ("Tu es un COMMANDANT OPERATIF (echelon division), doctrine OTAN. Tu conduis une campagne pour prendre "
            "l'ile d'Altis objectif par objectif. On te donne ta situation et les objectifs ennemis ATTAQUABLES "
            "(proches de ton front). Choisis LE PROCHAIN objectif a prendre et justifie en 1-2 phrases (valeur, "
            "securiser un axe, proximite du front, neutraliser une menace). Reponds UNIQUEMENT en JSON : "
            '{"objectif":"<nom exact de la liste>","justification":"<1-2 phrases claires>"}.')
    body = json.dumps({"model": MODEL, "stream": False, "format": "json", "options": {"temperature": 0.3},
                       "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": report}]}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(OLLAMA, body, {"Content-Type": "application/json"}), timeout=120))
    return json.loads(r["message"]["content"])


cat = json.load(open(STAFF + "/altis_catalog.json"))["objectifs"]
obj = {o["nom"]: o for o in cat if o["cat"] in ("ville", "bourg", "village")}
names = list(obj)
owner = {n: "opfor" for n in names}
start = min(names, key=lambda n: obj[n]["x"])            # debarquement a l'ouest (Kavala)
owner[start] = "blufor"
log = ["DEBOUT : debarquement amphibie a %s" % start]


def dist(a, b):
    return math.hypot(obj[a]["x"] - obj[b]["x"], obj[a]["y"] - obj[b]["y"])


def write(turn, target, dec):
    json.dump({"turn": turn, "owners": owner, "target": target, "commander": dec, "log": log[-12:],
               "blufor": sum(1 for v in owner.values() if v == "blufor"),
               "opfor": sum(1 for v in owner.values() if v == "opfor"), "total": len(names)},
              open(STAFF + "/altis_op.json", "w"))


write(0, None, {"objectif": "", "justification": "Tete de pont etablie. En attente d'ordres."})
turn = 0
while any(v == "opfor" for v in owner.values()) and turn < 90:
    turn += 1
    blu = [n for n in names if owner[n] == "blufor"]
    att = [n for n in names if owner[n] == "opfor" and min(dist(n, b) for b in blu) < 5500]
    if not att:
        att = sorted((n for n in names if owner[n] == "opfor"), key=lambda n: min(dist(n, b) for b in blu))[:5]
    rep = "SITUATION (campagne Altis, tour %d):\n" % turn
    rep += "Tu tiens %d objectifs : %s.\n" % (len(blu), ", ".join(blu[:14]))
    rep += "Objectifs ennemis ATTAQUABLES (proches de ton front) :\n"
    for n in sorted(att, key=lambda n: min(dist(n, b) for b in blu))[:8]:
        d = min(dist(n, b) for b in blu) / 1000
        rep += "  - %s (%s, valeur %d, garnison ~%d, %.1f km du front)\n" % (n, obj[n]["cat"], obj[n]["val"], obj[n]["bati"], d)
    try:
        dec = op_decide(rep)
    except Exception as e:
        dec = {"objectif": att[0], "justification": "(repli auto: %s)" % str(e)[:40]}
    tgt = dec.get("objectif", "")
    if tgt not in obj or owner.get(tgt) != "opfor":
        tgt = att[0]; dec["objectif"] = tgt
    dec["justification"] = (dec.get("justification", "") + " — delegue a l'officier tactique.")
    write(turn, tgt, dec)
    time.sleep(2.6)
    prob = max(0.45, min(0.9, 0.92 - obj[tgt]["bati"] / 320.0))
    if random.random() < prob:
        owner[tgt] = "blufor"; log.append("T%d : %s PRIS (%s)" % (turn, tgt, obj[tgt]["cat"]))
    else:
        log.append("T%d : assaut sur %s repousse — on persiste" % (turn, tgt))
    write(turn, tgt, dec)
    time.sleep(1.4)
log.append("CAMPAGNE TERMINEE — Altis sous controle BLUFOR" if not any(v == "opfor" for v in owner.values()) else "campagne suspendue")
write(turn, None, {"objectif": "", "justification": log[-1]})
print("FINI tours=%d blufor=%d/%d" % (turn, sum(1 for v in owner.values() if v == "blufor"), len(names)))
