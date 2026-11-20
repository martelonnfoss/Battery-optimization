import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # project root, so 'modell' can be imported

from pathlib import Path

import pandas as pd
import pyomo.environ as pyo

import modell.batteriparametere as b
from modell.part2.batterimodell import lag_modell
from modell.prisdata import priser, scenarioer, sannsynlighet


# 1. Løs en modell og kontroller solverstatus
#
# Objektivverdier og dualer brukes bare dersom modellen
# er løst optimalt.

def los_modell(modell, solver):

    resultat = solver.solve(modell)

    if not pyo.check_optimal_termination(resultat):
        raise RuntimeError(
            "Modellen ble ikke løst optimalt: "
            f"{resultat.solver.termination_condition}. "
            "Denne implementeringen forutsetter mulig recourse."
        )


# 2. Bygg masterproblemet
#
# Masteren velger driften i time 1–24.
# alfa er et optimistisk estimat på forventet dag-2-profitt.

def lag_master(pris_dag1):

    m = pyo.ConcreteModel()
    m.T = pyo.RangeSet(1, 24)

    m.lading = pyo.Var(m.T, bounds=(0, b.P_lading_max))
    m.utlading = pyo.Var(m.T, bounds=(0, b.P_utlading_max))
    m.energi = pyo.Var(m.T, bounds=(b.E_min, b.E_max))

    # Forventet profitt kan være negativ.
    m.alfa = pyo.Var(domain=pyo.Reals)

    def energibalanse(m, t):

        forrige = b.E_start if t == 1 else m.energi[t - 1]

        return m.energi[t] == (
            forrige
            + b.eta_lading * m.lading[t] * b.delta_t
            - m.utlading[t] * b.delta_t / b.eta_utlading
        )

    m.energibalanse = pyo.Constraint(m.T, rule=energibalanse)

    m.profitt_dag1 = pyo.Expression(
        expr=sum(
            pris_dag1[t]
            * (m.utlading[t] - m.lading[t])
            * b.delta_t
            for t in m.T
        )
    )

    # Alle kutt beholdes gjennom algoritmen.
    m.kutt = pyo.ConstraintList()

    m.profitt = pyo.Objective(
        expr=m.profitt_dag1 + m.alfa,
        sense=pyo.maximize
    )

    return m


# 3. Bygg delproblemet for ett scenario
#
# Delproblemet velger driften i time 25–48.
# Startenergien fastsettes gjennom en eksplisitt koblingslikning.
# Dualen til denne likningen brukes i optimalitetskuttet.

def lag_delproblem(pris_scenario):

    m = pyo.ConcreteModel()
    m.T = pyo.RangeSet(25, 48)

    m.lading = pyo.Var(m.T, bounds=(0, b.P_lading_max))
    m.utlading = pyo.Var(m.T, bounds=(0, b.P_utlading_max))
    m.energi = pyo.Var(m.T, bounds=(b.E_min, b.E_max))

    m.e_start = pyo.Var(domain=pyo.Reals)

    m.E24_fast = pyo.Param(
        initialize=b.E_start,
        mutable=True
    )

    # Rapportens likning (29).
    m.kobling = pyo.Constraint(expr=m.e_start == m.E24_fast)

    def energibalanse(m, t):

        forrige = m.e_start if t == 25 else m.energi[t - 1]

        return m.energi[t] == (
            forrige
            + b.eta_lading * m.lading[t] * b.delta_t
            - m.utlading[t] * b.delta_t / b.eta_utlading
        )

    m.energibalanse = pyo.Constraint(m.T, rule=energibalanse)
    m.sluttkrav = pyo.Constraint(expr=m.energi[48] == b.E_start)

    # Sannsynligheten tas med ved aggregeringen, ikke her.
    m.profitt = pyo.Objective(
        expr=sum(
            pris_scenario[t]
            * (m.utlading[t] - m.lading[t])
            * b.delta_t
            for t in m.T
        ),
        sense=pyo.maximize
    )

    m.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)

    return m


# 4. Evaluer alle scenarioer ved samme E24
#
# Hent optimal profitt og koblingsdual for hvert scenario.
# Beregn deretter de sannsynlighetsvektede gjennomsnittene.

