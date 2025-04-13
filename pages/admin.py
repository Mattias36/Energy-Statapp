from django.contrib import admin
from .models import Country, EnergyDomain, EnergyCategory, EnergySource, EnergyData

admin.site.register(Country)
admin.site.register(EnergyDomain)
admin.site.register(EnergyCategory)
admin.site.register(EnergySource)
admin.site.register(EnergyData)
