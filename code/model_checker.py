from copy import deepcopy
from collections import deque

PRIORITES = {"NON_URGENT": 1, "URGENT": 2, "URGENCE_ABSOLUE": 3}


def rendre_hashable(e):
    return (
        e["medecin_libre"],
        e["medecin_occupe"],
        e["siege_libre"],
        e["siege_occupe"],
        e["salle_attente"],
        e["consultation"],
        e["sortis"]
    )


def transitions_possibles(e):
    t = []

    if (
        e["medecin_libre"] == 1
        and e["siege_libre"] == 1
        and e["salle_attente"]
    ):
        t.append("Appel du patient prioritaire")

    if e["consultation"]:
        t.append("Fin de consultation")

    return t


def appliquer_transition(e, transition):
    n = deepcopy(e)

    if transition == "Appel du patient prioritaire":
        p = max(
            n["salle_attente"],
            key=lambda x: PRIORITES[x[1]]
        )

        s = list(n["salle_attente"])
        s.remove(p)

        n["salle_attente"] = tuple(s)
        n["consultation"] = (p,)

        n["medecin_libre"] = 0
        n["medecin_occupe"] = 1

        n["siege_libre"] = 0
        n["siege_occupe"] = 1

    elif transition == "Fin de consultation":
        p = n["consultation"][0]

        n["consultation"] = ()
        n["sortis"] = n["sortis"] + (p,)

        n["medecin_libre"] = 1
        n["medecin_occupe"] = 0

        n["siege_libre"] = 1
        n["siege_occupe"] = 0

    return n


def verifier_toutes_proprietes(e, n_patients):
    securite = len(e["consultation"]) <= 1

    terminal = not e["salle_attente"] and not e["consultation"]
    pas_deadlock = terminal or len(transitions_possibles(e)) > 0

    if e["consultation"]:
        prio_c = PRIORITES[e["consultation"][0][1]]
        prio_ok = all(
            PRIORITES[p[1]] <= prio_c
            for p in e["salle_attente"]
        )
    else:
        prio_ok = True

    I2 = e["medecin_libre"] + e["medecin_occupe"] == 1
    I3 = e["siege_libre"] + e["siege_occupe"] == 1
    I4 = (
        len(e["salle_attente"])
        + len(e["consultation"])
        + len(e["sortis"])
        == n_patients
    )

    return securite, pas_deadlock, prio_ok, I2, I3, I4


def model_checking(etat_initial):
    n_patients = (
        len(etat_initial["salle_attente"])
        + len(etat_initial["consultation"])
        + len(etat_initial["sortis"])
    )

    file = deque([(etat_initial, "Etat initial")])
    visites = set()
    etats = []
    violations = []

    while file:
        e, tr = file.popleft()
        h = rendre_hashable(e)

        if h in visites:
            continue

        visites.add(h)
        etats.append((e, tr))

        res = verifier_toutes_proprietes(e, n_patients)

        if not all(res):
            violations.append((e, tr) + res)

        for t in transitions_possibles(e):
            file.append((appliquer_transition(e, t), t))

    print(f"Marquages explores : {len(etats)}")
    print(f"Violations detectees : {len(violations)}")

    if not violations:
        print("SUCCES : toutes les proprietes sont verifiees.")

    return etats, violations


def afficher_etats(etats):
    for i, (etat, transition) in enumerate(etats):
        print(f"\nM{i} - {transition}")
        print("Salle attente :", etat["salle_attente"])
        print("Consultation  :", etat["consultation"])
        print("Sortis        :", etat["sortis"])


def main():
    etat_initial = {
        "medecin_libre": 1,
        "medecin_occupe": 0,
        "siege_libre": 1,
        "siege_occupe": 0,
        "salle_attente": (
            ("A", "NON_URGENT"),
            ("B", "URGENCE_ABSOLUE"),
            ("C", "URGENT")
        ),
        "consultation": (),
        "sortis": ()
    }

    etats, violations = model_checking(etat_initial)
    afficher_etats(etats)


if __name__ == "__main__":
    main()
