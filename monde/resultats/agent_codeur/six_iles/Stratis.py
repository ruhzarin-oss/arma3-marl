def gouverner(b, memoire):
    actions = []
    try:
        pop = b.get("population", {})
        sante = b.get("sante", {})
        fin = b.get("finances", {})
        stocks = b.get("stocks_publics", {})
        jour = int(b.get("jour", 1))
        marches = b.get("marches", {})

        dow = jour % 7
        market_closed = (dow == 3)
        pre_close = (dow == 2)

        prix_nour = 4.0
        prix_rem = 35.0
        for m in marches.values():
            if isinstance(m, dict):
                if "nourriture" in m and m["nourriture"].get("prix"):
                    prix_nour = float(m["nourriture"]["prix"])
                if "remedes" in m and m["remedes"].get("prix"):
                    prix_rem = float(m["remedes"]["prix"])

        menages = max(1, int(pop.get("menages", 5000)))
        menages_sans_nour = int(pop.get("menages_sans_nourriture", 0))
        marge_faim = float(pop.get("marge_faim", 0.0))
        nour_reserve = int(stocks.get("nourriture_population", 0))

        bud_int = fin.get("budget", {}).get("interieur", {})
        credit_int = float(bud_int.get("credit", 0))
        exec_int = float(bud_int.get("execute", 0))
        avail_int = max(0.0, credit_int - exec_int)

        # === FOOD (top priority) ===
        if not market_closed and avail_int > prix_nour * 200:
            if menages_sans_nour > 0:
                target = menages * 3
                max_food = 6
                chunk = 1000
            elif pre_close:
                target = menages * 2
                max_food = 6
                chunk = 1000
            elif nour_reserve < menages:
                target = menages * 2
                max_food = 5
                chunk = 1000
            elif marge_faim < 0.1:
                target = menages * 2
                max_food = 5
                chunk = 1000
            else:
                target = menages * 1.5
                max_food = 4
                chunk = 1000

            needed = max(0, int(target - nour_reserve))
            spent = 0.0
            for i in range(max_food):
                if needed <= 0 or len(actions) >= 6:
                    break
                remaining_budget = avail_int - spent
                if remaining_budget < prix_nour * 100:
                    break
                qty = min(chunk, needed, int(remaining_budget / prix_nour))
                if qty < 100:
                    break
                actions.append({"type": "acheter", "bien": "nourriture",
                                "quantite": int(qty), "destination": "population"})
                needed -= qty
                spent += qty * prix_nour

        # === SUBVENTIONS (safety net, critical on closed days) ===
        if len(actions) < 7:
            bud_s = fin.get("budget", {}).get("subventions", {})
            credit_s = float(bud_s.get("credit", 0))
            exec_s = float(bud_s.get("execute", 0))
            avail_s = max(0.0, credit_s - exec_s)

            if avail_s > 100:
                if menages_sans_nour > 0:
                    montant = min(int(avail_s * 0.95), 500000)
                elif market_closed:
                    montant = min(int(avail_s * 0.9), 450000)
                elif pre_close:
                    montant = min(int(avail_s * 0.8), 350000)
                elif marge_faim < 0.15:
                    montant = min(int(avail_s * 0.7), 300000)
                elif nour_reserve < menages:
                    montant = min(int(avail_s * 0.6), 250000)
                else:
                    montant = min(int(avail_s * 0.4), 150000)
                if montant > 50:
                    actions.append({"type": "subvention", "cible": "menages_pauvres",
                                    "montant": int(montant)})

        # === HEALTH ===
        if len(actions) < 8:
            infectes = int(sante.get("infectes", 0))
            nouveaux = int(sante.get("nouveaux_cas", 0))
            remedes = int(stocks.get("remedes", 0))

            if (infectes >= 1 or nouveaux >= 1) and remedes < 30:
                bud_h = fin.get("budget", {}).get("sante", {})
                credit_h = float(bud_h.get("credit", 0))
                exec_h = float(bud_h.get("execute", 0))
                avail_h = max(0.0, credit_h - exec_h)
                if avail_h > prix_rem * 5:
                    qty_r = min(30, int(avail_h / prix_rem))
                    if qty_r > 0:
                        actions.append({"type": "acheter", "bien": "remedes",
                                        "quantite": int(qty_r), "destination": "hopitaux"})

        # === FINANCES (emergency only) ===
        if len(actions) < 8:
            caisse = float(fin.get("caisse", 0))
            coussin = float(fin.get("coussin", 0))
            if caisse < coussin * 0.1:
                montant_d = min(int(coussin * 0.1 - caisse + 5000), 100000)
                if montant_d > 0:
                    actions.append({"type": "emettre_dette", "montant": int(montant_d),
                                    "duree_j": 364})

        # === MEMOIRE ===
        memoire["jour"] = jour
        memoire["nour_reserve"] = nour_reserve
        memoire["menages"] = menages
        memoire["menages_sans_nour"] = menages_sans_nour
        memoire["marge_faim"] = marge_faim

    except Exception:
        actions = []

    if not actions:
        actions.append({"type": "rien"})

    return actions[:8]
