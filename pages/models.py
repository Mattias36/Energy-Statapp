from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name


class EnergyDomain(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Energy Domain"
        verbose_name_plural = "Energy Domains"

    def __str__(self):
        return self.name


class EnergyCategory(models.Model):
    domain = models.ForeignKey(
        EnergyDomain, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Energy Category"
        verbose_name_plural = "Energy Categories"

    def __str__(self):
        return f"{self.domain.name} - {self.name}"


class EnergySource(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)
    category = models.ForeignKey(
        EnergyCategory, on_delete=models.CASCADE, related_name='sources')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subsources')

    class Meta:
        verbose_name = "Energy Source"
        verbose_name_plural = "Energy Sources"

    def __str__(self):
        return f"{self.name} ({self.unit})"


class EnergyData(models.Model):
    country = models.ForeignKey(
        Country, on_delete=models.CASCADE)
    source = models.ForeignKey(
        EnergySource, on_delete=models.CASCADE)
    category = models.ForeignKey(
        EnergyCategory, on_delete=models.CASCADE)
    year = models.IntegerField()
    value = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Energy Data"
        verbose_name_plural = "Energy Data"

    def __str__(self):
        return f"{self.country.code} | {self.source.name} | {self.year}: {self.value}"
