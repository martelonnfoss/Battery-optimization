"""
Illustrasjon av den stokastiske løsningen (to-trinns stokastisk optimering).

Øverst:  prisene over 48 timer (døgn 1 kjent, døgn 2 fem scenarier).
Nederst: batteriets energinivå. Døgn 1 er én felles plan for alle scenarier
         (beslutningen tas før prisen for døgn 2 er kjent), mens døgn 2
         har én tilpasset plan per scenario.

Leser resultatene fra modell/part2/resultater_stokastisk_s1–s5.csv,
som lages av modell/part2/stokastisk.py. Kjør stokastisk.py først.
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

prosjektmappe = Path(__file__).resolve().parent.parent
resultatmappe = prosjektmappe / "modell" / "part2"

scenarioer = ["s1", "s2", "s3", "s4", "s5"]
farger = {
    "s1": "blue",
    "s2": "darkorange",
    "s3": "green",
    "s4": "red",
    "s5": "purple",
}

resultater = {
    s: pd.read_csv(resultatmappe / f"resultater_stokastisk_{s}.csv", index_col="time")
    for s in scenarioer
}

# ---- Stil som ligner LaTeX ----
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Computer Modern Roman", "CMU Serif", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "cm",
    "font.size": 11,
})

fig, (ax_pris, ax_energi) = plt.subplots(2, 1, figsize=(9, 7), sharex=True,
                                         gridspec_kw={"height_ratios": [1, 1]})

timer_dag1 = list(range(1, 25))
timer_dag2 = list(range(25, 49))
# Energilinjene i døgn 2 starter i time 24, så de henger sammen med felles plan
timer_dag2_energi = [24] + timer_dag2

# ---- Øverst: priser ----
ax_pris.plot(timer_dag1, resultater["s1"].loc[timer_dag1, "pris_EUR_MWh"],
             color="black", marker="o", markersize=3, linewidth=1.2,
             label="Day 1: known prices")
for s in scenarioer:
    ax_pris.plot(timer_dag2, resultater[s].loc[timer_dag2, "pris_EUR_MWh"],
                 color=farger[s], marker="o", markersize=3, linewidth=1.2, label=s)
ax_pris.set_ylabel("Price [EUR/MWh]")
ax_pris.set_ylim(bottom=0)

# ---- Nederst: energinivå i batteriet ----
ax_energi.plot(timer_dag1, resultater["s1"].loc[timer_dag1, "energi_MWh"],
               color="black", marker="o", markersize=3, linewidth=1.5,
               label="Day 1: common decision")
for s in scenarioer:
    ax_energi.plot(timer_dag2_energi, resultater[s].loc[timer_dag2_energi, "energi_MWh"],
                   color=farger[s], marker="o", markersize=3, linewidth=1.2, label=s)
ax_energi.set_ylabel("Stored energy [MWh]")
ax_energi.set_xlabel("Model hour")
ax_energi.set_ylim(0, 120)

# ---- Felles for begge panelene ----
for ax in (ax_pris, ax_energi):
    ax.axvline(24.5, color="gray", linestyle="--", linewidth=1.2)
    ax.grid(True, color="0.9", linewidth=0.8)
    ax.set_xlim(1, 48)
    ymax = ax.get_ylim()[1]
    ax.text(12.5, ymax * 0.92, "Day 1", ha="center")
    ax.text(36.5, ymax * 0.92, "Day 2", ha="center")
ax_energi.set_xticks([1, 6, 12, 18, 24, 30, 36, 42, 48])

ax_pris.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3,
               fontsize=9, frameon=False)
ax_energi.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=6,
                 fontsize=9, frameon=False)

plt.tight_layout()
utfil = prosjektmappe / "analyses" / "stokastisk_losning.png"
plt.savefig(utfil, dpi=200, bbox_inches="tight")
print(f"Lagret figur: {utfil}")
plt.show()
