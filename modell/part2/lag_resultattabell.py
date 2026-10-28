import pandas as pd
from pathlib import Path


# 1. Finn mappen med resultatfilene

mappe = Path(__file__).resolve().parent


# 2. Les resultatene fra de tre metodene

ev = pd.read_csv(mappe / "oppsummering_EV.csv")

scenario = pd.read_csv(
    mappe / "scenario_resultater.csv"
).sort_values("scenario")

stokastisk = pd.read_csv(
    mappe / "oppsummering_stokastisk.csv"
)


# 3. Beregn forventet profitt for den stokastiske løsningen

stokastisk_profitt = (
    stokastisk["sannsynlighet"]
    * stokastisk["total_profitt_EUR"]
).sum()

# Alle scenariene har samme energi etter time 24.
stokastisk_energi = stokastisk["energi_time24_MWh"].iloc[0]


# 4. Samle radene til tabellen

rader = []

rader.append([
    "EV: forventet prisbane",
    ev["profitt_EUR"].iloc[0],
    ev["energi_time24_MWh"].iloc[0]
])

for _, rad in scenario.iterrows():
    rader.append([
        f"Scenario {rad['scenario']} kjent på forhånd",
        rad["profitt_EUR"],
        rad["energi_time24_MWh"]
    ])

rader.append([
    "Stokastisk løsning",
    stokastisk_profitt,
    stokastisk_energi
])


# 5. Formater tall med to desimaler
# Eksempel: 7224.4016 blir 7\,224,40 i LaTeX.

def formater_tall(tall):
    tekst = f"{tall:,.2f}"
    tekst = tekst.replace(",", " ")
    tekst = tekst.replace(".", ",")
    tekst = tekst.replace(" ", r"\,")
    return tekst


# 6. Lag LaTeX-tabellen

latex = r"""\begin{table}[htbp]
\centering
\small
\caption{Objektverdier over 48 timer og lagret energi etter døgn 1.}
\label{tab:resultater-del2}
\begin{tabular}{lrr}
\toprule
Løsning & \shortstack{Objektverdi\\[EUR]} & \shortstack{$E_{24}$\\[MWh]} \\
\midrule
"""

for navn, profitt, energi in rader:
    latex += (
        f"{navn} & "
        f"{formater_tall(profitt)} & "
        f"{formater_tall(energi)}"
        + r" \\"
        + "\n"
    )

latex += r"""\bottomrule
\end{tabular}

\medskip
\begin{minipage}{0.95\linewidth}
\footnotesize
EV-verdien gjelder den forventede prisbanen.
Scenarioverdiene gjelder hvert scenario kjent på forhånd.
Den stokastiske verdien er forventet profitt med 20\,\%
sannsynlighet for hvert scenario.
Alle løsningene har sluttenergi på 50 MWh.
\end{minipage}
\end{table}
"""


# 7. Skriv ut tabellen og lagre den som en tekstfil

print(latex)

(mappe / "resultattabell.tex").write_text(
    latex,
    encoding="utf-8"
)