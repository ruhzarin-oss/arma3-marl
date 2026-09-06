#!/usr/bin/env python3
"""freshness_detect.py — cote instrument de mesure du banc de fraicheur (Fable, 25/08).

Prend en entree :
  - une liste d'evenements serveur (wall_time_reception_python, on: bool) — recus par le
    meme canal TCP natif que les observations (voir harmattan_actuator_native.sqf, ligne
    "FRESH_FLASH on=..."), donc avec le meme retard reseau que le vrai flux.
  - la sequence de cadres captures (wall_time, luminosite_moyenne) via capture_receiver.py.

Detecte les instants ou la luminosite moyenne franchit un seuil (flash = plein blanc),
apparie chaque franchissement au basculement serveur le plus proche, et calcule le retard.

Ce fichier ne SE CONNECTE A RIEN : il prend des sequences en entree et rend des nombres.
Le branchement live (lire le canal TCP natif + CaptureReceiver en direct) est un fil
separe, deliberement pas construit ici — mesurer d'abord que la logique de detection est
correcte hors-ligne, brancher le direct ensuite.
"""
import statistics


def detect_flash_edges(frames, threshold=0.5):
    """frames: liste de (wall_time, luminosite_moyenne in [0,1]), triee par temps.
    Rend la liste des wall_time ou la luminosite franchit `threshold` en MONTANT
    (transition sombre -> clair, un flash = panneau blanc qui apparait)."""
    edges = []
    prev = None
    for ts, lum in frames:
        if prev is not None and prev < threshold <= lum:
            edges.append(ts)
        prev = lum
    return edges


def match_latency(server_events, detected_edges, max_pair_s=1.0):
    """Apparie chaque bascule serveur (on=True) au flash detecte le plus proche APRES elle.
    Rend (latences_s, n_manques) : n_manques = bascules on=True sans flash detecte proche
    (controle positif : doit etre 0 sur un banc sain)."""
    on_events = [t for t, on in server_events if on]
    latencies = []
    n_missed = 0
    used = set()
    for t_on in on_events:
        candidates = [e for e in detected_edges if e not in used and 0 <= (e - t_on) <= max_pair_s]
        if not candidates:
            n_missed += 1
            continue
        best = min(candidates, key=lambda e: e - t_on)
        used.add(best)
        latencies.append(best - t_on)
    return latencies, n_missed


def summarize(latencies, n_expected):
    if not latencies:
        return {"n": 0, "median_ms": None, "p95_ms": None, "controle_positif": "0/%d — BANC EN PANNE" % n_expected}
    s = sorted(latencies)
    median_ms = statistics.median(s) * 1000
    p95_idx = min(len(s) - 1, int(round(0.95 * (len(s) - 1))))
    p95_ms = s[p95_idx] * 1000
    return {
        "n": len(s),
        "median_ms": round(median_ms, 1),
        "p95_ms": round(p95_ms, 1),
        "controle_positif": f"{len(s)}/{n_expected}",
        "verdict_p95_500ms": "PASSE" if p95_ms <= 500 else "ECHOUE",
    }


def _selftest():
    """Fabrique un serveur qui bascule toutes les 2 s et un flux de cadres avec un retard
    CONNU (180 ms) + un peu de bruit, verifie que la mesure retrouve ~180 ms. Puis un
    controle negatif : aucun flash dans les cadres -> 0 detecte, banc juge EN PANNE."""
    import random
    random.seed(0)

    server_events = [(2.0 * i, True) if i % 2 == 0 else (2.0 * i, False) for i in range(1, 21)]
    on_times = [t for t, on in server_events if on]

    KNOWN_DELAY = 0.180
    frames = []
    t = 0.0
    lum = 0.05
    while t < 42.0:
        near_flash = any(abs(t - (ot + KNOWN_DELAY)) < 0.02 for ot in on_times)
        lum = 0.9 if near_flash or lum > 0.5 and t < 42 and any(abs(t - (ot + KNOWN_DELAY)) < 1.0 for ot in on_times) else lum
        # simulation simple : monte au flash + jitter, redescend apres ~0.3s
        target = 0.9 if any(0 <= t - (ot + KNOWN_DELAY) < 0.3 for ot in on_times) else 0.05
        lum += (target - lum) * 0.6
        frames.append((t, lum + random.uniform(-0.02, 0.02)))
        t += 1.0 / 30

    edges = detect_flash_edges(frames, threshold=0.5)
    latencies, n_missed = match_latency(server_events, edges)
    summary = summarize(latencies, n_expected=len(on_times))

    print(f"[selftest] {len(on_times)} bascules on, {len(edges)} flashs detectes, "
          f"{n_missed} manques, resume={summary}")
    assert n_missed == 0, "controle positif rate : des flashs connus ne sont pas retrouves"
    assert abs(summary["median_ms"] - KNOWN_DELAY * 1000) < 40, \
        f"latence mesuree {summary['median_ms']} ms loin du retard connu {KNOWN_DELAY*1000} ms"
    print("[selftest] retard injecte (180 ms) retrouve par la mesure, a <40 ms pres")

    # controle negatif : pas de flash du tout dans les cadres -> banc doit se declarer EN PANNE
    flat_frames = [(t, 0.05) for t in range(0, 42)]
    edges2 = detect_flash_edges(flat_frames)
    lat2, missed2 = match_latency(server_events, edges2)
    summary2 = summarize(lat2, n_expected=len(on_times))
    assert summary2["n"] == 0 and "PANNE" in summary2["controle_positif"]
    print(f"[selftest] controle negatif (aucun flash) correctement juge EN PANNE : {summary2}")


if __name__ == "__main__":
    _selftest()
