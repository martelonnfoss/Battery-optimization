import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # project root, so 'modell' can be imported

import pandas as pd
import pyomo.environ as pyo
from pathlib import Path

from modell.prisdata import priser
from modell.part2.batterimodell import lag_modell


# 1. Hent prisene

# Døgn 1: kjente priser.
pris_dag1 = priser.loc[1:24, "forventet_pris"].to_dict()

# Døgn 2: én prisbane med forventet pris for hver time.
# Vi kaller denne prisbanen "EV".
pris_dag2 = {
    "EV": priser.loc[25:48, "forventet_pris"].to_dict()
}

# Modellen bruker bare denne ene prisbanen.
sannsynlighet = {
    "EV": 1.0
}


# 2. Bygg batterimodellen

modell = lag_modell(
    pris_dag1,
    pris_dag2,
    sannsynlighet
)


# 3. Løs modellen

solver = pyo.SolverFactory("gurobi")
losning = solver.solve(modell)

if not pyo.check_optimal_termination(losning):
    raise RuntimeError(
        f"Modellen ble ikke løst optimalt: "
        f"{losning.solver.termination_condition}"
    )


# 4. Hent resultatene for alle 48 timer

lading = []
utlading = []
energi = []

for t in range(1, 49):

    if t <= 24:
        lading.append(pyo.value(modell.lading[t]))
        utlading.append(pyo.value(modell.utlading[t]))
        energi.append(pyo.value(modell.energi[t]))

    else:
        lading.append(pyo.value(modell.lading2[t, "EV"]))
        utlading.append(pyo.value(modell.utlading2[t, "EV"]))
        energi.append(pyo.value(modell.energi2[t, "EV"]))


# 5. Samle resultatene i en dataframe

resultater = pd.DataFrame(index=range(1, 49))
resultater.index.name = "time"

resultater["pris_EUR_MWh"] = priser["forventet_pris"]
resultater["lading_MW"] = lading
resultater["utlading_MW"] = utlading
resultater["energi_MWh"] = energi

# Hvert tidssteg varer i 1 time.
resultater["profitt_EUR"] = (
    resultater["pris_EUR_MWh"]
    * (resultater["utlading_MW"] - resultater["lading_MW"])
    * 1
)


# 6. Skriv ut resultatene

print("\nResultater med forventede priser (EV):")
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
    f"{pyo.value(modell.energi2[48, 'EV']):.2f} MWh"
)


# 7. Lagre timeplanen og en kort oppsummering

resultatmappe = Path(__file__).resolve().parent

resultater.to_csv(
    resultatmappe / "resultater_EV.csv"
)

oppsummering = pd.DataFrame({
    "metode": ["EV"],
    "profitt_EUR": [pyo.value(modell.profitt)],
    "energi_time24_MWh": [pyo.value(modell.energi[24])],
    "energi_time48_MWh": [
        pyo.value(modell.energi2[48, "EV"])
    ]
})

oppsummering.to_csv(
    resultatmappe / "oppsummering_EV.csv",
    index=False
)