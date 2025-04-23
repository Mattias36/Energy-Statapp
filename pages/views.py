from django.shortcuts import render
from .models import EnergyData, Country

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
