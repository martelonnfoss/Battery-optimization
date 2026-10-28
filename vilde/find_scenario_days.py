"""
Finds the most representative day for each of the five price scenarios:

  s1  Low price level with small price variations
  s2  Low/moderate price level
  s3  Normal/typical price day
  s4  High price level with larger price variations
  s5  Extreme/high price day with price spike(s)

Method:
  1. Each day is described by three key figures:
       mean – average price over the day          (price level)
       std  – standard deviation over the day     (price variation)
       max  – highest hourly price of the day     (price spike)
  2. The key figures are converted to percentiles (0-100) among all days of
     the year, so they become comparable even though they have different scales.
  3. Each scenario has a target in percentiles (see TARGETS below). The day
     closest to the target (Euclidean distance) is selected.

All prices are in EUR/MWh.
"""

import pandas as pd
import numpy as np

INPUT_FILE = "NO2_2025_forenklet.csv"
PRICE_COLUMN = "EUR_per_MWh"   # prices in EUR/MWh
PRICE_UNIT = "EUR/MWh"
OUTPUT_FILE = "scenariodager_NO2_2025.csv"      # used by modell/prisdata.py and part2/
SUMMARY_FILE = "scenario_oppsummering.csv"

# Target for each scenario, in percentiles: (mean, std, max)
# Adjust these if you want other definitions of the scenarios.
TARGETS = {
    "s1": {"description": "Low price level, small variations",          "mean": 10, "std": 10, "max": 10},
    "s2": {"description": "Low/moderate price level",                   "mean": 30, "std": 30, "max": 30},
    "s3": {"description": "Normal/typical price day",                   "mean": 50, "std": 50, "max": 50},
    "s4": {"description": "High price level, larger variations",        "mean": 80, "std": 80, "max": 80},
    "s5": {"description": "Extreme/high price day with price spike(s)", "mean": 97, "std": 97, "max": 99},
}
KEY_FIGURES = ["mean", "std", "max"]

# --- 1. Read data and compute key figures per day -----------------------------
df = pd.read_csv(INPUT_FILE)
df["hour"] = df.groupby("dato").cumcount()   # hour of the day, 0-23

days = df.groupby("dato")[PRICE_COLUMN].agg(mean="mean", std="std", min="min", max="max")

# --- 2. Percentiles -----------------------------------------------------------
pct = days.rank(pct=True) * 100

# --- 3. Distance from each day to each scenario target ------------------------
distance = pd.DataFrame({
    s: np.sqrt(sum((pct[k] - target[k]) ** 2 for k in KEY_FIGURES))
    for s, target in TARGETS.items()
})

# --- 4. Select the best day per scenario --------------------------------------
summary = []
rows = []
for s, target in TARGETS.items():
    date = distance[s].idxmin()
    summary.append({
        "scenario": s,
        "description": target["description"],
        "date": date,
        "mean_EUR_per_MWh": days.loc[date, "mean"],
        "std_EUR_per_MWh": days.loc[date, "std"],
        "min_EUR_per_MWh": days.loc[date, "min"],
        "max_EUR_per_MWh": days.loc[date, "max"],
    })
    prices = df.loc[df["dato"] == date, PRICE_COLUMN].values
    for t, p in enumerate(prices):
        rows.append({"scenario": s, "date": date, PRICE_COLUMN: p,
                     "time_start": t, "time_end": t + 1})

summary = pd.DataFrame(summary)
pd.set_option("display.width", 140)
print(summary.round(1).to_string(index=False))
print(f"\nAnnual average price: {days['mean'].mean():.1f} {PRICE_UNIT}")

# Save: one row per scenario and hour (5 x 24 rows)
pd.DataFrame(rows).to_csv(OUTPUT_FILE, index=False)
summary.to_csv(SUMMARY_FILE, index=False)
print(f"\nSaved hourly prices to {OUTPUT_FILE} and the summary to {SUMMARY_FILE}")

# --- Optional: plot -----------------------------------------------------------
try:
    import matplotlib.pyplot as plt
    plt.figure(figsize=(9, 4.5))
    for _, r in summary.iterrows():
        prices = df.loc[df["dato"] == r["date"], PRICE_COLUMN].values
        plt.plot(range(24), prices, marker="o", markersize=3,
                 label=f"{r['scenario']}: {r['date']}")
    plt.xlabel("Hour of day")
    plt.ylabel(f"Price [{PRICE_UNIT}]")
    plt.title("Representative days for the price scenarios – NO2 2025")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
    #plt.savefig("scenariodager_NO2_2025.png", dpi=150)
except ImportError:
    pass
