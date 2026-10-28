from pathlib import Path

import matplotlib.pyplot as plt
import pyomo.environ as pyo

from input_data import load_prices
from battery_model import build_model
from run_comparison import solve_model


def plot_sp_energy(sp):
    """Figur 1: felles dag 1 og scenarioavhengig dag 2."""
    fig, ax = plt.subplots(figsize=(9, 4.5))

    # E_t er energien ved slutten av time t.
    # Derfor tar vi også med startpunktet ved time 0.
    hours1 = list(range(25))
    energy1 = [pyo.value(sp.E_init)] + [
        pyo.value(sp.E1[t]) for t in sp.T1
    ]

    ax.plot(
        hours1, energy1,
        color="black", linewidth=2.5,
        label="Common first-stage schedule",
    )

    # Alle scenariokurvene starter i det samme punktet ved time 24.
    for s in sp.S:
        hours2 = [24] + list(sp.T2)
        energy2 = [pyo.value(sp.E1[24])] + [
            pyo.value(sp.E2[t, s]) for t in sp.T2
        ]
        ax.plot(hours2, energy2, label=s)

    ax.axvline(24, color="grey", linestyle=":", linewidth=1)
    ax.axhline(
        pyo.value(sp.E_min),
        color="grey", linestyle="--", linewidth=1,
    )
    ax.axhline(
        pyo.value(sp.E_max),
        color="grey", linestyle="--", linewidth=1,
    )

    ax.set(
        xlabel="Elapsed time [h]",
        ylabel="Stored energy [MWh]",
        title="Stochastic battery schedule",
        xlim=(0, 48),
        ylim=(0, 110),
    )
    ax.grid(alpha=0.25)
    ax.legend(ncol=2)
    fig.tight_layout()

    # fig.savefig("sp_energy.png", dpi=300, bbox_inches="tight")
    return fig


def plot_day1_operation(sp, ev):
    """Figur 2: pris og drift på dag 1."""
    fig, axes = plt.subplots(
        3, 1, figsize=(9, 8), sharex=True
    )

    hours = list(sp.T1)

    prices = [pyo.value(sp.lambda1[t]) for t in hours]
    axes[0].step(hours, prices, where="mid", color="black")
    axes[0].set_ylabel("Price\n[EUR/MWh]")

    # Positiv nettoeffekt betyr levering til nettet.
    for model, name, style in [
        (sp, "SP", "-"),
        (ev, "EV", "--"),
    ]:
        net_export = [
            pyo.value(model.P_dis1[t] - model.P_ch1[t])
            for t in hours
        ]
        axes[1].step(
            hours, net_export,
            where="mid", linestyle=style,
            linewidth=2, label=name,
        )

        energy = [
            pyo.value(model.E1[t]) for t in hours
        ]
        axes[2].plot(
            hours, energy,
            linestyle=style, linewidth=2, label=name,
        )

    axes[1].axhline(0, color="grey", linewidth=0.8)
    axes[1].set_ylabel("Net export\n[MW]")
    axes[2].set_ylabel("Stored energy\n[MWh]")
    axes[2].set_xlabel("Hour")

    for ax in axes:
        ax.grid(alpha=0.25)

    axes[1].legend()
    axes[2].legend()
    axes[0].set_title("First-stage operation: EV and SP")

    fig.tight_layout()

    # fig.savefig("day1_operation.png", dpi=300, bbox_inches="tight")
    return fig


def plot_linking_energy(sp, ev, perfect_information):
    """Figur 3: sammenlign energien som overføres til dag 2."""
    labels = ["EV", "SP"] + [
        f"PI: {s}" for s in perfect_information
    ]

    levels = [
        pyo.value(ev.E1[24]),
        pyo.value(sp.E1[24]),
    ] + [
        pyo.value(model.E1[24])
        for model in perfect_information.values()
    ]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    colors = ["tab:orange", "tab:blue"] + [
        "tab:grey"
    ] * len(perfect_information)

    bars = ax.bar(labels, levels, color=colors)
    ax.bar_label(bars, fmt="%.2f", padding=3)

    ax.axhline(
        pyo.value(sp.E_min),
        color="grey", linestyle="--", linewidth=1,
    )
    ax.set(
        ylabel="Stored energy after hour 24 [MWh]",
        title="Energy transferred to the second stage",
        ylim=(0, 115),
    )
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    fig.tight_layout()

    # fig.savefig("energy_after_hour24.png", dpi=300, bbox_inches="tight")
    return fig


def main():
    root = Path(__file__).resolve().parent.parent

    day1, day2 = load_prices(
        root / "data" / "clean_data" / "gjennomsnittsdag_NO2_2025.csv",
        root / "scenariodager_NO2_2025.csv",
    )

    probabilities = {s: 0.2 for s in day2}

    sp = solve_model(
        build_model(day1, day2, probabilities)
    )

    mean_profile = [
        sum(probabilities[s] * day2[s][h] for s in day2)
        for h in range(24)
    ]

    ev = solve_model(
        build_model(day1, {"EV": mean_profile}, {"EV": 1.0})
    )

    perfect_information = {
        s: solve_model(
            build_model(day1, {s: day2[s]}, {s: 1.0})
        )
        for s in day2
    }

   

    plot_sp_energy(sp)
    plt.show(block=True)
    
    plot_day1_operation(sp, ev)
    plt.show(block=True)
    
    plot_linking_energy(sp, ev, perfect_information)
    plt.show(block=True)


if __name__ == "__main__":
   main()