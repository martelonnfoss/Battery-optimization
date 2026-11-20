"""
Figur 1: Electricity prices over the 48-hour planning horizon.

Døgn 1: kjent pris = gjennomsnittsdagen fra data_prep/find_average_day.py
Døgn 2: fem prisscenarier fra data_prep/find_scenario_days.py

Kjør først find_average_day.py og find_scenario_days.py, deretter dette skriptet.
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# ---- Filstier (samme filer som find_average_day.py og find_scenario_days.py lager) ----
prosjektmappe = Path(__file__).resolve().parent.parent
datamappe = prosjektmappe / "data" / "clean_data"

gjennomsnittsdag_fil = datamappe / "gjennomsnittsdag_NO2_2025.csv"   # fra find_average_day.py
scenariodager_fil = datamappe / "scenariodager_NO2_2025.csv"         # fra find_scenario_days.py

dag1 = pd.read_csv(gjennomsnittsdag_fil).sort_values("time_start")
dag2 = pd.read_csv(scenariodager_fil)

scenarioer = ["s1", "s2", "s3", "s4", "s5"]
farger = {
    "s1": "blue",
    "s2": "darkorange",
    "s3": "green",
    "s4": "red",
    "s5": "purple",
}

# ---- Stil som ligner LaTeX ----
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Computer Modern Roman", "CMU Serif", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "cm",
    "font.size": 11,
})

fig, ax = plt.subplots(figsize=(9, 4.5))

# Døgn 1: kjente priser, modelltime 1–24
timer_dag1 = dag1["time_start"] + 1
ax.plot(timer_dag1, dag1["EUR_per_MWh"], color="black", marker="o",
        markersize=4, linewidth=1.2, label="Day 1: known prices")

# Døgn 2: scenarier, modelltime 25–48
for s in scenarioer:
    dag = dag2[dag2["scenario"] == s].sort_values("time_start")
    ax.plot(dag["time_start"] + 25, dag["EUR_per_MWh"], color=farger[s],
            marker="o", markersize=4, linewidth=1.2, label=s)

# Skille mellom døgnene
ax.axvline(24.5, color="gray", linestyle="--", linewidth=1.2)

ymax = 240
ax.text(12.5, ymax * 0.93, "Day 1", ha="center")
ax.text(36.5, ymax * 0.93, "Day 2", ha="center")

ax.set_xlim(1, 48)
ax.set_ylim(0, ymax)
ax.set_xticks([1, 6, 12, 18, 24, 30, 36, 42, 48])
ax.set_yticks([0, 50, 100, 150, 200])
ax.set_xlabel("Model hour")
ax.set_ylabel("Price [EUR/MWh]")
ax.grid(True, color="0.9", linewidth=0.8)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3,
          fontsize=9, frameon=False, handlelength=2)

plt.tight_layout()

utfil_png = prosjektmappe / "analyses" / "prisscenarioer_48t.png"
plt.savefig(utfil_png, dpi=200, bbox_inches="tight")
print(f"Lagret figur: {utfil_png}")
plt.show()
