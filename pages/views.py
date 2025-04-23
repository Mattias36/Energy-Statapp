from django.shortcuts import render
from .models import EnergyData, Country


def home(request):
    countries = Country.objects.all()
    return render(request, "pages/home.html", {'countries': countries})

# funkcjonalnosc home() przeniesiono w country_view().
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

    from collections import defaultdict
    total_by_year = defaultdict(float)
    for record in data:
        total_by_year[record.year] += record.value

    # param for graph
    graph_type = request.GET.get('graph_type', 'bar')  # 'bar' -- default
    year_range = request.GET.get('year_range', None)

    if year_range:
        year_range = list(map(int, year_range.split(',')))
        data = [d for d in data if d.year in year_range]

    context = {
        'countries': countries,
        'selected_country': selected_country.name, # full name for details.html "selected_country" par.
        'table': table,
        'years': years,
        'total_by_year': total_by_year,
        'total_years': [y for y in years if y in total_by_year],
        'total_values': [round(total_by_year[y], 3) for y in years if y in total_by_year],
        'graph_type': graph_type,
        'year_range': year_range,
    }
    return render(request, "pages/details.html", context)

# ?+ jesli wszystkie wiersze w tabeli sa puste nie wyswietlac caly wiersz

