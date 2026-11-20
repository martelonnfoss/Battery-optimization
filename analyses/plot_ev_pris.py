"""
Plotter forventet pris (EV) over 48-timershorisonten.

Døgn 1: kjente priser (gjennomsnittsdag).
Døgn 2: de fem scenarioene stiplet, og forventet pris (EV) som heltrukken linje,
        slik at man ser at EV er det sannsynlighetsvektede snittet av scenarioene.

Prisene hentes fra modell/prisdata.py, samme kilde som optimeringsmodellen bruker.
"""
import sys
from pathlib import Path
import matplotlib.pyplot as plt

prosjektmappe = Path(__file__).resolve().parent.parent
sys.path.append(str(prosjektmappe / "modell"))
from prisdata import priser, scenarioer  # noqa: E402

farger = {
    "s1": "tab:blue",
    "s2": "tab:orange",
    "s3": "tab:green",
    "s4": "tab:brown",
    "s5": "tab:purple",
}

timer_dag1 = list(range(1, 25))
timer_dag2 = list(range(25, 49))

fig, ax = plt.subplots(figsize=(10, 4.5))

# Døgn 1: kjente priser
ax.plot(timer_dag1, priser.loc[timer_dag1, "s1"], color="black",
        marker="o", markersize=3, linewidth=1.5, label="Day 1: known prices")

# Døgn 2: scenarioene stiplet
for s in scenarioer:
    ax.plot(timer_dag2, priser.loc[timer_dag2, s],
            color=farger[s], linestyle="--", linewidth=1.2, alpha=0.75,
            label=s)

# Døgn 2: forventet pris (EV) heltrukken
ax.plot(timer_dag2, priser.loc[timer_dag2, "forventet_pris"],
        color="crimson", linewidth=2.5, marker="o", markersize=4,
        label="Expected value (EV)")

# Skille mellom døgnene
ax.axvline(24.5, color="gray", linestyle="--", linewidth=1)
ymax = priser[scenarioer].max().max()
ax.text(12.5, ymax * 1.02, "Day 1", ha="center")
ax.text(36.5, ymax * 1.02, "Day 2", ha="center")

ax.set_xlim(1, 48)
ax.set_ylim(0, ymax * 1.10)
ax.set_xticks([1, 6, 12, 18, 24, 30, 36, 42, 48])
ax.set_xlabel("Model hour")
ax.set_ylabel("Price [EUR/MWh]")
ax.grid(True, alpha=0.3)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.22), ncol=4,
          fontsize=8, frameon=False)

plt.tight_layout()
utfil = prosjektmappe / "analyses" / "ev_prisprofil.png"
plt.savefig(utfil, dpi=200, bbox_inches="tight")
print(f"Lagret figur: {utfil}")
plt.show()
