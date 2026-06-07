"""
simulateur.py
=============
Simulateur pas-à-pas du réseau de Petri coloré — Triage médical
Section 6.1 du rapport — Projet GM 2026 (CY Tech ING1)

Exécution : python3 simulateur.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

# ---------------------------------------------------------------------------
# Données globales
# ---------------------------------------------------------------------------

PRIORITES = {
    "NON_URGENT":       1,
    "URGENT":           2,
    "URGENCE_ABSOLUE":  3
}

places = {
    "medecin_libre":  1,   # P3
    "medecin_occupe": 0,   # P4
    "siege_libre":    1,   # P5
    "siege_occupe":   0,   # P6
    "salle_attente":  [],  # P2
    "consultation":   [],  # P7
    "sortis":         []   # P8
}

ordre_attendu = []  # ordre théorique de sortie, trié par priorité décroissante


# ---------------------------------------------------------------------------
# Affichage de l'état courant
# ---------------------------------------------------------------------------

def afficher_etat():
    print("\n--- État du réseau ---")
    for nom, valeur in places.items():
        print(f"{nom} : {valeur}")


# ---------------------------------------------------------------------------
# Fonctions de vérification (appelées après chaque franchissement)
# ---------------------------------------------------------------------------

def verifier_securite():
    """
    Propriété 1 — Sûreté :
    Jamais deux patients simultanément en consultation.
    Correspond au P-invariant y2 : P3 + P4 = 1 → P4 ≤ 1.
    """
    return (len(places["consultation"]) <= 1
            and places["medecin_occupe"] <= 1)


def verifier_ressources():
    """
    P-invariants structurels I2 et I3 :
      P3 + P4 = 1  (un seul médecin)
      P5 + P6 = 1  (un seul siège)
    """
    return (places["medecin_libre"] + places["medecin_occupe"] == 1
            and places["siege_libre"] + places["siege_occupe"] == 1)


def verifier_priorite_sim():
    """
    Propriété 4 — Respect des priorités :
    Si un patient est en consultation, aucun patient plus prioritaire
    ne doit être en attente (conséquence de la garde G(T4)).
    """
    if not places["consultation"]:
        return True
    prio_en_cours = PRIORITES[places["consultation"][0]["priorite"]]
    return all(
        PRIORITES[p["priorite"]] <= prio_en_cours
        for p in places["salle_attente"]
    )


def verifier_absence_deadlock():
    """
    Propriété 3 — Absence d'interblocage :
    Retourne True si AUCUN interblocage n'est détecté.
    - T4 franchissable si patients en attente + ressources libres
    - T5 franchissable si patient en consultation
    - Etat terminal (plus de patients) : blocage légitime, pas critique
    """
    # Cas 1 : T4 peut se déclencher
    if (places["salle_attente"]
            and places["medecin_libre"] == 1
            and places["siege_libre"] == 1):
        return True
    # Cas 2 : T5 peut se déclencher
    if places["consultation"]:
        return True
    # Cas 3 : plus de patients → état terminal légitime
    if not places["salle_attente"] and not places["consultation"]:
        return True
    # Sinon : patients en attente mais ressources bloquées → interblocage réel
    return False


def verifier_vivacite_finale():
    """
    Propriété 2 — Vivacité globale (vérification finale) :
    Tous les patients ont été traités et sont sortis du système.
    """
    return (len(places["salle_attente"]) == 0
            and len(places["consultation"]) == 0)


def verifier_toutes_les_proprietes(contexte):
    """Vérifie les 4 propriétés et affiche le résultat."""
    sec  = verifier_securite()
    res  = verifier_ressources()
    prio = verifier_priorite_sim()
    dead = verifier_absence_deadlock()

    print(f"Vérification des propriétés après : {contexte}")

    print(("[OK] Sécurité respectée : jamais deux patients en consultation."
           if sec  else "[!!] Sécurité violée : plusieurs patients en consultation."))
    print(("[OK] Invariant respecté : médecin et siège conservés."
           if res  else "[!!] Invariant violé : problème sur les ressources."))
    print(("[OK] Priorité respectée."
           if prio else "[!!] Priorité violée."))
    print(("[OK] Pas de deadlock."
           if dead else "[!!] Deadlock détecté."))


# ---------------------------------------------------------------------------
# Transitions du réseau
# ---------------------------------------------------------------------------

def entree_patient(nom, priorite):
    """
    T3 — Entrée d'un patient dans la salle d'attente (P2).
    Mise à jour de l'ordre théorique de sortie (trié par priorité décroissante).
    """
    patient = {"nom": nom, "priorite": priorite}
    places["salle_attente"].append(patient)
    ordre_attendu.append(patient)
    # Tri de l'ordre attendu selon la priorité décroissante
    ordre_attendu.sort(key=lambda p: PRIORITES[p["priorite"]], reverse=True)
    print(f"\n{nom} arrive avec priorité {priorite}.")
    verifier_toutes_les_proprietes(f"arrivée de {nom}")


def appel_patient():
    """
    T4 — Appel du patient le plus prioritaire en consultation.
    Garde G(T4) : sélection du patient avec prio(x) = max(Salle_attente).
    Préconditions : P3 ≥ 1, P5 ≥ 1, P2 ≥ 1.
    """
    if (places["medecin_libre"] == 1
            and places["siege_libre"] == 1
            and places["salle_attente"]):

        # Garde G(T4) : patient le plus prioritaire
        patient = max(
            places["salle_attente"],
            key=lambda p: PRIORITES[p["priorite"]]
        )
        places["salle_attente"].remove(patient)
        places["medecin_libre"]  -= 1
        places["medecin_occupe"] += 1
        places["siege_libre"]    -= 1
        places["siege_occupe"]   += 1
        places["consultation"].append(patient)

        print(f"\n{patient['nom']} appelé en consultation.")
        verifier_toutes_les_proprietes(f"appel de {patient['nom']}")
    else:
        print("\nAppel impossible : ressources occupées ou salle vide.")


def fin_consultation():
    """
    T5 — Fin de consultation.
    Déplace le patient de P7 (Consultation) vers P8 (Sortis).
    Restitue les ressources : P4 → P3 et P6 → P5.
    """
    if places["consultation"]:
        patient = places["consultation"].pop(0)
        places["sortis"].append(patient)
        places["medecin_occupe"] -= 1
        places["medecin_libre"]  += 1
        places["siege_occupe"]   -= 1
        places["siege_libre"]    += 1

        print(f"\n{patient['nom']} termine sa consultation et sort.")
        verifier_toutes_les_proprietes(f"sortie de {patient['nom']}")
    else:
        print("\nAucun patient en consultation.")


# ---------------------------------------------------------------------------
# Scénario principal (section 7.1 du rapport)
# ---------------------------------------------------------------------------

def main():
    print("Début de la simulation du réseau de Petri médical")

    # Arrivées des patients
    entree_patient("Patient A", "NON_URGENT")
    entree_patient("Patient B", "URGENCE_ABSOLUE")
    entree_patient("Patient C", "URGENT")
    afficher_etat()

    appel_patient()
    afficher_etat()

    fin_consultation()
    afficher_etat()

    appel_patient()
    afficher_etat()

    fin_consultation()
    afficher_etat()

    appel_patient()
    afficher_etat()

    fin_consultation()
    afficher_etat()

    # Vérification finale de vivacité
    print("\n--- Vérification finale ---")
    if verifier_vivacite_finale():
        print("[OK] Vivacite respectee : tous les patients arrives ont ete pris en charge puis sont sortis.")
    else:
        print("[!!] Vivacite violee : certains patients sont encore bloques.")

    print("\nFin de la simulation.")


if __name__ == "__main__":
    main()
