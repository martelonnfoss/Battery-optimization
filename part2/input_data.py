import numpy as np
import pandas as pd


def read_profile(frame):
    """Returner 24 kronologiske priser i EUR/MWh."""
    frame = frame.sort_values("time_start").copy()

    if len(frame) != 24:
        raise ValueError("Hver prisprofil må ha 24 rader.")

    starts = pd.to_numeric(frame["time_start"], errors="raise")
    ends = pd.to_numeric(frame["time_end"], errors="raise")

    if not np.array_equal(starts.to_numpy(), np.arange(24)):
        raise ValueError("time_start må være 0, 1, ..., 23.")

    if not np.array_equal(ends.to_numpy(), np.arange(1, 25)):
        raise ValueError("time_end må være 1, 2, ..., 24.")

    prices = pd.to_numeric(frame["EUR_per_MWh"], errors="raise")

    if not np.isfinite(prices.to_numpy()).all():
        raise ValueError("Prisene må være endelige tall uten mangler.")

    return prices.tolist()


def load_prices(day1_path, scenarios_path):
    day1_frame = pd.read_csv(day1_path)
    scenarios_frame = pd.read_csv(scenarios_path)

    if scenarios_frame["scenario"].isna().any():
        raise ValueError("Scenario-ID kan ikke mangle.")

    required = {"s1", "s2", "s3", "s4", "s5"}
    if set(scenarios_frame["scenario"]) != required:
        raise ValueError("Scenarioene må være s1, s2, s3, s4 og s5.")

    day1 = read_profile(day1_frame)

    day2 = {
        s: read_profile(scenarios_frame.query("scenario == @s"))
        for s in sorted(required)
    }

    return day1, day2