def evaluer_delproblemer(delproblemer, energi, vekter, solver):

    phi_forventet = 0.0
    pi_forventet = 0.0

    for s, m in delproblemer.items():

        m.E24_fast.set_value(energi)
        los_modell(m, solver)

        phi = pyo.value(m.profitt)
        pi = m.dual.get(m.kobling)

        if pi is None:
            raise RuntimeError(f"Mangler koblingsdual for scenario {s}.")

        phi_forventet += vekter[s] * phi
        pi_forventet += vekter[s] * pi

    return phi_forventet, pi_forventet


# 5. Legg til et aggregert optimalitetskutt
#
# alfa <= forventet profitt ved undersøkt E24
#         + forventet dual * (ny E24 - undersøkt E24)

def legg_til_kutt(master, energi, phi, pi):

    master.kutt.add(
        master.alfa <= phi + pi * (master.energi[24] - energi)
    )


# 6. Ta en kopi av førstetrinnsplanen
#
# Kopien bevares selv om masteren får nye verdier senere.

def hent_timeplan(master):

    return pd.DataFrame({
        "time": list(master.T),
        "lading_MW": [pyo.value(master.lading[t]) for t in master.T],
        "utlading_MW": [pyo.value(master.utlading[t]) for t in master.T],
        "energi_MWh": [pyo.value(master.energi[t]) for t in master.T]
    })


# 7. Kjør Benders-algoritmen
#
# Pseudokode:
#
# Lag et første kutt ved E24 = E_start.
# Sett LB = -uendelig og UB = +uendelig.
#
# Gjenta:
#   Løs masteren og oppdater UB.
#   Evaluer delproblemene ved masterens E24.
#   Oppdater LB og behold beste gjennomførbare plan.
#   Stopp hvis UB - LB er innenfor toleransen.
#   Ellers legg til et nytt kutt.

def los_benders(
    pris_dag1,
    pris_dag2,
    vekter,
    solver,
    relativ_toleranse=1e-6,
    absolutt_toleranse=1e-4,
    maks_iterasjoner=200
):

    master = lag_master(pris_dag1)

    delproblemer = {
        s: lag_delproblem(pris_dag2[s])
        for s in vekter
    }

    # Første kutt hindrer at masteren blir ubegrenset.
    phi, pi = evaluer_delproblemer(
        delproblemer, b.E_start, vekter, solver
    )
    legg_til_kutt(master, b.E_start, phi, pi)

    LB = float("-inf")
    UB = float("inf")
    beste = None
    historikk = []

    for k in range(1, maks_iterasjoner + 1):

        # a. Løs masteren med kuttene som finnes.
        los_modell(master, solver)

        energi = pyo.value(master.energi[24])
        dag1 = pyo.value(master.profitt_dag1)
        alfa = pyo.value(master.alfa)
        masterverdi = pyo.value(master.profitt)

        # b. Masteren gir en øvre grense ved maksimering.
        UB = min(UB, masterverdi)

        # c. Beregn faktisk forventet profitt på dag 2.
        phi, pi = evaluer_delproblemer(
            delproblemer, energi, vekter, solver
        )

        faktisk_totalprofitt = dag1 + phi

        # d. Behold den beste gjennomførbare løsningen.
        if faktisk_totalprofitt > LB:

            LB = faktisk_totalprofitt

            beste = {
                "totalprofitt": faktisk_totalprofitt,
                "profitt_dag1": dag1,
                "profitt_dag2": phi,
                "E24": energi,
                "timeplan": hent_timeplan(master)
            }

        # e. Kontroller grensene og beregn stoppkriteriet.
        gap = UB - LB

        # Relativt gap i prosent av nedre grense (som i rapporten).
        gap_prosent = 100 * gap / max(1.0, abs(LB))

        tillatt_gap = (
            absolutt_toleranse
            + relativ_toleranse * max(1.0, abs(LB))
        )

        numerisk_margin = (
            1e-6 + 1e-8 * max(1.0, abs(LB), abs(UB))
        )

        if gap < -numerisk_margin:
            raise RuntimeError(
                f"UB < LB i iterasjon {k}. "
                "Kontroller dualfortegn og kutt."
            )

        historikk.append({
            "iterasjon": k,
            "E24_MWh": energi,
            "alfa_EUR": alfa,
            "faktisk_dag2_EUR": phi,
            "dual_EUR_per_MWh": pi,
            "LB_EUR": LB,
            "UB_EUR": UB,
            "gap_EUR": gap,
            "gap_prosent": gap_prosent
        })

        print(
            f"Iterasjon {k}: E24={energi:.4f}, "
            f"LB={LB:.6f}, UB={UB:.6f}, gap={gap:.6f}, "
            f"gap={gap_prosent:.4f} %"
        )

        if gap <= tillatt_gap:
            return beste, pd.DataFrame(historikk)

        # f. Oppdater masteren før neste iterasjon.
        legg_til_kutt(master, energi, phi, pi)

    raise RuntimeError(
        f"Ingen konvergens etter {maks_iterasjoner} iterasjoner. "
        f"LB={LB:.6f}, UB={UB:.6f}."
    )


