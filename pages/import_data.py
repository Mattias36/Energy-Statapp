# pages/import_data.py

# jak skompilować:
# python manage.py shell
# (w shellu)
# from pages import import_data
# import_data.run()
# quit() - po zmianach w kodzie trzeba dać quit i uruchomić od nowa

import os
import django


def run():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'Energy_Statistic_App.settings')
    django.setup()

    from pages.models import Country, EnergyDomain, EnergyCategory, EnergySource, EnergyData
    import pandas as pd

    file_path = r'data\Energy statistical country datasheets 2024-04 for web.xlsx'
    df = pd.read_excel(file_path,
                       sheet_name='CZ', skiprows=7, usecols=range(2, 35), header=None)  # zmiana sheet name na jakiś z arkusza

    years = df.iloc[0, 1:].astype(int).tolist()
    df = df[4:].copy()
    df.reset_index(drop=True, inplace=True)
    df.columns = ['source'] + years

    # Znajdź początek kategorii "Production"
    start_index = df[df['source'] == 'Production'].index[0]

    # Znajdź pierwszy pusty wiersz po "Production"
    end_index = start_index
    for i in range(start_index + 1, len(df)):
        if pd.isna(df.loc[i, 'source']):
            break
        end_index = i

    # Wytnij tylko dane z Production
    df = df.loc[start_index:end_index].copy()
    df.reset_index(drop=True, inplace=True)

    # Kraj – poprawka na kod
    country, created = Country.objects.get_or_create(
        name='Czechia')  # tu zmienić na kraj
    if created or not country.code:
        country.code = 'CZ'  # tu na kod kraju
        country.save()

    domain, _ = EnergyDomain.objects.get_or_create(
        name='Energy Balance')  # nazwa domeny
    category, _ = EnergyCategory.objects.get_or_create(
        name='Production', domain=domain)  # nazwa kategorii

    hierarchy = {
        "Solid fossil fuels": ["of which hard coal", "of which brown coal"],
        "Oil and petroleum products": ["of which crude oil and NGL"],
        "Renewables and biofuels": [
            "Hydro", "Wind", "Solar photovoltaic", "Solar thermal", "Solid biofuels", "Biogases", "Liquid biofuels"
        ]
    }

    parent_source = None

    for idx, row in df.iterrows():
        name = str(row['source']).strip()

        if name == "Production":
            continue

        values_only = row[1:].dropna()
        if values_only.empty:
            break

        # sprawdzanie czy to podźródło
        is_subsource = False
        for parent, children in hierarchy.items():
            if name in children:
                is_subsource = True
                break

        if is_subsource:
            print(f'  ⨯ Pominięto podźródło: {name}')
            continue  # POMIJAMY dodawanie podźródeł

        # tworzenie głównego źródła
        source, _ = EnergySource.objects.get_or_create(
            name=name,
            category=category,
            parent=None,
            defaults={"unit": "Mtoe"}
        )
        print(f'✓ Główne źródło: {name}')

        for year in years:
            value = row[year]
            if pd.notnull(value):
                EnergyData.objects.get_or_create(
                    country=country,
                    source=source,
                    year=year,
                    value=value,
                    category=category
                )
