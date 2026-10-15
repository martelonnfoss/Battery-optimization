"""
Finner den mest gjennomsnittlige dagen i den forenklede prisfila (NO2_2025_forenklet.csv).

Fila har kolonnene dato, EUR_per_MWh, time_start og time_end.
Døgnene med 23 og 25 timer er allerede fjernet, så alle døgn har 24 timer
og starter ved midnatt norsk tid.

Metode:
  1. Lager en gjennomsnittlig døgnprofil: snittprisen for hver time 0-23 over hele året.
  2. Måler hvor langt hver dag ligger fra denne profilen (RMSE, time for time).
  3. Dagen med minst avvik er "den mest gjennomsnittlige dagen".
"""

import pandas as pd
import numpy as np

FIL = "NO2_2025_forenklet.csv"   # endre sti ved behov
PRISKOLONNE = "EUR_per_MWh"
UTFIL = "gjennomsnittsdag_NO2_2025.csv"

# --- 1. Les data -------------------------------------------------------------
df = pd.read_csv(FIL)
df["time"] = df.groupby("dato").cumcount()   # time i døgnet, 0-23

# Matrise: én rad per dato, 24 kolonner (time 0-23)
dager = df.pivot(index="dato", columns="time", values=PRISKOLONNE)

# --- 2. Gjennomsnittlig døgnprofil --------------------------------------------
snittprofil = dager.mean(axis=0)

# --- 3. Avvik for hver dag ---------------------------------------------------
rmse = np.sqrt(((dager - snittprofil) ** 2).mean(axis=1))
rangering = rmse.sort_values()

# --- 4. Resultat -------------------------------------------------------------
beste_dato = rangering.index[0]
beste_dag = df[df["dato"] == beste_dato]

print(f"Mest gjennomsnittlige dag: {beste_dato} "
      f"(time_start {beste_dag['time_start'].min()}–{beste_dag['time_start'].max()})")
print(f"  RMSE mot snittprofil : {rangering.iloc[0]:.4f} {PRISKOLONNE}")
print(f"  Dagens snittpris      : {beste_dag[PRISKOLONNE].mean():.4f}  "
      f"(årssnitt: {snittprofil.mean():.4f})")
print("\nTopp 5 kandidater:")
for dato, verdi in rangering.head(5).items():
    print(f"  {dato}  RMSE = {verdi:.4f}")

# Lagre de 24 timene i samme format som den forenklede fila,
# men med time_start/time_end nummerert 0-24 for prosjektets første døgn
ut = pd.DataFrame({
    "dato": beste_dato,
    "EUR_per_MWh": beste_dag["EUR_per_MWh"].values,
    "time_start": range(24),
    "time_end": range(1, 25),
})
ut.to_csv(UTFIL, index=False)
print(f"\nLagret de 24 timene til {UTFIL}")

# --- Valgfritt: plott ---------------------------------------------------------
try:
    import matplotlib.pyplot as plt
    plt.figure(figsize=(9, 4))
    plt.plot(range(24), snittprofil.values, "--", label="Gjennomsnittsprofil 2025")
    plt.plot(range(24), ut[PRISKOLONNE], marker="o", label=f"Valgt dag: {beste_dato}")
    plt.xlabel("Time")
    plt.ylabel(PRISKOLONNE)
    plt.title("Mest gjennomsnittlige dag – NO2 2025")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("gjennomsnittsdag_NO2_2025.png", dpi=150)
except ImportError:
    pass