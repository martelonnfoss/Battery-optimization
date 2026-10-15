import pandas as pd

df = pd.read_csv("NO2_2025.csv")

price_col = "NOK_per_kWh"

# 1) Sjekk manglende verdier (NaN)
n_missing = df[price_col].isna().sum()
print(f"Antall manglende verdier: {n_missing}")

if n_missing > 0:
    print("\nRader med manglende verdi:")
    print(df[df[price_col].isna()])

# 2) Sjekk verdier lik 0
n_zero = (df[price_col] == 0).sum()
print(f"\nAntall verdier lik 0: {n_zero}")

if n_zero > 0:
    print("\nRader med pris = 0:")
    print(df[df[price_col] == 0])

# 3) Litt ekstra: rask oversikt over hele kolonnen
print("\nOppsummering av prisdata:")
print(df[price_col].describe())

# 4) Sjekk om dere faktisk har riktig antall rader (365 dager x 24 timer = 8760)
print(f"\nAntall rader totalt: {len(df)} (forventet ca. 8760)")