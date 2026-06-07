"""
model_checker.py
================
Model checker exhaustif du réseau de Petri coloré — Triage médical
Section 6.2 du rapport — Projet GM 2026 (CY Tech ING1)

Algorithme : exploration BFS (parcours en largeur) de l'espace des marquages.
Vérifie à chaque marquage :
  - Propriété 1 : Sûreté          (jamais 2 patients en consultation)
  - Propriété 3 : Absence deadlock (syst. ne se bloque pas si patients présents)
  - Propriété 4 : Respect priorités(patient le plus prioritaire appelé en premier)
  - P-invariant I2 : P3 + P4 = 1  (médecin)
  - P-invariant I3 : P5 + P6 = 1  (siège)
  - P-invariant I4 : P2+P7+P8 = n (conservation des patients)

Exécution : python3 model_checker.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from copy import deepcopy
from collections import deque

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

PRIORITES = {
    "NON_URGENT":       1,
    "URGENT":           2,
    "URGENCE_ABSOLUE":  3
}

# Marquage initial (section 7.1 du rapport)
# Les patients sont représentés par des tuples (nom, priorite) pour être
# hachables (nécessaire pour la détection des marquages déjà visités).
ETAT_INITIAL = {
    "medecin_libre":  1,
    "medecin_occupe": 0,
    "siege_libre":    1,
    "siege_occupe":   0,
    "salle_attente": (
        ("Patient A", "NON_URGENT"),
        ("Patient B", "URGENCE_ABSOLUE"),
        ("Patient C", "URGENT"),
    ),
    "consultation": (),
    "sortis":       ()
}


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def rendre_hashable(etat):
    """
    Convertit un état en tuple hachable pour la détection des doublons.
    Toutes les listes de patients sont déjà des tuples dans le model checker.
    """
    return (
        etat["medecin_libre"],
        etat["medecin_occupe"],
        etat["siege_libre"],
        etat["siege_occupe"],
        etat["salle_attente"],
        etat["consultation"],
        etat["sortis"]
    )


def afficher_patients(liste):
    """Formate une liste de patients (tuples) en chaîne lisible."""
    if not liste:
        return "(vide)"
    return " → ".join(f"{nom}({prio})" for nom, prio in liste)


def afficher_etat(numero, etat, transition="État initial"):
    """Affiche un marquage dans le format rapport."""
    print("\n" + "=" * 60)
    print(f"M{numero} — {transition}")
    print("=" * 60)
    print(f"Médecin : libre={etat['medecin_libre']} | occupé={etat['medecin_occupe']}")
    print(f"Siège   : libre={etat['siege_libre']} | occupé={etat['siege_occupe']}")
    print(f"Attente : {afficher_patients(etat['salle_attente'])}")
    print(f"Consultation : {afficher_patients(etat['consultation'])}")
    print(f"Sortis : {afficher_patients(etat['sortis'])}")


# ---------------------------------------------------------------------------
# Dynamique du réseau (transitions)
# ---------------------------------------------------------------------------

def transitions_possibles(etat):
    """
    Retourne la liste des transitions franchissables depuis l'état donné.
    - T4 (Appel) : médecin libre + siège libre + patients en attente
    - T5 (Fin)   : patient en consultation
    """
    t = []
    if (etat["medecin_libre"] == 1
            and etat["siege_libre"] == 1
            and etat["salle_attente"]):
        t.append("Appel du patient prioritaire")
    if etat["consultation"]:
        t.append("Fin de consultation")
    return t


def appliquer_transition(etat, transition):
    """
    Calcule le marquage successeur après franchissement d'une transition.
    Retourne un nouvel état (deep copy) sans modifier l'état d'entrée.
    """
    n = deepcopy(etat)

    if transition == "Appel du patient prioritaire":
        # Garde G(T4) : sélection du patient le plus prioritaire
        patient = max(
            n["salle_attente"],
            key=lambda p: PRIORITES[p[1]]
        )
        salle = list(n["salle_attente"])
        salle.remove(patient)
        n["salle_attente"]  = tuple(salle)
        n["consultation"]   = (patient,)
        n["medecin_libre"]  = 0
        n["medecin_occupe"] = 1
        n["siege_libre"]    = 0
        n["siege_occupe"]   = 1

    elif transition == "Fin de consultation":
        patient             = n["consultation"][0]
        n["consultation"]   = ()
        n["sortis"]         = n["sortis"] + (patient,)
        n["medecin_libre"]  = 1
        n["medecin_occupe"] = 0
        n["siege_libre"]    = 1
        n["siege_occupe"]   = 0

    return n


# ---------------------------------------------------------------------------
# Vérification des propriétés sur un marquage
# ---------------------------------------------------------------------------

def verifier_toutes_proprietes(etat, n_patients):
    """
    Vérifie les 4 propriétés critiques et les 3 P-invariants sur un marquage.

    Retourne un tuple de 6 booléens :
      (securite, pas_deadlock, prio_ok, I2, I3, I4)
    """
    # ------------------------------------------------------------------
    # Propriété 1 — Sûreté
    # Au plus 1 patient en consultation (P-invariant y2 : P3+P4=1 → P4≤1)
    # ------------------------------------------------------------------
    securite = len(etat["consultation"]) <= 1

    # ------------------------------------------------------------------
    # Propriété 3 — Absence d'interblocage
    # Si des patients sont présents, au moins une transition est franchissable.
    # L'état terminal (plus de patients) n'est pas un blocage critique.
    # ------------------------------------------------------------------
    terminal     = (not etat["salle_attente"] and not etat["consultation"])
    pas_deadlock = terminal or len(transitions_possibles(etat)) > 0

    # ------------------------------------------------------------------
    # Propriété 4 — Respect des priorités
    # Si un patient est en consultation, aucun patient plus prioritaire
    # ne doit être en attente (conséquence structurelle de la garde G(T4)).
    # ------------------------------------------------------------------
    if etat["consultation"]:
        prio_en_cours = PRIORITES[etat["consultation"][0][1]]
        prio_ok = all(
            PRIORITES[p[1]] <= prio_en_cours
            for p in etat["salle_attente"]
        )
    else:
        prio_ok = True

    # ------------------------------------------------------------------
    # P-invariants structurels
    # I2 : P3 + P4 = 1  (un seul médecin)
    # I3 : P5 + P6 = 1  (un seul siège)
    # I4 : P2 + P7 + P8 = n  (conservation des patients, modèle fermé)
    # ------------------------------------------------------------------
    I2 = etat["medecin_libre"] + etat["medecin_occupe"] == 1
    I3 = etat["siege_libre"]   + etat["siege_occupe"]   == 1
    I4 = (
        len(etat["salle_attente"])
        + len(etat["consultation"])
        + len(etat["sortis"])
    ) == n_patients

    return securite, pas_deadlock, prio_ok, I2, I3, I4


# ---------------------------------------------------------------------------
# Algorithme de model checking — BFS exhaustif
# ---------------------------------------------------------------------------

def model_checking(etat_initial):
    """
    Explore exhaustivement tous les marquages atteignables depuis etat_initial
    par parcours en largeur (BFS) et vérifie les propriétés sur chacun.

    Retourne
    --------
    etats      : list of (etat, transition)   — tous les marquages explorés
    violations : list of (etat, transition, *resultats) — marquages en violation
    """
    n_patients = (
        len(etat_initial["salle_attente"])
        + len(etat_initial["consultation"])
        + len(etat_initial["sortis"])
    )

    file    = deque([(etat_initial, "Etat initial")])
    visites = set()
    etats      = []
    violations = []

    while file:
        etat, transition = file.popleft()
        h = rendre_hashable(etat)

        if h in visites:
            continue          # marquage déjà exploré
        visites.add(h)
        etats.append((etat, transition))

        resultats = verifier_toutes_proprietes(etat, n_patients)

        if not all(resultats):
            violations.append((etat, transition) + resultats)

        # Ajout des successeurs dans la file
        for t in transitions_possibles(etat):
            successeur = appliquer_transition(etat, t)
            file.append((successeur, t))

    return etats, violations


# ---------------------------------------------------------------------------
# Affichage des résultats
# ---------------------------------------------------------------------------

def afficher_resultats(etats, violations, n_patients):
    """Affiche le bilan complet du model checking au format rapport."""
    print("MODEL CHECKING DU RÉSEAU DE PETRI MÉDICAL")
    print(f"Nombre total de marquages atteignables : {len(etats)}")

    for i, (etat, transition) in enumerate(etats):
        afficher_etat(i, etat, transition)
        sec, nd, _, I2, I3, _ = verifier_toutes_proprietes(etat, n_patients)
        print("Vérification :")
        print(f"Sécurité               : {'OK' if sec       else 'ERREUR'}")
        print(f"Conservation ressources: {'OK' if I2 and I3 else 'ERREUR'}")
        print(f"Absence de deadlock    : {'OK' if nd        else 'ERREUR'}")

    print("\n" + "=" * 60)
    print("RÉSULTAT FINAL")
    print("=" * 60)
    if not violations:
        print("Toutes les propriétés sont vérifiées sur les marquages atteignables.")
    else:
        print("Une propriété est violée dans au moins un marquage.")


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main():
    etats, violations = model_checking(ETAT_INITIAL)

    n_patients = (
        len(ETAT_INITIAL["salle_attente"])
        + len(ETAT_INITIAL["consultation"])
        + len(ETAT_INITIAL["sortis"])
    )
    afficher_resultats(etats, violations, n_patients)


if __name__ == "__main__":
    main()
