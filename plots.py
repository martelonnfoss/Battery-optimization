import pandas as pd
import matplotlib.pyplot as plt

# ---- Last inn data ----
df = pd.read_csv("NO2_2025.csv")
df["time_start"] = pd.to_datetime(df["time_start"], utc=True).dt.tz_convert("Europe/Oslo")
df["date"] = df["time_start"].dt.date
df["hour"] = df["time_start"].dt.hour

price_col = "NOK_per_kWh"

# ---- Beregn dags-statistikk ----
daily = df.groupby("date")[price_col].agg(["mean", "min", "max"]).reset_index()
daily["range"] = daily["max"] - daily["min"]

# ---- Definer scenarioene ----
scenario_info = {
    "S1": {"pct": 0.10, "desc": "Low price level, small variations", "prob": 0.10},
    "S2": {"pct": 0.30, "desc": "Low/moderate price level",          "prob": 0.20},
    "S3": {"pct": 0.50, "desc": "Normal/typical price day",          "prob": 0.40},
    "S4": {"pct": 0.75, "desc": "High price level, larger variations","prob": 0.20},
    "S5": {"pct": 0.98, "desc": "Extreme/high price day, peak(s)",   "prob": 0.10},
}

# ---- Velg representativ dag for hvert scenario ----
selected_days = {}
for name, info in scenario_info.items():
    if name == "S5":
        # Ekte ekstremdag: dagen med høyeste maks-pris i hele datasettet
        chosen = daily.loc[daily["max"].idxmax()]
    else:
        target = daily["mean"].quantile(info["pct"])
        candidates = daily.iloc[(daily["mean"] - target).abs().argsort()[:10]]
        if name in ["S1", "S3"]:
            chosen = candidates.sort_values("range").iloc[0]        # lav variasjon
        elif name == "S4":
            chosen = candidates.sort_values("range", ascending=False).iloc[0]  # høy variasjon
        else:
            chosen = candidates.iloc[0]
    selected_days[name] = chosen["date"]

print("Valgte dager per scenario:")
for name, d in selected_days.items():
    print(f"  {name}: {d}")

# ---- Hent timesprofiler for valgte dager ----
scenario_profiles = {
    name: df[df["date"] == d].sort_values("hour").set_index("hour")[price_col]
    for name, d in selected_days.items()
}

# ---- Plot 1: Timesprofil for hvert scenariodøgn ----
fig, ax = plt.subplots(figsize=(10, 6))
for name, profile in scenario_profiles.items():
    ax.plot(profile.index, profile.values, marker="o",
            label=f"{name} ({selected_days[name]}) - {scenario_info[name]['desc']}")

ax.set_xlabel("Time på døgnet")
ax.set_ylabel("Pris (NOK/kWh)")
ax.set_title("Representative scenariodøgn for NO2, 2025")
ax.set_xticks(range(0, 24))
ax.legend(fontsize=8, loc="upper left")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("scenario_profiles.png", dpi=150)
plt.show()

# ---- Plot 2: Sannsynlighet vs. gjennomsnittspris per scenario ----
fig, ax1 = plt.subplots(figsize=(8, 5))
names = list(scenario_info.keys())
probs = [scenario_info[n]["prob"] for n in names]
means = [scenario_profiles[n].mean() for n in names]

ax1.bar(names, means, color="steelblue")
ax1.set_ylabel("Gjennomsnittspris (NOK/kWh)")

ax2 = ax1.twinx()
ax2.plot(names, probs, color="darkred", marker="o", linestyle="--")
ax2.set_ylabel("Sannsynlighet", color="darkred")
ax2.tick_params(axis="y", labelcolor="darkred")

ax1.set_title("Gjennomsnittspris og sannsynlighet per scenario")
plt.tight_layout()
plt.savefig("scenario_summary.png", dpi=150)
plt.show()

# ---- Oppsummeringstabell ----
summary = pd.DataFrame({
    "Scenario": names,
    "Dato": [selected_days[n] for n in names],
    "Beskrivelse": [scenario_info[n]["desc"] for n in names],
    "Sannsynlighet": probs,
    "Snittpris": [round(scenario_profiles[n].mean(), 3) for n in names],
    "Makspris": [round(scenario_profiles[n].max(), 3) for n in names],
    "Minpris": [round(scenario_profiles[n].min(), 3) for n in names],
})
print("\nOppsummeringstabell:")
print(summary.to_string(index=False))
summary.to_csv("scenario_summary.csv", index=False)