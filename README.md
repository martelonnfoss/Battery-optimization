# Battery optimization

Vi planlegger lading og utlading av et batteri med usikre strømpriser på dag 2. Del 2 sammenligner tre måter å bruke prisdataene på. Del 3 løser den stokastiske modellen med Benders-dekomponering.


## Gjenskap resultatene

De ferdige prisfilene ligger i `data/clean_data/`. For å lage dem på nytt fra rådata, kjør `clean_data_day_ahead.py`, `find_average_day.py` og `find_scenario_days.py` i den rekkefølgen fra `data_prep/`.

```text
python modell/part2/forventet_verdi.py
python modell/part2/ett_scenario.py
python modell/part2/stokastisk.py
python modell/part3/benders.py
```

- `forventet_verdi.py` løser modellen med gjennomsnittsprisen for hver time på dag 2.
- `ett_scenario.py` løser modellen med én kjent prisbane. Sett `scenario` til henholdsvis `s1`, `s2`, `s3`, `s4` og `s5`, og kjør skriptet én gang for hver verdi.
- `stokastisk.py` løser alle fem scenarioene sammen med én felles plan for dag 1.
- `benders.py` løser den stokastiske modellen med Benders og sammenligner med løsningen fra del 2. Begge gir en forventet fortjeneste på 8 123,24 euro.

Del 2 skriver resultater til `modell/part2/`. Benders skriver sammenligningen, timeplanene og konvergensen til `modell/part3/benders_resultater/`.


