from django.shortcuts import render
from .models import EnergyData, Country, EnergyCategory
from django.http import JsonResponse

def home(request):
    countries = Country.objects.all()
    categories = EnergyCategory.objects.all()
    selected_category_id = request.GET.get('category')

    try:
        selected_category_id = int(
            selected_category_id) if selected_category_id else None
    except (TypeError, ValueError):
        selected_category_id = None
   
    context = {
        'countries': countries,
        'categories': categories,
        'selected_category_id': selected_category_id,
    }
    return render(request, "pages/home.html", context)

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
        # full name for details.html "selected_country" par.
        'selected_country': selected_country.name,
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
def compare_data(request):
    country_codes = request.GET.getlist('countries[]')
    category_name = 'Production'

    response_data = {}

    for code in country_codes:
        country = Country.objects.get(code=code)
        data = EnergyData.objects.select_related('source', 'country', 'category') \
            .filter(country__code=code, category__name=category_name)

        total_by_year = {}
        for record in data:
            total_by_year[record.year] = total_by_year.get(record.year, 0) + record.value

        sorted_years = sorted(total_by_year.keys())
        sorted_values = [round(total_by_year[y], 3) for y in sorted_years]

        response_data[country.name] = {
            'years': sorted_years,
            'values': sorted_values
        }

    return JsonResponse(response_data)