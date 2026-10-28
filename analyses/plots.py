from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# ---- Load the scenario days (same file as the optimisation model uses) ----
project_root = Path(__file__).resolve().parent.parent
df = pd.read_csv(project_root / "scenariodager_NO2_2025.csv")

date_col = "date" if "date" in df.columns else "dato"   # older files use "dato"
price_col = "EUR_per_kWh"

descriptions = {
    "s1": "Low price level, small variations",
    "s2": "Low/moderate price level",
    "s3": "Normal/typical price day",
    "s4": "High price level, larger variations",
    "s5": "Extreme/high price day, peak(s)",
}

# ---- Plot: hourly price profile for each scenario day ----
fig, ax = plt.subplots(figsize=(10, 6))
for s, desc in descriptions.items():
    day = df[df["scenario"] == s].sort_values("time_start")
    date = day[date_col].iloc[0]
    ax.plot(day["time_start"], day[price_col], marker="o",
            label=f"{s.upper()} ({date}) - {desc}")

ax.set_xlabel("Hour of day")
ax.set_ylabel("Price [EUR/kWh]")
ax.set_title("Representative scenario days for NO2, 2025")
ax.set_xticks(range(0, 24))
ax.legend(fontsize=8, loc="upper left")
ax.grid(True, alpha=0.3)
plt.tight_layout()
#plt.savefig("scenario_profiles.png", dpi=150)
plt.show()
