from django.shortcuts import render
from .models import EnergyData, Country
from collections import defaultdict

def home(request):
    countries = Country.objects.all()
    return render(request, "pages/home.html", {'countries': countries})

# funkcjonalnosc home() przeniesiono w country_view().
from utils.stats import get_latest_value, get_trend_percentage, format_gas_trend, format_nuclear_status
from utils.stats_average import stats_average
from utils.predictions import predict_future_usage, format_future_usage

def country_view(request, country_code):
    countries = Country.objects.all()
    selected_country = Country.objects.get(code=country_code)

    data = EnergyData.objects.select_related(
        'source', 'country', 'category'
    ).filter(country__code=country_code, category__name='Production')

    table = {}
    years = sorted(set(d.year for d in data))
    for record in data:
        source = record.source.name
        year = record.year
        value = record.value
        if source not in table:
            table[source] = {}
        table[source][year] = value

    total_by_year = defaultdict(float)
    for record in data:
        total_by_year[record.year] += record.value

    # get_lates_value zwraca (year, value), dlatego "_" --> year jesli trzeba
    _, nuclear_latest = get_latest_value(data, "Nuclear")
    nuclear_status = format_nuclear_status(nuclear_latest, total_by_year.get(years[-1], 0))

    gas_trend = get_trend_percentage(data, "Natural gas")
    gas_status = format_gas_trend(gas_trend)

    _, renewable_total = get_latest_value(data, "Renewables and biofuels")
    _, waste_total = get_latest_value(data, "Wastes, Non-Renewable")

    context = {
        'countries': countries,
        'selected_country': selected_country.name, # full name for details.html "selected_country" par.
        'table': table,
        'years': years,
        'total_by_year': total_by_year,
        'total_years': [y for y in years if y in total_by_year],
        'total_values': [round(total_by_year[y], 3) for y in years if y in total_by_year],
        'graph_type': request.GET.get('graph_type', 'bar'),
        'year_range': request.GET.get('year_range'),
        # ewentualnie mozna przeniesiesc Insights (nuclear_status, gas_status, etc.) do osobnego kontekstu lub struktury
        'nuclear_status': nuclear_status,
        'gas_status': gas_status,
        'renewable_total': round(renewable_total or 0, 3),
        'waste_total': round(waste_total or 0, 3),
    }

    averages_by_source = stats_average()
    country_rankings = {
        source: next((entry for entry in entries if entry["country"] == selected_country.name), None)
        for source, entries in averages_by_source.items()
    }

    context.update({
        "country_rankings": country_rankings,
    })

    future_usage = format_future_usage(data)

    context.update({
        'future_usage': future_usage,
    })

    return render(request, "pages/details.html", context)

# ?+ jesli wszystkie wiersze w tabeli sa puste nie wyswietlac caly wiersz
