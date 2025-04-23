from django.shortcuts import render
from .models import EnergyData, Country, EnergyCategory
from django.http import JsonResponse
from collections import defaultdict

def home(request):
    selected_country_code = request.GET.get('country')  # UWAGA: teraz bez domyślnego 'PL'
    countries = Country.objects.all()

    table = {}
    years = []
    total_by_year = {}

    if selected_country_code:  # tylko jak ktoś wybrał kraj
        data = EnergyData.objects.select_related(
            'source', 'country', 'category'
        ).filter(country__code=selected_country_code, category__name='Production')

        from collections import defaultdict
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

    context = {
        'countries': countries,
        'selected_country': selected_country_code,
        'table': table,
        'years': years,
        'total_by_year': total_by_year,
        'total_years': [y for y in years if y in total_by_year],
        'total_values': [round(total_by_year[y], 3) for y in years if y in total_by_year],
    }
    return render(request, "pages/home.html", context)

# funkcjonalnosc home() przeniesiono w country_view().
from utils.stats import get_latest_value, get_trend_percentage, format_gas_trend, format_nuclear_status
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
        # full name for details.html "selected_country" par.
        'selected_country': selected_country.name,
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
    return render(request, "pages/details.html", context)

# ?+ jesli wszystkie wiersze w tabeli sa puste nie wyswietlac caly wiersz
def compare_data(request):
    country_codes = request.GET.getlist('countries[]')
    category_name = 'Production'

    response_data = []

    for code in country_codes:
        country = Country.objects.get(code=code)
        data = EnergyData.objects.select_related('source', 'country', 'category') \
            .filter(country__code=code, category__name=category_name)

        total_by_year = {}
        for record in data:
            total_by_year[record.year] = total_by_year.get(record.year, 0) + record.value

        sorted_years = sorted(total_by_year.keys())
        sorted_values = [round(total_by_year[y], 3) for y in sorted_years]

        response_data.append({
            'name': country.name,
            'total_values': sorted_values
        })

    return JsonResponse(response_data, safe=False)