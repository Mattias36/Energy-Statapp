from django.shortcuts import render
from .models import EnergyData, Country, EnergyCategory, EnergyDomain
from django.http import JsonResponse
from collections import defaultdict
from utils.stats import get_latest_value, get_trend_percentage, format_gas_trend, format_nuclear_status, get_countryinfo
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from utils.stats_average import stats_average
from utils.predictions import predict_future_usage, format_future_usage
from django.core.serializers.json import DjangoJSONEncoder
import random
import json

def home(request):
    
    top6_by_year = {}

    for year in range(2021, 1999, -1):
        top6 = (
            EnergyData.objects
            .filter(
                category__domain__name="Energy Balance",
                category__name="Production",
                year=year
            )
            .values('country__code', 'country__name')
            .annotate(total_value=Sum('value'))
            .order_by('-total_value')[:6]
        )
        top6_by_year[year] = [
            {
                'code': row['country__code'],
                'name': row['country__name'],
                'rank': i + 1,
                'value': round(row['total_value'], 2)
            }
            for i, row in enumerate(top6)
        ]

    # dane do wykresu (losowo 10 krajów)
    countries = list(Country.objects.values_list('name', flat=True))
    selected = random.sample(countries, min(10, len(countries)))
    data_by_country = {}

    for country in selected:
        values = (
            EnergyData.objects
            .filter(
                country__name=country,
                category__name="Final energy consumption"
            )
            .order_by('year')
            .values('year', 'value')
        )
        data_by_country[country] = {v['year']: v['value'] for v in values}

    chart_data = {
        "countries": selected,
        "data_by_country": data_by_country
    }

    return render(request, "pages/home.html", {
        'top6_by_year': json.dumps(top6_by_year, cls=DjangoJSONEncoder),
        'chart_data': json.dumps(chart_data, cls=DjangoJSONEncoder)
    })

def about_us(request):
    selected_country_code = request.GET.get('country')
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
    return render(request, "pages/about_us.html", context)

def categories(request):
    categories = EnergyCategory.objects.all()
    return render(request, "pages/categories.html", {
        'categories': categories
    })

CATEGORY_DESCRIPTIONS = {
    "Production": (
        "The 'Production' category reflects the total amount of energy generated within a country "
        "from all available sources. It includes energy derived from fossil fuels (like coal, oil, and gas), "
        "renewable sources (such as wind, solar, hydro), and nuclear power. This metric is crucial for understanding "
        "a country's self-sufficiency in energy generation and its reliance on domestic versus imported energy sources."
    ),
    "Final energy consumption": (
        "This category provides insight into the total amount of energy consumed by end users in different sectors, "
        "including households, transportation, industry, services, and agriculture. Unlike gross consumption, it excludes "
        "energy losses during transformation and transmission. Understanding final consumption helps identify which sectors "
        "are the most energy-intensive and where efficiency improvements can have the greatest impact."
    ),
    "Gross Electricity Generation, by Fuel  [TWh]": (
        "This dataset presents the total electricity produced in a country, broken down by the type of fuel used "
        "in the generation process. It includes electricity from conventional sources such as coal, natural gas, and nuclear, "
        "as well as from renewable sources like wind, solar, and biomass. Analyzing this data reveals a country’s energy mix "
        "and its progress towards sustainable and low-carbon electricity generation."
    ),
    "Gross Heat Generation [PJ]": (
        "The 'Gross Heat Generation' category captures the total heat produced primarily in combined heat and power (CHP) "
        "plants and heat-only boiler stations. It reflects the energy generated for heating purposes across residential, "
        "commercial, and industrial buildings. Monitoring this data is essential for understanding thermal energy needs "
        "and the role of district heating systems in national energy infrastructure."
    )
}

def category_detail(request, category_id):
    category = get_object_or_404(EnergyCategory, id=category_id)
    countries = Country.objects.filter(energydata__category=category).distinct()

    description = CATEGORY_DESCRIPTIONS.get(category.name, "This category provides detailed energy data.")

    return render(request, "pages/category_detail.html", {
        "category": category,
        "countries": countries,
        "category_description": description
    })

