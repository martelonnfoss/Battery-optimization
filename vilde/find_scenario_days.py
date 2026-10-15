"""
Finner den beste representative dagen for hvert av de fem prisscenarioene:

  s1  Lavt prisnivå med små prisvariasjoner
  s2  Lavt/moderat prisnivå
  s3  Normal/typisk prisdag
  s4  Høyt prisnivå med større prisvariasjoner
  s5  Ekstrem/høy prisdag med pristopp(er)

Metode:
  1. Hver dag beskrives med tre nøkkeltall:
       snitt – gjennomsnittspris i døgnet       (prisnivå)
       std   – standardavvik over døgnet         (prisvariasjon)
       maks  – høyeste timepris i døgnet         (pristopp)
  2. Nøkkeltallene gjøres om til persentiler (0-100) blant alle årets dager,
     slik at de blir sammenlignbare selv om de har ulik skala.
  3. Hvert scenario har et mål i persentiler (se MAL under). Dagen som ligger
     nærmest målet (euklidsk avstand) velges.
  4. I tillegg plasseres alle dager i scenarioet de ligger nærmest. Andelen
     dager i hvert scenario kan brukes som sannsynlighet i en stokastisk modell.
"""

import pandas as pd
import numpy as np

FIL = "NO2_2025_forenklet.csv"
PRISKOLONNE = "EUR_per_MWh"
UTFIL = "scenariodager_NO2_2025.csv"

# Mål for hvert scenario, i persentiler: (snitt, std, maks)
# Juster disse om dere vil ha andre definisjoner av scenarioene.
MAL = {
    "s1": {"beskrivelse": "Lavt prisnivå, små variasjoner",      "snitt": 10, "std": 10, "maks": 10},
    "s2": {"beskrivelse": "Lavt/moderat prisnivå",                 "snitt": 30, "std": 30, "maks": 30},
    "s3": {"beskrivelse": "Normal/typisk prisdag",                 "snitt": 50, "std": 50, "maks": 50},
    "s4": {"beskrivelse": "Høyt prisnivå, større variasjoner",     "snitt": 80, "std": 80, "maks": 80},
    "s5": {"beskrivelse": "Ekstrem/høy prisdag med pristopp(er)",  "snitt": 97, "std": 97, "maks": 99},
}
NOKKELTALL = ["snitt", "std", "maks"]

# --- 1. Les data og lag nøkkeltall per dag ------------------------------------
df = pd.read_csv(FIL)
df["time"] = df.groupby("dato").cumcount()   # time i døgnet, 0-23

dager = df.groupby("dato")[PRISKOLONNE].agg(snitt="mean", std="std", maks="max")

# --- 2. Persentiler ---------------------------------------------------------
pers = dager.rank(pct=True) * 100

# --- 3. Avstand fra hver dag til hvert scenariomål ----------------------------
avstand = pd.DataFrame({
    s: np.sqrt(sum((pers[k] - mal[k]) ** 2 for k in NOKKELTALL))
    for s, mal in MAL.items()
})

# --- 4. Velg beste dag per scenario + sannsynligheter ---------------------------
naermeste = avstand.idxmin(axis=1)               # scenarioet hver dag ligner mest
sannsynlighet = naermeste.value_counts(normalize=True).reindex(MAL.keys(), fill_value=0)

oppsummering = []
rader = []
for s, mal in MAL.items():
    dato = avstand[s].idxmin()
    oppsummering.append({
        "scenario": s,
        "beskrivelse": mal["beskrivelse"],
        "dato": dato,
        "snitt": dager.loc[dato, "snitt"],
        "std": dager.loc[dato, "std"],
        "maks": dager.loc[dato, "maks"],
        "sannsynlighet": sannsynlighet[s],
    })
    priser = df.loc[df["dato"] == dato, PRISKOLONNE].values
    for t, p in enumerate(priser):
        rader.append({"scenario": s, "dato": dato, PRISKOLONNE: p,
                      "time_start": t, "time_end": t + 1})

oppsummering = pd.DataFrame(oppsummering)
pd.set_option("display.width", 120)
print(oppsummering.round({"snitt": 1, "std": 1, "maks": 1, "sannsynlighet": 3}).to_string(index=False))
print(f"\nÅrssnitt: {dager['snitt'].mean():.1f} {PRISKOLONNE}")

# Lagre: én rad per scenario og time (5 x 24 rader)
pd.DataFrame(rader).to_csv(UTFIL, index=False)
oppsummering.to_csv("scenario_oppsummering.csv", index=False)
print(f"\nLagret timeprisene til {UTFIL} og oppsummeringen til scenario_oppsummering.csv")

# --- Valgfritt: plott ---------------------------------------------------------
try:
    import matplotlib.pyplot as plt
    plt.figure(figsize=(9, 4.5))
    for _, r in oppsummering.iterrows():
        priser = df.loc[df["dato"] == r["dato"], PRISKOLONNE].values
        plt.plot(range(24), priser, marker="o", markersize=3,
                 label=f"{r['scenario']}: {r['dato']} (p={r['sannsynlighet']:.2f})")
    plt.xlabel("Time")
    plt.ylabel(PRISKOLONNE)
    plt.title("Representative dager for prisscenarioene – NO2 2025")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("scenariodager_NO2_2025.png", dpi=150)
except ImportError:
    pass