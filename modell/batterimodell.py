import pyomo.environ as pyo


def lag_modell(pris_dag1, pris_dag2, sannsynlighet):

    # 1. Batteriparametere fra del 1

    E_min = 10
    E_max = 100
    E_start = 50

    P_lading_max = 25
    P_utlading_max = 25

    eta_lading = 0.95
    eta_utlading = 0.95

    delta_t = 1


    # 2. Opprett modellen, timene og scenariene

    modell = pyo.ConcreteModel()

    modell.T1 = pyo.RangeSet(1, 24)
    modell.T2 = pyo.RangeSet(25, 48)

    # Scenariene hentes fra sannsynlighetsordboken.
    modell.S = pyo.Set(initialize=list(sannsynlighet.keys()))


    # 3. Beslutningsvariabler for døgn 1
    # Disse er felles for alle scenarier.

    modell.lading = pyo.Var(
        modell.T1,
        bounds=(0, P_lading_max)
    )

    modell.utlading = pyo.Var(
        modell.T1,
        bounds=(0, P_utlading_max)
    )

    modell.energi = pyo.Var(
        modell.T1,
        bounds=(E_min, E_max)
    )


    # 4. Beslutningsvariabler for døgn 2
    # Disse kan være forskjellige mellom scenariene.
    # Eksempel: modell.lading2[25, "s1"]

    modell.lading2 = pyo.Var(
        modell.T2,
        modell.S,
        bounds=(0, P_lading_max)
    )

    modell.utlading2 = pyo.Var(
        modell.T2,
        modell.S,
        bounds=(0, P_utlading_max)
    )

    modell.energi2 = pyo.Var(
        modell.T2,
        modell.S,
        bounds=(E_min, E_max)
    )


    # 5. Energibalanse for døgn 1

    def energibalanse_dag1(modell, t):

        if t == 1:
            energi_forrige_time = E_start
        else:
            energi_forrige_time = modell.energi[t - 1]

        return modell.energi[t] == (
            energi_forrige_time
            + eta_lading * modell.lading[t] * delta_t
            - modell.utlading[t] * delta_t / eta_utlading
        )

    modell.energibalanse1 = pyo.Constraint(
        modell.T1,
        rule=energibalanse_dag1
    )


    # 6. Energibalanse for døgn 2

    def energibalanse_dag2(modell, t, s):

        if t == 25:
            # Alle scenarier starter med samme energi fra døgn 1.
            energi_forrige_time = modell.energi[24]
        else:
            energi_forrige_time = modell.energi2[t - 1, s]

        return modell.energi2[t, s] == (
            energi_forrige_time
            + eta_lading * modell.lading2[t, s] * delta_t
            - modell.utlading2[t, s] * delta_t / eta_utlading
        )

    modell.energibalanse2 = pyo.Constraint(
        modell.T2,
        modell.S,
        rule=energibalanse_dag2
    )


    # 7. Sluttkrav for hvert scenario

    def sluttkrav(modell, s):
        return modell.energi2[48, s] == E_start

    modell.sluttkrav = pyo.Constraint(
        modell.S,
        rule=sluttkrav
    )


    # 8. Profitt i døgn 1

    profitt_dag1 = sum(
        pris_dag1[t]
        * (modell.utlading[t] - modell.lading[t])
        * delta_t
        for t in modell.T1
    )


    # 9. Forventet profitt i døgn 2

    profitt_dag2 = sum(
        sannsynlighet[s]
        * sum(
            pris_dag2[s][t]
            * (modell.utlading2[t, s] - modell.lading2[t, s])
            * delta_t
            for t in modell.T2
        )
        for s in modell.S
    )


    # 10. Maksimer samlet forventet profitt

    modell.profitt = pyo.Objective(
        expr=profitt_dag1 + profitt_dag2,
        sense=pyo.maximize
    )

    return modell