# 8. Hent data og kjør algoritmen
#
# Prisformatet er identisk med stokastisk.py:
#   pris_dag1[t], t = 1,...,24
#   pris_dag2[s][t], t = 25,...,48

def main():

    pris_dag1 = priser.loc[1:24, "s1"].to_dict()

    pris_dag2 = {
        s: priser.loc[25:48, s].to_dict()
        for s in scenarioer
    }

    solver = pyo.SolverFactory("gurobi")

    if not solver.available(exception_flag=False):
        raise RuntimeError("Gurobi er ikke tilgjengelig.")

    relativ_toleranse = 1e-6
    absolutt_toleranse = 1e-4

    beste, historikk = los_benders(
        pris_dag1,
        pris_dag2,
        sannsynlighet,
        solver,
        relativ_toleranse=relativ_toleranse,
        absolutt_toleranse=absolutt_toleranse
    )

    # 9. Løs den eksisterende Part-2-modellen som referanse.
    #
    # Samme priser, sannsynligheter og batteriparametere brukes.

    referanse = lag_modell(
        pris_dag1, pris_dag2, sannsynlighet
    )
    los_modell(referanse, solver)

    referanse_total = pyo.value(referanse.profitt)

    referanse_dag1 = sum(
        pris_dag1[t]
        * (
            pyo.value(referanse.utlading[t])
            - pyo.value(referanse.lading[t])
        )
        * b.delta_t
        for t in referanse.T1
    )

    sammenligning = pd.DataFrame([
        {
            "metode": "Benders",
            "totalprofitt_EUR": beste["totalprofitt"],
            "dag1_EUR": beste["profitt_dag1"],
            "forventet_dag2_EUR": beste["profitt_dag2"],
            "E24_MWh": beste["E24"]
        },
        {
            "metode": "Stokastisk Part 2",
            "totalprofitt_EUR": referanse_total,
            "dag1_EUR": referanse_dag1,
            "forventet_dag2_EUR": referanse_total - referanse_dag1,
            "E24_MWh": pyo.value(referanse.energi[24])
        }
    ])

    print("\nSammenligning med Part 2:")
    print(sammenligning.round(6).to_string(index=False))

    # 10. Sammenlign alle førstetrinnsbeslutningene.

    timeplan = beste["timeplan"].copy()

    for navn, variabel in [
        ("lading", referanse.lading),
        ("utlading", referanse.utlading),
        ("energi", referanse.energi)
    ]:
        enhet = "MWh" if navn == "energi" else "MW"

        timeplan[f"{navn}_Part2_{enhet}"] = [
            pyo.value(variabel[t])
            for t in referanse.T1
        ]

    print("\nFørstetrinnsplaner:")
    print(timeplan.round(6).to_string(index=False))

    forskjell = abs(beste["totalprofitt"] - referanse_total)

    tillatt_forskjell = (
        absolutt_toleranse
        + relativ_toleranse * max(1.0, abs(referanse_total))
        + 1e-6
    )

    print(f"\nObjektivforskjell: {forskjell:.8f} EUR")

    if forskjell > tillatt_forskjell:
        raise RuntimeError(
            "Benders og Part 2 avviker mer enn toleransen."
        )

    print("Objektivverdiene samsvarer innen toleransen.")

    # 11. Lagre resultatene i en egen mappe.

    resultatmappe = Path(__file__).resolve().parent / "benders_resultater"
    resultatmappe.mkdir(exist_ok=True)

    historikk.to_csv(
        resultatmappe / "konvergens.csv",
        index=False
    )

    sammenligning.to_csv(
        resultatmappe / "sammenligning.csv",
        index=False
    )

    timeplan.to_csv(
        resultatmappe / "forstetrinn.csv",
        index=False
    )

    print(f"\nResultater lagret i: {resultatmappe}")


if __name__ == "__main__":
    main()