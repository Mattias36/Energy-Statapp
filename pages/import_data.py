# pages/import_data.py

# jak skompilować:
# python manage.py shell
# from pages import import_data
# import_data.run()
# quit() - po zmianach w kodzie trzeba dać quit i uruchomić od nowa

import os
import django

def run():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Energy_Statistic_App.settings')
    django.setup()

    from pages.models import Country, EnergyDomain, EnergyCategory, EnergySource, EnergyData
    import pandas as pd

    FILE_PATH = r'data\Energy statistical country datasheets 2024-04 for web.xlsx'
    SKIP_SHEETS = ["Contents", "footnotes and sources", "energy flows-energy balances", "energy products-energy balances", "EU27_2020"]
    VALID_YEARS = list(range(2000, 2022))
    hierarchy = {
        "Solid fossil fuels": ["of which hard coal", "of which brown coal"],
        "Oil and petroleum products": ["of which crude oil and NGL"],
        "Renewables and biofuels": [
            "Hydro", "Wind", "Solar photovoltaic", "Solar thermal", "Solid biofuels", "Biogases", "Liquid biofuels"
        ]
    }


    # skip_sources = [
    #     "of which hard coal", "of which brown coal", "Solar thermal",
    #     "Geothermal", "Solid biofuels and renewable waste", "Biogases",
    #     "Liquid biofuels", "Ambient heat (from heat pumps)",
    #     "Iron and steel", "Chemical and petrochemical", "Non-ferrous metals",
    #     "Non-metallic minerals", "Mining and quarrying", "Food, beverages and tobacco",
    #     "Textile and leather", "Paper, pulp and print", "Transport equipment",
    #     "Machinery", "Wood and wood products", "Construction", "Other industry",
    #     "Rail", "Road", "Domestic aviation", "Domestic navigation",
    #     "Pipeline transport", "Other transport", "by Fuel/Product", "by Sector"
    # ]

    # skip_sources_electricity = [
    # "of which hard coal", "of which brown coal", "of which natural gas",
    # "Hydro", "Wind", "Solid biofuels and renewable wastes", "Biogases",
    # "Liquid biofuels", "Solar", "Geothermal", "Tide, Wave and Ocean",
    # "by fuel/product", "by type of generation"
    # ]

    skip_sources_heat = [
        "of which hard coal", "of which brown coal", "of which natural gas",
        "Solid biofuels and renewable wastes", "Biogases", "Liquid biofuels",
        "Solar thermal", "Geothermal", "Ambient heat",
        "by fuel/product"
    ]


    xls = pd.ExcelFile(FILE_PATH)
    for sheet in xls.sheet_names:
        if sheet in SKIP_SHEETS:
            continue

        try:
            meta_df = pd.read_excel(FILE_PATH, sheet_name=sheet, usecols="D", nrows=5, header=None)
            country_name = str(meta_df.iloc[4, 0]).strip()
        except Exception as e:
            print(f"⨯ Nie udało się pobrać kraju z {sheet}: {e}")
            continue

        country, _ = Country.objects.get_or_create(name=country_name)
        country.code = sheet
        country.save()

        df = pd.read_excel(FILE_PATH, sheet_name=sheet, skiprows=7, usecols=range(2, 35), header=None)
        years = df.iloc[0, 1:].tolist()
        year_map = {i+1: int(y) for i, y in enumerate(years) if pd.notnull(y) and int(y) in VALID_YEARS}
        df = df[4:].copy()
        columns = ['source'] + [year for year in year_map.values()]
        df = df.iloc[:, :len(columns)]
        df.columns = columns
       

        if "Gross Heat Generation [PJ]" not in df["source"].values:
            continue
        
        match_index = df[df["source"].astype(str).str.strip() == "Gross Heat Generation [PJ]"].index
        if match_index.empty:
            continue
        start_index = match_index[0]
        end_index = start_index
    
        for i in range(start_index + 1, len(df)):
            raw_name = df.loc[i, "source"]
            if pd.isna(raw_name):
                break  # kończymy tylko gdy puste pole
            name = str(raw_name).strip()
            if name in skip_sources_heat:
                continue
            end_index = i
    
        data_section = df.loc[start_index + 1:end_index].copy().reset_index(drop=True)
    
        domain, _ = EnergyDomain.objects.get_or_create(name="Heat Production (Heat Sold)")
        category, _ = EnergyCategory.objects.get_or_create(name="Gross Heat Generation [PJ]", domain=domain)
    
        for _, row in data_section.iterrows():
            source_name = str(row["source"]).strip()
            if not source_name or source_name in skip_sources_heat:
                print(f"  ⨯ Pominięto podźródło: {source_name}")
                continue
            
            source, _ = EnergySource.objects.get_or_create(
                name=source_name, category=category, parent=None, defaults={"unit": "PJ"}
            )
            print(f"✓ {country_name} - Heat Production - {category.name}: {source_name}")
    
            for year in year_map.values():
                value = row.get(year, None)
                if pd.notnull(value):
                    EnergyData.objects.get_or_create(
                        country=country,
                        source=source,
                        year=year,
                        value=value,
                        category=category
                    )