def country_view(request, country_code):
    countries = Country.objects.all()
    selected_country = Country.objects.get(code=country_code)
    # Pobranie wybranej kategorii z GET, domyślnie "Production"
    category_id = request.GET.get("category")
    if category_id:
        selected_category = get_object_or_404(EnergyCategory, id=category_id)
    else:
        selected_category = EnergyCategory.objects.get(name="Production")

    data = EnergyData.objects.select_related(
        'source', 'country', 'category'
    ).filter(country__code=country_code, category=selected_category)


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
        'selected_country_code': selected_country.code,
        'selected_category': data[0].category if data else None,
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

    future_usage_raw = format_future_usage(data)
    future_usage_fixed = {}

    for source, info in future_usage_raw.items():
        predictions = info.get('predictions', {})
        fixed_predictions = {int(year): val for year, val in predictions.items()}
        future_usage_fixed[source] = {
            **info,
            'predictions': fixed_predictions
        }

    context.update({
        'future_usage': future_usage_fixed,
    })

    wiki_info = get_countryinfo(selected_country.name)
    context.update({
        'wiki_info': wiki_info
    })

    category_name = selected_category.name.lower()
    category_explanation = ""

    if "final energy consumption" in category_name:
        category_explanation = "Final Energy Consumption refers to the total energy consumed by end users like households, industry, and transportation."
    elif "gross electricity generation" in category_name:
        category_explanation = "Gross Electricity Generation includes all the electricity produced by power plants before subtracting the energy used by the plant itself."
    elif "gross heat generation" in category_name:
        category_explanation = (
            "Gross Heat Generation refers to the total heat output by thermal systems for district heating or industrial purposes. "
            "You can explore this data visually in the heatmap below."
        )

    context.update({
        'category_explanation': category_explanation,
    })

    category_name = selected_category.name.lower()

    if selected_category.pk == 12:
        generation_data_qs = EnergyData.objects.filter(
            country__code=country_code,
            category=selected_category
        ).select_related('source')

        raw_data = defaultdict(dict)
        years_set = set()

        for record in generation_data_qs:
            raw_data[record.source.name][record.year] = record.value
            years_set.add(record.year)

        generation_years = sorted(years_set)
        latest_year = max(generation_years)

        # ostatni rok w PIECHART, w trend graphie wszystkie
        latest_year_data = {
            fuel: values.get(latest_year, 0)
            for fuel, values in raw_data.items()
        }

        # by valuee
        sorted_data = sorted(latest_year_data.items(), key=lambda x: x[1], reverse=True)

        # top7 + everything else -- other
        top7 = sorted_data[:7]
        other_total = sum(value for _, value in sorted_data[7:])

        total = sum(value for _, value in top7) + other_total

        percentage_data = {}
        for year in generation_years:
            year_data = {
                fuel: raw_data[fuel].get(year, 0)
                for fuel in raw_data
            }

            sorted_data = sorted(year_data.items(), key=lambda x: x[1], reverse=True)
            top7 = sorted_data[:7]
            other_total = sum(val for _, val in sorted_data[7:])
            total = sum(val for _, val in top7) + other_total

            for fuel, val in top7:
                percentage_data.setdefault(fuel, {})[year] = round((val / total) * 100, 2)

            if other_total > 0:
                percentage_data.setdefault("Other", {})[year] = round((other_total / total) * 100, 2)

        context.update({
            'generation_data': percentage_data,
            'generation_years': generation_years,
        })

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

def heatmap_data_view(request):
    year = int(request.GET.get("year", 2020))

    try:
        category = EnergyCategory.objects.get(name="Gross Heat Generation [PJ]")
    except EnergyCategory.DoesNotExist:
        return JsonResponse({})

    data = {}
    for country in Country.objects.all():
        total = EnergyData.objects.filter(
            country=country,
            category=category,
            year=year
        ).aggregate(sum=Sum('value'))['sum']
        if total is not None:
            data[country.code] = round(total, 2)  # <--- użyj code, nie name

    return JsonResponse(data)

def heatmap_page_view(request):
    return render(request, "pages/heatmap.html")


def heat_insight_view(request, country_code):
    year = int(request.GET.get("year", 2020))

    try:
        category = EnergyCategory.objects.get(name="Gross Heat Generation [PJ]")
    except EnergyCategory.DoesNotExist:
        return JsonResponse({"error": "Category not found"}, status=404)

    # total heat descending
    ranking_qs = EnergyData.objects.filter(category=category, year=year).values(
        'country__name', 'country__code').annotate(total_heat=Sum('value')).order_by('-total_heat')

    ranking = list(ranking_qs)

    #  index of requested country
    index = next((i for i, entry in enumerate(ranking) if entry['country__code'] == country_code), None)
    if index is None:
        return JsonResponse({"error": "Country data not found in ranking"}, status=404)

    top_3 = ranking[:3]

    neighbors_count = 2
    start = max(3, index - neighbors_count)
    end = index + neighbors_count + 1
    neighbors = ranking[start:end]
    neighbors = [n for n in neighbors if n not in top_3]

    country_entry = ranking[index]

    # rank to all entries ---> list rank
    full_list = []
    for i, entry in enumerate(ranking):
        full_list.append({
            'rank': i + 1,
            'country__name': entry['country__name'],
            'country__code': entry['country__code'],
            'total_heat': entry['total_heat'],
        })

    # Insight text
    country_total = country_entry['total_heat']
    insight = (
        f"In {year}, {country_entry['country__name']} generated {round(country_total, 2)} PJ of heat energy. "
        f"It ranks {index + 1} among all countries in this category."
    )

    return JsonResponse({
        "year": year,
        "category": category.name,
        "insight": insight,
        "ranking": {
            "top_3": top_3,
            "country_index": index + 1,
            "country_entry": country_entry,
            "neighbors": neighbors,
            "full_list": full_list,
        }
    })


def rankings_view(request):
    categories = EnergyCategory.objects.all()
    selected_id = request.GET.get("category_id")
    selected_year = request.GET.get("year", "summary")  # "summary" = sumaryczne 2000–2021
    rankings = []
    unit = None

    if selected_id:
        try:
            selected_category = EnergyCategory.objects.get(id=selected_id)
        except EnergyCategory.DoesNotExist:
            selected_category = None
    else:
        selected_category = EnergyCategory.objects.filter(name__iexact="Production").first()
        selected_id = selected_category.id if selected_category else None

    if selected_category:
        unit_map = {
            "Production": "Mtoe",
            "Final energy consumption": "Mtoe",
            "Gross Electricity Generation, by Fuel  [TWh]": "TWh",
            "Gross Heat Generation [PJ]": "PJ"
        }
        unit = unit_map.get(selected_category.name, "")

        queryset = EnergyData.objects.filter(category=selected_category)
        if selected_year != "summary":
            queryset = queryset.filter(year=int(selected_year))

        data = (
            queryset
            .values("country__name", "country__code")
            .annotate(total=Sum("value"))
            .order_by("-total")
        )
        rankings = [
            {
                "name": entry["country__name"],
                "code": entry["country__code"],
                "total": entry["total"]
            }
            for entry in data
        ]

    return render(request, "pages/rankings.html", {
        "categories": categories,
        "selected_category": selected_category,
        "unit": unit,
        "rankings": rankings,
        "selected_year": selected_year,
        "year_range": list(range(2021, 1999, -1))
    })
