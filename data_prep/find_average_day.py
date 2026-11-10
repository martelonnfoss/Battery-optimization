"""
Finds the most average day in the simplified price file (NO2_2025_forenklet_day_ahead.csv).

The file has the columns dato, EUR_per_MWh, time_start and time_end.
The days with 23 and 25 hours have already been removed, so every day has 24 hours
and starts at midnight Norwegian time.

Method:
  1. Build an average daily profile: the mean price for each hour 0-23 over the whole year.
  2. Measure how far each day is from this profile (RMSE, hour by hour).
  3. The day with the smallest deviation is "the most average day".
"""

import pandas as pd
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent   # Battery-optimization
import numpy as np

INPUT_FILE = PROJECT_ROOT / "data" / "clean_data" / "NO2_2025_forenklet_day_ahead.csv"
PRICE_COLUMN = "EUR_per_MWh"
OUTPUT_FILE = PROJECT_ROOT / "data" / "clean_data" / "gjennomsnittsdag_NO2_2025.csv"   # used by modell/prisdata.py and part2/

# --- 1. Read data ------------------------------------------------------------
df = pd.read_csv(INPUT_FILE)
df["hour"] = df.groupby("dato").cumcount()   # hour of the day, 0-23

# Matrix: one row per date, 24 columns (hour 0-23)
days = df.pivot(index="dato", columns="hour", values=PRICE_COLUMN)

# --- 2. Average daily profile ------------------------------------------------
average_profile = days.mean(axis=0)

# --- 3. Deviation for each day -----------------------------------------------
rmse = np.sqrt(((days - average_profile) ** 2).mean(axis=1))
ranking = rmse.sort_values()

# --- 4. Result ---------------------------------------------------------------
best_date = ranking.index[0]
best_day = df[df["dato"] == best_date]

print(f"Most average day: {best_date} "
      f"(time_start {best_day['time_start'].min()}–{best_day['time_start'].max()})")
print(f"  RMSE vs. average profile : {ranking.iloc[0]:.4f} {PRICE_COLUMN}")
print(f"  Mean price of the day    : {best_day[PRICE_COLUMN].mean():.4f}  "
      f"(annual mean: {average_profile.mean():.4f})")
print("\nTop 5 candidates:")
for date, value in ranking.head(5).items():
    print(f"  {date}  RMSE = {value:.4f}")

# Save the 24 hours in the same format as the simplified file,
# but with time_start/time_end numbered 0-24 for the first day of the project
out = pd.DataFrame({
    "dato": best_date,
    "EUR_per_MWh": best_day["EUR_per_MWh"].values,
    "time_start": range(24),
    "time_end": range(1, 25),
})
out.to_csv(OUTPUT_FILE, index=False)
print(f"\nSaved the 24 hours to {OUTPUT_FILE}")

# --- Optional: plot ----------------------------------------------------------
try:
    import matplotlib.pyplot as plt
    plt.figure(figsize=(9, 4))
    plt.plot(range(24), average_profile.values, "--", label="Average profile 2025")
    plt.plot(range(24), out[PRICE_COLUMN], marker="o", label=f"Selected day: {best_date}")
    plt.xlabel("Hour")
    plt.ylabel(PRICE_COLUMN)
    plt.title("Most average day – NO2 2025")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
    #plt.savefig(PROJECT_ROOT / "gjennomsnittsdag_NO2_2025.png", dpi=150)
except ImportError:
    pass
