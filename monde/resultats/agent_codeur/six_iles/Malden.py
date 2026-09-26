def gouverner(b, memoire):
    actions = []
    try:
        pop = b.get("population", {})
        sante = b.get("sante", {})
        fin = b.get("finances", {})
        stocks = b.get("stocks_publics", {})
        jour = int(b.get("jour", 1))
        marches = b.get("marches", {})

        dow = (jour - 1) % 7
        market_closed = (dow == 2)

        prix_nour = 4.0
        prix_rem = 35.0
        for m in marches.values():
            if isinstance(m, dict):
                n = m.get("nourriture", {})
                if isinstance(n, dict) and n.get("prix", 0) > 0:
                    prix_nour = float(n["prix"])
                r = m.get("remedes", {})
                if isinstance(r, dict) and r.get("prix", 0) > 0:
                    prix_rem = float(r["prix"])

        menages = max(1, int(pop.get("menages", 5000)))
        menages_sans_nour = int(pop.get("menages_sans_nourriture", 0))
        marge_faim = float(pop.get("marge_faim", 0.0))
        nour_reserve = int(stocks.get("nourriture_population", 0))
        remedes_stock = int(stocks.get("remedes", 0))

        bud_int = fin.get("budget", {}).get("interieur", {})
        avail_int = max(0.0, float(bud_int.get("credit", 0)) - float(bud_int.get("execute", 0)))

        bud_subv = fin.get("budget", {}).get("subventions", {})
        avail_subv = max(0.0, float(bud_subv.get("credit", 0)) - float(bud_subv.get("execute", 0)))

        bud_sant = fin.get("budget", {}).get("sante", {})
        avail_sant = max(0.0, float(bud_sant.get("credit", 0)) - float(bud_sant.get("execute", 0)))

        # === FOOD: aggressive stockpiling before market close (dow=2) ===
        if not market_closed:
            if dow == 0:
                target = menages * 5
            elif dow == 1:
                target = menages * 4
            elif dow in (3, 4):
                target = menages * 2
            else:
                target = menages * 1

            if nour_reserve < target and avail_int > prix_nour * 300:
                needed = target - nour_reserve
                max_aff = int(avail_int / prix_nour) if prix_nour > 0 else 0
                qty1 = min(int(needed), max_aff, 2000)
                if qty1 > 100:
                    actions.append({"type": "acheter", "bien": "nourriture", "quantite": qty1, "destination": "population"})
                remaining = target - nour_reserve - qty1
                if remaining > 200 and len(actions) < 6:
                    qty2 = min(int(remaining), max_aff - qty1, 2000)
                    if qty2 > 100:
                        actions.append({"type": "acheter", "bien": "nourriture", "quantite": qty2, "destination": "population"})

        # === MARKET CLOSED: import as backup ===
        if market_closed and nour_reserve < menages * 2 and avail_int > prix_nour * 500:
            imp_px = prix_nour * 1.2
            if imp_px > 0:
                qty_imp = min(1500, int(avail_int / imp_px))
                if qty_imp > 100:
                    actions.append({"type": "importer", "bien": "nourriture", "quantite": qty_imp})

        # === SUBVENTIONS: reserve for critical moments only ===
        if avail_subv > 5000:
            if market_closed and nour_reserve < menages:
                montant = min(int(avail_subv * 0.4), 200000)
            elif menages_sans_nour > 200:
                montant = min(int(avail_subv * 0.3), 150000)
            elif dow == 1 and nour_reserve < menages:
                montant = min(int(avail_subv * 0.15), 80000)
            else:
                montant = 0
            if montant > 1000:
                actions.append({"type": "subvention", "cible": "menages_pauvres", "montant": montant})

        # === HEALTH ===
        infectes = int(sante.get("infectes", 0))
        nouveaux = int(sante.get("nouveaux_cas", 0))
        if (infectes >= 1 or nouveaux >= 1) and remedes_stock < 30 and avail_sant > prix_rem * 10:
            qty_rem = min(20, int(avail_sant / prix_rem))
            if qty_rem > 0:
                actions.append({"type": "acheter", "bien": "remedes", "quantite": qty_rem, "destination": "hopitaux"})

        # === FINANCES: emergency only ===
        caisse = float(fin.get("caisse", 0))
        coussin = float(fin.get("coussin", 0))
        if caisse < coussin * 0.08:
            montant_d = int(min(coussin * 0.08 - caisse + 30000, 80000))
            if montant_d > 0:
                actions.append({"type": "emettre_dette", "montant": montant_d, "duree_j": 364})

        # === MEMOIRE ===
        memoire["jour"] = jour
        memoire["dow"] = dow
        memoire["nour_reserve"] = nour_reserve
        memoire["menages"] = menages
        memoire["avail_subv"] = avail_subv

    except Exception:
        actions = []

    if not actions:
        actions.append({"type": "rien"})

    return actions[:8]
