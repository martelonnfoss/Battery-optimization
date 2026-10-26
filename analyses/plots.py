import pandas as pd
import matplotlib.pyplot as plt

# ---- Load data ----
df = pd.read_csv("/Users/vildevikane/Desktop/Battery-optimization/data/NO2_2025.csv")
df["time_start"] = pd.to_datetime(df["time_start"], utc=True).dt.tz_convert("Europe/Oslo")
df["date"] = df["time_start"].dt.date
df["hour"] = df["time_start"].dt.hour

# Convert prices from EUR/kWh to EUR/MWh
df["EUR_per_MWh"] = df["EUR_per_kWh"] * 1000
price_col = "EUR_per_MWh"
price_unit = "EUR/MWh"

# ---- Compute daily statistics ----
daily = df.groupby("date")[price_col].agg(["mean", "min", "max"]).reset_index()
daily["range"] = daily["max"] - daily["min"]

# ---- Define the scenarios ----
scenario_info = {
    "S1": {"pct": 0.10, "desc": "Low price level, small variations", "prob": 0.10},
    "S2": {"pct": 0.30, "desc": "Low/moderate price level",          "prob": 0.20},
    "S3": {"pct": 0.50, "desc": "Normal/typical price day",          "prob": 0.40},
    "S4": {"pct": 0.75, "desc": "High price level, larger variations","prob": 0.20},
    "S5": {"pct": 0.98, "desc": "Extreme/high price day, peak(s)",   "prob": 0.10},
}

# ---- Select a representative day for each scenario ----
selected_days = {}
for name, info in scenario_info.items():
    if name == "S5":
        # True extreme day: the day with the highest max price in the whole dataset
        chosen = daily.loc[daily["max"].idxmax()]
    else:
        target = daily["mean"].quantile(info["pct"])
        candidates = daily.iloc[(daily["mean"] - target).abs().argsort()[:10]]
        if name in ["S1", "S3"]:
            chosen = candidates.sort_values("range").iloc[0]        # low variation
        elif name == "S4":
            chosen = candidates.sort_values("range", ascending=False).iloc[0]  # high variation
        else:
            chosen = candidates.iloc[0]
    selected_days[name] = chosen["date"]

print("Selected days per scenario:")
for name, d in selected_days.items():
    print(f"  {name}: {d}")

# ---- Get hourly profiles for the selected days ----
scenario_profiles = {
    name: df[df["date"] == d].sort_values("hour").set_index("hour")[price_col]
    for name, d in selected_days.items()
}

# ---- Plot 1: Hourly profile for each scenario day ----
fig, ax = plt.subplots(figsize=(10, 6))
for name, profile in scenario_profiles.items():
    ax.plot(profile.index, profile.values, marker="o",
            label=f"{name} ({selected_days[name]}) - {scenario_info[name]['desc']}")

ax.set_xlabel("Hour of day")
ax.set_ylabel(f"Price [{price_unit}]")
ax.set_title("Representative scenario days for NO2, 2025")
ax.set_xticks(range(0, 24))
ax.legend(fontsize=8, loc="upper left")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("scenario_profiles.png", dpi=150)
plt.show()

# ---- Plot 2: Probability vs. average price per scenario ----
fig, ax1 = plt.subplots(figsize=(8, 5))
names = list(scenario_info.keys())
probs = [scenario_info[n]["prob"] for n in names]
means = [scenario_profiles[n].mean() for n in names]

ax1.bar(names, means, color="steelblue")
ax1.set_ylabel(f"Average price [{price_unit}]")

ax2 = ax1.twinx()
ax2.plot(names, probs, color="darkred", marker="o", linestyle="--")
ax2.set_ylabel("Probability", color="darkred")
ax2.tick_params(axis="y", labelcolor="darkred")

ax1.set_title("Average price and probability per scenario")
plt.tight_layout()
plt.savefig("scenario_summary.png", dpi=150)
plt.show()

# ---- Summary table ----
summary = pd.DataFrame({
    "Scenario": names,
    "Date": [selected_days[n] for n in names],
    "Description": [scenario_info[n]["desc"] for n in names],
    "Probability": probs,
    "Mean_price_EUR_per_MWh": [round(scenario_profiles[n].mean(), 2) for n in names],
    "Max_price_EUR_per_MWh": [round(scenario_profiles[n].max(), 2) for n in names],
    "Min_price_EUR_per_MWh": [round(scenario_profiles[n].min(), 2) for n in names],
})
print("\nSummary table:")
print(summary.to_string(index=False))
summary.to_csv("scenario_summary.csv", index=False)