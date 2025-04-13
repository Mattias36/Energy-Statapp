from django.shortcuts import render
from .models import EnergyData
# Create your views here.


def home(request):
    latest_year = EnergyData.objects.order_by('-year').first().year
    data = EnergyData.objects.filter(
        year=latest_year).select_related('source', 'country')

    context = {
        'year': latest_year,
        'data': data,
    }
    return render(request, "pages/home.html", context)
