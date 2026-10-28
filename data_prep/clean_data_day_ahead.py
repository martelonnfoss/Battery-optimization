"""
Simplifies the day-ahead price data (data/raw_data/day_ahead_no2_2025_hourly.csv)
into exactly the same format as NO2_2025_forenklet.csv:
  - Timestamps (UTC) are converted to Norwegian local time.
  - Removes the two days that do not have 24 hours (30 March with 23 hours
    and 26 October with 25 hours, due to daylight saving time).
  - time_start and time_end become running hour numbers (0-1, 1-2, ...).
  - dato is the Norwegian local date.
  - Prices are in EUR/MWh, rounded to 2 decimals.

Result: 363 days x 24 hours = 8712 rows, each day starting at midnight.
"""

import pandas as pd
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent   # Battery-optimization

INPUT_FILE = PROJECT_ROOT / "data" / "raw_data" / "day_ahead_no2_2025_hourly.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "clean_data" / "NO2_2025_forenklet_day_ahead.csv"

df = pd.read_csv(INPUT_FILE)
local = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("Europe/Oslo")
df["dato"] = local.dt.strftime("%Y-%m-%d")
df = df.sort_values("timestamp").reset_index(drop=True)

# Remove days that do not have 24 hours
hours_per_day = df.groupby("dato")["dato"].transform("size")
removed = sorted(df.loc[hours_per_day != 24, "dato"].unique())
df = df[hours_per_day == 24].reset_index(drop=True)

out = pd.DataFrame({
    "dato": df["dato"],
    "EUR_per_MWh": df["da_price_EUR_MWh"].round(2),
    "time_start": range(len(df)),          # 0, 1, 2, ...
    "time_end": range(1, len(df) + 1),     # 1, 2, 3, ...
})

out.to_csv(OUTPUT_FILE, index=False)
print(out.head())
print(f"\nRemoved days: {', '.join(removed)}")
print(f"Saved {len(out)} rows ({len(out) // 24} days) to {OUTPUT_FILE}")
