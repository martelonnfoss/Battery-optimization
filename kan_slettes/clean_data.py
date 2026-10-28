"""
Forenkler NO2-prisdataene:
  - Fjerner de to døgnene som ikke har 24 timer (30. mars med 23 timer og
    26. oktober med 25 timer, på grunn av sommertid/vintertid).
  - time_start og time_end blir løpende timenummer i stedet for tidsstempler.
    Første time får time_start = 0 og time_end = 1, neste 1 og 2, osv.
  - dato er norsk lokal dato, hentet rett fra tidsstempelet.
  - Prisen gjøres om fra EUR/kWh til EUR/MWh (ganger med 1000).
  - NOK- og EXR-kolonnene tas ikke med.

Resultatet er 363 døgn x 24 timer = 8712 rader, der hvert døgn starter ved midnatt.
"""

import pandas as pd

FIL = "data/NO2_2025.csv"
UTFIL = "NO2_2025_forenklet.csv"

df = pd.read_csv(FIL)
df["dato"] = df["time_start"].str[:10]   # tidsstempelet står i lokal tid

# Fjern døgn som ikke har 24 timer
timer_per_dogn = df.groupby("dato")["dato"].transform("size")
fjernet = sorted(df.loc[timer_per_dogn != 24, "dato"].unique())
df = df[timer_per_dogn == 24].reset_index(drop=True)

ut = pd.DataFrame({
    "dato": df["dato"],
    "EUR_per_MWh": (df["EUR_per_kWh"] * 1000).round(2),
    "time_start": range(len(df)),          # 0, 1, 2, ...
    "time_end": range(1, len(df) + 1),     # 1, 2, 3, ...
})

ut.to_csv(UTFIL, index=False)
print(ut.head())
print(f"\nFjernet døgn: {', '.join(fjernet)}")
print(f"Lagret {len(ut)} rader ({len(ut) // 24} døgn) til {UTFIL}")