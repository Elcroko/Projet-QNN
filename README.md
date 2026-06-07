# Vérification Formelle d'Applications Critiques avec Réseaux de Petri
### Sujet 4 — Système de triage médical

---

## Auteurs

| Nom | Prénom |
|-----|--------|
| BEY | Benjamin |
| FRANÇAIS | Noé |
| EL HAJ-BENALI | Anas |
| ARES-WAGNER | Baptiste |
| CHURCH | William |
| OUHAB | Mohammed |

---

## Table des matières

1. [Description du projet](#1-description-du-projet)
2. [Contexte et motivation](#2-contexte-et-motivation)
3. [Structure du dépôt](#3-structure-du-dépôt)
4. [Le système modélisé](#4-le-système-modélisé)
5. [Le Réseau de Petri Coloré (CPN)](#5-le-réseau-de-petri-coloré-cpn)
6. [Propriétés formelles vérifiées](#6-propriétés-formelles-vérifiées)
7. [Implémentation Python](#7-implémentation-python)
8. [Comment exécuter](#8-comment-exécuter)
9. [Résultats](#9-résultats)
10. [Limites et extensions](#10-limites-et-extensions)
11. [Références](#11-références)

---

## 1. Description du projet

Ce projet applique les **méthodes formelles** — et plus précisément le **model checking** — à un système de triage médical d'urgences hospitalières.

Le système est modélisé sous forme de **Réseau de Petri Coloré (CPN)** : un formalisme mathématique rigoureux qui permet de représenter les ressources partagées, la concurrence et les politiques de priorité. Deux programmes Python ont été développés :

- **`simulateur.py`** : simule pas à pas le déroulement du triage (entrées de patients, appels, fins de consultation) en vérifiant les propriétés en temps réel.
- **`model_checker.py`** : explore **exhaustivement** l'intégralité de l'espace des états atteignables (par BFS) et vérifie automatiquement 4 propriétés critiques et 3 P-invariants sur chaque marquage.

**Résultat final : 0 violation détectée sur 7 marquages explorés. Toutes les propriétés sont vérifiées.**

---

## 2. Contexte et motivation

### Pourquoi les méthodes formelles ?

Les systèmes critiques (aéronautique, ferroviaire, médical) ne peuvent pas se contenter de tests empiriques : un test ne couvre qu'un nombre fini de scénarios et ne garantit pas l'exhaustivité. Les méthodes formelles reposent sur trois piliers :

1. Un **modèle mathématique précis** du système
2. Une **spécification formelle** des propriétés attendues (LTL, CTL)
3. Une **vérification automatique et exhaustive**

### Conformité aux standards

La norme **IEC 62304** classe les logiciels médicaux en niveaux A, B, C. Pour le **niveau C** (défaillance pouvant causer la mort), des activités formelles de vérification sont explicitement requises. Notre système — où une inversion de priorité peut engager le pronostic vital — relève de ce niveau.

### Pourquoi les Réseaux de Petri Colorés ?

Le système de triage présente trois caractéristiques clés :

- **Partage de ressources** : un seul médecin, un seul siège
- **Politique de priorité sur les données** : la couleur du jeton encode le niveau d'urgence
- **Absence de contraintes temporelles quantitatives strictes**

Les CPN offrent le meilleur compromis : modèle compact, logique de priorité dans la garde G(T4), et riche panoplie d'analyses structurelles (P-invariants, bornitude).

---

## 3. Structure du dépôt

```
Projet-QNN/
│
├── code/
│   ├── simulateur.py                        # Simulation pas à pas du réseau de Petri
│   └── model_checker.py                     # Model checker exhaustif (BFS)
│
├── rapport_projets_Reseaux_de_Petri.pdf     # Rapport complet (17 pages)
├── reseau_petri_tri_medical.pdf             # Schéma du réseau de Petri coloré
└── README.md                                # Ce fichier
```

---

## 4. Le système modélisé

### Contexte

Un **poste de triage médical** dans un service d'urgences hospitalier, dans sa version simplifiée :

- **1 médecin** (peut être libre ou occupé)
- **1 siège de consultation** (peut être libre ou occupé)
- **1 salle d'attente** (contient les patients en attente)

### Niveaux de priorité des patients

Chaque patient reçoit à son entrée l'un des trois niveaux d'urgence :

| Niveau | Valeur numérique | Description |
|--------|-----------------|-------------|
| `URGENCE_ABSOLUE` | 3 | Pronostic vital engagé — priorité maximale |
| `URGENT` | 2 | Prioritaire sur les patients non urgents |
| `NON_URGENT` | 1 | Pris en charge quand aucun patient plus prioritaire n'attend |

### Événements élémentaires

Le système repose sur trois événements :

1. **Entrée d'un patient** dans la salle d'attente
2. **Appel du patient le plus prioritaire** (si médecin libre ET siège libre)
3. **Fin de consultation** et libération des ressources

---

## 5. Le Réseau de Petri Coloré (CPN)

### Définition formelle

Un CPN est un n-uplet `N = (P, T, F, C, G, W, M0)` où :
- `P` : ensemble fini de **places**
- `T` : ensemble fini de **transitions**
- `F` : relation de flux (arcs)
- `C` : ensemble des **couleurs** (types de jetons)
- `G` : fonction de **garde** (condition de franchissement)
- `W` : fonction de poids des arcs
- `M0` : **marquage initial**

### Couleurs utilisées

```
C = { URGENCE_ABSOLUE, URGENT, NON_URGENT, ressource }
```

Fonction de priorité : `prio(URGENCE_ABSOLUE) = 3`, `prio(URGENT) = 2`, `prio(NON_URGENT) = 1`

### Les 9 places

| Place | Nom | Signification | Marquage initial |
|-------|-----|---------------|-----------------|
| P0 | `travaille_pas` | Médecin hors service | 1 jeton ressource |
| P1 | `travaille` | Médecin en service | vide |
| P2 | `Salle_attente` | Patients en attente | multiensemble de patients |
| P3 | `M_libre` | Médecin disponible | 1 jeton ressource |
| P4 | `M_occupé` | Médecin en consultation | vide |
| P5 | `S_libre` | Siège disponible | 1 jeton ressource |
| P6 | `S_occupé` | Siège en consultation | vide |
| P7 | `Consultation` | Patient en cours de traitement | vide |
| P8 | `Sortis` | Patients traités et sortis | vide |

### Les 5 transitions

| Transition | Rôle | Garde / Préconditions |
|------------|------|-----------------------|
| T1 — Médecin commence | Prise de service : P0 → P1 | Toujours franchissable |
| T2 — Médecin arrête | Fin de service : P1 → P0 | Toujours franchissable |
| T3 — Entrée | Nouveau patient dans P2 | Toujours franchissable |
| T4 — Appel patient | P2, P3, P5, P1 → P4, P6, P7 | **G(T4)** : `prio(x) = max(P2)` + arc *autorise* (P1 ≥ 1) |
| T5 — Fin consultation | P7, P4, P6 → P8, P3, P5 | P7 ≥ 1 |

> **Garde G(T4)** : la transition T4 choisit **toujours le patient le plus prioritaire** parmi ceux en salle d'attente. C'est le mécanisme central qui garantit le respect des priorités.

### Matrice d'incidence

La matrice `C ∈ Z^(9x5)` encode les variations de marquage lors du franchissement de chaque transition :

```
Place             T1    T2    T3    T4    T5
travaille_pas     -1    +1     0     0     0
travaille         +1    -1     0     0     0
Salle_attente      0     0    +1    -1     0
M_libre            0     0     0    -1    +1
M_occupe           0     0     0    +1    -1
S_libre            0     0     0    -1    +1
S_occupe           0     0     0    +1    -1
Consultation       0     0     0    +1    -1
Sortis             0     0     0     0    +1
```

### Les 4 P-invariants

Un **P-invariant** est une quantité conservée dans tout état atteignable (vecteur `y >= 0` tel que `y^T * C = 0`). Quatre P-invariants indépendants ont été calculés :

| P-invariant | Équation | Interprétation |
|-------------|----------|----------------|
| **y1** | P0 + P1 = 1 | Le sous-réseau d'activité médecin est toujours cohérent |
| **y2** | P3 + P4 = 1 | Il n'y a qu'un seul médecin (libre OU occupé, jamais les deux) |
| **y3** | P5 + P6 = 1 | Il n'y a qu'un seul siège (libre OU occupé, jamais les deux) |
| **y4** | P2 + P7 + P8 = n | Le nombre total de patients est constant (conservation) |

> **y2** est particulièrement important : il prouve **structurellement** la sûreté — `P3 + P4 = 1` implique `P4 <= 1`, donc jamais deux patients en consultation simultanément, quelle que soit la configuration.

---

## 6. Propriétés formelles vérifiées

### Propriété 1 — Sûreté (Safety)

**Objectif** : Un médecin ne peut pas prendre en charge deux patients simultanément.

```
LTL : G ¬(medecin_occupe ∧ deuxieme_patient_en_consultation)
CTL : AG ¬(q ∧ r)
```

**Preuve** : Par l'absurde — si le médecin est occupé (`q`) ET un deuxième patient est en consultation (`r`), on obtient `¬p ∧ p`, contradiction. Structurellement garantie par le P-invariant **y2** (`P3 + P4 = 1`).

---

### Propriété 2 — Vivacité (Liveness)

**Objectif** : Tout patient qui arrive finit par être pris en charge (aucune famine).

```
LTL : G (patient_en_attente => F patient_pris_en_charge)
CTL : AG (p => AF r)
```

**Preuve** : Si un patient `p` est en attente, le médecin sera éventuellement libre (`F q`), et `p` reste en attente jusqu'à sa prise en charge. Par modus ponens, `p ∧ q => r`. Donc `F r`.

---

### Propriété 3 — Absence d'interblocage (No Deadlock)

**Objectif** : Le système ne peut jamais se bloquer en présence de patients à traiter.

```
LTL : G (att => ¬deadlock)
CTL : AG (att => EX vrai)
```

Avec `att` = « salle d'attente non vide OU patient en consultation ».

**Preuve par cas** :
- Si `P2 > 0` et `P3 = P5 = 1` → T4 est franchissable
- Si `P7 > 0` → T5 est franchissable
- Si `P2 > 0` et `P3 = 0` ou `P5 = 0` → `P4 = 1` ou `P6 = 1`, donc `P7 > 0` et T5 est franchissable

Dans tous les cas où `att` est vrai, au moins une transition est franchissable.

---

### Propriété 4 — Respect des priorités

**Objectif** : Un patient plus prioritaire en attente est toujours appelé avant un patient moins prioritaire.

```
LTL : G (appel(c) => ¬att(c'), c' > c)
CTL : AG (...)
```

**Preuve** : La garde G(T4) impose `prio(x) = max{prio(y) | y dans P2}`. Si un patient de priorité `c'` plus élevée attend, T4 ne peut pas choisir un patient de priorité `c` inférieure.

---

### Synthèse des propriétés

| Propriété | LTL | CTL |
|-----------|-----|-----|
| Sûreté | `G ¬(q ∧ r)` | `AG ¬(q ∧ r)` |
| Vivacité | `G (p => F r)` | `AG (p => AF r)` |
| Absence de deadlock | `G (att => ¬deadlock)` | `AG (att => EX vrai)` |
| Respect des priorités | `G (appel(c) => ¬att(c'), c' > c)` | `AG (...)` |

---

## 7. Implémentation Python

### `simulateur.py` — Simulation pas à pas

Ce fichier simule le réseau de Petri de façon **impérative et séquentielle**. L'état global est stocké dans un dictionnaire `places`.

**Fonctions principales :**

| Fonction | Rôle |
|----------|------|
| `entree_patient(nom, priorite)` | Ajoute un patient dans `salle_attente` |
| `appel_patient()` | Appelle le patient le plus prioritaire (implémente la garde G(T4)) |
| `fin_consultation()` | Libère le médecin et le siège, déplace le patient vers `sortis` |
| `verifier_securite()` | Vérifie la propriété 1 — au plus 1 patient en consultation |
| `verifier_ressources()` | Vérifie les P-invariants I2 (`P3+P4=1`) et I3 (`P5+P6=1`) |
| `verifier_priorite_sim()` | Vérifie la propriété 4 — pas d'inversion de priorité |
| `verifier_absence_deadlock()` | Vérifie la propriété 3 — aucun blocage en présence de patients |
| `verifier_vivacite_finale()` | Vérifie la propriété 2 à la fin — tous les patients sont sortis |
| `afficher_verifications()` | Affiche l'état de toutes les vérifications après chaque événement |

**Structure de l'état (places) :**

```python
places = {
    "medecin_libre": 1,    # P3 : 1 = médecin disponible
    "medecin_occupe": 0,   # P4 : 1 = médecin en consultation
    "siege_libre": 1,      # P5 : 1 = siège disponible
    "siege_occupe": 0,     # P6 : 1 = siège occupé
    "salle_attente": [],   # P2 : liste des patients en attente
    "consultation": [],    # P7 : patient en cours de consultation (max 1)
    "sortis": []           # P8 : patients traités et partis
}
```

---

### `model_checker.py` — Vérification exhaustive

Ce fichier implémente un **model checker par BFS** qui explore l'intégralité de l'espace des états atteignables. Contrairement au simulateur, l'état est représenté avec des **tuples immuables** (hashables) pour permettre la détection des états déjà visités.

**Algorithme BFS :**

```
1. Initialiser la file BFS avec l'état initial
2. Pour chaque état e dépilé :
   a. Si déjà visité → ignorer
   b. Marquer comme visité
   c. Vérifier les 4 propriétés + 3 P-invariants sur e
   d. Si violation → enregistrer
   e. Calculer toutes les transitions franchissables depuis e
   f. Ajouter les états successeurs dans la file
3. Afficher le bilan (marquages explorés, violations détectées)
```

**Fonctions principales :**

| Fonction | Rôle |
|----------|------|
| `rendre_hashable(e)` | Convertit l'état en tuple pour la détection des doublons |
| `transitions_possibles(e)` | Retourne la liste des transitions franchissables depuis l'état `e` |
| `appliquer_transition(e, transition)` | Retourne le nouvel état après franchissement (deepcopy) |
| `verifier_toutes_proprietes(e, n_patients)` | Vérifie sûreté, deadlock, priorités, I2, I3, I4 sur l'état `e` |
| `model_checking(etat_initial)` | Boucle BFS principale — retourne tous les états et violations |
| `afficher_etats(etats)` | Affiche le contenu de chaque marquage exploré |

**Complexité :** `O(|M| x |T|)` où `|M|` = nombre de marquages atteignables et `|T|` = nombre de transitions. Ici `|M| = 7`, `|T| = 5` — exécution quasi-instantanée.

---

## 8. Comment exécuter

### Prérequis

- Python 3.7 ou supérieur
- Aucune bibliothèque externe requise (uniquement `copy` et `collections` de la bibliothèque standard)

### Lancer le simulateur

```bash
python code/simulateur.py
```

Le simulateur exécute le scénario avec 3 patients (A NON_URGENT, B URGENCE_ABSOLUE, C URGENT) et affiche les vérifications après chaque événement.

### Lancer le model checker

```bash
python code/model_checker.py
```

Le model checker explore exhaustivement tous les marquages atteignables et affiche :
- Le nombre de marquages explorés
- Le nombre de violations détectées
- Le contenu de chaque marquage (M0 à M6)

### Scénario par défaut

Les deux scripts utilisent le même scénario de départ :

```python
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
```

**Ordre de prise en charge attendu : B → C → A**

---

## 9. Résultats

### Trace du simulateur

```
Patient A arrive (priorité NON_URGENT).
  Sécurité OK | Ressources OK | Priorités OK | Absence deadlock OK
Patient B arrive (priorité URGENCE_ABSOLUE).
  Sécurité OK | Ressources OK | Priorités OK | Absence deadlock OK
Patient C arrive (priorité URGENT).
  Sécurité OK | Ressources OK | Priorités OK | Absence deadlock OK
Patient B appelé en consultation.
  Sécurité OK | Ressources OK | Priorités OK | Absence deadlock OK
Patient B termine et sort.
Patient C appelé en consultation.
  Sécurité OK | Ressources OK | Priorités OK | Absence deadlock OK
Patient C termine et sort.
Patient A appelé en consultation.
  Sécurité OK | Ressources OK | Priorités OK | Absence deadlock OK
Patient A termine et sort.
Vivacité respectée : tous les patients ont été pris en charge.
```

### Graphe des marquages atteignables

```
M0 --Appel B--> M1 --Fin B--> M2 --Appel C--> M3 --Fin C--> M4 --Appel A--> M5 --Fin A--> ((M6))
```

| État | Transition | Salle d'attente | Consultation | Sortis |
|------|-----------|-----------------|--------------|--------|
| M0 | État initial | A, B, C | vide | vide |
| M1 | Appel prioritaire | A, C | B | vide |
| M2 | Fin consultation | A, C | vide | B |
| M3 | Appel prioritaire | A | C | B |
| M4 | Fin consultation | A | vide | B, C |
| M5 | Appel prioritaire | vide | A | B, C |
| M6 | Fin consultation | vide | vide | B, C, A |

> M6 est l'état terminal légitime (double cercle dans le graphe). Ce n'est pas un deadlock : tous les patients ont été traités.

### Vérification sur tous les marquages

| Marquage | Sûreté | Deadlock | Priorités | I2: P3+P4=1 | I3: P5+P6=1 | I4: patients |
|----------|--------|----------|-----------|-------------|-------------|--------------|
| M0 | OK | OK | OK | OK | OK | OK |
| M1 | OK | OK | OK | OK | OK | OK |
| M2 | OK | OK | OK | OK | OK | OK |
| M3 | OK | OK | OK | OK | OK | OK |
| M4 | OK | OK | OK | OK | OK | OK |
| M5 | OK | OK | OK | OK | OK | OK |
| M6 | OK | OK | OK | OK | OK | OK |

**Bilan : 0 violation détectée sur 7 marquages — toutes les propriétés sont vérifiées.**

### Sortie du model checker

```
Marquages explores : 7
Violations detectees : 0
SUCCES : toutes les proprietes sont verifiees.
```

---

## 10. Limites et extensions

Le modèle actuel est volontairement simplifié pour maintenir un espace d'états fini et vérifiable exhaustivement. Plusieurs extensions seraient envisageables :

| Extension | Description | Outil adapté |
|-----------|-------------|-------------|
| **Multi-ressources** | Plusieurs médecins et salles — concurrence réelle et explosion de l'espace d'états | LoLA, NuSMV |
| **Contraintes temporelles** | Vérifier « tout URGENCE_ABSOLUE est pris en charge en moins de T minutes » | TINA, UPPAAL |
| **Patients dynamiques** | Flux continu de patients, en bornant le nombre maximum de patients simultanés | CPN Tools |
| **T-invariants** | La séquence T4*T5 forme le T-invariant fondamental — prouverait structurellement la vivacité | Analyse algébrique |
| **Validation industrielle** | Le modèle est importable dans CPN Tools ou TINA pour reproduction et tests LTL plus complexes | CPN Tools, TINA |

---

## 11. Références

| # | Référence |
|---|-----------|
| [1] | E. M. Clarke, O. Grumberg, D. Peled. *Model Checking*. MIT Press, 1999. |
| [2] | C. Baier, J.-P. Katoen. *Principles of Model Checking*. MIT Press, 2008. |
| [3] | A. Pnueli. *The Temporal Logic of Programs*. FOCS, IEEE, 1977. |
| [4] | E. M. Clarke, E. A. Emerson. *Design and Synthesis of Synchronization Skeletons Using Branching Time Temporal Logic*. Logics of Programs Workshop, LNCS 131, Springer, 1982. |
| [5] | J.-P. Queille, J. Sifakis. *Specification and Verification of Concurrent Systems in CESAR*. LNCS 137, Springer, 1982. |
| [6] | R. Alur, D. L. Dill. *A Theory of Timed Automata*. Theoretical Computer Science, 126(2), 1994. |
| [7] | C. A. Petri. *Kommunikation mit Automaten*. Thesis, Universität Hamburg, 1962. |
| [8] | K. Jensen. *Coloured Petri Nets: Basic Concepts, Analysis Methods and Practical Use*. Springer, 1992. |
| [9] | C. A. R. Hoare. *Communicating Sequential Processes*. Prentice Hall, 1985. |
| [10] | R. Milner. *A Calculus of Communicating Systems*. LNCS 92, Springer, 1980. |
| [11] | G. J. Holzmann. *The SPIN Model Checker: Primer and Reference Manual*. Addison-Wesley, 2003. |
| [12] | IEC. *IEC 62304: Medical Device Software — Software Life Cycle Processes*. International Electrotechnical Commission, 2006 (amend. 2015). |
