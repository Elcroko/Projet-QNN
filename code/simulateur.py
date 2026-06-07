PRIORITES = {"NON_URGENT": 1, "URGENT": 2, "URGENCE_ABSOLUE": 3}

places = {
    "medecin_libre": 1,
    "medecin_occupe": 0,
    "siege_libre": 1,
    "siege_occupe": 0,
    "salle_attente": [],
    "consultation": [],
    "sortis": []
}

ordre_attendu = []


def verifier_securite():
    return len(places["consultation"]) <= 1 and places["medecin_occupe"] <= 1


def verifier_ressources():
    return (
        places["medecin_libre"] + places["medecin_occupe"] == 1
        and places["siege_libre"] + places["siege_occupe"] == 1
    )


def verifier_priorite_sim():
    if not places["consultation"]:
        return True

    prio = PRIORITES[places["consultation"][0]["priorite"]]

    return all(
        PRIORITES[p["priorite"]] <= prio
        for p in places["salle_attente"]
    )


def verifier_absence_deadlock():
    if (
        places["salle_attente"]
        and places["medecin_libre"] == 1
        and places["siege_libre"] == 1
    ):
        return True

    if places["consultation"]:
        return True

    if not places["salle_attente"] and not places["consultation"]:
        return True

    return False


def verifier_vivacite_finale():
    return (
        len(places["salle_attente"]) == 0
        and len(places["consultation"]) == 0
    )


def afficher_verifications():
    print(
        "Sécurité OK" if verifier_securite() else "Sécurité NON OK",
        "| Ressources OK" if verifier_ressources() else "| Ressources NON OK",
        "| Priorités OK" if verifier_priorite_sim() else "| Priorités NON OK",
        "| Absence deadlock OK" if verifier_absence_deadlock() else "| Deadlock détecté"
    )


def entree_patient(nom, priorite):
    patient = {"nom": nom, "priorite": priorite}
    places["salle_attente"].append(patient)

    ordre_attendu.append(patient)
    ordre_attendu.sort(
        key=lambda p: PRIORITES[p["priorite"]],
        reverse=True
    )

    print(f"\nPatient {nom} arrive (priorité {priorite}).")
    afficher_verifications()


def appel_patient():
    if (
        places["medecin_libre"] == 1
        and places["siege_libre"] == 1
        and places["salle_attente"]
    ):
        patient = max(
            places["salle_attente"],
            key=lambda p: PRIORITES[p["priorite"]]
        )

        places["salle_attente"].remove(patient)

        places["medecin_libre"] -= 1
        places["medecin_occupe"] += 1

        places["siege_libre"] -= 1
        places["siege_occupe"] += 1

        places["consultation"].append(patient)

        print(f"\nPatient {patient['nom']} appelé en consultation.")
        afficher_verifications()


def fin_consultation():
    if places["consultation"]:
        patient = places["consultation"].pop(0)
        places["sortis"].append(patient)

        places["medecin_occupe"] -= 1
        places["medecin_libre"] += 1

        places["siege_occupe"] -= 1
        places["siege_libre"] += 1

        print(f"\nPatient {patient['nom']} termine et sort.")


def main():
    print("Début de la simulation du réseau de Petri médical")

    entree_patient("A", "NON_URGENT")
    entree_patient("B", "URGENCE_ABSOLUE")
    entree_patient("C", "URGENT")

    while places["salle_attente"] or places["consultation"]:
        if places["salle_attente"]:
            appel_patient()
        if places["consultation"]:
            fin_consultation()

    if verifier_vivacite_finale():
        print("\nVivacité respectée : tous les patients ont été pris en charge.")


if __name__ == "__main__":
    main()
