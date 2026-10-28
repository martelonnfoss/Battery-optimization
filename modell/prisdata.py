import pandas as pd
from pathlib import Path




# 1. Definer scenarier og sannsynligheter

scenarioer = ["s1", "s2", "s3", "s4", "s5"]

sannsynlighet = {
    "s1": 0.20,
    "s2": 0.20,
    "s3": 0.20,
    "s4": 0.20,
    "s5": 0.20
}


# 2. Finn prosjektmappen og les inn prisfilene

# Denne filen ligger i "modell".
# parent.parent går opp til "Battery-optimization".
prosjektmappe = Path(__file__).resolve().parent.parent

dag1 = pd.read_csv(
    prosjektmappe / "data" / "clean_data" / "gjennomsnittsdag_NO2_2025.csv"
)

dag2 = pd.read_csv(
    prosjektmappe / "data" / "clean_data" / "scenariodager_NO2_2025.csv"
)


# 3. Kontroller at vi har riktige timer og scenarier

# Hver dag skal ha én rad for hver time_start fra 0 til 23.
assert sorted(dag1["time_start"].tolist()) == list(range(24)), \
    "Døgn 1 må inneholde nøyaktig én rad for hver time fra 0 til 23."

assert set(dag2["scenario"]) == set(scenarioer), \
    "Scenariofilen må inneholde s1, s2, s3, s4 og s5."

for s in scenarioer:
    timer = dag2.loc[dag2["scenario"] == s, "time_start"]

    assert sorted(timer.tolist()) == list(range(24)), \
        f"{s} må inneholde nøyaktig én rad for hver time fra 0 til 23."

assert abs(sum(sannsynlighet.values()) - 1.0) < 0.000001, \
    "Sannsynlighetene må summere til 1."


# 4. Lag pristabellen for døgn 1

dag1 = dag1.sort_values("time_start")

# Samme kjente priser i alle fem scenarier i døgn 1.
priser_dag1 = pd.DataFrame({
    s: dag1["EUR_per_MWh"].to_numpy()
    for s in scenarioer
})

# Modellens timer er 1–24.
priser_dag1.index = range(1, 25)


# 5. Lag pristabellen for døgn 2

# pivot gjør scenarionavnene til kolonner.
# Hver rad blir én time, med én pris for hvert scenario.
priser_dag2 = dag2.pivot(
    index="time_start",
    columns="scenario",
    values="EUR_per_MWh"
)

# Sorter timene og sett kolonnene i rekkefølgen s1–s5.
priser_dag2 = priser_dag2.sort_index()
priser_dag2 = priser_dag2[scenarioer]

# Lokal time 0–23 blir modelltime 25–48.
priser_dag2.index = range(25, 49)


# 6. Sett sammen begge døgn til én dataframe

priser = pd.concat([priser_dag1, priser_dag2])

priser.index.name = "time"
priser.columns.name = None

# Kontroller at alle prisfeltene er fylt ut.
assert priser.notna().all().all(), \
    "Pristabellen inneholder manglende priser."


# 7. Beregn forventet pris for hver time

priser["forventet_pris"] = 0.0

for s in scenarioer:
    priser["forventet_pris"] += sannsynlighet[s] * priser[s]


# 8. Vis og lagre tabellen når denne filen kjøres

if __name__ == "__main__":
    print("\nPriser i EUR/MWh:")
    print(priser.round(2).to_string())

    print("\nSannsynligheter:")
    for s in scenarioer:
        print(f"{s}: {sannsynlighet[s]:.0%}")

    # Lagre en oversiktlig CSV ved siden av Python-filen.
    priser.to_csv(
        prosjektmappe / "modell" / "prisoversikt.csv"
    )

    print("\nPristabellen er lagret i modell/prisoversikt.csv")