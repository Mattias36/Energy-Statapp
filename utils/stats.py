# Plik z funkcjami pomocniczymi do analizy danych energetycznych (w folderze funkcji pomocniczych utils)
import requests
# colors, cz.kodu, etc.
from django.utils.html import format_html

def get_latest_value(data, source_name):
    #  zwraca najnowsza wartosc dla danego zrodla
    values = [(d.year, d.value) for d in data if d.source.name == source_name]
    if not values:
        return None, None
    return values[-1]    # jesli tabela posortowana, jesli nie sorted to ew przeciazyc funkcje

def get_trend_percentage(data, source_name):
    # pomocnicza w ocenie trendu dla kazdego zrodla
    # trend % pomiędzy pierwszym a ostatnim rokiem dla danego zrodla
    # +? dodanie przeciazenia: trend w zakresie wybranym
    values = sorted([(d.year, d.value) for d in data if d.source.name == source_name])
    if len(values) < 2:
        return None
    start, end = values[0][1], values[-1][1] # pierwszy, ostatni
    if start == 0:
        return None
    return round(((end - start) / start) * 100, 2)


def format_nuclear_status(latest_value, total_energy_value):
    #Jeśli brakuje danych lub total = 0, zwracamy info
    if latest_value is None or total_energy_value in (None, 0):
        return format_html('<span style="color:gray;">No data available</span>')

    # procentowy udzial energii jadrowej
    nuclear_percentage = (latest_value / total_energy_value) * 100 if total_energy_value else 0
    if nuclear_percentage > 10:
        return format_html(
            '<span style="color:green;">Good ({}%)</span>',
            f"{nuclear_percentage:.2f}"
        )
    else:
        return format_html(
            '<span style="color:red;">Poor ({}%)</span>',
            f"{nuclear_percentage:.2f}"
        )

def format_gas_trend(trend):
    return format_html(
        '<span style="color:{};">{}%</span>',
        "green" if trend and trend > 0 else "red",
        trend if trend is not None else "–"
    )
# +? format dla innych funkcji, wartosci thresholds porownujace cala europe i formatowanie na ich podstawie,
# profil uzytkownika na ktorym wybiera parametry istotne do wyswietlenia


def get_countryinfo(country_name):
    ''' return dla polski rzedu:
    1. get https://en.wikipedia.org/api/rest_v1/page/summary/Poland
    2. jesli ok(200) - title, description (Country in Central Europe), summary (wiekszy opis), flaga, '''
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{country_name}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            'title': data.get('title'),
            'description': data.get('description'),
            'summary': data.get('extract'),
            'thumbnail': data.get('thumbnail', {}).get('source'),
            'content_urls': data.get('content_urls', {}).get('desktop', {}).get('page'),
        }
    return None
# proponuje filter tagow by wyswietlac info bezposrednio o energetyce jesli jest na stronie
