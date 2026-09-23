import requests
import pandas as pd
import time
from datetime import date, timedelta

area = "NO2"
year = 2025

start_date = date(year, 1, 1)
end_date = date(year, 12, 31)

all_prices = []
failed_days = []

current_date = start_date
while current_date <= end_date:
    month = current_date.month
    day = current_date.day
    url = f"https://www.hvakosterstrommen.no/api/v1/prices/{year}/{month:02d}-{day:02d}_{area}.json"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        all_prices.extend(data)
    except requests.exceptions.RequestException as e:
        print(f"Feil ved henting av {current_date}: {e}")
        failed_days.append(current_date)

    current_date += timedelta(days=1)
    time.sleep(0.1)  # liten pause for å ikke overbelaste APIet

df = pd.DataFrame(all_prices)
df.to_csv("NO2_2025.csv", index=False)

print(f"Hentet {len(df)} timesverdier ({len(df)//24} dager) for {area} i {year}")
if failed_days:
    print(f"Feilet for {len(failed_days)} dager: {failed_days}")