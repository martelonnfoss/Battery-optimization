from pathlib import Path

import pandas as pd
import pyomo.environ as pyo

from input_data import load_prices
from battery_model import build_model


def solve_model(model, solver_name="gurobi"):
    solver = pyo.SolverFactory(solver_name)

    if not solver.available(exception_flag=False):
        raise RuntimeError(f"Solver er ikke tilgjengelig: {solver_name}")

    result = solver.solve(model)

    if not pyo.check_optimal_termination(result):
        raise RuntimeError(
            f"Ingen bekreftet optimal løsning: "
            f"{result.solver.termination_condition}"
        )

    return model


def summary_row(name, model):
    return {
        "case": name,
        "objective_EUR": pyo.value(model.objective),
        "day1_profit_EUR": pyo.value(model.profit1),
        "expected_day2_profit_EUR": sum(
            pyo.value(model.rho[s] * model.profit2[s])
            for s in model.S
        ),
        "E24_MWh": pyo.value(model.E1[24]),
    }


def main():
    project_root = Path(__file__).resolve().parent.parent

    # Juster disse hvis datafilene er lagret et annet sted.
    day1_path = project_root / "data" / "clean_data" / "gjennomsnittsdag_NO2_2025.csv"
    scenarios_path = project_root / "scenariodager_NO2_2025.csv"

    day1, day2 = load_prices(day1_path, scenarios_path)

    # De fem faktiske scenarioene er like sannsynlige.
    probabilities = {s: 0.2 for s in day2}

    rows = []

    # 1. Stokastisk løsning
    sp = solve_model(build_model(day1, day2, probabilities))
    rows.append(summary_row("SP", sp))

    # 2. Expected-value-modell: gjennomsnittspris for hver time
    mean_profile = [
        sum(probabilities[s] * day2[s][h] for s in day2)
        for h in range(24)
    ]

    ev = solve_model(
        build_model(day1, {"EV": mean_profile}, {"EV": 1.0})
    )
    rows.append(summary_row("EV", ev))

    # 3. Ett scenario om gangen, kjent på forhånd
    ws_value = 0.0

    for s in day2:
        model = solve_model(
            build_model(day1, {s: day2[s]}, {s: 1.0})
        )

        rows.append(summary_row(f"Perfect information: {s}", model))
        ws_value += probabilities[s] * pyo.value(model.objective)

    print(pd.DataFrame(rows).to_string(index=False))
    print(f"\nForventet overskudd med perfekt informasjon: {ws_value:.2f} EUR")
    print(f"Stokastisk overskudd: {pyo.value(sp.objective):.2f} EUR")


if __name__ == "__main__":
    main()