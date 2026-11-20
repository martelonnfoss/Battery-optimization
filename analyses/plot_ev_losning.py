"""
Illustrasjon av expected value-løsningen (EV).

Øverst:  prisene over 48 timer. Døgn 1 er kjent, og i døgn 2 brukes én
         forventet pris (EV) i stedet for de fem scenarioene.
Nederst: batteriets energinivå. Siden modellen bare ser én pris for døgn 2,
         blir det én plan over hele horisonten.

Leser resultatene fra modell/part2/resultater_EV.csv,
som lages av modell/part2/forventet_verdi.py. Kjør forventet_verdi.py først.
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

prosjektmappe = Path(__file__).resolve().parent.parent
resultater = pd.read_csv(prosjektmappe / "modell" / "part2" / "resultater_EV.csv",
                         index_col="time")

ev_farge = "crimson"

# ---- Stil som ligner LaTeX (samme som de andre figurene) ----
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Computer Modern Roman", "CMU Serif", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "cm",
    "font.size": 11,
})

fig, (ax_pris, ax_energi) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

timer_dag1 = list(range(1, 25))
timer_dag2 = list(range(25, 49))
# Energilinjen i døgn 2 starter i time 24, så den henger sammen med døgn 1
timer_dag2_energi = [24] + timer_dag2

# ---- Øverst: priser ----
ax_pris.plot(timer_dag1, resultater.loc[timer_dag1, "pris_EUR_MWh"],
             color="black", marker="o", markersize=3, linewidth=1.2,
             label="Day 1: known prices")
ax_pris.plot(timer_dag2, resultater.loc[timer_dag2, "pris_EUR_MWh"],
             color=ev_farge, marker="o", markersize=3, linewidth=1.2,
             label="Day 2: expected value (EV)")
ax_pris.set_ylabel("Price [EUR/MWh]")
ax_pris.set_ylim(0, 240)   # samme skala som de andre prisfigurene

# ---- Nederst: energinivå i batteriet ----
ax_energi.plot(timer_dag1, resultater.loc[timer_dag1, "energi_MWh"],
               color="black", marker="o", markersize=3, linewidth=1.5,
               label="Day 1")
ax_energi.plot(timer_dag2_energi, resultater.loc[timer_dag2_energi, "energi_MWh"],
               color=ev_farge, marker="o", markersize=3, linewidth=1.2,
               label="Day 2: EV")
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

ax_pris.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2,
               fontsize=9, frameon=False)
ax_energi.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2,
                 fontsize=9, frameon=False)

plt.tight_layout()
utfil = prosjektmappe / "analyses" / "ev_losning.png"
plt.savefig(utfil, dpi=200, bbox_inches="tight")
print(f"Lagret figur: {utfil}")
plt.show()
