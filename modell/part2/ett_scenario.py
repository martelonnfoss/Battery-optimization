import pandas as pd
import pyomo.environ as pyo
from pathlib import Path

from modell.prisdata import priser
from modell.part2.batterimodell import lag_modell


# 1. Velg scenario

scenario = "s1"


# 2. Hent priser for de to døgnene

# Døgn 1: prisene er like i alle scenariokolonnene.
pris_dag1 = priser.loc[1:24, scenario].to_dict()

# Døgn 2: legg prisene under navnet på scenarioet.
pris_dag2 = {
    scenario: priser.loc[25:48, scenario].to_dict()
}

# I denne kjøringen antar vi at det valgte scenarioet skjer sikkert.
sannsynlighet = {
    scenario: 1.0
}


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


# 5. Hent resultatene for alle 48 timer

lading = []
utlading = []
energi = []

for t in range(1, 49):

    if t <= 24:
        lading.append(pyo.value(modell.lading[t]))
        utlading.append(pyo.value(modell.utlading[t]))
        energi.append(pyo.value(modell.energi[t]))

    else:
        lading.append(pyo.value(modell.lading2[t, scenario]))
        utlading.append(pyo.value(modell.utlading2[t, scenario]))
        energi.append(pyo.value(modell.energi2[t, scenario]))


# 6. Samle resultatene i en dataframe

resultater = pd.DataFrame(index=range(1, 49))
resultater.index.name = "time"

resultater["pris_EUR_MWh"] = priser[scenario]
resultater["lading_MW"] = lading
resultater["utlading_MW"] = utlading
resultater["energi_MWh"] = energi

# Hver time varer i 1 time.
resultater["profitt_EUR"] = (
    resultater["pris_EUR_MWh"]
    * (resultater["utlading_MW"] - resultater["lading_MW"])
    * 1
)


# 7. Skriv ut resultatene

print(f"\nResultater for {scenario}:")
print(resultater.round(2).to_string())

print(
    f"\nTotal profitt: "
    f"{pyo.value(modell.profitt):.2f} EUR"
)

print(
    f"Energi etter time 24: "
    f"{pyo.value(modell.energi[24]):.2f} MWh"
)

print(
    f"Energi etter time 48: "
    f"{pyo.value(modell.energi2[48, scenario]):.2f} MWh"
)


# 8. Lagre timeplanen

resultatmappe = Path(__file__).resolve().parent

resultater.to_csv(
    resultatmappe / f"resultater_{scenario}.csv"
)


# 9. Oppdater den samlede scenariooversikten

oppsummeringsfil = resultatmappe / "scenario_resultater.csv"

ny_rad = pd.DataFrame({
    "scenario": [scenario],
    "profitt_EUR": [pyo.value(modell.profitt)],
    "energi_time24_MWh": [pyo.value(modell.energi[24])],
    "energi_time48_MWh": [
        pyo.value(modell.energi2[48, scenario])
    ]
})

if oppsummeringsfil.exists():
    oppsummering = pd.read_csv(oppsummeringsfil)

    # Fjern gammelt resultat for dette scenarioet.
    oppsummering = oppsummering[
        oppsummering["scenario"] != scenario
    ]

    oppsummering = pd.concat(
        [oppsummering, ny_rad],
        ignore_index=True
    )

else:
    oppsummering = ny_rad

oppsummering = oppsummering.sort_values("scenario")

oppsummering.to_csv(
    oppsummeringsfil,
    index=False
)

print("\nOppsummering av scenariene som er kjørt:")
print(oppsummering.round(2).to_string(index=False))