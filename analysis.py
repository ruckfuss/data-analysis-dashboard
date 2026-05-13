# analysis.py
import pandas as pd
import requests

def fetch_data():
    url = "https://disease.sh/v3/covid-19/countries"
    data = requests.get(url).json()
    return pd.DataFrame([{
        "country": c["country"],
        "cases": c["cases"],
        "deaths": c["deaths"],
        "population": c["population"],
        "death_rate": round(c["deaths"]/c["cases"]*100, 2) if c["cases"] > 0 else 0
    } for c in data])

if __name__ == "__main__":
    df = fetch_data()
    print("=== GLOBAL SUMMARY ===")
    print(f"Total countries: {len(df)}")
    print(f"Total cases: {df['cases'].sum():,}")
    print(f"Total deaths: {df['deaths'].sum():,}")
    print(f"Average death rate: {df['death_rate'].mean():.2f}%")
    print(f"Highest death rate: {df.nlargest(1,'death_rate')[['country','death_rate']].to_string(index=False)}")
    print(f"Most cases: {df.nlargest(1,'cases')[['country','cases']].to_string(index=False)}")