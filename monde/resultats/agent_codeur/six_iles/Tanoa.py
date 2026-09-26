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
        is_closed = (dow == 3)
        day_before = (dow == 2)

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
        remedes_stock = int(stocks.get("remedes", 0))

        # === FOOD: aggressive stocking, especially before closed day ===
        if not is_closed and prix_nour > 0:
            if day_before:
                target = menages * 10
            elif marge_faim < 0.1:
                target = menages * 8
            elif menages_sans_nour > 0:
                target = menages * 7
            else:
                target = menages * 5

            if nour_reserve < target:
                budget_int = fin.get("budget", {}).get("interieur", {})
                credit_int = float(budget_int.get("credit", 0))
                exec_int = float(budget_int.get("execute", 0))
                avail = max(0.0, credit_int - exec_int) * 0.95

                needed = target - nour_reserve
                max_buy = int(avail / prix_nour) if prix_nour > 0 else 0

                # Debt backup if budget insufficient before closed day
                if day_before and max_buy < needed * 0.5 and len(actions) < 5:
                    caisse = float(fin.get("caisse", 0))
                    coussin = float(fin.get("coussin", 0))
                    if caisse > coussin * 0.3:
                        extra = int(min(needed * prix_nour * 0.5, 500000))
                        if extra > 30000:
                            actions.append({"type": "emettre_dette", "montant": extra, "duree_j": 364})
                            avail += extra * 0.9
                            max_buy = int(avail / prix_nour)

                # Buy in batches of 1500, up to 4 orders
                for _ in range(4):
                    if len(actions) >= 6:
                        break
                    qty = min(1500, needed, max_buy)
                    if qty > 50:
                        actions.append({"type": "acheter", "bien": "nourriture", "quantite": qty, "destination": "population"})
                        needed -= qty
                        max_buy -= qty
                    else:
                        break

        # === IMPORT: supplement if critically short ===
        if not is_closed and nour_reserve < menages * 3 and len(actions) < 7:
            budget_int = fin.get("budget", {}).get("interieur", {})
            credit_int = float(budget_int.get("credit", 0))
            exec_int = float(budget_int.get("execute", 0))
            avail = max(0.0, credit_int - exec_int) * 0.85
            imp_price = prix_nour * 1.2
            if imp_price > 0 and avail > imp_price * 50:
                qty = min(500, int(avail / imp_price))
                if qty > 30:
                    actions.append({"type": "importer", "bien": "nourriture", "quantite": qty})

        # === SUBVENTIONS: primary anti-hunger lever ===
        budget_subv = fin.get("budget", {}).get("subventions", {})
        credit_subv = float(budget_subv.get("credit", 0))
        exec_subv = float(budget_subv.get("execute", 0))
        avail_subv = max(0.0, credit_subv - exec_subv)

        if avail_subv > 300 and len(actions) < 8:
            if day_before or is_closed or menages_sans_nour > 0:
                montant = int(avail_subv * 0.98)
            elif marge_faim < 0.08:
                montant = int(avail_subv * 0.85)
            elif nour_reserve < menages * 4:
                montant = int(avail_subv * 0.7)
            else:
                montant = int(avail_subv * 0.4)
            if montant > 150:
                actions.append({"type": "subvention", "cible": "menages_pauvres", "montant": montant})

        # === HEALTH: maintain remedy stock ===
        infectes = int(sante.get("infectes", 0))
        nouveaux = int(sante.get("nouveaux_cas", 0))
        if (infectes >= 1 or nouveaux >= 1) and remedes_stock < 50 and len(actions) < 8:
            budget_sant = fin.get("budget", {}).get("sante", {})
            credit_sant = float(budget_sant.get("credit", 0))
            exec_sant = float(budget_sant.get("execute", 0))
            avail_sant = max(0.0, credit_sant - exec_sant)
            if avail_sant > prix_rem * 12:
                qty_rem = min(20, int(avail_sant / prix_rem) - 1)
                if qty_rem > 0:
                    actions.append({"type": "acheter", "bien": "remedes", "quantite": qty_rem, "destination": "hopitaux"})

        # === TAXES: one-time reduction to boost purchasing power ===
        if not memoire.get("taxes_done") and not day_before and not is_closed and len(actions) < 8:
            tva_cats = fin.get("tva_categories", {})
            if float(tva_cats.get("super_reduite", 0.06)) > 0:
                actions.append({"type": "fixer_tva", "categorie": "super_reduite", "valeur": 0.0})
            memoire["taxes_done"] = True

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
