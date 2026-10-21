import math

import pyomo.environ as pyo


def build_model(price_day1, price_day2, probabilities):
    """
    price_day1: liste med 24 priser.
    price_day2: dictionary {scenario: liste med 24 priser}.
    probabilities: dictionary {scenario: sannsynlighet}.

    Priser: EUR/MWh. Effekt: MW. Energi: MWh.
    """

    if len(price_day1) != 24:
        raise ValueError("Dag 1 må ha 24 priser.")

    if not price_day2:
        raise ValueError("Minst ett scenario må oppgis.")

    if any(len(prices) != 24 for prices in price_day2.values()):
        raise ValueError("Hvert scenario må ha 24 priser.")

    if set(price_day2) != set(probabilities):
        raise ValueError("Priser og sannsynligheter må ha samme scenarioer.")

    if any(not math.isfinite(p) or p < 0
           for p in probabilities.values()):
        raise ValueError("Sannsynligheter må være endelige og ikke-negative.")

    if not math.isclose(sum(probabilities.values()), 1.0):
        raise ValueError("Sannsynlighetene må summere til 1.")

    all_prices = list(price_day1) + [
        price
        for profile in price_day2.values()
        for price in profile
    ]
    if not all(math.isfinite(price) for price in all_prices):
        raise ValueError("Alle priser må være endelige tall.")

    m = pyo.ConcreteModel()

    # Mengder fra rapporten
    m.T1 = pyo.RangeSet(1, 24)
    m.T2 = pyo.RangeSet(25, 48)
    m.S = pyo.Set(initialize=list(price_day2), ordered=True)

    # Batteriparametere
    m.E_min = pyo.Param(initialize=10.0)
    m.E_max = pyo.Param(initialize=100.0)
    m.P_ch_max = pyo.Param(initialize=25.0)
    m.P_dis_max = pyo.Param(initialize=25.0)
    m.eta_ch = pyo.Param(initialize=0.95)
    m.eta_dis = pyo.Param(initialize=0.95)
    m.E_init = pyo.Param(initialize=50.0)
    m.dt = pyo.Param(initialize=1.0)

    # Pris- og sannsynlighetsparametere
    m.lambda1 = pyo.Param(
        m.T1,
        initialize={t: price_day1[t - 1] for t in m.T1},
    )
    m.lambda2 = pyo.Param(
        m.T2, m.S,
        initialize={
            (t, s): price_day2[s][t - 25]
            for t in m.T2 for s in m.S
        },
    )
    m.rho = pyo.Param(m.S, initialize=probabilities)

    # Førstetrinnsvariabler: felles for alle scenarioer
    m.P_ch1 = pyo.Var(
        m.T1, bounds=lambda m, t: (0, m.P_ch_max)
    )
    m.P_dis1 = pyo.Var(
        m.T1, bounds=lambda m, t: (0, m.P_dis_max)
    )
    m.E1 = pyo.Var(
        m.T1, bounds=lambda m, t: (m.E_min, m.E_max)
    )

    # Andretrinnsvariabler: scenarioavhengige
    m.P_ch2 = pyo.Var(
        m.T2, m.S, bounds=lambda m, t, s: (0, m.P_ch_max)
    )
    m.P_dis2 = pyo.Var(
        m.T2, m.S, bounds=lambda m, t, s: (0, m.P_dis_max)
    )
    m.E2 = pyo.Var(
        m.T2, m.S, bounds=lambda m, t, s: (m.E_min, m.E_max)
    )

    # Likning (3): energibalanse på dag 1
    def balance1(m, t):
        previous = m.E_init if t == 1 else m.E1[t - 1]

        return m.E1[t] == (
            previous
            + m.eta_ch * m.P_ch1[t] * m.dt
            - m.P_dis1[t] * m.dt / m.eta_dis
        )

    m.balance1 = pyo.Constraint(m.T1, rule=balance1)

    # Likning (4) og (5): kobling og energibalanse på dag 2
    def balance2(m, t, s):
        previous = m.E1[24] if t == 25 else m.E2[t - 1, s]

        return m.E2[t, s] == (
            previous
            + m.eta_ch * m.P_ch2[t, s] * m.dt
            - m.P_dis2[t, s] * m.dt / m.eta_dis
        )

    m.balance2 = pyo.Constraint(m.T2, m.S, rule=balance2)

    # Likning (14): sluttenergi lik startenergi
    m.terminal = pyo.Constraint(
        m.S,
        rule=lambda m, s: m.E2[48, s] == m.E_init,
    )

    # Overskudd på dag 1
    m.profit1 = pyo.Expression(
        expr=sum(
            m.lambda1[t] * (m.P_dis1[t] - m.P_ch1[t]) * m.dt
            for t in m.T1
        )
    )

    # Overskudd på dag 2 per scenario
    def profit2(m, s):
        return sum(
            m.lambda2[t, s]
            * (m.P_dis2[t, s] - m.P_ch2[t, s])
            * m.dt
            for t in m.T2
        )

    m.profit2 = pyo.Expression(m.S, rule=profit2)

    # Likning (2): forventet samlet overskudd
    m.objective = pyo.Objective(
        expr=m.profit1 + sum(
            m.rho[s] * m.profit2[s] for s in m.S
        ),
        sense=pyo.maximize,
    )

    return m