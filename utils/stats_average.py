# utils/stats_average.py

from collections import defaultdict
from pages.models import EnergyData, Country, EnergyCategory
from django.db.models import Max

def stats_average():
    """
    Oblicza średnie wartości produkcji energii dla kraj + kategoria zrodla energii.
    Zwraca strukturę zawierającą miejsce danego kraju w każdej kategorii.

    return 'Nuclear': {'rank': , 'average': , 'value': , 'total_countries': }
    """
    category = EnergyCategory.objects.get(name="Production")
    data = EnergyData.objects.select_related('country', 'source', 'category').filter(category=category)

    latest_year = data.aggregate(Max("year"))["year__max"]
    country_totals = defaultdict(float)
    source_shares = defaultdict(list)

    # country_model - jedno data entry (country)
    # count avg, tez dodac nie dla share a dla wejsciowych danych
    for country_model in data.filter(year=latest_year):
        country = country_model.country
        source = country_model.source.name
        value = country_model.value

        country_totals[country.name] += value

    for country_model in data.filter(year=latest_year):
        country = country_model.country
        source = country_model.source.name
        value = country_model.value

        total = country_totals[country.name]
        if total > 0:
            share = (value / total) * 100
            source_shares[source].append((country.name, round(share, 2)))

    # Teraz ranking
    rankings = {}

    for source, entries in source_shares.items():
        sorted_entries = sorted(entries, key=lambda x: x[1], reverse=True)
        rankings[source] = [
            {
                "country": country,
                "share_percent": percent,
                "rank": i + 1,
                "of": len(sorted_entries),
                "average": round(sum(p for _, p in entries) / len(entries), 2)
            }
            for i, (country, percent) in enumerate(sorted_entries)
        ]

    return rankings
