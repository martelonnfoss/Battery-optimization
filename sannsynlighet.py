import pandas as pd
from scipy.stats import skew

df = pd.read_csv("NO2_2025.csv")
df["time_start"] = pd.to_datetime(df["time_start"], utc=True).dt.tz_convert("Europe/Oslo")
df["date"] = df["time_start"].dt.date

price_col = "NOK_per_kWh"
daily_mean = df.groupby("date")[price_col].mean()

print("Skjevhet (skewness) i daglig snittpris:", round(skew(daily_mean), 2))
print("(0 = symmetrisk, >0 = høyreskjev/lang hale mot høye priser, <0 = venstreskjev)")

# Histogram for visuell sjekk
import matplotlib.pyplot as plt
plt.hist(daily_mean, bins=30, edgecolor="black")
plt.xlabel("Daglig gjennomsnittspris (NOK/kWh)")
plt.ylabel("Antall dager")
plt.title("Fordeling av daglig gjennomsnittspris, NO2 2025")
plt.savefig("price_distribution.png", dpi=150)
plt.show()