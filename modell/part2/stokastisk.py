import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # project root, so 'modell' can be imported

import pandas as pd
import pyomo.environ as pyo
from pathlib import Path

from modell.prisdata import priser, scenarioer, sannsynlighet
from modell.part2.batterimodell import lag_modell


# 1. Hent priser for døgn 1

# Prisene i døgn 1 er like i alle scenariene.
# Derfor kan vi hente dem fra s1-kolonnen.
pris_dag1 = priser.loc[1:24, "s1"].to_dict()


# 2. Hent priser for døgn 2 i alle fem scenarier

pris_dag2 = {}

for s in scenarioer:
    pris_dag2[s] = priser.loc[25:48, s].to_dict()

# Sannsynlighetene importeres fra prisdata.py:
# 20 % for hvert scenario.


# 3. Bygg batterimodellen

modell = lag_modell(
    pris_dag1,
    pris_dag2,
    sannsynlighet
)


# 4. Løs modellen

solver = pyo.SolverFactory("gurobi")
losning = solver.solve(modell)

if not pyo.check_optimal_termination(losning):
    raise RuntimeError(
        f"Modellen ble ikke løst optimalt: "
        f"{losning.solver.termination_condition}"
    )


# 5. Klargjør lagring av resultater

resultatmappe = Path(__file__).resolve().parent

oppsummering = []


# 6. Hent og lagre timeplanen for hvert scenario

for s in scenarioer:

    lading = []
    utlading = []
    energi = []

    for t in range(1, 49):

        if t <= 24:
            # Samme beslutninger i døgn 1 for alle scenarier.
            lading.append(pyo.value(modell.lading[t]))
            utlading.append(pyo.value(modell.utlading[t]))
            energi.append(pyo.value(modell.energi[t]))

        else:
            # Scenarioavhengige beslutninger i døgn 2.
            lading.append(pyo.value(modell.lading2[t, s]))
            utlading.append(pyo.value(modell.utlading2[t, s]))
            energi.append(pyo.value(modell.energi2[t, s]))


    # Lag en dataframe med hele 48-timersplanen.
    resultater = pd.DataFrame(index=range(1, 49))
    resultater.index.name = "time"

    resultater["pris_EUR_MWh"] = priser[s]
    resultater["lading_MW"] = lading
    resultater["utlading_MW"] = utlading
    resultater["energi_MWh"] = energi

    # Hvert tidssteg varer i 1 time.
    resultater["profitt_EUR"] = (
        resultater["pris_EUR_MWh"]
        * (resultater["utlading_MW"] - resultater["lading_MW"])
        * 1
    )


    # Beregn profitt for de to døgnene.
    profitt_dag1 = resultater.loc[1:24, "profitt_EUR"].sum()
    profitt_dag2 = resultater.loc[25:48, "profitt_EUR"].sum()

    total_profitt = profitt_dag1 + profitt_dag2


    # Legg scenarioets resultat til oppsummeringen.
    oppsummering.append({
        "scenario": s,
        "sannsynlighet": sannsynlighet[s],
        "profitt_dag1_EUR": profitt_dag1,
        "profitt_dag2_EUR": profitt_dag2,
        "total_profitt_EUR": total_profitt,
        "energi_time24_MWh": pyo.value(modell.energi[24]),
        "energi_time48_MWh": pyo.value(modell.energi2[48, s])
    })


    # Lagre timeplanen for dette scenarioet.
    resultater.to_csv(
        resultatmappe / f"resultater_stokastisk_{s}.csv"
    )

    # Skriv ut den felles planen for døgn 1 bare én gang.
    if s == scenarioer[0]:
        print("\nFelles plan for døgn 1:")
        print(resultater.loc[1:24].round(2).to_string())

    # Skriv ut planen for døgn 2 for hvert scenario.
    print(f"\nPlan for døgn 2 – scenario {s}:")
    print(resultater.loc[25:48].round(2).to_string())

# 7. Lag og skriv ut oppsummeringstabellen

oppsummering = pd.DataFrame(oppsummering)

print("\nResultater per scenario i den stokastiske løsningen:")
print(oppsummering.round(2).to_string(index=False))


# 8. Beregn forventet profitt

forventet_profitt = (
    oppsummering["sannsynlighet"]
    * oppsummering["total_profitt_EUR"]
).sum()

# Kontroller at tabellen gir samme profitt som målfunksjonen.
assert abs(
    forventet_profitt - pyo.value(modell.profitt)
) < 0.00001, "Profittberegningen stemmer ikke med modellen."

print(
    f"\nForventet profitt: "
    f"{forventet_profitt:.2f} EUR"
)

print(
    f"Felles energi etter time 24: "
    f"{pyo.value(modell.energi[24]):.2f} MWh"
)


# 9. Lagre oppsummeringen

oppsummering.to_csv(
    resultatmappe / "oppsummering_stokastisk.csv",
    index=False
)

print("\nTimeplaner og oppsummering er lagret i modell-mappen.")